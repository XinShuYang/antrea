# -*- coding: utf-8 -*-

import re
import json
import tiktoken
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain.chat_models import ChatOpenAI
# from langchain_openai import ChatOpenAI
from github import Github
from github import Auth
import argparse

tokenizer = tiktoken.encoding_for_model("gpt-4-0314")

## GPT4
body_prompt_jude = "Given the main text of a problem data, please analyze that content and determine whether it describes an error message. If it does, please output True; if not, please output False. The required output format is {'result': (True or False)}. Think step by step and provide the result. Main text content:"
comments_prompt_jude = "I have a list of conversations that contain multiple dialogues. Please analyze whether these conversations include specific solutions or clear instructions for operational steps. If so, output as True; otherwise, output as False. The output format should be {'result': True or False}. Let's proceed step by step."
# 1.
sys_summary_prompt = "You are an experienced data analysis engineer, particularly skilled at analyzing and extracting key information from multiple conversations and integrating it into a coherent text. Please answer the questions as well as you can!"
hum_summary_prompt = """There is an issue data from the Antrea project, where only the dialogue content from multiple commenters under the Issue data is taken and provided to you. Now you need to analyze these dialogue contents and extract the key information to merge into a smooth text.
                        Important hints:
                            1.The key information should be specific, explicit, and clear in its description of the solution.
                            2.After extracting the key information, compose it into a text passage. This should be from the perspective of the proposer, using the first-person narrative to rephrase the information. Moreover, the tone of the text should reflect that it is being considered from the standpoint of proposing solutions and presenting outcomes.
                            3.If information about a PR submission is provided outside the context of the conversation, then this PR is certainly a solution to the current problem. The text information should include the names of the files involved, the names of the functions within these files, and detailed changes within the code of these functions. Display the code changes using Markdown format. At the end of the text information, declare that the issue has been resolved and provide the specific date, accurate to the day.
                            4.The text information should avoid including expressions that reveal twists or interpretative statements based on new findings or results that emerged later.
                        Exact requirements:
                            1.The text information must not contain words composed of '@' followed by any characters, such as @uablrek.
                            2.The text information must not contain descriptions of inquiries or expressions of gratitude.
                            3.The text information must not contain descriptions of PR requests, submissions, closures, etc.
                            4.The text information must not contain suggestions for modifications to documentation.
                        Make sure to base your analysis on the important hints, strictly follow the requirements and use this to assist in generating a brief text content from analyzing multiple conversation contents. The output format should be {{'result':'brief text content'}}. Think step by step and provide the results!"
                        Issue comments: {info}
                        PR information: {pr_info}
                     """
# 2.
sample_prompt_summary = "You have a list of dialogues that mainly discuss and attempt to solve a certain problem. Information on the solutions should include specific methods or clear operation instructions, along with detailed parameter configurations. Please summarize the main solutions from these dialogues, making sure to retain the complete commands and parameter settings. Finally, from the perspective of the advisor, use the second person to express the solution methods. Avoid using pronouns, and the longer the sentences, the better. Take it step by step."

##local model
sample_prompt_summary = "I have a list of dialogues; please summarize the dialogue text. The summary should involve specific solutions or clear directive operations, without any pronouns. Lastly, express the entire text in the first person, and the longer the sentences, the better. step by step!"


# sample_prompt_summary = "You have a list of dialogues that mainly discuss and attempt to solve a certain problem. Information on the solutions should include specific methods or clear operation instructions, along with detailed parameter configurations. Please summarize the main solutions from these dialogues, making sure to retain the complete commands and parameter settings. Finally, from the perspective of the advisor, use the second person to express the solution methods. Avoid using pronouns, and the longer the sentences, the better. Take it step by step."
# sample_prompt_summary = "Given a list of dialogues, you need to extract key information from the conversational data. The key information should involve specific solutions or clear operational instructions, as well as detailed parameter configurations. Then, integrate them into a single sentence. Retain the complete commands and parameter configurations, do not include pronominal references, avoid suggestions for modifying documents, and finally, express the entire sentence from the perspective of the advisor using the second person. The longer the sentence, the better. Take it step by step."
# sample_prompt_summary = local_summary_prompt


def chat_generate(chat_model, source, prompt, model_type='GPT'):
    content = None
    for _ in range(5):
        try:
            if model_type == 'GPT':
                chat = chat_model([
                    SystemMessage(
                        content=prompt
                    ),
                    HumanMessage(content=f"{source}"),
                ])
                content = chat.content
            else:
                chat = chat_model([SystemMessage(content=prompt), HumanMessage(content=f"{source}"), ])
                content = chat.content
        except:
            if _ == 4:
                print(f"Request failed!")
        else:
            break

    return content


