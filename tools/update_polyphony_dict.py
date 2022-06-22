import json
import logging
import os
import re
import sys
import colorlog
import constant
from Mandarin2Cantonese import is_mandarins


def check_files(file_path):
    colorlog.info('解析文件：{}'.format(os.path.basename(file_path)))
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            f.truncate(0)
        colorlog.critical(' {}为空'.format(file_path))
        sys.exit(0)


def update(file_from, file_to):
    file_name = os.path.basename(file_to)
    with open(file_to, 'a+', encoding='utf-8') as f:
        f.seek(0)
        try:
            polyphony_dict: dict = json.load(f)
        except Exception as e:
            f.seek(0)
            if f.read() == '':
                colorlog.warning(' 数据文件为空：{}'.format(file_to))
                polyphony_dict = {}
            else:
                colorlog.critical('解析失败：{}'.format(e))
                sys.exit(0)
        before = len(polyphony_dict)
        with open(file_from, 'r+', encoding='utf-8') as t:
            try:
                for line in t:
                    strings = line.replace('\n', '').split(':')
                    mandarin_check = is_mandarins(strings[0])
                    if file_name == os.path.basename(constant.polyphony_ignore_file):
                        cantonese_check = re.match(r'^[a-zA-Z]+\d?/[a-zA-Z]+\d?$', strings[1]) is not None
                    else:
                        cantonese_check = re.match(r'^[a-zA-Z]+\d?$', strings[1]) is not None
                    if len(strings) != 2 or not mandarin_check or not cantonese_check:
                        raise Exception('解析失败')
                    polyphony_dict[strings[0]] = strings[1]
                    colorlog.info(' 添加{}'.format(strings))
            except Exception as e:
                colorlog.critical(' {}:<{}>'.format(e, line))
            else:
                colorlog.info(' 清空源文件')
                t.truncate(0)
                t.flush()
                polyphony_dict = dict(sorted(polyphony_dict.items(), key=lambda d: d[1]))
                f.truncate(0)
                f.flush()
                json.dump(polyphony_dict, f)
        colorlog.info('{}新增{}'.format(file_name, len(polyphony_dict) - before))


if __name__ == '__main__':
    colorlog.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s : %(message)s',
                         datefmt='%Y/%m/%d %H:%M:%S')
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    temp_file = os.path.join(root, constant.polyphony_temp)
    polyphony_file = os.path.join(root, constant.polyphony_file)
    check_files(temp_file)
    update(temp_file, polyphony_file)

    ignore_file = os.path.join(root, constant.polyphony_ignore_temp)
    polyphony_ignore = os.path.join(root, constant.polyphony_ignore_file)
    check_files(ignore_file)
    update(ignore_file, polyphony_ignore)
