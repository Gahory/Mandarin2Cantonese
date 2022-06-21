# coding:utf-8
import datetime
import json
import os
import re
import sys
import requests
from bs4 import BeautifulSoup
import constant


def get_cantonese():
    """获取文件名和内容"""
    title = ''
    data = []
    index = 0
    polyphony_dict, polyphony_ignore = get_polyphony_dict()
    with open(constant.mandarin_file, 'r', encoding=constant.encoding) as f:
        for line in f:
            index += 1
            print('正在处理第{}行...'.format(index))
            line_temp = line.replace(' ', '')
            mandarins = [x for x in re.split(r'[^\u4e00-\u9fa5]', line_temp) if x != '']
            for mandarin in mandarins:
                html_text = get_html(mandarin)
                cantonese = analysis(mandarin, html_text, polyphony_dict, polyphony_ignore)
                line_temp = line_temp.replace(mandarin, cantonese, 1)
            if title == '':
                title = line_temp.replace('\n', '')
            else:
                data.append(line)
                data.append(line_temp)
    return data, title


def save_cantonese(data, title):
    """输出最终文件"""
    file_suffix = datetime.datetime.now().strftime(constant.suffix)
    output_file = os.path.join(constant.output_dir, '.'.join([title, file_suffix]))
    with open(output_file, 'w', encoding=constant.encoding) as f:
        f.writelines(data)


def check_files(file_name):
    """检查文件"""
    if not os.path.exists(file_name):
        with open(file_name, 'w') as f:
            f.truncate(0)
        print('{}为空'.format(file_name))
        sys.exit(0)


def get_html(mandarin):
    """获取转换后页面"""
    url = 'https://shyyp.net/search'
    headers = {
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'
    }
    params = {
        'q': mandarin
    }
    n = 3
    while n > 0:
        try:
            print(' 发送请求')
            response = requests.get(url, params=params, headers=headers, timeout=30, verify=False)
            print(' 接受完毕')
        except Exception as e:
            print(' {}'.format(e))
        else:
            return response.text
        finally:
            n -= 1
    sys.exit(0)


def analysis(mandarin, html_text, polyphony_dict, polyphony_ignore):
    """html解析"""
    result = []
    index = 0
    soup = BeautifulSoup(html_text, features='lxml')
    tables = soup.find_all(name='table')
    for table in tables:
        if table.find_all(name='td', text='读音') is not None:
            spans = table.find_all(name='span', attrs={'class': 'PSX text-xl pl-2 pr-1 py-2 PS_jyutping'})
            polyphony = {re.sub(r'\d$', '', x.string) for x in spans}
            polyphony = deal_with_polyphony(mandarin[index], polyphony, polyphony_dict, polyphony_ignore)
            result.append('/'.join(polyphony))
            index += 1
    return ' '.join(result)


def deal_with_polyphony(mandarin, polyphony, polyphony_dict, polyphony_ignore):
    """处理多音字"""
    if not constant.polyphony_flag or len(polyphony) <= 1:
        return polyphony
    if mandarin in polyphony_ignore or mandarin in constant.polyphony_cache:
        return polyphony
    if mandarin in polyphony_dict:
        return [polyphony_dict[mandarin]]
    constant.polyphony_cache.add(polyphony)
    with open(constant.polyphony_temp, 'a', encoding=constant.encoding) as f:
        line = ':'.join([mandarin, '/'.join(polyphony)]) + '\n'
        f.write(line)
    return polyphony


def get_polyphony_dict():
    """读取多音字映射关系"""
    if not constant.polyphony_flag:
        return {}
    with open(constant.polyphony_file, 'r', encoding=constant.encoding) as f:
        try:
            polyphony_dict = json.load(f)
        except Exception as e:
            print(str(e))
            polyphony_dict = {}
    with open(constant.polyphony_ignore_file, 'r', encoding=constant.encoding) as f:
        try:
            polyphony_ignore = json.load(f)
        except Exception as e:
            print(str(e))
            polyphony_ignore = {}
    return polyphony_dict, polyphony_ignore


def convert():
    """转换入口"""
    check_files(constant.mandarin_file)
    data, title = get_cantonese()
    save_cantonese(data, title)


requests.packages.urllib3.disable_warnings()
convert()