def get_pull_request(auth, issue_id):
    # Public Web Github
    g = Github(auth=auth)
    repo = g.get_repo('antrea-io/antrea')

    issue = repo.get_issue(number=int(issue_id))
    data = None
    # 通过时间线事件查找相关的提交
    for event in issue.get_timeline():
        # 检查事件类型
        # print(event.event)
        if event.event == "referenced":
            try:
                # 获取事件相关的提交SHA
                commit_sha = event.commit_id
                # 获取提交对象
                commit = repo.get_commit(sha=commit_sha)
            except:
                return []
            pr_str = f"PR submission information:{{'commit_message':{commit.commit.message},'commit_date':{commit.commit.author.date}}}。"
            # 获取文件更改信息
            for file in commit.files:
                pr_str += f"Filename and changes made to the file:{{'filename':{file.filename},'diff':{file.patch}}}"
            data = pr_str

    return data


def get_public_data(public_data_dir):
    num_id = 0
    result_list = []
    unuseful_sentences1 = "This issue is stale because it has been open 90 days with no activity. Remove stale label or comment, or this will be closed in 90 days"
    unuseful_sentences2 = "This issue is stale because it has been open 180 days with no activity. Remove stale label or comment, or this will be closed in 180 days"
    with open(f'{public_data_dir}', 'r', encoding='utf-8') as fp:
        for _, issue in enumerate(fp):
            result_comments = {}
            issue_line = eval(issue)
            # if issue_line["issue_id"]=="1171":
            #     print('xx')
            if len(issue_line['comment']) > 0:
                issue_comments = list(dict.fromkeys(issue_line['comment']))
                issue_comments_fl = [sent for sent in issue_comments if
                                     sent != unuseful_sentences1 and sent != unuseful_sentences2]
                issue_comments_cl = [sent for sent in issue_comments_fl if
                                     'close' not in sent.split(' ') and 'Closing' not in sent.split(' ') and
                                     'Close' not in sent.split(' ') and 'closing' not in sent.split(' ')]

                if len(issue_comments_cl) > 0:
                    res = False
                    if len(issue_comments_cl) == 1 and len(issue_comments_cl[0].split(' ')) >= 20:
                        res = True

                    if len(issue_comments_cl) == 2 and len(issue_comments_cl[0].split(' ')) >= 10 and len(
                            issue_comments_cl[1].split(' ')) >= 10:
                        res = True

                    if len(issue_comments_cl) > 2:
                        res = True

                    if res:
                        result_comments['id'] = num_id
                        result_comments['issue_id'] = issue_line['issue_id']
                        result_comments['labels'] = issue_line["lable"]
                        result_comments['title'] = issue_line['title']
                        result_comments['body'] = issue_line['body']
                        result_comments['comments'] = issue_comments_cl

            if result_comments != {}:
                if '**Test plan**' not in result_comments['body']:
                    if len(result_comments['body'].split(' ')) > 20 and all(
                            substring not in ''.join(result_comments['labels']) for substring in
                            ['area/test', 'failing-test']):
                        if len(result_comments['comments']) == 1:
                            if len(result_comments['comments'][0].split(' ')) > 50:
                                num_id += 1
                                result_list.append(result_comments)
                        else:
                            num_id += 1
                            result_list.append(result_comments)
    return result_list


def get_private_data(private_data_dir):
    num_id = 0
    result_list = []
    unuseful_sentences1 = ''
    unuseful_sentences2 = ''
    with open(f'{private_data_dir}', 'r', encoding='utf-8') as fe:
        for _, issue in enumerate(json.load(fe)):
            result_comments = {}
            issue_line = issue
            if len(issue_line['comments']) > 0:
                issue_comments = list(dict.fromkeys(issue_line['comments']))
                issue_comments_fl = [sent for sent in issue_comments if
                                     sent != unuseful_sentences1 and sent != unuseful_sentences2]
                issue_comments_cl = [sent for sent in issue_comments_fl if
                                     'close' not in sent.split(' ') and 'Closing' not in sent.split(' ') and
                                     'Close' not in sent.split(' ') and 'closing' not in sent.split(' ')
                                     ]
                # and 'patches' not in sent.split(' ') and 'patch' not in sent.split(' ')]

                if len(issue_comments_cl) > 0:
                    res = False
                    if len(issue_comments_cl) == 1 and len(issue_comments_cl[0].split(' ')) >= 20:
                        res = True

                    if len(issue_comments_cl) == 2 and len(issue_comments_cl[0].split(' ')) >= 10 and len(
                            issue_comments_cl[1].split(' ')) >= 10:
                        res = True

                    if len(issue_comments_cl) > 2:
                        res = True

                    if res:
                        result_comments['id'] = num_id
                        result_comments['title'] = issue_line['title']
                        result_comments['body'] = issue_line['body']
                        result_comments['comments'] = issue_comments_cl

            if result_comments != {}:
                if '**Test plan**' not in result_comments['body']:
                    if len(result_comments['body'].split(' ')) > 10:
                        if len(result_comments['comments']) == 1:
                            if len(result_comments['comments'][0].split(' ')) > 50:
                                num_id += 1
                                result_list.append(result_comments)
                        else:
                            num_id += 1
                            result_list.append(result_comments)
    return result_list


