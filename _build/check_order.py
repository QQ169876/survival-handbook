# -*- coding: utf-8 -*-
"""
check_order.py —— 校验《穿越生存手册》README 的「排序依据速查表」是否覆盖全部分册。

用途：新增或修订分册后跑一次，避免漏排、避免顺序表与 分册/ 目录脱节。

    python _build/check_order.py

检查三件事：
  1. 分册/ 目录下的每个 docx，在速查表里是否都有对应行；
  2. 速查表里列出的册号，是否都能在 分册/ 目录里找到文件；
  3. 速查表的阶段编号是否连续、无跳号（阶段 0~9 + 贯穿）。

退出码 0 = 通过；1 = 有问题。
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
README = os.path.join(ROOT, 'README.md')
VOL_DIR = os.path.join(ROOT, '分册')

# 速查表允许出现的非数字条目（贯穿项）
EXTRA_OK = ('诗词', '小说')


def volumes_on_disk():
    """分册/ 目录下实际存在的册号 -> 文件名"""
    out = {}
    if not os.path.isdir(VOL_DIR):
        return out
    for f in sorted(os.listdir(VOL_DIR)):
        m = re.match(r'(\d{2})_.*\.docx$', f)
        if m and not f.startswith('~$'):
            out[int(m.group(1))] = f
    return out


def table_rows(text):
    """从 README 的「排序依据速查表」章节里取册号 -> 阶段"""
    a = text.find('## 排序依据速查表')
    if a < 0:
        return {}
    b = text.find('\n## ', a + 10)
    sec = text[a:b if b > 0 else len(text)]
    rows = {}
    for line in sec.splitlines():
        line = line.strip()
        if not line.startswith('|'):
            continue
        cells = [c.strip() for c in line.strip('|').split('|')]
        if len(cells) < 2:
            continue
        head = cells[0]
        if head in ('分册',) or set(head) <= set('-: '):
            continue
        m = re.match(r'^(\d{2})\b', head)
        if m:
            rows[int(m.group(1))] = cells[1]
        elif any(k in head for k in EXTRA_OK):
            rows[head] = cells[1]
    return rows


def main():
    if not os.path.exists(README):
        print('找不到 README.md：%s' % README)
        return 1
    text = io.open(README, encoding='utf-8').read()
    disk = volumes_on_disk()
    rows = table_rows(text)

    problems = []
    numbered = {k: v for k, v in rows.items() if isinstance(k, int)}

    miss = sorted(set(disk) - set(numbered))
    if miss:
        problems.append('这些分册在速查表里没有排序依据行：%s'
                        % '、'.join('%02d (%s)' % (n, disk[n]) for n in miss))

    ghost = sorted(set(numbered) - set(disk))
    if ghost:
        problems.append('速查表里这些册号在 分册/ 目录找不到文件：%s'
                        % '、'.join('%02d' % n for n in ghost))

    for k in ('诗词', '小说'):
        if k not in rows and not any(k in str(x) for x in rows):
            problems.append('速查表缺少贯穿项：%s/' % k)

    stages = set()
    for v in rows.values():
        m = re.match(r'^(\d+)$', v.strip())
        if m:
            stages.add(int(m.group(1)))
        elif '贯穿' not in v:
            problems.append('阶段字段写法不规范（应为 0~9 或「贯穿」）：%s' % v)
    if stages:
        want = set(range(min(stages), max(stages) + 1))
        gap = sorted(want - stages)
        if gap:
            problems.append('阶段编号不连续，缺：%s' % '、'.join(map(str, gap)))

    print('分册/ 目录：%d 册；速查表：%d 行' % (len(disk), len(rows)))
    if problems:
        print('\n[不通过] 需要对使用顺序重新排序：')
        for p in problems:
            print('  - ' + p)
        print('\n按 README「新增分册时怎么排（判定流程）」插入后，再跑一次本脚本。')
        return 1
    print('[通过] 速查表已覆盖全部分册，阶段编号连续。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
