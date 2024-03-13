# -*- coding: utf-8 -*-

import os
import json
import argparse


def main(args):
    json_data = []
    extra_labels = []
    mapped_labels = {
        'kind/bug': 'bug',
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

    # op: add new labels
    source_labels_path = './source_labels.json'
    if os.path.exists(source_labels_path) and os.path.getsize(source_labels_path) > 4:
        with open(source_labels_path, 'r', encoding='utf-8') as fp:
            mapped_labels = json.load(fp)
        if args.add_labels is not None:
            mapped_labels.update(eval(args.add_labels))
            with open(source_labels_path, 'w', encoding='utf-8') as fp:
                json.dump(mapped_labels, fp, indent=1)
    else:
        if args.add_labels is not None:
            mapped_labels.update(eval(args.add_labels))
        with open(source_labels_path, 'w', encoding='utf-8') as fp:
            json.dump(mapped_labels, fp, indent=1)

    if len(args.assign_labels) > 0:
        for lb in args.assign_labels:
                if lb not in list(mapped_labels.values()):
                    print('Please specify the correct labels name !')
                    exit(-1)

        labels_mapping = {key: value for key, value in mapped_labels.items() if value in args.assign_labels}
    else:
        labels_mapping = mapped_labels

    with open('issue_filter.json', 'r', encoding='utf-8') as f:
        num = 0
        for i, issue in enumerate(f):

            issue = eval(issue)
            result_labels = []

            if len(issue["lable"]) > 0:
                source_label = issue["lable"]
                middle_label = [item.split('/', 2)[0] + '/' + item.split('/', 2)[1] if item not in list(
                    labels_mapping.keys()) and item.count('/') > 1 else item for
                                item in source_label]
                for idx, label in enumerate(middle_label):
                    if label in list(labels_mapping.keys()):
                        result_labels.append(labels_mapping[label])
                    else:
                        extra_labels.append(source_label[idx])
            else:
                continue

            if len(result_labels) == 0: continue

            data_format = {
                "id": "identity_" + str(num),
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
            num += 1

    if len(json_data) > 0:
        with open('issue_datasets.json', 'w') as fp:
            json.dump(json_data, fp, indent=1)

    if len(extra_labels) > 0:
        with open('extra_labels.json', 'w') as fp:
            json.dump(list(set(extra_labels)), fp, indent=1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--assign-labels', nargs='+', default=[], help='get mutil parameters')
    parser.add_argument('--add-labels', type=str, default=None, help='Dictionary parameter')
    args = parser.parse_args()
    main(args)
