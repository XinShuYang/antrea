// Copyright 2026 Antrea Authors
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package e2e

import (
	"context"
	"fmt"
	"net"
	"sync"
	"testing"
	"time"

	"github.com/stretchr/testify/require"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/resource"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/util/wait"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/util/retry"
)

type PodRecoveryResult struct {
	PodName              string
	NodeName             string
	ErrorDetected        bool
	ErrorReason          string
	RecoveredOnAttempt   int
	InterfaceCreateTimes []time.Duration
}

// TestWindowsStressRollout verifies the performance, migration, and recovery times of Antrea on Windows Nodes
// under high Pod density stress. It simulates a Node Rollout scenario with 80 Pods:
// 1. Deploys 80 Pods on Windows Node A.
// 2. Verifies initial connectivity and detects HNS / interface creation errors.
// 3. For any Pod with errors, restarts the Pod (workaround) and runs traffic verification after each restart,
//    logging the recovery attempt number and interface creation duration for each attempt.
// 4. Cordons Node A, and simultaneously deletes Node A's pods, schedules them on Node B, and rolls out the Antrea Agent.
// 5. Verifies connectivity on Node B, applies the workaround for any errors, and logs timing metrics.
func TestWindowsStressRollout(t *testing.T) {
	skipIfNoWindowsNodes(t)

	if len(clusterInfo.windowsNodes) < 2 {
		t.Skip("Skipping test as it requires at least 2 Windows nodes to simulate rollout migration")
	}

	data, err := setupTest(t)
	require.NoError(t, err, "Error when setting up test")
	defer teardownTest(t, data)

	// Identify Node A and Node B
	nodeA := nodeName(clusterInfo.windowsNodes[0])
	nodeB := nodeName(clusterInfo.windowsNodes[1])
	t.Logf("Using Windows Node A: '%s' and Windows Node B: '%s' for rollout migration simulation", nodeA, nodeB)

	// Ensure both nodes are uncordoned at the end of the test
	defer func() {
		t.Logf("Ensuring both Windows nodes are uncordoned at test completion")
		_ = cordonNode(data.clientset, nodeA, false)
		_ = cordonNode(data.clientset, nodeB, false)
	}()

	// Create a Linux client Pod on the control-plane Node to act as the traffic prober.
	linuxNodeName := controlPlaneNodeName()
	linuxPodName := randName("stress-client-linux-")
	clientPodInfo := PodInfo{
		Name:      linuxPodName,
		Namespace: data.testNamespace,
		NodeName:  linuxNodeName,
		OS:        "linux",
	}

	t.Logf("Creating Linux prober Pod %s on Node '%s'", linuxPodName, linuxNodeName)
	err = data.createToolboxPodOnNode(clientPodInfo.Name, clientPodInfo.Namespace, clientPodInfo.NodeName, false)
	require.NoError(t, err, "Failed to create Linux prober Pod")
	defer deletePodWrapper(t, data, clientPodInfo.Namespace, clientPodInfo.Name)

	// Wait for Linux prober Pod to be running and get its IP
	clientIPs, err := data.podWaitForIPs(defaultTimeout, clientPodInfo.Name, clientPodInfo.Namespace)
	require.NoError(t, err, "Failed to wait for Linux prober Pod to get IP")
	t.Logf("Linux prober Pod IP: %v", clientIPs)

	// Define scale = 80 pods to reproduce HNS timeout under stress
	scales := []int{80}

	for _, scale := range scales {
		t.Run(fmt.Sprintf("Scale-%d-Pods", scale), func(t *testing.T) {
			roundCtx, roundCancel := context.WithTimeout(context.Background(), 60*time.Minute)
			defer roundCancel()

			t.Logf("=== Starting Round: %d Pods Rollout Migration & Workaround Verification ===", scale)
			roundStartTime := time.Now()

			// Ensure both nodes are uncordoned at the start of each round
			err = cordonNode(data.clientset, nodeA, false)
			require.NoError(t, err, "Failed to uncordon Node A")
			err = cordonNode(data.clientset, nodeB, false)
			require.NoError(t, err, "Failed to uncordon Node B")

			var nodeAPodNames []string
			var nodeAPodInfos []PodInfo
			var nodeBPodNames []string
			var nodeBPodInfos []PodInfo

			for i := 0; i < scale; i++ {
				podNameA := fmt.Sprintf("win-stress-%d-nodea-%d", scale, i)
				nodeAPodNames = append(nodeAPodNames, podNameA)
				nodeAPodInfos = append(nodeAPodInfos, PodInfo{
					Name:      podNameA,
					Namespace: data.testNamespace,
					NodeName:  nodeA,
					OS:        "windows",
				})

				podNameB := fmt.Sprintf("win-stress-%d-nodeb-%d", scale, i)
				nodeBPodNames = append(nodeBPodNames, podNameB)
				nodeBPodInfos = append(nodeBPodInfos, PodInfo{
					Name:      podNameB,
					Namespace: data.testNamespace,
					NodeName:  nodeB,
					OS:        "windows",
				})
			}

			// Defer cleanup of all Pods created in this round
			defer func() {
				t.Logf("Cleaning up all Windows Pods for scale %d", scale)
				cleanupCtx, cleanupCancel := context.WithTimeout(context.Background(), 2*time.Minute)
				defer cleanupCancel()

				deleteOptions := metav1.DeleteOptions{
					GracePeriodSeconds: new(int64), // immediate deletion
				}
				listOptions := metav1.ListOptions{
					LabelSelector: fmt.Sprintf("app=windows-stress-test,scale=%d", scale),
				}
				_ = data.clientset.CoreV1().Pods(data.testNamespace).DeleteCollection(cleanupCtx, deleteOptions, listOptions)

				// Wait until all Pods are deleted
				_ = wait.PollUntilContextTimeout(cleanupCtx, 2*time.Second, 2*time.Minute, false, func(ctx context.Context) (bool, error) {
					podList, err := data.clientset.CoreV1().Pods(data.testNamespace).List(ctx, listOptions)
					if err != nil {
						return false, err
					}
					return len(podList.Items) == 0, nil
				})
			}()

			limits := corev1.ResourceList{
				corev1.ResourceCPU:    resource.MustParse("25m"),
				corev1.ResourceMemory: resource.MustParse("40Mi"),
			}

			// 1. Deploy 'scale' agnhost Pods to Windows Node A in parallel
			t.Logf("Step 1: Deploying %d Pods on Windows Node A: '%s'", scale, nodeA)
			nodeACreationStart := time.Now()
			var wg sync.WaitGroup
			var createErrorsA []error
			var muA sync.Mutex

			for _, pi := range nodeAPodInfos {
				wg.Add(1)
				go func(podInfo PodInfo) {
					defer wg.Done()
					err := NewPodBuilder(podInfo.Name, data.testNamespace, agnhostImage).
						OnNode(nodeA).
						WithRestartPolicy(corev1.RestartPolicyAlways).
						WithResources(nil, limits).
						WithLabels(map[string]string{
							"app":   "windows-stress-test",
							"scale": fmt.Sprintf("%d", scale),
							"node":  nodeA,
						}).
						Create(data)
					if err != nil {
						muA.Lock()
						createErrorsA = append(createErrorsA, fmt.Errorf("failed to create Pod %s on Node A: %v", podInfo.Name, err))
						muA.Unlock()
					}
				}(pi)
			}
			wg.Wait()
			if len(createErrorsA) > 0 {
				t.Fatalf("Failed to create Node A Pods: %v", createErrorsA)
			}

			// 2. Wait for Node A Pods to be Running
			t.Logf("Step 2: Waiting for %d Pods on Node A to reach Running state...", scale)
			labelSelectorA := fmt.Sprintf("app=windows-stress-test,scale=%d,node=%s", scale, nodeA)
			_, _ = data.waitForStressPodsRunning(roundCtx, labelSelectorA, scale)
			nodeAPodsReadyDuration := time.Since(nodeACreationStart)
			t.Logf("Initial Node A Pod deployment phase finished in %v", nodeAPodsReadyDuration)

			// 3. Verify traffic on Node A, detect errors, and apply Pod restart workaround
			t.Logf("Step 3: Verifying traffic & applying Pod restart workaround for any failing Pods on Node A...")
			resultsA := verifyAndRecoverPods(t, data, clientPodInfo, clientIPs, nodeAPodInfos, scale, nodeA, limits)
			printRecoverySummary(t, fmt.Sprintf("Node A (%s)", nodeA), resultsA)

			// 4. Cordon Node A and trigger simultaneous switchover to Node B
			t.Logf("Step 4: Cordoning Node A: '%s' to simulate rollout drain", nodeA)
			err = cordonNode(data.clientset, nodeA, true)
			require.NoError(t, err, "Failed to cordon Node A")

			t.Logf("Step 5: Triggering simultaneous migration and Antrea rollout...")
			switchoverStartTime := time.Now()

			var deleteNodeAPodsDuration time.Duration
			var createNodeBPodsDuration time.Duration
			var rolloutAntreaDuration time.Duration

			var createErrorsB []error
			var muB sync.Mutex

			wg.Add(3)

			// Task A: Delete all test pods on Node A
			go func() {
				defer wg.Done()
				t.Logf("[Switchover] Deleting all test pods on Node A...")
				deleteStart := time.Now()
				deleteOptions := metav1.DeleteOptions{
					GracePeriodSeconds: new(int64), // immediate deletion
				}
				_ = data.clientset.CoreV1().Pods(data.testNamespace).DeleteCollection(roundCtx, deleteOptions, metav1.ListOptions{
					LabelSelector: labelSelectorA,
				})

				_ = wait.PollUntilContextTimeout(roundCtx, 1*time.Second, 2*time.Minute, false, func(ctx context.Context) (bool, error) {
					podList, err := data.clientset.CoreV1().Pods(data.testNamespace).List(ctx, metav1.ListOptions{
						LabelSelector: labelSelectorA,
					})
					if err != nil {
						return false, err
					}
					return len(podList.Items) == 0, nil
				})
				deleteNodeAPodsDuration = time.Since(deleteStart)
				t.Logf("[Switchover] Node A Pods deletion completed in %v", deleteNodeAPodsDuration)
			}()

			// Task B: Deploy 'scale' agnhost Pods to Windows Node B
			go func() {
				defer wg.Done()
				t.Logf("[Switchover] Creating %d test pods on Node B...", scale)
				createStart := time.Now()
				var wgB sync.WaitGroup
				for _, pi := range nodeBPodInfos {
					wgB.Add(1)
					go func(podInfo PodInfo) {
						defer wgB.Done()
						err := NewPodBuilder(podInfo.Name, data.testNamespace, agnhostImage).
							OnNode(nodeB).
							WithRestartPolicy(corev1.RestartPolicyAlways).
							WithResources(nil, limits).
							WithLabels(map[string]string{
								"app":   "windows-stress-test",
								"scale": fmt.Sprintf("%d", scale),
								"node":  nodeB,
							}).
							Create(data)
						if err != nil {
							muB.Lock()
							createErrorsB = append(createErrorsB, fmt.Errorf("failed to create Pod %s on Node B: %v", podInfo.Name, err))
							muB.Unlock()
						}
					}(pi)
				}
				wgB.Wait()
				createNodeBPodsDuration = time.Since(createStart)
				t.Logf("[Switchover] Node B Pods creation completed in %v", createNodeBPodsDuration)
			}()

			// Task C: Rollout/Restart Antrea Agent
			go func() {
				defer wg.Done()
				t.Logf("[Switchover] Rolling out Antrea Agent...")
				rolloutStart := time.Now()
				err := data.RestartAntreaAgentPods(15 * time.Minute)
				if err != nil {
					t.Logf("[Switchover] Antrea Agent rollout failed: %v", err)
				}
				rolloutAntreaDuration = time.Since(rolloutStart)
				t.Logf("[Switchover] Antrea Agent rollout completed in %v", rolloutAntreaDuration)
			}()

			wg.Wait()
			if len(createErrorsB) > 0 {
				t.Fatalf("Failed during switchover creation: %v", createErrorsB)
			}

			// 5. Wait for Node B Pods to reach Running state
			t.Logf("Step 6: Waiting for Node B Pods to reach Running state...")
			labelSelectorB := fmt.Sprintf("app=windows-stress-test,scale=%d,node=%s", scale, nodeB)
			_, _ = data.waitForStressPodsRunning(roundCtx, labelSelectorB, scale)
			nodeBPodsReadyDuration := time.Since(switchoverStartTime)
			t.Logf("Initial Node B Pod deployment phase finished in %v", nodeBPodsReadyDuration)

			// 6. Verify traffic on Node B, detect errors, and apply Pod restart workaround
			t.Logf("Step 7: Verifying traffic & applying Pod restart workaround for any failing Pods on Node B...")
			resultsB := verifyAndRecoverPods(t, data, clientPodInfo, clientIPs, nodeBPodInfos, scale, nodeB, limits)
			printRecoverySummary(t, fmt.Sprintf("Node B (%s)", nodeB), resultsB)

			totalRoundDuration := time.Since(roundStartTime)

			// Print performance metrics summary
			t.Logf("==========================================================================================")
			t.Logf("PERFORMANCE METRICS SUMMARY - SCALE: %d PODS", scale)
			t.Logf("------------------------------------------------------------------------------------------")
			t.Logf("[Phase 1] Node A (%s) Deployment Time          : %v", nodeA, nodeAPodsReadyDuration)
			t.Logf("[Phase 2] Node A (%s) Pods Deletion Time       : %v", nodeA, deleteNodeAPodsDuration)
			t.Logf("[Phase 3] Node B (%s) Pods Creation Time       : %v", nodeB, createNodeBPodsDuration)
			t.Logf("[Phase 4] Antrea Agent Rollout Time            : %v", rolloutAntreaDuration)
			t.Logf("[Phase 5] Node B (%s) Deployment Time          : %v", nodeB, nodeBPodsReadyDuration)
			t.Logf("[Overall] Total Round Duration                 : %v", totalRoundDuration)
			t.Logf("==========================================================================================")
		})
	}
}

