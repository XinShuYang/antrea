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

package v1alpha2

import (
	"context"

	v1alpha2 "antrea.io/antrea/pkg/apis/crd/v1alpha2"
	scheme "antrea.io/antrea/pkg/client/clientset/versioned/scheme"
	v1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	types "k8s.io/apimachinery/pkg/types"
	watch "k8s.io/apimachinery/pkg/watch"
	gentype "k8s.io/client-go/gentype"
)

// TrafficControlsGetter has a method to return a TrafficControlInterface.
// A group's client should implement this interface.
type TrafficControlsGetter interface {
	TrafficControls() TrafficControlInterface
}

// TrafficControlInterface has methods to work with TrafficControl resources.
type TrafficControlInterface interface {
	Create(ctx context.Context, trafficControl *v1alpha2.TrafficControl, opts v1.CreateOptions) (*v1alpha2.TrafficControl, error)
	Update(ctx context.Context, trafficControl *v1alpha2.TrafficControl, opts v1.UpdateOptions) (*v1alpha2.TrafficControl, error)
	Delete(ctx context.Context, name string, opts v1.DeleteOptions) error
	DeleteCollection(ctx context.Context, opts v1.DeleteOptions, listOpts v1.ListOptions) error
	Get(ctx context.Context, name string, opts v1.GetOptions) (*v1alpha2.TrafficControl, error)
	List(ctx context.Context, opts v1.ListOptions) (*v1alpha2.TrafficControlList, error)
	Watch(ctx context.Context, opts v1.ListOptions) (watch.Interface, error)
	Patch(ctx context.Context, name string, pt types.PatchType, data []byte, opts v1.PatchOptions, subresources ...string) (result *v1alpha2.TrafficControl, err error)
	TrafficControlExpansion
}

// trafficControls implements TrafficControlInterface
type trafficControls struct {
	*gentype.ClientWithList[*v1alpha2.TrafficControl, *v1alpha2.TrafficControlList]
}

// newTrafficControls returns a TrafficControls
func newTrafficControls(c *CrdV1alpha2Client) *trafficControls {
	return &trafficControls{
		gentype.NewClientWithList[*v1alpha2.TrafficControl, *v1alpha2.TrafficControlList](
			"trafficcontrols",
			c.RESTClient(),
			scheme.ParameterCodec,
			"",
			func() *v1alpha2.TrafficControl { return &v1alpha2.TrafficControl{} },
			func() *v1alpha2.TrafficControlList { return &v1alpha2.TrafficControlList{} }),
	}
}
