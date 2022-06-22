# coding:utf-8
import datetime
import json
import logging
import colorlog
import os
import re
import sys
import requests
from bs4 import BeautifulSoup
import constant
from tools import format_lyrics


def is_mandarins(word):
    """是否是全中文字符或字符串"""
    if re.match(r'[^\u4e00-\u9fa5]', word) is None:
        return True
    return False


def split_to_words_retain_separator(line):
    """分割成单词或单字，保留分割符"""
    return [x for x in re.split(r'([^a-zA-Z\d/])', line) if x not in [' ', '']]


def split_to_segments_retain_separator(line):
    """分割成语句段，保留分割符"""
    return [x for x in re.split(r'([^\u4e00-\u9fa5a-zA-Z\d\x20])', line) if x != '']


def get_cantonese_dict():
    """获取本地字典"""
    colorlog.info(' 获取本地字典')
    with open(constant.cantonese_dict_file, 'a+', encoding='utf-8') as f:
        f.seek(0)
        try:
            cantonese_dict = json.load(f)
        except Exception as e:
            colorlog.info(' {}'.format(e))
            f.seek(0)
            if f.read() == '':
                colorlog.warning('  本地字典为空')
                cantonese_dict = {}
            else:
                colorlog.critical('  本地字典解析失败：{}'.format(e))
                sys.exit(0)
    colorlog.info(' -共包含{}个字'.format(len(cantonese_dict)))
    return cantonese_dict


def get_polyphony_dict():
    """读取多音字映射关系"""
    if not constant.polyphony_flag:
        return {}
    colorlog.info(' 初始化多音字映射规则')
    with open(constant.polyphony_file, 'r', encoding=constant.encoding) as f:
        try:
            polyphony_dict = json.load(f)
        except Exception as e:
            f.seek(0)
            if f.read() == '':
                colorlog.warning('  映射规则为空')
            else:
                colorlog.critical('  映射规则解析失败：{}'.format(e))
            polyphony_dict = {}
    colorlog.info(' -共包含{}个映射规则'.format(len(polyphony_dict)))
    with open(constant.polyphony_ignore_file, 'r', encoding=constant.encoding) as f:
        try:
            polyphony_ignore = json.load(f)
        except Exception as e:
            f.seek(0)
            if f.read() == '':
                colorlog.warning('  忽略规则为空')
            else:
                colorlog.critical('  忽略规则解析失败：{}'.format(e))
            polyphony_ignore = {}
    colorlog.info(' -共包含{}个忽略规则'.format(len(polyphony_ignore)))
    return polyphony_dict, polyphony_ignore


def get_html(mandarin):
    """获取页面"""
    url = 'https://shyyp.net/search'
    headers = {
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/102.0.0.0 Safari/537.36 '
    }
    params = {
        'q': mandarin
    }
    n = 3
    while n > 0:
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30, verify=False)
        except Exception as e:
            colorlog.warning(' 失败重试：{}'.format(e))
        else:
            return response.text
        finally:
            n -= 1
    colorlog.critical(' 超过最大请求次数：{}'.format(n))
    sys.exit(0)


def analysis_and_update(mandarin, html_text, cantonese_dict):
    """html解析"""
    index = 0
    soup = BeautifulSoup(html_text, features='lxml')
    tables = soup.find_all(name='table')
    for table in tables:
        if table.find_all(name='td', text='读音') is not None:
            spans = table.find_all(name='span', attrs={'class': 'PSX text-xl pl-2 pr-1 py-2 PS_jyutping'})
            polyphony = list({x.string for x in spans})
            mandarin_check = len(mandarin[index]) == 1 and is_mandarins(mandarin[index])
            polyphony_check = isinstance(polyphony, list) and len(polyphony) > 0
            if mandarin_check and polyphony_check:
                cantonese_dict[mandarin[index]] = polyphony
            else:
                colorlog.warning(' 字典格式错误，key：{}，value：{}'.format(mandarin[index], polyphony))
            index += 1