func verifyAndRecoverPods(
	t *testing.T,
	data *TestData,
	clientPodInfo PodInfo,
	clientIPs *PodIPs,
	podInfos []PodInfo,
	scale int,
	nodeName string,
	limits corev1.ResourceList,
) []PodRecoveryResult {
	results := make([]PodRecoveryResult, len(podInfos))
	var wg sync.WaitGroup
	// Concurrency limiter to prevent API server throttling
	sem := make(chan struct{}, 10)

	for i, pi := range podInfos {
		wg.Add(1)
		go func(idx int, podInfo PodInfo) {
			defer wg.Done()
			sem <- struct{}{}
			defer func() { <-sem }()

			results[idx] = verifyAndRecoverSinglePod(t, data, clientPodInfo, clientIPs, podInfo, scale, nodeName, limits, 20)
		}(i, pi)
	}

	wg.Wait()
	return results
}

func verifyAndRecoverSinglePod(
	t *testing.T,
	data *TestData,
	clientPodInfo PodInfo,
	clientIPs *PodIPs,
	podInfo PodInfo,
	scale int,
	nodeName string,
	limits corev1.ResourceList,
	maxRetries int,
) PodRecoveryResult {
	res := PodRecoveryResult{
		PodName:  podInfo.Name,
		NodeName: nodeName,
	}

	// Initial health check
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	pod, err := data.clientset.CoreV1().Pods(podInfo.Namespace).Get(ctx, podInfo.Name, metav1.GetOptions{})
	cancel()

	isHealthy := false
	if err == nil && pod.Status.Phase == corev1.PodRunning && pod.Status.PodIP != "" {
		podIPs := &PodIPs{IPv4: parseStressIP(pod.Status.PodIP)}
		pingErr1 := data.RunPingCommandFromTestPod(clientPodInfo, data.testNamespace, podIPs, toolboxContainerName, 2, 0, false)
		pingErr2 := data.RunPingCommandFromTestPod(podInfo, data.testNamespace, clientIPs, "agnhost", 2, 0, false)
		if pingErr1 == nil && pingErr2 == nil {
			isHealthy = true
		} else {
			res.ErrorDetected = true
			res.ErrorReason = fmt.Sprintf("Traffic ping failed (Linux->Win: %v, Win->Linux: %v)", pingErr1, pingErr2)
		}
	} else {
		res.ErrorDetected = true
		if err != nil {
			res.ErrorReason = fmt.Sprintf("Get Pod error: %v", err)
		} else {
			res.ErrorReason = fmt.Sprintf("Pod phase: %s, PodIP: '%s'", pod.Status.Phase, pod.Status.PodIP)
		}
	}

	if !isHealthy && res.ErrorDetected {
		t.Logf("[ERROR DETECTED] Pod %s on Node %s: %s. Initiating workaround (restarting pod)...", podInfo.Name, nodeName, res.ErrorReason)

		for attempt := 1; attempt <= maxRetries; attempt++ {
			t.Logf("[WORKAROUND] Pod %s on Node %s: Restart attempt %d/%d...", podInfo.Name, nodeName, attempt, maxRetries)
			recreateStart := time.Now()

			// Delete pod
			delCtx, delCancel := context.WithTimeout(context.Background(), 30*time.Second)
			_ = data.clientset.CoreV1().Pods(podInfo.Namespace).Delete(delCtx, podInfo.Name, metav1.DeleteOptions{
				GracePeriodSeconds: new(int64),
			})
			delCancel()

			// Wait for pod deletion
			_ = wait.PollUntilContextTimeout(context.Background(), 1*time.Second, 30*time.Second, false, func(ctx context.Context) (bool, error) {
				_, err := data.clientset.CoreV1().Pods(podInfo.Namespace).Get(ctx, podInfo.Name, metav1.GetOptions{})
				return err != nil, nil
			})

			// Re-create pod
			createErr := NewPodBuilder(podInfo.Name, podInfo.Namespace, agnhostImage).
				OnNode(nodeName).
				WithRestartPolicy(corev1.RestartPolicyAlways).
				WithResources(nil, limits).
				WithLabels(map[string]string{
					"app":   "windows-stress-test",
					"scale": fmt.Sprintf("%d", scale),
					"node":  nodeName,
				}).
				Create(data)

			if createErr != nil {
				t.Logf("Pod %s restart attempt #%d: Re-creation error: %v", podInfo.Name, attempt, createErr)
			}

			// Wait for pod running and IP
			runningPod, waitErr := data.waitForSinglePodRunningAndIP(podInfo.Name, podInfo.Namespace, 2*time.Minute)
			ifaceCreationTime := time.Since(recreateStart)
			res.InterfaceCreateTimes = append(res.InterfaceCreateTimes, ifaceCreationTime)

			t.Logf("Pod %s restart attempt #%d: interface creation time = %v", podInfo.Name, attempt, ifaceCreationTime)

			if waitErr != nil {
				t.Logf("Pod %s restart attempt #%d: Pod failed to reach Running state with IP: %v", podInfo.Name, attempt, waitErr)
				continue
			}

			// Traffic verification after restart
			restartedPodIPs := &PodIPs{IPv4: parseStressIP(runningPod.Status.PodIP)}
			pErr1 := data.RunPingCommandFromTestPod(clientPodInfo, data.testNamespace, restartedPodIPs, toolboxContainerName, 2, 0, false)
			pErr2 := data.RunPingCommandFromTestPod(podInfo, data.testNamespace, clientIPs, "agnhost", 2, 0, false)

			if pErr1 == nil && pErr2 == nil {
				res.RecoveredOnAttempt = attempt
				t.Logf("[WORKAROUND RECOVERED] Pod %s on Node %s RECOVERED on restart attempt #%d! Interface creation time for attempt #%d: %v", podInfo.Name, nodeName, attempt, attempt, ifaceCreationTime)
				return res
			}

			t.Logf("Pod %s restart attempt #%d: Traffic verification failed (Linux->Win: %v, Win->Linux: %v). Will retry...", podInfo.Name, attempt, pErr1, pErr2)
		}

		t.Logf("[WORKAROUND FAILED] Pod %s on Node %s failed to recover after %d restart attempts", podInfo.Name, nodeName, maxRetries)
	}

	return res
}

