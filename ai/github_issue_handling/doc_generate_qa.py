# -*- coding: utf-8 -*-

import os
import re
import glob
import json
import tiktoken
import argparse
from itertools import chain
from tqdm.auto import tqdm
from langchain.chat_models import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage

tokenizer = tiktoken.encoding_for_model("gpt-4-0613")

sys_prompt = "You are an assistant with a very strong logical ability and information analysis capability, especially adept at extracting high-quality question-and-answer pairs from articles. Please answer the questions as well as you can!"

hum_prompt = """It is known that the Antrea project has a markdown document related to the introduction and application of {fn}. This document has been divided into multiple sections according to the headings, with each section consisting of a higher-level heading and its content, as well as a subheading and its content. You are now provided with a section of content from the markdown document to generate Q&A pairs.
                Important Tips:
                    1.You can use the headings as the questions (Q), and the content under the headings as the answers (A).
                    2.The construction elements of Question Q *It should clearly define the main idea, have a clear relationship between the questions, be articulated in an easy-to-understand manner, and should not use imperative sentences to pose questions. The relationships between the nouns mentioned in the document should be clearly organized. The longer the text, the better.*
                    3.The construction elements of Answer A *It should retain the original content of the text while adding explanations already present in the document. Detailed operations (including the execution of commands) should be clearly explained, and it is best to add one's own understanding on top of the document's logic. The longer the text, the better.*
                Example of generating Q&A pairs:
                    1.'Q':"How can you view or change the log verbosity level of the Antrea Controller, Antrea Agent, or Flow Aggregator using Antrea?" ,'A': "Starting from version 0.10.0, Antrea supports showing or changing the log\nverbosity level of Antrea Controller or Antrea Agent using the `antctl log-level`\ncommand. Starting from version 1.5, Antrea supports showing or changing the\nlog verbosity level of the Flow Aggregator using the `antctl log-level` command.\nThe command can only run locally inside the `antrea-controller`, `antrea-agent`\nor `flow-aggregator` container.\n\nThe following command prints the current log verbosity level:\n\n```bash\nantctl log-level\n```\n\nThis command updates the log verbosity level (the `LEVEL` argument must be an\ninteger):\n\n```bash\nantctl log-level LEVEL\n```\n".
                    2.'Q':"After installing Antrea version 1.6, how to display the log verbosity level of the Flow Aggregator within the antrea-agent or flow-aggregator containers?",'A':"Starting from version 1.5, Antrea supports showing or changing the\nlog verbosity level of the Flow Aggregator using the `antctl log-level` command.\nThe command can only run locally inside the `antrea-controller`, `antrea-agent`\nor `flow-aggregator` container.\n\nThe following command prints the current log verbosity level:\n\n```bash\nantctl log-level\n```\n".
                    3.'Q':"After installing Antrea version 1.5, how to change the log verbosity level of the Flow Aggregator within the antrea-controller container?" ,'A':"Starting from version 1.5, Antrea supports showing or changing the\nlog verbosity level of the Flow Aggregator using the `antctl log-level` command.\nThe command can only run locally inside the `antrea-controller`, `antrea-agent`\nor `flow-aggregator` container.\n\nThe following command prints the current log verbosity level:\n\n```bash\nantctl log-level\n```\n\nThis command updates the log verbosity level (the `LEVEL` argument must be an\ninteger):\n\n```bash\nantctl log-level LEVEL\n```\n".
                Antrea Project Summary Information:
                    Antrea is a Kubernetes networking solution intended to be Kubernetes native. It operates at Layer 3/4 to provide networking and security services for a Kubernetes cluster, leveraging Open vSwitch as the networking data plane.Open vSwitch is a widely adopted high-performance programmable virtual switch; Antrea leverages it to implement Pod networking and security features. For instance, Open vSwitch enables Antrea to implement Kubernetes Network Policies in a very efficient manner. This document primarily concerns the introduction and usage of Antrea's basic functions.
                    Antrea has been tested with Kubernetes clusters running version 1.16 or later.
                        1.NodeIPAMController must be enabled in the Kubernetes cluster.When deploying a cluster with kubeadm the --pod-network-cidr <cidr> option must be specified. Alternately, NodeIPAM feature of Antrea Controller should be enabled and configured.
                        2.Open vSwitch kernel module must be present on every Kubernetes node.
                Be sure to use the important tips as a benchmark, focusing on analyzing the structure of the question Q and the corresponding structure of the answer A in the Q&A example, and use this to generate well-informed, logically clear, and precise Q&A pairs, The output format for the Q&A pair should be '''[{{'Q':"question content", 'A':"answer content"}}, *generate at least {qa_num} QA pairs.*]'''. thinking step by step and providing the results.
                block document:
            """
