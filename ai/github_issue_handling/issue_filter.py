# -*- coding: utf-8 -*-

import os
import json

if __name__ == '__main__':

    filter_list = []
    if os.path.exists('issue_filter.json'):
        os.remove('issue_filter.json')
    with open('issue_filter.json', 'a', encoding='utf-8') as fp:
        with open('issue.json', 'r', encoding='utf-8') as f:
            for data in f:
                _data = eval(data)
                if _data['issue_id'] in filter_list:
                    continue
                else:
                    filter_list.append(_data['issue_id'])
                    json.dump(_data, fp)
                    fp.write('\n')