func (data *TestData) waitForSinglePodRunningAndIP(podName, namespace string, timeout time.Duration) (*corev1.Pod, error) {
	var targetPod *corev1.Pod
	err := wait.PollUntilContextTimeout(context.Background(), 2*time.Second, timeout, false, func(ctx context.Context) (bool, error) {
		pod, err := data.clientset.CoreV1().Pods(namespace).Get(ctx, podName, metav1.GetOptions{})
		if err != nil {
			return false, nil
		}
		if pod.Status.Phase == corev1.PodRunning && pod.Status.PodIP != "" {
			targetPod = pod
			return true, nil
		}
		return false, nil
	})
	return targetPod, err
}

func printRecoverySummary(t *testing.T, phaseName string, results []PodRecoveryResult) {
	total := len(results)
	errCount := 0
	recoveredCount := 0

	t.Logf("==========================================================================================")
	t.Logf("WORKAROUND & RECOVERY SUMMARY - %s (TOTAL PODS: %d)", phaseName, total)
	t.Logf("------------------------------------------------------------------------------------------")
	for _, r := range results {
		if r.ErrorDetected {
			errCount++
			if r.RecoveredOnAttempt > 0 {
				recoveredCount++
				t.Logf("[RECOVERED] Pod: %s | Node: %s | Error: %s | Recovered on Attempt #: %d | Interface Creation Times per Attempt: %v",
					r.PodName, r.NodeName, r.ErrorReason, r.RecoveredOnAttempt, r.InterfaceCreateTimes)
			} else {
				t.Logf("[FAILED RECOVERY] Pod: %s | Node: %s | Error: %s | Failed after attempts | Interface Creation Times per Attempt: %v",
					r.PodName, r.NodeName, r.ErrorReason, r.InterfaceCreateTimes)
			}
		}
	}
	if errCount == 0 {
		t.Logf("No errors detected across all %d Pods during %s.", total, phaseName)
	} else {
		t.Logf("Summary: %d / %d Pods encountered errors, %d / %d successfully recovered via workaround.",
			errCount, total, recoveredCount, errCount)
	}
	t.Logf("==========================================================================================")
}

