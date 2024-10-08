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

package v1beta1

import (
	"context"

	v1beta1 "antrea.io/antrea/pkg/apis/crd/v1beta1"
	scheme "antrea.io/antrea/pkg/client/clientset/versioned/scheme"
	v1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	types "k8s.io/apimachinery/pkg/types"
	watch "k8s.io/apimachinery/pkg/watch"
	gentype "k8s.io/client-go/gentype"
)

// ClusterGroupsGetter has a method to return a ClusterGroupInterface.
// A group's client should implement this interface.
type ClusterGroupsGetter interface {
	ClusterGroups() ClusterGroupInterface
}

// ClusterGroupInterface has methods to work with ClusterGroup resources.
type ClusterGroupInterface interface {
	Create(ctx context.Context, clusterGroup *v1beta1.ClusterGroup, opts v1.CreateOptions) (*v1beta1.ClusterGroup, error)
	Update(ctx context.Context, clusterGroup *v1beta1.ClusterGroup, opts v1.UpdateOptions) (*v1beta1.ClusterGroup, error)
	// Add a +genclient:noStatus comment above the type to avoid generating UpdateStatus().
	UpdateStatus(ctx context.Context, clusterGroup *v1beta1.ClusterGroup, opts v1.UpdateOptions) (*v1beta1.ClusterGroup, error)
	Delete(ctx context.Context, name string, opts v1.DeleteOptions) error
	DeleteCollection(ctx context.Context, opts v1.DeleteOptions, listOpts v1.ListOptions) error
	Get(ctx context.Context, name string, opts v1.GetOptions) (*v1beta1.ClusterGroup, error)
	List(ctx context.Context, opts v1.ListOptions) (*v1beta1.ClusterGroupList, error)
	Watch(ctx context.Context, opts v1.ListOptions) (watch.Interface, error)
	Patch(ctx context.Context, name string, pt types.PatchType, data []byte, opts v1.PatchOptions, subresources ...string) (result *v1beta1.ClusterGroup, err error)
	ClusterGroupExpansion
}

// clusterGroups implements ClusterGroupInterface
type clusterGroups struct {
	*gentype.ClientWithList[*v1beta1.ClusterGroup, *v1beta1.ClusterGroupList]
}

// newClusterGroups returns a ClusterGroups
func newClusterGroups(c *CrdV1beta1Client) *clusterGroups {
	return &clusterGroups{
		gentype.NewClientWithList[*v1beta1.ClusterGroup, *v1beta1.ClusterGroupList](
			"clustergroups",
			c.RESTClient(),
			scheme.ParameterCodec,
			"",
			func() *v1beta1.ClusterGroup { return &v1beta1.ClusterGroup{} },
			func() *v1beta1.ClusterGroupList { return &v1beta1.ClusterGroupList{} }),
	}
}