def main(args):
    data_type = args.data_type if args.data_type else 'public'
    use_model_type = args.use_model_type if args.use_model_type else 'GPT'

    auth = Auth.Token(args.OAuth2_token)
    gpt_model = ChatOpenAI(openai_api_key=args.openai_key, model_name='gpt-4-0613', temperature=0)
    local_model = ChatOpenAI(openai_api_key=args.local_api_key, model_name=args.local_model_name,
                             openai_api_base=args.local_api_base,
                             temperature=0)

    assert data_type != 'private' or use_model_type != 'GPT', "Parameters values 'private' and 'GPT' cannot be used together"

    result_list = []
    if data_type == 'public':
        result_list = get_public_data(args.public_data_dir)
        with open('public_solution_data.json', 'w', encoding='utf-8') as fs:
            json.dump(result_list, fs, indent=4)
    elif data_type == 'private':
        result_list = get_private_data(args.private_data_dir)
        with open('private_solution_data.json', 'w', encoding='utf-8') as fs:
            json.dump(result_list, fs, indent=4)
    else:

        raise "Parameters data_type are incorrect"

    if len(result_list) > 0:
        result = []
        num_ic = 0
        for idx, data in enumerate(result_list):
            print(idx, end='  ')
            input_cont = {}
            input_cont['comments'] = data['comments']
            content = ''
            # gpt model
            if use_model_type == 'GPT':
                # Reduce token expenditure
                body_len = len(tokenizer.encode(data['body']))
                comments_len = len(tokenizer.encode(' '.join(data['comments'])))
                comments_data = f"""Conversation List: {input_cont['comments']}"""

                if body_len < comments_len:
                    # 判断是否是一个错误信息的描述
                    body_result = chat_generate(gpt_model, source=data['body'], prompt=body_prompt_jude)
                    if body_result:
                        # 判断对话内容中是否是有提供明确的解决方法
                        comments_result = chat_generate(gpt_model, source=comments_data, prompt=comments_prompt_jude)
                        if comments_result:
                            pass
                        else:
                            continue
                    else:
                        continue
                else:
                    comments_result = chat_generate(gpt_model, source=comments_data, prompt=comments_prompt_jude)
                    if comments_result:
                        body_result = chat_generate(gpt_model, source=data['body'], prompt=body_prompt_jude)
                        if body_result:
                            pass
                        else:
                            continue
                    else:
                        continue

                if body_result and comments_result:
                    PR = get_pull_request(auth, data['issue_id'])
                    # source = hum_summary_prompt.format(info=input_cont, pr_info=pr if pr else None)
                    # content = chat_generate(gpt_model,source=source, prompt=sys_summary_prompt)

                    input_cont['comments'].append(PR)
                    if len(tokenizer.encode(f"{input_cont['comments']}")) > 6000:
                        continue
                    source = f"""Conversation List: {input_cont['comments']}"""
                    content = chat_generate(gpt_model, source=source, prompt=sample_prompt_summary)

            # local model
            else:
                source = f"""Conversation List: {input_cont}"""
                content = chat_generate(local_model, source=source, prompt=sample_prompt_summary,
                                        model_type=use_model_type)

            if content != '':
                qa_format = {
                    "id": "identity_" + str(num_ic),
                    "conversations": [
                        {
                            "from": "human",
                            "value": f"issue title:{data['title']},issue body:{data['body']}"
                        },
                        {
                            "from": "gpt",
                            "value": f"{content}"
                        }
                    ]
                }

                num_ic += 1
                result.append(qa_format)
        if len(result) > 0:
            with open(f"./{data_type}_solution_dataset.json", 'w', encoding='utf-8') as fc:
                json.dump(result, fc, indent=6)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--OAuth2-token', default=None, required=True, help="GitHub personal account access token")
    parser.add_argument('--openai-key', default=None, required=True, help='OpenAI key for GPT-4')

    parser.add_argument('--local-api-key', default="EMPTY",
                        help="example:EMPTY ,For details, please refer to the Langchain documentation.")
    parser.add_argument('--local-model-name', default='vicuna-base_docs_v2',
                        help="example:vicuna ,For details, please refer to the Langchain documentation.")
    parser.add_argument('--local-api-base', default='http://8.217.24.14:8001/v1',
                        help="example:'http://ip:port/v1',For details, please refer to the Langchain documentation.")

    parser.add_argument('--data-type', default='public',
                        help="Select the type of data processing, open-source data 'public', and private data 'private'.")
    parser.add_argument('--public-data-dir', default=None, required=True,
                        help="Open-source data path")
    parser.add_argument('--private-data-dir', default=None,
                        help="Private-source data path")
    parser.add_argument('--use-model-type', default='GPT',
                        help="There are two models for processing data: using the online model 'GPT', and using the local model 'vicuna'")
    args = parser.parse_args()
    main(args)
