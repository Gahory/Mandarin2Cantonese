# coding:utf-8
import datetime
import json
import os
import re
import sys
import requests
from bs4 import BeautifulSoup
import constant


def get_cantonese_dict():
    """获取本地字典"""
    print(' 获取本地字典')
    with open(constant.cantonese_dict_file, 'a+', encoding='utf-8') as f:
        f.seek(0)
        try:
            cantonese_dict = json.load(f)
        except Exception as e:
            print(' {}'.format(e))
            f.seek(0)
            if f.read() == '':
                cantonese_dict = {}
            else:
                sys.exit(0)
    print(' -共包含{}个字'.format(len(cantonese_dict)))
    return cantonese_dict


def get_polyphony_dict():
    """读取多音字映射关系"""
    if not constant.polyphony_flag:
        return {}
    print(' 初始化多音字映射规则')
    with open(constant.polyphony_file, 'r', encoding=constant.encoding) as f:
        try:
            polyphony_dict = json.load(f)
        except Exception as e:
            print(str(e))
            polyphony_dict = {}
    print(' -共包含{}个映射规则'.format(len(polyphony_dict)))
    with open(constant.polyphony_ignore_file, 'r', encoding=constant.encoding) as f:
        try:
            polyphony_ignore = json.load(f)
        except Exception as e:
            print(str(e))
            polyphony_ignore = {}
    print(' -共包含{}个忽略规则'.format(len(polyphony_ignore)))
    return polyphony_dict, polyphony_ignore


def get_unknown_mandarins(line, cantonese_dict):
    """删选出未知的字符"""
    line = ''.join(['*' if x in cantonese_dict else x for x in line])
    return [x for x in re.split(r'[^\u4e00-\u9fa5]', line) if x != '']


def update_cantonese_dict(mandarins, cantonese_dict):
    """添加未知字典元素"""
    for mandarin in mandarins:
        print(' 本地字典未命中')
        html_text = get_html(mandarin)
        analysis_and_update(mandarin, html_text, cantonese_dict)
        print(' 本地字典新增{}'.format(len(mandarin)))


def get_html(mandarin):
    """获取页面"""
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
            print('  发送请求')
            response = requests.get(url, params=params, headers=headers, timeout=30, verify=False)
            print('  接受完毕')
        except Exception as e:
            print(' {}'.format(e))
        else:
            return response.text
        finally:
            n -= 1
    sys.exit(0)


def analysis_and_update(mandarin, html_text, cantonese_dict):
    """html解析"""
    index = 0
    soup = BeautifulSoup(html_text, features='lxml')
    tables = soup.find_all(name='table')
    for table in tables:
        if table.find_all(name='td', text='读音') is not None:
            spans = table.find_all(name='span', attrs={'class': 'PSX text-xl pl-2 pr-1 py-2 PS_jyutping'})
            polyphony = {x.string for x in spans}
            cantonese_dict[mandarin[index]] = list(polyphony)
            index += 1


def convert(line, cantonese_dict, polyphony_dict, polyphony_ignore):
    """转换"""
    if line == '\n':
        print(' 跳过空行')
        return ''
    strings = [x for x in re.split(r'([^\u4e00-\u9fa5])', line) if x != '']
    for index in range(0, len(strings)):
        if re.match(r'[\u4e00-\u9fa5]', strings[index]) is None:
            continue
        cantonese = []
        for mandarin in strings[index]:
            polyphony = {re.sub(r'\d$', '', x) for x in cantonese_dict.get(mandarin, mandarin)}
            polyphony = deal_with_polyphony(mandarin, polyphony, polyphony_dict, polyphony_ignore)
            cantonese.append('/'.join(polyphony))
        strings[index] = ' '.join(cantonese)
    return ''.join(strings)


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


def update_cantonese_dict_file(before, cantonese_dict):
    """更新字典文件"""
    print('更新本地字典文件')
    with open(constant.cantonese_dict_file, 'a+', encoding='utf-8') as f:
        f.truncate(0)
        f.flush()
        json.dump(cantonese_dict, f)
        print('新增{}'.format(len(cantonese_dict) - before))


def convert_cantonese():
    """获取文件名和内容"""
    title = ''
    data = []
    index = 0
    print('初始化数据...')
    cantonese_dict = get_cantonese_dict()
    cantonese_dict_len = len(cantonese_dict)
    polyphony_dict, polyphony_ignore = get_polyphony_dict()
    print('初始化完毕')
    with open(constant.mandarin_file, 'r', encoding=constant.encoding) as f:
        for line in f:
            index += 1
            print('正在处理第{}行...'.format(index))
            line = line[-1] == '\n' and line or line + '\n'
            line_temp = line.replace(' ', '')
            unknown_mandarins = get_unknown_mandarins(line_temp, cantonese_dict)
            update_cantonese_dict(unknown_mandarins, cantonese_dict)
            cantonese = convert(line_temp, cantonese_dict, polyphony_dict, polyphony_ignore)
            if title == '':
                title = cantonese.replace('\n', '')
            else:
                data.append(line)
                data.append(cantonese)
    if len(cantonese_dict) > cantonese_dict_len:
        update_cantonese_dict_file(cantonese_dict_len, cantonese_dict)
    else:
        print('本地字典无新增')
    return data, title


def save_cantonese(data, title):
    """输出最终文件"""
    file_suffix = datetime.datetime.now().strftime(constant.suffix)
    output_file = os.path.join(constant.output_dir, '.'.join([title, file_suffix]))
    with open(output_file, 'w', encoding=constant.encoding) as f:
        f.writelines(data)
    print('输出文件：{}'.format(output_file))


def check_files(file_name):
    """检查文件"""
    if not os.path.exists(file_name):
        with open(file_name, 'w') as f:
            f.truncate(0)
        print('{}为空'.format(file_name))
        sys.exit(0)


def mandarin_to_cantonese():
    """转换入口"""
    check_files(constant.mandarin_file)
    data, title = convert_cantonese()
    save_cantonese(data, title)


requests.packages.urllib3.disable_warnings()
mandarin_to_cantonese()
