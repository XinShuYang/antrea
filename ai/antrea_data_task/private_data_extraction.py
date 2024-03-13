# -*- coding: utf-8 -*-

import re
import glob
import json
from lxml import etree
import argparse


def extra_cgi_to_json(args):
    example_datas = []
    cgi_list = glob.glob(f'{args.private_cgi_file}/*.cgi')
    for idx, cgi_path in enumerate(cgi_list):
        issue_dict = {}
        issue_dict['id'] = idx
        with open(cgi_path, 'r', encoding='utf-8') as file:
            cgi_content = file.read()
        html_tree = etree.HTML(cgi_content)

        # title
        title = html_tree.xpath('//title/text()')[0]
        # issue_dict['title'] = title.strip()

        pattern = r"Bug \d+ – \[[^\]]+\] "
        title_text = re.sub(pattern, '', title)
        title_text = re.sub(r'Bug \d+ – ', '', title_text)
        issue_dict['title'] = title_text.strip()
        issue_dict['comments'] = []

        # conversation
        comment_n = 0
        closing_phrases = ["close as verified with build", "Closing bug.", "Closing this bug."]
        while True:
            if comment_n == 0:
                body_text = html_tree.xpath(f'//*[@id="comment_text_{comment_n}"]//text()')
                text = ' '.join([text.replace('\xa0', ' ').replace('\t', ' ') for text in body_text])
                issue_dict['body'] = text.strip()
            else:
                conversation_text = html_tree.xpath(f'//*[@id="comment_text_{comment_n}"]//text()')

                if len(conversation_text) == 0: break

                if len(conversation_text) == 1:
                    issue_dict['comments'].append(f"comment #{comment_n}: None")
                    comment_n += 1
                    continue

                if any(phrases in ' '.join([text.replace('\xa0', ' ').replace('\t', ' ') for text in conversation_text])
                       for phrases in closing_phrases):
                    issue_dict['comments'].append(f"comment #{comment_n}: None")
                    comment_n += 1
                    continue

                text = ' '.join([text.replace('\xa0', ' ').replace('\t', ' ') for text in conversation_text])
                issue_dict['comments'].append(f"comment #{comment_n}: {text.strip()}")

            comment_n += 1

        label = html_tree.xpath('//*[@class="label"]//text()')
        example_datas.append(issue_dict)

        with open('./private_data.json', 'w', encoding='utf-8') as fp:
            json.dump(example_datas, fp, indent=4)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--private-cgi-file', default=None, required=True,
                        help='This is the folder path where the CGI file is located.')
    args = parser.parse_args()
    extra_cgi_to_json(args)