refined_hum_prompt = """
                    It is known that the Antrea project has a markdown document related to the introduction and application of '{fn}'. This document has been divided into multiple sections according to the headings, with each section consisting of a higher-level heading and its content, as well as a subheading and its content. You are now provided with a section of content from the markdown document to generate Q&A pairs.
                    Important Notice:
                        1.You may use headings for the question Q, with the content below the heading serving as the answer A.
                        2.Command line instruction strings, yaml configuration files, and other logs or error messages in block documents are usually enclosed within ``` to demarcate the command string, yaml configuration, or other log and error messages.
                        3.The answer A must contain the complete command string or yaml configuration file or other log and error information without truncation, preserving the original content in full. Do not make any other changes.
                    Exact Requirements:
                        1.Construction elements for the question Q: The main point should be clear, with understandable relationships between the questions, and the expressions should be easy to understand. Do not use imperative sentences for questions. The relationships between the terms mentioned in the document should be clearly organized. The longer the text, the better.
                        2.Construction elements for the answer A: The answer must contain detailed and complete command strings or yaml configuration files, or other log and error information as originally presented in the content. It is acceptable to add your own understanding based on the existing logic of the document. The longer the text, the better.
                        3.Each generated QA pair in the answer A must include a complete command line execution command string, or a yaml configuration file, or other complete log and error information. If the answer A does not contain a complete command string, yaml configuration file, or other log and error information, then that QA pair is incorrect.
                    Strictly follow the important notes to generate information-rich, logically clear, and coherent QA pairs. The output format for the Q&A pairs should be: '''[{{'Q': "Question Content", 'A': "Answer Content"}}]'''. Think step by step and provide the results.
                    block document: 
                    """

title_prompt = "It is known that the Antrea project has a markdown document related to the introduction and application of '{fn}'. I will give you a heading text from this document or two heading texts with a clear parent-child relationship, please generate a question sentence for me. The output format should be: '''{{'Question': one succinct question sentence}}'''，Please strictly adhere to the output format!"

title_prompt_3 = "It is known that the Antrea project has a markdown document related to the introduction and application of '{fn}'. I will give you a title from this document or two related titles with a clear hierarchy, along with a segment of body text. Please distill the information from the body text to refine the title(s), and then create just one concise question sentence. The output format should be: '''{{'Question': one succinct question sentence}}'''，Please strictly adhere to the output format!"


def chat_generate(chat_model, prompt, source):
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
            content = eval(chat.content)['Question']
            # content = chat.content
        except:
            if _ == 4:
                print(f"block is false")
                content = None
        else:
            content = content
            break

    return content


def get_title(txt):
    return re.search(r'#.*?\n', txt).group()


def get_context(txt):
    return re.search(r'#.*?\n', txt).end()


def get_qa_format(idx, inputs, outputs):
    if isinstance(inputs, list):
        pass
    else:
        print("The data format generated by GPT is not an iterator.")
        pass
    try:
        for qa in inputs:
            qa_format = {
                "id": "identity_" + str(idx),
                "conversations": [
                    {
                        "from": "human",
                        "value": f"{qa['Q']}"
                    },
                    {
                        "from": "gpt",
                        "value": f"{qa['A']}"
                    }
                ]
            }
            outputs.append(qa_format)
            idx += 1
    except:
        pass
    return idx, outputs


def get_q_format(idx, in_dox, q_txt, a_txt):
    qa_format = {
        "id": "identity_" + str(idx),
        # "doc": f'{in_dox}',
        "conversations": [
            {
                "from": "human",
                "value": f"{q_txt}"
            },
            {
                "from": "gpt",
                "value": f"{a_txt}"
            }
        ]
    }
    idx += 1
    return idx, qa_format