def deal_with_polyphony(mandarin, polyphony, polyphony_dict, polyphony_ignore):
    """处理多音字"""
    if not constant.polyphony_flag or len(polyphony) <= 1:
        return polyphony
    if mandarin in polyphony_ignore or mandarin in constant.polyphony_cache:
        return polyphony
    if mandarin in polyphony_dict:
        return [polyphony_dict[mandarin]]
    constant.polyphony_cache.add(mandarin)
    with open(constant.polyphony_temp, 'a', encoding=constant.encoding) as f:
        line = ':'.join([mandarin, '/'.join(polyphony)]) + '\n'
        f.write(line)
    return polyphony


def format_string(mandarin, cantonese):
    """格式化字符串"""
    if cantonese in ['', '\n']:
        return mandarin, cantonese
    # 分离每个汉字、单词和符号
    mandarins = split_to_words_retain_separator(mandarin)
    cantonese = split_to_words_retain_separator(cantonese)
    if len(cantonese) != len(mandarins):
        colorlog.warning(' 数据长度不相等，mandarins：{}，cantonese：{}'.format(len(mandarins), len(cantonese)))
    # 计算每个汉字/单词/符号合适的长度
    mandarins_lengths = [
        len(mandarins[i]) if mandarins[i] == cantonese[i] else len(cantonese[i]) > 1 and len(cantonese[i]) - 1 or 1
        for i in range(len(mandarins) - 1)]
    cantonese_lengths = [
        len(cantonese[i]) if mandarins[i] == cantonese[i] else len(cantonese[i]) > 1 and len(cantonese[i]) or 2
        for i in range(len(cantonese) - 1)]
    # 根据指定长度格式化汉字/单词
    format_mandarin = ['{string:<{len}}'.format(string=mandarins[i], len=mandarins_lengths[i]) for i in
                       range(len(mandarins_lengths))]
    format_cantonese = ['{string:<{len}}'.format(string=cantonese[i], len=cantonese_lengths[i]) for i in
                        range(len(cantonese_lengths))]
    # 优化4个unicode字符长度后的制表符，替换为空格
    # for index in range(len(format_mandarin) - 2, -1, -1):
    #     if len(format_mandarin[index]) != 3:
    #         continue
    #     format_mandarin[index] = ' '.join([format_mandarin[index], format_mandarin[index + 1]])
    #     format_cantonese[index] = ' '.join([format_cantonese[index], format_cantonese[index + 1]])
    #     format_mandarin.pop(index + 1)
    #     format_cantonese.pop(index + 1)
    # 制表
    format_mandarin = '\t'.join(format_mandarin) + '\n'
    format_cantonese = '\t'.join(format_cantonese) + '\n'
    # 优化符号格式，去掉前/后制表
    table_label = '\t'
    fmt = r'([（(]){0}|{0}([：:]){0}|{0}([)）])'.format(table_label)
    format_mandarin = re.sub(fmt, r'\g<1>\g<2>\g<3>', format_mandarin)
    format_cantonese = re.sub(fmt, r'\g<1>\g<2>\g<3>', format_cantonese)

    return format_mandarin, format_cantonese


def get_unknown_mandarins(text, cantonese_dict):
    """筛选出本地字典未知的字符，拼接成字符串"""
    mandarin = ''.join([x for x in re.split(r'[^\u4e00-\u9fa5]', text) if x != ''])
    return ''.join({x for x in mandarin if x not in cantonese_dict})


def deal_with_unknown_mandarins(cantonese_dict, text):
    """处理未知字符，更新字典"""
    unknown_mandarin = get_unknown_mandarins(text, cantonese_dict)
    colorlog.info('检查到未知字符数量：{}'.format(len(unknown_mandarin)))
    step = 10
    for i in range(0, len(unknown_mandarin), step):
        mandarin = unknown_mandarin[i:i + step]
        colorlog.info(' 联网更新第{}段数据，长度{}...'.format(int(i / step + 1), len(mandarin)))
        before = len(cantonese_dict)
        html_text = get_html(mandarin)
        analysis_and_update(mandarin, html_text, cantonese_dict)
        colorlog.info(' 字典新增{}'.format(len(cantonese_dict) - before))


