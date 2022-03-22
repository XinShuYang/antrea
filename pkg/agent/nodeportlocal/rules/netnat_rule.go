//go:build windows
// +build windows

// Copyright 2022 Antrea Authors
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

package rules

import (
	"fmt"

	"k8s.io/klog/v2"

	"antrea.io/antrea/pkg/agent/openflow"
	"antrea.io/antrea/pkg/agent/route"
	"antrea.io/antrea/pkg/agent/util"
)

// Use antrea-nat netnatstaticmapping rules as NPL implementation
const (
	antreaNatNPL = "antrea-nat"
)

// InitRules initializes rules based on the netnatstaticmapping implementation on windows
func InitRules() PodPortRules {
	return NewNetNatRules()
}

type netnatRules struct {
	name string
}

// NewNetNatRules retruns a new instance of netnatRules.
func NewNetNatRules() *netnatRules {
	nnRule := netnatRules{
		name: antreaNatNPL,
	}
	return &nnRule
}

// Init initializes IPTABLES rules for NPL.
func (nn *netnatRules) Init() error {
	if err := nn.initRules(); err != nil {
		return fmt.Errorf("initialization of NPL iptables rules failed: %v", err)
	}
	return nil
}

// initRules creates or reuses NetNatStaticMapping table as NPL rule instance on Windows.
func (nn *netnatRules) initRules() error {
	if err := util.NewNetNat(antreaNatNPL, route.PodCIDRIPv4); err != nil {
		klog.InfoS("Successfully created NetNat rule", "name", antreaNatNPL, "CIDR", route.PodCIDRIPv4)
		return err
	}
	return nil
}

// AddRule appends a rule in NetNatStaticMapping table.
func (nn *netnatRules) AddRule(nodePort int, podIP string, podPort int, protocol string) error {
	nodePort16 := openflow.PortToUint16(nodePort)
	podPort16 := openflow.PortToUint16(podPort)
	podAddr := fmt.Sprintf("%s:%d", podIP, podPort16)
	if err := util.ReplaceNetNatStaticMapping(antreaNatNPL, "0.0.0.0", nodePort16, podIP, podPort16, protocol); err != nil {
		return err
	}
	klog.InfoS("Successfully added NetNat rule", "podAddr", podAddr, "nodePort", nodePort16, "protocol", protocol)
	return nil
}

// AddAllRules constructs a list of NPL rules and performs NetNatStaticMapping replacement.
func (nn *netnatRules) AddAllRules(nplList []PodNodePort) error {
	for _, nplData := range nplList {
		for _, protocol := range nplData.Protocols {
			nodePort16 := openflow.PortToUint16(nplData.NodePort)
			podPort16 := openflow.PortToUint16(nplData.PodPort)
			podAddr := fmt.Sprintf("%s:%d", nplData.PodIP, podPort16)
			if err := util.ReplaceNetNatStaticMapping(antreaNatNPL, "0.0.0.0", nodePort16, nplData.PodIP, podPort16, protocol); err != nil {
				return err
			}
			klog.InfoS("Successfully added NetNatStaticMapping rule", "podAddr", podAddr, "nodePort", nodePort16, "protocol", protocol)
		}
	}
	return nil
}

// DeleteRule deletes a specific NPL rule from NetNatStaticMapping table
func (nn *netnatRules) DeleteRule(nodePort int, podIP string, podPort int, protocol string) error {
	nodePort16 := openflow.PortToUint16(nodePort)
	podPort16 := openflow.PortToUint16(podPort)
	podAddr := fmt.Sprintf("%s:%d", podIP, podPort16)
	if err := util.RemoveNetNatStaticMappingByNPLTuples(antreaNatNPL, "0.0.0.0", nodePort16, podIP, podPort16, protocol); err != nil {
		return err
	}
	klog.InfoS("Successfully deleted NetNatStaticMapping rule", "podAddr", podAddr, "nodePort", nodePort16, "protocol", protocol)
	return nil
}

// DeleteAllRules deletes the NetNatStaticMapping table in the node
func (nn *netnatRules) DeleteAllRules() error {
	if err := util.RemoveNetNatStaticMappingByNAME(antreaNatNPL); err != nil {
		return err
	}
	klog.InfoS("Successfully deleted all NPL NetNatStaticMapping rules", "NatName", antreaNatNPL)
	return nil
}
