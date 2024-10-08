// Copyright 2024 Antrea Authors
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

package v1beta2

import (
	"context"

	v1beta2 "antrea.io/antrea/pkg/apis/controlplane/v1beta2"
	scheme "antrea.io/antrea/pkg/client/clientset/versioned/scheme"
	v1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	watch "k8s.io/apimachinery/pkg/watch"
	gentype "k8s.io/client-go/gentype"
)

// EgressGroupsGetter has a method to return a EgressGroupInterface.
// A group's client should implement this interface.
type EgressGroupsGetter interface {
	EgressGroups() EgressGroupInterface
}

// EgressGroupInterface has methods to work with EgressGroup resources.
type EgressGroupInterface interface {
	Get(ctx context.Context, name string, opts v1.GetOptions) (*v1beta2.EgressGroup, error)
	List(ctx context.Context, opts v1.ListOptions) (*v1beta2.EgressGroupList, error)
	Watch(ctx context.Context, opts v1.ListOptions) (watch.Interface, error)
	EgressGroupExpansion
}

// egressGroups implements EgressGroupInterface
type egressGroups struct {
	*gentype.ClientWithList[*v1beta2.EgressGroup, *v1beta2.EgressGroupList]
}

// newEgressGroups returns a EgressGroups
func newEgressGroups(c *ControlplaneV1beta2Client) *egressGroups {
	return &egressGroups{
		gentype.NewClientWithList[*v1beta2.EgressGroup, *v1beta2.EgressGroupList](
			"egressgroups",
			c.RESTClient(),
			scheme.ParameterCodec,
			"",
			func() *v1beta2.EgressGroup { return &v1beta2.EgressGroup{} },
			func() *v1beta2.EgressGroupList { return &v1beta2.EgressGroupList{} }),
	}
}