def convert(mandarin, cantonese_dict, polyphony_dict, polyphony_ignore):
    """转换"""
    if mandarin == '\n':
        colorlog.info(' 跳过空行')
        return ''
    mandarins = split_to_segments_retain_separator(mandarin)
    for index in range(len(mandarins)):
        if re.search(r'[\u4e00-\u9fa5]', mandarins[index]) is None:
            continue
        cantonese = []
        for word in split_to_words_retain_separator(mandarins[index]):
            polyphony = {re.sub(r'\d$', '', x) for x in cantonese_dict.get(word, [word])}
            polyphony = deal_with_polyphony(word, polyphony, polyphony_dict, polyphony_ignore)
            cantonese.append('/'.join(polyphony))
        mandarins[index] = ' '.join(cantonese)
    return ''.join(mandarins)


def update_cantonese_dict_file(cantonese_dict, old_len):
    """更新字典文件"""
    if len(cantonese_dict) > old_len:
        colorlog.info('更新本地字典文件...')
        cantonese_dict = dict(sorted(cantonese_dict.items(), key=lambda d: d[1]))
        with open(constant.cantonese_dict_file, 'a+', encoding='utf-8') as f:
            f.truncate(0)
            f.flush()
            json.dump(cantonese_dict, f)
        colorlog.info('更新完成，新增{}'.format(len(cantonese_dict) - old_len))
    else:
        colorlog.info('本地字典无新增')


def convert_cantonese():
    """获取文件名和内容"""
    title = ''
    data = []
    index = 0
    colorlog.info('初始化数据...')
    cantonese_dict = get_cantonese_dict()
    cantonese_dict_len = len(cantonese_dict)
    polyphony_dict, polyphony_ignore = get_polyphony_dict()
    colorlog.info('初始化完毕')
    with open(constant.mandarin_file, 'r', encoding=constant.encoding) as f:
        deal_with_unknown_mandarins(cantonese_dict, f.read())
        f.seek(0)
        for mandarin in f:
            index += 1
            colorlog.info('正在处理第{}行...'.format(index))
            mandarin = mandarin[-1] == '\n' and mandarin or mandarin + '\n'
            mandarin = re.sub(r'\x20*/\x20*', '|', mandarin)
            cantonese = convert(mandarin, cantonese_dict, polyphony_dict, polyphony_ignore)
            if title == '':
                title = cantonese.replace('\n', '')
                title = re.sub(r'[\\/:*?”<>|]', '_', title)
            else:
                format_mandarin, format_cantonese = format_string(mandarin, cantonese)
                data.append(format_mandarin + format_cantonese)
    update_cantonese_dict_file(cantonese_dict, cantonese_dict_len)
    return title, data


def save_cantonese(title, data):
    """输出最终文件"""
    file_suffix = datetime.datetime.now().strftime(constant.suffix)
    if not os.path.exists(constant.output_dir):
        os.makedirs(constant.output_dir)
    output_file = os.path.join(constant.output_dir, '.'.join([title, file_suffix]))
    with open(output_file, 'w', encoding=constant.encoding) as f:
        f.writelines(data)
    colorlog.info('输出文件：{}'.format(output_file))


def check_files(file_name):
    """检查文件"""
    if not os.path.exists(file_name):
        with open(file_name, 'w') as f:
            f.truncate(0)
        colorlog.critical('{}为空'.format(file_name))
        sys.exit(0)


def mandarin_to_cantonese():
    """转换入口"""
    check_files(constant.mandarin_file)
    title, data = convert_cantonese()
    save_cantonese(title, data)


if __name__ == '__main__':
    colorlog.basicConfig(level=logging.INFO, format='%(log_color)s%(asctime)s - %(levelname)s : %(message)s',
                         datefmt='%Y/%m/%d %H:%M:%S')
    requests.packages.urllib3.disable_warnings()
    format_lyrics.formate_lyrics()
    mandarin_to_cantonese()
