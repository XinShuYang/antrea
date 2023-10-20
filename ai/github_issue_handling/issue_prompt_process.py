# -*- coding: utf-8 -*-

import os
import json

if __name__ == "__main__":
    json_data = []
    extra_labels = []
    labels_mapping = {'kind/bug': 'bug',
                      'kind/support': 'support',
                      'kind/feature': 'feature',
                      'proposal': 'proposal',
                      'area/api': 'api',
                      'area/arch/arm': 'arm',
                      'area/component/agent': 'agent',
                      'area/component/antctl': 'antctl',
                      'area/component/cni': 'cni',
                      'area/component/octant-plugin': 'octant-plugin',
                      'area/flow-visibility': 'flow-visibility',
                      'area/monitoring': 'monitoring',
                      'area/multi-cluster': 'multi-cluster',
                      'area/interface': 'interface',
                      'area/network-policy': 'network-policy',
                      'area/ovs': 'ovs',
                      'area/provider': 'provider',
                      'area/proxy': 'proxy',
                      'area/test': 'test',
                      'area/transit': 'transit',
                      'area/security': 'security',
                      'area/build-release': 'build-release',
                      'area/OS/linux': 'linux',
                      'area/OS/windows': 'windows'
                      }

    with open('issue_filter.json', 'r', encoding='utf-8') as f:

        for i, issue in enumerate(f):

            issue = eval(issue)
            result_labels = []

            if len(issue["lable"]) > 0:
                source_label = issue["lable"]
                middle_label = [item.split('/', 2)[0] + '/' + item.split('/', 2)[1] if item not in list(labels_mapping.keys()) and item.count('/') > 1 else item for
                                item in source_label]
                for idx,label in enumerate(middle_label):
                    if label in list(labels_mapping.keys()):
                        result_labels.append(labels_mapping[label])
                    else:
                        extra_labels.append(source_label[idx])
            else:
                continue

            if len(result_labels) == 0: continue

            data_format = {
                "id": "identity_" + str(i),
                "conversations": [
                    {
                        "from": "human",
                        "value": f"title: {issue['title']}. body: {issue['body']}"
                    },
                    {
                        "from": "gpt",
                        "value": f"{list(set(result_labels))}"
                    }
                ]
            }

            if data_format['conversations'][1]['value'] == "No label":
                continue
            json_data.append(data_format)

    if len(json_data) > 0:
        with open('issue_datasets.json', 'w') as fp:
            json.dump(json_data, fp, indent=1)

    if len(extra_labels) > 0:
        with open('extra_labels.json', 'w') as fp:
            json.dump(list(set(extra_labels)), fp, indent=1)
