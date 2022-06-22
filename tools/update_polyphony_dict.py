import json
import os
import sys
import constant


def check_files(file_path):
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            f.truncate(0)
        print('{}为空'.format(file_path))
        sys.exit(0)


def update(file_from, file_to):
    with open(file_to, 'a+', encoding='utf-8') as f:
        f.seek(0)
        try:
            polyphony_dict = json.load(f)
        except Exception as e:
            print('{}'.format(e))
            f.seek(0)
            if f.read() == '':
                polyphony_dict = {}
            else:
                sys.exit(0)
        before = len(polyphony_dict)
        with open(file_from, 'r+', encoding='utf-8') as t:
            try:
                for line in t:
                    strings = line.replace('\n', '').split(':')
                    polyphony_dict[strings[0]] = len(strings) > 1 and strings[1] or 'NA'
                    print('添加{}'.format(strings))
            except Exception as e:
                print('{}:{}'.format(e, line))
            else:
                t.truncate(0)
                t.flush()
        f.truncate(0)
        f.flush()
        json.dump(polyphony_dict, f)
        print('{}新增{}'.format(file_to, len(polyphony_dict) - before))


root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

temp_file = os.path.join(root, constant.polyphony_temp)
polyphony_file = os.path.join(root, constant.polyphony_file)
check_files(temp_file)
update(temp_file, polyphony_file)


ignore_file = os.path.join(root, constant.polyphony_ignore_temp)
polyphony_ignore = os.path.join(root, constant.polyphony_ignore_file)
check_files(ignore_file)
update(ignore_file, polyphony_ignore)