def get_block_data(doc_contexts, drop_len=1):
    block_dict_data = {}
    block_data = []
    block_context = ['## ' + context if idx != 0 else context for idx, context in
                     enumerate(doc_contexts.split('\n## ')) if
                     '<!-- toc -->' not in context and '<!-- TOC -->' not in context]
    for i, block in enumerate(block_context):

        one_title = get_title(block)
        one_context = block[get_context(block):]

        if i == 0 and len(block_context) > 1:
            if len(one_context) > 0:
                block_dict_data[one_title] = one_context
                continue
            else:
                continue

        # 处理只有一个一级标题文档
        if i == 0 and len(block_context) == 1:
            block_data.append(block)
            block_dict_data[one_title] = one_context
            continue

        if len(re.findall('\n### ', block)) >= 2:
            two_level_context = [context if idx == 0 else '### ' + context for idx, context in
                                 enumerate(block.split('\n### '))]
            block_data.append(block_context[0] + two_level_context[0])

            one_title = get_title(block_context[0])
            two_title = get_title(two_level_context[0])
            two_context = two_level_context[0][get_context(two_level_context[0]):]
            if len(two_context) > 0:
                block_dict_data[one_title + two_title] = two_context

            for j, two_level_block in enumerate(two_level_context):
                if j == 0: continue

                t_title = get_title(two_level_context[0])
                three_title = get_title(two_level_block)
                three_context = two_level_block[get_context(two_level_block):]

                if len(re.findall('\n#### ', two_level_block)) >= 2:
                    three_level_context = [context if idx == 0 else '#### ' + context for idx, context in
                                           enumerate(two_level_block.split('\n#### '))]

                    block_data.append(two_level_context[0] + three_level_context[0])

                    tr_title = get_title(two_level_context[0])
                    four_title = get_title(three_level_context[0])
                    four_text = three_level_context[0][get_context(three_level_context[0]):]
                    if len(four_text) > 0:
                        block_dict_data[tr_title + four_title] = four_text

                    for m, three_level_block in enumerate(three_level_context):
                        if m == 0: continue

                        tf_title = get_title(three_level_context[0])
                        five_title = get_title(three_level_block)
                        five_context = three_level_block[get_context(three_level_block):]

                        if len(re.findall('\n##### ', three_level_block)) >= 2:

                            four_level_context = [context if idx == 0 else '##### ' + context for idx, context in
                                                  enumerate(three_level_block.split('\n##### '))]

                            block_data.append(three_level_context[0] + four_level_context[0])

                            tc_title = get_title(three_level_context[0])
                            six_title = get_title(four_level_context[0])
                            six_context = four_level_context[0][get_context(four_level_context[0]):]
                            if len(six_context) > 0:
                                block_dict_data[tc_title + six_title] = six_context

                            for n, four_level_block in enumerate(four_level_context):
                                if n == 0: continue

                                ts_title = get_title(four_level_context[0])
                                seven_title = get_title(four_level_block)
                                seven_context = four_level_block[get_context(four_level_block):]

                                if len(re.findall('\n###### ', four_level_block)) >= 2:
                                    print('有6级标题，请做处理！')
                                elif len(re.findall('\n###### ', four_level_block)) == 1:
                                    block_data.append(four_level_block)

                                    tv123_context = '\n' + four_level_block.split('\n### ')[-1]
                                    match_t123 = re.compile(r'(?<=#)[^#\n]*(?=\n)').findall(four_level_block)
                                    tv123_title = '##' + match_t123[0] + '\n' + '###' + match_t123[1] + '\n'
                                    if len(tv123_context) > 0:
                                        block_dict_data[tv123_title] = tv123_context

                                else:
                                    if len(seven_context.split(' ')) >= drop_len:
                                        block_data.append(four_level_context[0] + four_level_block)
                                        block_dict_data[ts_title + seven_title] = seven_context
                                    else:
                                        pass

                        elif len(re.findall('\n##### ', three_level_block)) == 1:
                            block_data.append(three_level_block)

                            tv12_context = '\n' + three_level_block.split('\n### ')[-1]
                            match_t12 = re.compile(r'(?<=#)[^#\n]*(?=\n)').findall(three_level_block)
                            tv12_title = '##' + match_t12[0] + '\n' + '###' + match_t12[1] + '\n'
                            if len(tv12_context) > 0:
                                block_dict_data[tv12_title] = tv12_context

                        else:
                            if len(five_context.split(' ')) >= drop_len:
                                block_data.append(three_level_context[0] + three_level_block)
                                block_dict_data[tf_title + five_title] = five_context
                            else:
                                pass
                elif len(re.findall('\n#### ', two_level_block)) == 1:
                    block_data.append(two_level_block)

                    tv1_context = '\n' + two_level_block.split('\n### ')[-1]
                    match_t1 = re.compile(r'(?<=#)[^#\n]*(?=\n)').findall(two_level_block)
                    tv1_title = '##' + match_t1[0] + '\n' + '###' + match_t1[1] + '\n'
                    if len(tv1_context) > 0:
                        block_dict_data[tv1_title] = tv1_context

                else:
                    if len(three_context.split(' ')) >= drop_len:
                        block_data.append(two_level_context[0] + two_level_block)
                        block_dict_data[t_title + three_title] = three_context
                    else:
                        pass
        elif len(re.findall('\n### ', block)) == 1:
            block_data.append(block)

            tv_context = '\n' + block.split('\n### ')[-1]
            match_t = re.compile(r'(?<=#)[^#\n]*(?=\n)').findall(block)
            tv_title = '##' + match_t[0] + '\n' + '###' + match_t[1] + '\n'
            if len(tv_context) > 0:
                block_dict_data[tv_title] = tv_context
        else:
            block_data.append(block_context[0] + block)
            o_title = get_title(block_context[0])
            block_dict_data[o_title + one_title] = one_context

    return block_dict_data


