# -*- coding: utf-8 -*-
import os
import re
import json
import requests


def get_data(url, timeout=None, links=False):
    params = {"state": "closed", "type": "issue", "per_page": 50}
    headers = {"Authorization": "Bearer **Your GitHub account access token** "}
    try:
        response = requests.get(url, params=params, headers=headers, timeout=timeout)
        if response and response.status_code == 200:
            if links:
                useful_issue = [issue for issue in response.json() if "pull_request" not in issue]
                return useful_issue, response.links
            else:
                return response.json()
    except Exception() as e:
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

        with open('checkpoint.json', 'w', encoding='utf-8') as f:
            json.dump([url_check, self.issue_n], f)

    def get_issue_data(self, url, timeout, check=False):
        if check:
            if os.path.exists('./checkpoint.json'):
                with open('./checkpoint.json', 'r', encoding='utf-8') as f:
                    url_check = json.load(f)
                    url = url_check[0]
                    self.issue_n = url_check[1]
        else:
            pass
        issues = get_data(url, timeout, links=True)
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
        comments = get_data(url, self.timeout)
        for comment in comments:
            body = comment.get('body', '').strip().strip('\r').strip('\n').strip('\r').strip()
            if body and not body.startswith(self.comment_filter):
                result_comment.append(body)
        return result_comment

    def get_commitid(self, id, url):
        commmit_id = []
        events = get_data(url, self.timeout)
        for event in events:
            commit_url = event['commit_url']
            if commit_url:
                # print(commit_url)
                commit = get_data(commit_url, self.timeout)
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

    def parse_close_bug(self, issues_data):
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

    def get_all_data(self):
        issues, links_status = self.get_issue_data(self.url, self.timeout, check=True)
        if issues is not None and links_status is not None:
            self.parse_close_bug(issues)
            self.save_data()
            self.result_data = []

            while "next" in links_status:
                # 获取下一页的URL
                try:
                    url = links_status["next"]["url"]
                    issues, links_status = self.get_issue_data(url, self.timeout)
                    self.parse_close_bug(issues)
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

    def show_result(self):
        print('..')


if __name__ == "__main__":
    # test 50 issues
    issue = Issue('https://api.github.com/repos/antrea-io/antrea/issues')
    issue.get_all_data()
    issue.save_data()
