# -*- coding: utf-8 -*-

import os
import json

if __name__ == "__main__":
    json_data = []
    labels_replace = {'bug': 'api',
                      'support': 'arm',
                      'feature': 'agent',
                      'proposal': 'antctl'
                      }
    labels_useful = ['api', 'arm', 'agent', 'antctl', 'cni', 'octant-plugin', 'flow-visibility', 'monitoring',
                     'multi-cluster',
                     'interface', 'network-policy', 'ovs', 'provider', 'proxy', 'test', 'transit', 'security',
                     'build-release']

    with open('issue.json', 'r', encoding='utf-8') as f:

        for idx, issue in enumerate(f):

            issue = eval(issue)
            result_labels = []

            if len(issue["lable"]) > 0:
                labels_pro = list(set([res_label for items in [str.split('/') for str in issue["lable"]] for res_label in items]))
                for label in labels_pro:
                    if label in labels_useful:
                        result_labels.append(label)
                    if label in list(labels_replace.keys()):
                        result_labels.append(labels_replace[label])
            else:
                continue

            if len(result_labels) == 0: continue

            data_format = {
                "id": "identity_" + str(idx),
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
        with open('issue_datasets_v2.json', 'w') as fp:
            json.dump(json_data, fp, indent=1)
