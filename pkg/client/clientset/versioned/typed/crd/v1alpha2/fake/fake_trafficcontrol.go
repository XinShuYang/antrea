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

package fake

import (
	"context"

	v1alpha2 "antrea.io/antrea/pkg/apis/crd/v1alpha2"
	v1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	labels "k8s.io/apimachinery/pkg/labels"
	types "k8s.io/apimachinery/pkg/types"
	watch "k8s.io/apimachinery/pkg/watch"
	testing "k8s.io/client-go/testing"
)

// FakeTrafficControls implements TrafficControlInterface
type FakeTrafficControls struct {
	Fake *FakeCrdV1alpha2
}

var trafficcontrolsResource = v1alpha2.SchemeGroupVersion.WithResource("trafficcontrols")

var trafficcontrolsKind = v1alpha2.SchemeGroupVersion.WithKind("TrafficControl")

// Get takes name of the trafficControl, and returns the corresponding trafficControl object, and an error if there is any.
func (c *FakeTrafficControls) Get(ctx context.Context, name string, options v1.GetOptions) (result *v1alpha2.TrafficControl, err error) {
	obj, err := c.Fake.
		Invokes(testing.NewRootGetAction(trafficcontrolsResource, name), &v1alpha2.TrafficControl{})
	if obj == nil {
		return nil, err
	}
	return obj.(*v1alpha2.TrafficControl), err
}

// List takes label and field selectors, and returns the list of TrafficControls that match those selectors.
func (c *FakeTrafficControls) List(ctx context.Context, opts v1.ListOptions) (result *v1alpha2.TrafficControlList, err error) {
	obj, err := c.Fake.
		Invokes(testing.NewRootListAction(trafficcontrolsResource, trafficcontrolsKind, opts), &v1alpha2.TrafficControlList{})
	if obj == nil {
		return nil, err
	}

	label, _, _ := testing.ExtractFromListOptions(opts)
	if label == nil {
		label = labels.Everything()
	}
	list := &v1alpha2.TrafficControlList{ListMeta: obj.(*v1alpha2.TrafficControlList).ListMeta}
	for _, item := range obj.(*v1alpha2.TrafficControlList).Items {
		if label.Matches(labels.Set(item.Labels)) {
			list.Items = append(list.Items, item)
		}
	}
	return list, err
}

// Watch returns a watch.Interface that watches the requested trafficControls.
func (c *FakeTrafficControls) Watch(ctx context.Context, opts v1.ListOptions) (watch.Interface, error) {
	return c.Fake.
		InvokesWatch(testing.NewRootWatchAction(trafficcontrolsResource, opts))
}

// Create takes the representation of a trafficControl and creates it.  Returns the server's representation of the trafficControl, and an error, if there is any.
func (c *FakeTrafficControls) Create(ctx context.Context, trafficControl *v1alpha2.TrafficControl, opts v1.CreateOptions) (result *v1alpha2.TrafficControl, err error) {
	obj, err := c.Fake.
		Invokes(testing.NewRootCreateAction(trafficcontrolsResource, trafficControl), &v1alpha2.TrafficControl{})
	if obj == nil {
		return nil, err
	}
	return obj.(*v1alpha2.TrafficControl), err
}

// Update takes the representation of a trafficControl and updates it. Returns the server's representation of the trafficControl, and an error, if there is any.
func (c *FakeTrafficControls) Update(ctx context.Context, trafficControl *v1alpha2.TrafficControl, opts v1.UpdateOptions) (result *v1alpha2.TrafficControl, err error) {
	obj, err := c.Fake.
		Invokes(testing.NewRootUpdateAction(trafficcontrolsResource, trafficControl), &v1alpha2.TrafficControl{})
	if obj == nil {
		return nil, err
	}
	return obj.(*v1alpha2.TrafficControl), err
}

// Delete takes name of the trafficControl and deletes it. Returns an error if one occurs.
func (c *FakeTrafficControls) Delete(ctx context.Context, name string, opts v1.DeleteOptions) error {
	_, err := c.Fake.
		Invokes(testing.NewRootDeleteActionWithOptions(trafficcontrolsResource, name, opts), &v1alpha2.TrafficControl{})
	return err
}

// DeleteCollection deletes a collection of objects.
func (c *FakeTrafficControls) DeleteCollection(ctx context.Context, opts v1.DeleteOptions, listOpts v1.ListOptions) error {
	action := testing.NewRootDeleteCollectionAction(trafficcontrolsResource, listOpts)

	_, err := c.Fake.Invokes(action, &v1alpha2.TrafficControlList{})
	return err
}

// Patch applies the patch and returns the patched trafficControl.
func (c *FakeTrafficControls) Patch(ctx context.Context, name string, pt types.PatchType, data []byte, opts v1.PatchOptions, subresources ...string) (result *v1alpha2.TrafficControl, err error) {
	obj, err := c.Fake.
		Invokes(testing.NewRootPatchSubresourceAction(trafficcontrolsResource, name, pt, data, subresources...), &v1alpha2.TrafficControl{})
	if obj == nil {
		return nil, err
	}
	return obj.(*v1alpha2.TrafficControl), err
}
