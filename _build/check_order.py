# -*- coding: utf-8 -*-
"""
check_order.py —— 校验《穿越生存手册》README 的「排序依据速查表」是否覆盖全部分册。

用途：新增或修订分册后跑一次，避免漏排、避免顺序表与 分册/ 目录脱节。

    python _build/check_order.py

检查四件事：
  1. 分册/ 目录下的每个 docx，在速查表里是否都有对应行；
  2. 速查表里列出的册号，是否都能在 分册/ 目录里找到文件；
  3. 纯文本资料目录（诗词/、小说/、经济/）是否在速查表里有对应条目；
  4. 速查表的阶段编号是否连续、无跳号（阶段 0~9 + 贯穿）。

退出码 0 = 通过；1 = 有问题。
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
README = os.path.join(ROOT, 'README.md')
VOL_DIR = os.path.join(ROOT, '分册')

# 速查表允许出现的非数字条目（纯文本资料目录，无需逐册列行）
EXTRA_OK = ('诗词', '小说', '经济', '电力')


def volumes_on_disk():
    """分册/ 各篇下实际存在的册号 -> 相对路径（编号 01~32 全局唯一，跨篇不变）"""
    out = {}
    if not os.path.isdir(VOL_DIR):
        return out
    for dirpath, _dirs, files in os.walk(VOL_DIR):
        for f in sorted(files):
            if f.startswith('~$') or not f.endswith('.docx'):
                continue
            m = re.match(r'(\d{2})_.*\.docx$', f)
            if m:
                out[int(m.group(1))] = os.path.relpath(
                    os.path.join(dirpath, f), ROOT).replace('\\', '/')
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

    # 纯文本资料目录：只要速查表里出现过该目录名即可，不必逐册列行
    for d in EXTRA_OK:
        if not os.path.isdir(os.path.join(ROOT, d)):
            continue
        n = len([f for f in os.listdir(os.path.join(ROOT, d))
                 if f.endswith('.txt')])
        if n and not any(d in str(k) for k in rows):
            problems.append('纯文本资料目录 %s/（%d 个 txt）在速查表里没有条目' % (d, n))
        else:
            print('  %s/：%d 个 txt，速查表已收录' % (d, n))

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
    by_tier = {}
    for n, p in sorted(disk.items()):
        by_tier.setdefault(p.split('/')[1] if '/' in p else '分册', []).append(n)
    for k in sorted(by_tier):
        print('  %s：%d 册（%s）' % (k, len(by_tier[k]),
                                '、'.join('%02d' % n for n in by_tier[k])))
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
