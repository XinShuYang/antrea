# -*- coding: utf-8 -*-

import os
import json
import argparse
from langchain.chat_models import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage

body_prompts = {'body_prompt_1': """This is an issue data from the Antrea project on GitHub. In this data, the content of the first comment mainly includes the error message content when the author runs the project and the explanation content that the author tries to solve based on the error message. It also includes additional content from the author seeking help and expressing gratitude. Now, it is necessary to remove from this comment content that includes the author's requests for help and expressions of gratitude, retaining the error message content when the project is run and the explanation content that the author attempts to solve based on the error message.
                                    Firstly, you need to delete irrelevant content from the comment according to the following rules. The rules are as follows:
                                        a. Delete all words in the content that are composed of '@' followed by any character, such as @uablrek. This represents the author's name. The comment content should not contain the author's name.
                                        b. Delete sentences in the content that indicate the author needs help, as these are unrelated to the error messages of the project.
                                        c. Delete sentences in the content that express gratitude, as these are unrelated to the error messages of the project.
                                    Secondly, after deleting irrelevant content, you need to ensure the accuracy of the final comment content information according to the following requirements:
                                        The content should fully retain the error message content when the project is run and the explanation content that the author tries to solve based on the error message.
                                        The content should not contain words composed of '@' followed by any character, such as @uablrek.
                                        The content should not contain inquiries, expressions of gratitude and other descriptive content.
                                        The content should not include 'I', 'you', 'me', 'he' and other pronouns and words that represent salutations.
                                    Please follow the above rules and requirements, maintain the integrity of the error message descriptions that have not been deleted, and ensure the smoothness of the sentences after deleting irrelevant content. Avoid introducing personal interpretations, do not output unrelated or excessive information. Each step needs to be carefully considered, then output the result!
                                    Comment : 
                                """
    ,
                'body_prompt_2': """This is an Issue data from the Antrea project on GitHub. In this data, the content of the first comment mainly includes the error message when the author runs the project and the author's attempts to solve it based on the error message, as well as additional content such as the author's requests for help, thanks, and greetings.
                                    Now, it is necessary to remove from this comment content that includes the author's requests for help, thanks, and greetings, and completely retain the error message when the project is run and the author's attempts to resolve it based on the error message.
                                    The final output should not include the following information, the requirements are as follows:
                                        1. The sentence content should retain all links that start with https://github.com."
                                        2. The sentence content should not contain words composed of '@+ any characters', such as @uablrek.
                                        3. The sentence content should not contain descriptions of inquiries, greetings, or expressions of gratitude.
                                        4. The sentence content should not contain pronouns and other words expressing address such as 'I', 'you', 'me', 'he'.
                                    Follow the requirements to ensure the completeness of the error message content description and the fluency of the sentence after removing irrelevant content. Avoid introducing personal interpretation, do not output irrelevant or redundant information. Each step should be carefully considered, and then the result should be output!
                                    Comment:
                                """
    ,
                'body_prompt_3': """This is issue data from the Antrea project on GitHub. The body of this issue primarily contains descriptions of error messages encountered when running the project, descriptions of tests the author performed in attempts to resolve the issue, and content where the author seeks help, expresses gratitude, or sends greetings.
                                    Now, the task is to remove non-essential information from the body content while preserving the rest. The criteria are as follows:
                                        1. Preserve any error messages that occurred during project execution and any template formatting information related to the issue in the body.
                                        2. Retain all descriptions of the author's tests performed in attempts to resolve the problem.
                                        3. Exclude words formed by '@' followed by any characters in the body, such as @uablrek.
                                        4. Remove any content where the author is seeking help, sending greetings, expressing gratitude, etc.
                                    Adhere to these rules, ensuring the integrity and fluidity of the remaining content after removing non-essential information from the body. Please think carefully step by step, avoid personal interpretation, do not include irrelevant or redundant information, and then produce the output!
                                    Body: 
                                """
                }

label_prompt = """
                This is a labeled Issue data from the Antrea project on GitHub. The labels are assigned by manually interpreting the content of the Issue's body to determine its relevant categories. Each Issue can only be tagged with one or more labels from this list: ['bug', 'support', 'feature', 'proposal', 'api', 'arm', 'agent', 'antctl', 'cni', 'octant-plugin', 'flow-visibility', 'monitoring', 'multi-cluster', 'interface', 'network-policy', 'ovs', 'provider', 'proxy', 'test', 'transit', 'security', 'build-release', 'linux', 'windows'].
                Currently, there is an Issue from the Antrea project on GitHub with known title, body, and label(s). Your task is to analyze the title and body to interpret why this Issue was assigned these specific label(s) and summarize the main information from the analysis results. The output format should be {"result": 'The reason for choosing this label, without including the label word in the reasoning'}. Please think step by step and provide a concise and specific outcome!
                """


def main(args):
    json_data = []
    json_no_label_data = []
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
        no_label_num = 0
        for i, issue in enumerate(f):

            issue = eval(issue)
            result_labels = []
            if len(issue["lable"]) == 0:
                format = {
                    "id": "identity_" + str(no_label_num),
                    "conversations": [
                        {
                            "from": "human",
                            "value": f"title: {issue['title']}. body: {issue['body']}"
                        },
                        {
                            "from": "gpt",
                            "value": ''
                        }
                    ]
                }
                json_no_label_data.append(format)
                no_label_num += 1

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

            # prompt
            body_content = None
            label_result = list(set(result_labels))
            body_result = issue['body']
            # enhance
            def prompt_processing(prompt, source, issue_id):
                content = None
                messages = [
                    SystemMessage(
                        content=prompt
                    ),
                    HumanMessage(content=f"{source}"),
                ]

                for _ in range(5):
                    try:
                        chat = chat_model(messages)
                    except:
                        if _ == 4:
                            print(f"issue id {issue_id} false")
                            content = None
                    else:
                        content = chat.content
                        break

                return content

            if args.body_prompt:
                chat_model = ChatOpenAI(openai_api_key=args.openai_key, model_name='gpt-3.5-turbo-16k', temperature=0.3)

                try:
                    prompt = body_prompts[args.body_prompt]
                except:
                    raise ValueError("The body_prompt parameter is incorrect")
                body_content = prompt_processing(prompt=prompt, source=body_result, issue_id=issue['issue_id'])

            if body_content:
                body_result = body_content

            data_format = {
                "id": "identity_" + str(num),
                "conversations": [
                    {
                        "from": "human",
                        "value": f"title: {issue['title']}. body: {body_result}"
                    },
                    {
                        "from": "gpt",
                        "value": f"{label_result}"
                    }
                ]
            }

            json_data.append(data_format)
            num += 1

    if len(json_data) > 0:
        with open('issue_train_datasets.json', 'w') as fp:
            json.dump(json_data, fp, indent=4)

    if len(json_no_label_data) > 0:
        with open('issue_datasets_no_label.json', 'w') as fp:
            json.dump(json_no_label_data, fp, indent=4)

    if len(extra_labels) > 0:
        with open('extra_labels.json', 'w') as fp:
            json.dump(list(set(extra_labels)), fp, indent=4)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--assign-labels', nargs='+', default=[], help='Get mutil parameters')
    parser.add_argument('--add-labels', type=str, default=None, help='Dictionary parameter')
    parser.add_argument('--body-prompt', type=str, default=None,
                        help="Issue body prompt,Primarily summarize the body data, by default it is not applied, the V5 training data currently generated uses 'body_prompt_3'.")
    parser.add_argument('--openai-key', type=str, default=None,
                        help='When using ChatGPT to process the body, an OpenAI key is required.')
    args = parser.parse_args()
    main(args)
