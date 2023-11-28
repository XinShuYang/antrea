# -*- coding: utf-8 -*-

import json
import argparse
from openai import OpenAI


max_tokens = 4096
temperature = 0.3
sys_prompt = "You are an assistant for Antrea, a software that provides networking and security services for a Kubernetes cluster. Please only output the classification results, with the optional word list for classification results ['bug', 'support', 'feature', 'proposal', 'api', 'arm', 'agent', 'antctl', 'cni', 'octant-plugin', 'flow-visibility', 'monitoring', 'multi-cluster', 'interface', 'network-policy', 'ovs', 'provider', 'proxy', 'test', 'transit', 'security', 'build-release', 'linux', 'windows']. You can only select one or more words from these words as the output result, which are enclosed in quotation marks and connected by commas."


def main(args):
    # you openai key
    openai_api_key = args.openai_key
    # The job id of the model is trained using the training data based on chatgpt
    ft_job_id = args.job_id

    client = OpenAI(api_key=openai_api_key)
    ft_model_name = client.fine_tuning.jobs.retrieve(ft_job_id).fine_tuned_model

    with open('issue_datasets_no_label.json', 'r', encoding='utf-8') as fp:
        json_data = json.load(fp)
        for i, dt in enumerate(json_data):
            messages = [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": dt['conversations'][0]['value']}
            ]
            response = client.chat.completions.create(
                model=ft_model_name,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=messages
            )

            dt['conversations'][1]['value'] = str([response.choices[0].message.content.replace("'", "")])

        with open('issue_evaluate_datasets.json', 'w', encoding='utf-8') as ft:
            json.dump(json_data, ft, indent=4)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--openai-key', type=str, default=None, required=True, help='Need openai key')
    parser.add_argument('--job-id', type=str, default=None, required=True,
                        help='The job ID of the model after ChatGPT training has been completed.')
    args = parser.parse_args()
    main(args)