func cordonNode(clientset kubernetes.Interface, nodeName string, cordon bool) error {
	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()

	return retry.RetryOnConflict(retry.DefaultRetry, func() error {
		node, err := clientset.CoreV1().Nodes().Get(ctx, nodeName, metav1.GetOptions{})
		if err != nil {
			return err
		}
		if node.Spec.Unschedulable == cordon {
			return nil
		}
		node.Spec.Unschedulable = cordon
		_, err = clientset.CoreV1().Nodes().Update(ctx, node, metav1.UpdateOptions{})
		return err
	})
}

func parseStressIP(ipStr string) *net.IP {
	if ipStr == "" {
		return nil
	}
	ip := net.ParseIP(ipStr)
	return &ip
}

func (data *TestData) waitForStressPodsRunning(ctx context.Context, labelSelector string, expectedCount int) ([]corev1.Pod, error) {
	var runningPods []corev1.Pod
	err := wait.PollUntilContextCancel(ctx, 2*time.Second, false, func(ctx context.Context) (bool, error) {
		podList, err := data.clientset.CoreV1().Pods(data.testNamespace).List(ctx, metav1.ListOptions{
			LabelSelector: labelSelector,
		})
		if err != nil {
			return false, err
		}
		if len(podList.Items) < expectedCount {
			return false, nil
		}
		runningPods = nil
		for _, pod := range podList.Items {
			if pod.Status.Phase != corev1.PodRunning || pod.Status.PodIP == "" {
				return false, nil
			}
			runningPods = append(runningPods, pod)
		}
		return true, nil
	})
	return runningPods, err
}
