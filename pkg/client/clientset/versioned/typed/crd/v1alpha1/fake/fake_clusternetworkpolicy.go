// Copyright 2022 Antrea Authors
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

// Code generated by client-gen. DO NOT EDIT.

package fake

import (
	"context"

	v1alpha1 "antrea.io/antrea/pkg/apis/crd/v1alpha1"
	v1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	labels "k8s.io/apimachinery/pkg/labels"
	schema "k8s.io/apimachinery/pkg/runtime/schema"
	types "k8s.io/apimachinery/pkg/types"
	watch "k8s.io/apimachinery/pkg/watch"
	testing "k8s.io/client-go/testing"
)

// FakeClusterNetworkPolicies implements ClusterNetworkPolicyInterface
type FakeClusterNetworkPolicies struct {
	Fake *FakeCrdV1alpha1
}

var clusternetworkpoliciesResource = schema.GroupVersionResource{Group: "crd.antrea.io", Version: "v1alpha1", Resource: "clusternetworkpolicies"}

var clusternetworkpoliciesKind = schema.GroupVersionKind{Group: "crd.antrea.io", Version: "v1alpha1", Kind: "ClusterNetworkPolicy"}

// Get takes name of the clusterNetworkPolicy, and returns the corresponding clusterNetworkPolicy object, and an error if there is any.
func (c *FakeClusterNetworkPolicies) Get(ctx context.Context, name string, options v1.GetOptions) (result *v1alpha1.ClusterNetworkPolicy, err error) {
	obj, err := c.Fake.
		Invokes(testing.NewRootGetAction(clusternetworkpoliciesResource, name), &v1alpha1.ClusterNetworkPolicy{})
	if obj == nil {
		return nil, err
	}
	return obj.(*v1alpha1.ClusterNetworkPolicy), err
}

// List takes label and field selectors, and returns the list of ClusterNetworkPolicies that match those selectors.
func (c *FakeClusterNetworkPolicies) List(ctx context.Context, opts v1.ListOptions) (result *v1alpha1.ClusterNetworkPolicyList, err error) {
	obj, err := c.Fake.
		Invokes(testing.NewRootListAction(clusternetworkpoliciesResource, clusternetworkpoliciesKind, opts), &v1alpha1.ClusterNetworkPolicyList{})
	if obj == nil {
		return nil, err
	}

	label, _, _ := testing.ExtractFromListOptions(opts)
	if label == nil {
		label = labels.Everything()
	}
	list := &v1alpha1.ClusterNetworkPolicyList{ListMeta: obj.(*v1alpha1.ClusterNetworkPolicyList).ListMeta}
	for _, item := range obj.(*v1alpha1.ClusterNetworkPolicyList).Items {
		if label.Matches(labels.Set(item.Labels)) {
			list.Items = append(list.Items, item)
		}
	}
	return list, err
}

// Watch returns a watch.Interface that watches the requested clusterNetworkPolicies.
func (c *FakeClusterNetworkPolicies) Watch(ctx context.Context, opts v1.ListOptions) (watch.Interface, error) {
	return c.Fake.
		InvokesWatch(testing.NewRootWatchAction(clusternetworkpoliciesResource, opts))
}

// Create takes the representation of a clusterNetworkPolicy and creates it.  Returns the server's representation of the clusterNetworkPolicy, and an error, if there is any.
func (c *FakeClusterNetworkPolicies) Create(ctx context.Context, clusterNetworkPolicy *v1alpha1.ClusterNetworkPolicy, opts v1.CreateOptions) (result *v1alpha1.ClusterNetworkPolicy, err error) {
	obj, err := c.Fake.
		Invokes(testing.NewRootCreateAction(clusternetworkpoliciesResource, clusterNetworkPolicy), &v1alpha1.ClusterNetworkPolicy{})
	if obj == nil {
		return nil, err
	}
	return obj.(*v1alpha1.ClusterNetworkPolicy), err
}

// Update takes the representation of a clusterNetworkPolicy and updates it. Returns the server's representation of the clusterNetworkPolicy, and an error, if there is any.
func (c *FakeClusterNetworkPolicies) Update(ctx context.Context, clusterNetworkPolicy *v1alpha1.ClusterNetworkPolicy, opts v1.UpdateOptions) (result *v1alpha1.ClusterNetworkPolicy, err error) {
	obj, err := c.Fake.
		Invokes(testing.NewRootUpdateAction(clusternetworkpoliciesResource, clusterNetworkPolicy), &v1alpha1.ClusterNetworkPolicy{})
	if obj == nil {
		return nil, err
	}
	return obj.(*v1alpha1.ClusterNetworkPolicy), err
}

// UpdateStatus was generated because the type contains a Status member.
// Add a +genclient:noStatus comment above the type to avoid generating UpdateStatus().
func (c *FakeClusterNetworkPolicies) UpdateStatus(ctx context.Context, clusterNetworkPolicy *v1alpha1.ClusterNetworkPolicy, opts v1.UpdateOptions) (*v1alpha1.ClusterNetworkPolicy, error) {
	obj, err := c.Fake.
		Invokes(testing.NewRootUpdateSubresourceAction(clusternetworkpoliciesResource, "status", clusterNetworkPolicy), &v1alpha1.ClusterNetworkPolicy{})
	if obj == nil {
		return nil, err
	}
	return obj.(*v1alpha1.ClusterNetworkPolicy), err
}

// Delete takes name of the clusterNetworkPolicy and deletes it. Returns an error if one occurs.
func (c *FakeClusterNetworkPolicies) Delete(ctx context.Context, name string, opts v1.DeleteOptions) error {
	_, err := c.Fake.
		Invokes(testing.NewRootDeleteActionWithOptions(clusternetworkpoliciesResource, name, opts), &v1alpha1.ClusterNetworkPolicy{})
	return err
}

// DeleteCollection deletes a collection of objects.
func (c *FakeClusterNetworkPolicies) DeleteCollection(ctx context.Context, opts v1.DeleteOptions, listOpts v1.ListOptions) error {
	action := testing.NewRootDeleteCollectionAction(clusternetworkpoliciesResource, listOpts)

	_, err := c.Fake.Invokes(action, &v1alpha1.ClusterNetworkPolicyList{})
	return err
}

// Patch applies the patch and returns the patched clusterNetworkPolicy.
func (c *FakeClusterNetworkPolicies) Patch(ctx context.Context, name string, pt types.PatchType, data []byte, opts v1.PatchOptions, subresources ...string) (result *v1alpha1.ClusterNetworkPolicy, err error) {
	obj, err := c.Fake.
		Invokes(testing.NewRootPatchSubresourceAction(clusternetworkpoliciesResource, name, pt, data, subresources...), &v1alpha1.ClusterNetworkPolicy{})
	if obj == nil {
		return nil, err
	}
	return obj.(*v1alpha1.ClusterNetworkPolicy), err
}