def main(args):
    chat_model = ChatOpenAI(openai_api_key=args.openai_key, model_name='gpt-4-0613', temperature=0.9)

    if isinstance(args.docs_dir, str):
        all_path = glob.glob(f'{args.docs_dir}/*.md')
    else:
        raise 'args.docs_dir is error'

    num = 0
    data = {}
    data_result = []
    for idx, path in enumerate(all_path):

        doc_name = os.path.basename(path).split('.')[0]
        data[doc_name] = {}
        with open(path, 'r', encoding='utf-8') as fp:
            doc_context = fp.read()

        hash_sequences = re.findall(r'#+', doc_context)
        longest_sequence = max(hash_sequences, key=len)
        if len(longest_sequence) >= 5: print(len(longest_sequence))
        data[doc_name].update(get_block_data(doc_contexts=doc_context))

    for _, (doc, bz_block) in enumerate(data.items()):
        for idc, (title, block) in enumerate(bz_block.items()):
            block_sz = []
            if len(tokenizer.encode(block)) > 2500:
                sz = []
                bk_split = block.split('\n\n')
                for bs in bk_split:
                    sz.append(bs)
                    if len(tokenizer.encode(''.join(sz))) > 2000:
                        block_sz.append(''.join(sz))
                        if len(tokenizer.encode(block[len(''.join(sz[:-1])):])) <= 2500:
                            block_sz.append(block[len(''.join(sz[:-1])):])
                            break
                        else:
                            sz = []
            if len(block_sz) > 0:
                for block in block_sz:
                    if len(title.split(' ')) >= 8:
                        # 0.
                        sys_prompt = title_prompt.format(fn=doc_name)
                        source = 'title contxt: ' + title
                    else:
                        ## 1.
                        ## sys_prompt = title_prompt_2.format(fn=doc_name)
                        ## source = 'title context:' + title + '\n' + 'explanatory text:' + block
                        sys_prompt = title_prompt_3.format(fn=doc_name)
                        source = 'title context:' + title + '\n' + 'body text:' + block
                    q_result = chat_generate(chat_model, prompt=sys_prompt, source=source)
                    if q_result:
                        re_num, qa_format = get_q_format(idx=num, in_dox=doc, q_txt=q_result, a_txt=block)
                        data_result.append(qa_format)
                        num = re_num
            else:
                if len(title.split(' ')) >= 8:
                    # 0.
                    sys_prompt = title_prompt.format(fn=doc_name)
                    source = 'title contxt: ' + title
                else:
                    ## 1.
                    ## sys_prompt = title_prompt_2.format(fn=doc_name)
                    ## source = 'title context:' + title + '\n' + 'explanatory text:' + block
                    sys_prompt = title_prompt_3.format(fn=doc_name)
                    source = 'title context:' + title + '\n' + 'body text:' + block
                q_result = chat_generate(chat_model, prompt=sys_prompt, source=source)
                if q_result:
                    re_num, qa_format = get_q_format(idx=num, in_dox=doc, q_txt=q_result, a_txt=block)
                    data_result.append(qa_format)
                    num = re_num
            print(idc, end='---')
            print(f'{title}')

    if len(data_result) > 0:
        with open(f'{args.output}', 'w', encoding='utf-8') as f:
            json.dump(data_result, f, indent=4)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--docs-dir', default=None, required=True,
                        help="the folder where the document is located,example  docs_dir = './base_docs'")
    parser.add_argument('--openai-key', default=None, required=True, help='OpenAI key for GPT-4')
    parser.add_argument('--output', default=None, required=True, help='qa path')
    args = parser.parse_args()
    # docs_dir = './base_docs'
    main(args)
