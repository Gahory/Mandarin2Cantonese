import logging
import os
import colorlog
import constant


def formate_lyrics():
    """格式化并保留副本"""
    colorlog.info('格式化并保留副本...')
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if not os.path.exists(os.path.join(root, constant.lyrics_dir)):
        os.makedirs(os.path.join(root, constant.lyrics_dir))
    with open(os.path.join(root, constant.mandarin_file), 'r+', encoding='utf-8') as f:
        buffer = [line for line in f.readlines() if line != '\n']
        title = buffer[0].replace('\n', '')
        f.truncate(0)
        f.flush()
        f.seek(0)
        f.writelines(buffer)
        colorlog.info(' 重写文件，行数：{}'.format(len(buffer)))
        out = os.path.join(root, constant.lyrics_dir, title + '.txt')
        with open(out, 'w', encoding='utf-8') as t:
            t.writelines(buffer)
        colorlog.info('输出文件：{}'.format(out))


if __name__ == '__main__':
    colorlog.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s : %(message)s',
                         datefmt='%Y/%m/%d %H:%M:%S')
    formate_lyrics()
