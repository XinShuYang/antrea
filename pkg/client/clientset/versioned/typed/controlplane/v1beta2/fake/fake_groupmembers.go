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

	v1beta2 "antrea.io/antrea/pkg/apis/controlplane/v1beta2"
	v1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	testing "k8s.io/client-go/testing"
)

// FakeGroupMembers implements GroupMembersInterface
type FakeGroupMembers struct {
	Fake *FakeControlplaneV1beta2
	ns   string
}

var groupmembersResource = v1beta2.SchemeGroupVersion.WithResource("groupmembers")

var groupmembersKind = v1beta2.SchemeGroupVersion.WithKind("GroupMembers")

// Get takes name of the groupMembers, and returns the corresponding groupMembers object, and an error if there is any.
func (c *FakeGroupMembers) Get(ctx context.Context, name string, options v1.GetOptions) (result *v1beta2.GroupMembers, err error) {
	emptyResult := &v1beta2.GroupMembers{}
	obj, err := c.Fake.
		Invokes(testing.NewGetActionWithOptions(groupmembersResource, c.ns, name, options), emptyResult)

	if obj == nil {
		return emptyResult, err
	}
	return obj.(*v1beta2.GroupMembers), err
}
