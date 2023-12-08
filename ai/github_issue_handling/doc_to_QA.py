# -*- coding: utf-8 -*-

import os
import re
import glob
import json
from langchain.chat_models import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage

openai_key = 'chatgpt API'
chat_model = ChatOpenAI(openai_api_key=openai_key, model_name='gpt-3.5-turbo-16k', temperature=0.3)

prompt = "This is a .md document of the Antrea project on GitHub. The document content has been divided by titles. Now, I'm giving you a section containing the title and content of the document. You need to carefully read this section and convert its content into a Q&A pair. Each section can be converted into one or more Q&A pairs. The format of the Q&A pair is '''[{'Q': question content, 'A': answer content}, and so on]'''. Please think step by step and give the result."


def prompt_processing(chat_model, prompt, source):
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
                print(f"block is false")
                content = None
        else:
            content = chat.content
            break

    return content


if __name__ == '__main__':
    all_path = glob.glob('给出文档文件夹/*.md')
    num = 0
    datasets_result = []

    for idx, path in enumerate(all_path):
        print(idx)
        with open(path, 'r', encoding='utf-8') as fp:
            result = fp.read()
            context_block = [context for context in result.split('\n##') if
                             '<!-- toc -->' not in context and len(context) > 100]
            for con_b in context_block:
                # if num>0:break
                res = prompt_processing(chat_model, prompt=prompt, source=con_b)
                if res:
                    try:
                        qa_result = eval(res)
                        for qa in qa_result:
                            qa_format = {
                                "id": "identity_" + str(num),
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
                            datasets_result.append(qa_format)
                            num += 1
                    except:
                        print('xxx')
                        continue
    if len(datasets_result) > 0:
        with open('doc_datasets.json', 'w', encoding='utf-8') as f:
            json.dump(datasets_result, f, indent=4)
