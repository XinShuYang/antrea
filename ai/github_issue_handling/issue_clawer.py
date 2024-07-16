# -*- coding: utf-8 -*-

import os
import re
import json
import requests


def get_response_data(url, timeout=None, links=False):
    """
    Request data via GET.
    In order to use the GitHub API and increase the request limit, you need to generate a personal access token.
        op: log in to GitHub account ->Settings->Developer settings->Personal access tokens->Generate new token.
        example:
            headers = {"Authorization": "Bearer ghp_1Ir70BGA3qpM3gneMTNaCnH5xcODVn0Qck1b"}
    """
    params = {"state": "closed", "type": "issue", "per_page": 50}
    headers = {"Authorization": f"Bearer {token_config['token']}"}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=timeout)
        if response and response.status_code == 200:
            if links:
                # Filter out 'pull request' type of issue data, only get issue data.
                useful_issue = [issue for issue in response.json() if "pull_request" not in issue]
                return useful_issue, response.links
            else:
                return response.json()
        else:
            print("Request failed !!!")
            if links:
                return None, None
            else:
                return None
    except:
        print("Request failed !!!")
        if links:
            return None, None
        else:
            return None


class Issue():
    def __init__(self, url, timeout=20):
        self.issue_n = 0
        self.url = url
        self.timeout = timeout
        self.result_data = []
        self.comment_filter = ('/skip', '/test')

    def set_checkpoint(self, url_check):
        """
        set checkpoints to ensure that when the script is run again after being interrupted for the first time,
        it does not fetch data from the beginning but fetches data from the interrupted node.
        """
        with open('checkpoint.json', 'w', encoding='utf-8') as f:
            json.dump([url_check, self.issue_n], f)

    def get_close_data(self, url, timeout, check=False):
        if check:
            if os.path.exists('./checkpoint.json'):
                with open('./checkpoint.json', 'r', encoding='utf-8') as f:
                    url_check = json.load(f)
                    url = url_check[0]
                    self.issue_n = url_check[1]
        issues = get_response_data(url, timeout, links=True)
        return issues

    def remove_tag(self, text):
        if not text:
            return ''
        pattern = re.compile(r'<[^>]+>', re.S)
        return pattern.sub('', text)

    def get_lable(self, lables):
        result_label = []
        if not lables:
            return []
        for lable in lables:
            result_label.append(lable['name'])
        return result_label

    def get_commnents(self, url):
        result_comment = []
        comments = get_response_data(url, self.timeout)
        for comment in comments:
            body = comment.get('body', '').strip().strip('\r').strip('\n').strip('\r').strip()
            if body and not body.startswith(self.comment_filter):
                result_comment.append(body)
        return result_comment

    def get_commitid(self, id, url):
        commmit_id = []
        events = get_response_data(url, self.timeout)
        for event in events:
            commit_url = event['commit_url']
            if commit_url:
                # print(commit_url)
                commit = get_response_data(commit_url, self.timeout)
                message = commit['commit']['message']
                # print(message)
                if message:
                    numbers = re.findall(r'#\d{4,6}', message)
                    for num in numbers:
                        num = num[1:]
                        # print(num)
                        if num != id and num not in commmit_id:
                            commmit_id.append(num)
        return commmit_id

    def parse_issue(self, issues_data):
        for e in issues_data:
            tmp = dict()
            tmp['issue_id'] = e['url'].split('/')[-1]
            tmp['title'] = e['title']
            # print(type(e['body']))
            # break
            tmp['body'] = self.remove_tag(e['body'])
            tmp['state'] = e['state']

            tmp['lable'] = self.get_lable(e['labels'])
            tmp['comment'] = self.get_commnents(e['comments_url'])
            tmp['commmit_id'] = self.get_commitid(tmp['issue_id'], e['events_url'])

            self.result_data.append(tmp)

    def parse_close_issue(self, issues_data):
        for _, e in enumerate(issues_data):
            tmp = dict()
            tmp['issue_id'] = e['url'].split('/')[-1]
            # print(tmp['issue_id'])
            tmp['title'] = e['title']
            tmp['body'] = self.remove_tag(e['body'])

            tmp['state'] = e['state']
            if tmp['state'] != 'closed':
                continue

            tmp['lable'] = self.get_lable(e['labels'])
            tmp['comment'] = self.get_commnents(e['comments_url'])
            tmp['commmit_id'] = self.get_commitid(tmp['issue_id'], e['events_url'])

            self.issue_n += 1
            print(self.issue_n)

            self.result_data.append(tmp)

    def get_issue_data(self):
        issues, links_status = self.get_close_data(self.url, self.timeout, check=True)
        if issues is not None and links_status is not None:
            self.parse_close_issue(issues)
            self.save_data()
            self.result_data = []

            while "next" in links_status:
                # get the URL of the next page.
                try:
                    url = links_status["next"]["url"]
                    issues, links_status = self.get_close_data(url, self.timeout)
                    self.parse_close_issue(issues)
                except:
                    self.set_checkpoint(url)
                    print('error')
                    break

                self.save_data()
                self.result_data = []

    def save_data(self):
        with open('./issue.json', 'a', encoding='utf-8') as fp:
            for data in self.result_data:
                json.dump(data, fp)
                fp.write('\n')


if __name__ == "__main__":
    """
    This script is used to crawl issue data from Antrea. If network problems cause the script to stop executing and 
    output 'error', all you need to do is rerun the script.
    """
    # config
    # token_config = {"token": "Your GitHub account's Personal Access Token."}
    token_config = {"token": "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"}
    # init
    issue = Issue('https://api.github.com/repos/antrea-io/antrea/issues')
    # get issue
    issue.get_issue_data()
    # save data as JSON
    issue.save_data()
