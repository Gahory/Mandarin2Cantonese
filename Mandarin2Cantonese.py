# coding:utf-8
import os
import re
import sys
import requests
from bs4 import BeautifulSoup


def convert():
    file_name = 'mandarin.txt'
    if not os.path.exists(file_name):
        with open(file_name, 'w') as f:
            f.truncate(0)
        print('{}为空'.format(file_name))
        sys.exit(0)
    title = ''
    data = []
    index = 0
    with open(file_name, 'r', encoding='utf-8') as f:
        for line in f:
            index += 1
            print('正在处理第{}行...'.format(index))
            line = line.replace(' ', '')
            mandarins = [x for x in re.split(r'[^\u4e00-\u9fa5]', line) if x != '']
            for mandarin in mandarins:
                html_text = get_html(mandarin)
                cantonese = analysis(html_text)
                line = line.replace(mandarin, cantonese, 1)
            if title == '':
                title = line.replace('\n', '')
            else:
                data.append(line)
    with open(title + '.txt', 'a', encoding='utf-8') as f:
        f.writelines(data)


def get_html(mandarin):
    url = 'https://shyyp.net/search'
    headers = {
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'
    }
    params = {
        'q': mandarin
    }
    response = requests.get(url, params=params, headers=headers, verify=False)
    return response.text


def analysis(html_text):
    result = []
    soup = BeautifulSoup(html_text, features='lxml')
    tables = soup.find_all(name='table')
    for table in tables:
        if table.find_all(name='td', text='读音') is not None:
            spans = table.find_all(name='span', attrs={'class': 'PSX text-xl pl-2 pr-1 py-2 PS_jyutping'})
            result.append('/'.join([re.sub(r'\d$', '', x.string) for x in spans]))
    return ' '.join(result)


requests.packages.urllib3.disable_warnings()
convert()
