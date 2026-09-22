# -*- coding: utf-8 -*-
"""把维基文库抓取的兵书 wiki 源文本清洗成 bingfa.json（繁转简、去模板、切篇分段）。

数据源：_build/data/bingfa/*.wiki（中文维基文库 action=raw，公版古籍）
输出：_build/data/bingfa.json
用法：python prep_bingfa.py
"""
import io
import json
import os
import re

import zhconv

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "data", "bingfa")
OUT = os.path.join(HERE, "data", "bingfa.json")

# 书名 -> (源文件名列表, 是否跳过「目录」段)
BOOKS = [
    ("孙子兵法", ["孫子兵法.wiki"]),
    ("吴子兵法", ["吳子.wiki"]),
    ("司马法", ["司馬法.wiki"]),
    ("三略", ["三略.wiki"]),
    ("六韬", ["六韜.wiki"]),
    ("孙膑兵法", ["孫臏兵法.wiki"]),
    ("尉缭子", ["尉繚子_全覽.wiki"]),
    ("三十六计", ["三十六計.wiki", "三十六計_勝戰計.wiki", "三十六計_敵戰計.wiki",
                  "三十六計_攻戰計.wiki", "三十六計_混戰計.wiki",
                  "三十六計_並戰計.wiki", "三十六計_敗戰計.wiki"]),
]

DROP_LINE_PREFIX = ("__NOEDITSECTION__", "{{檢索", "[[Category", "[[分類")


def strip_templates(text):
    """去掉 {{...}} 模板（含跨行）"""
    out = []
    depth = 0
    i = 0
    n = len(text)
    while i < n:
        if text.startswith("{{", i):
            depth += 1
            i += 2
            continue
        if text.startswith("}}", i):
            depth = max(0, depth - 1)
            i += 2
            continue
        if depth == 0:
            out.append(text[i])
        i += 1
    return "".join(out)


def clean(text):
    text = strip_templates(text)
    text = re.sub(r"<ref[^>]*/>", "", text)
    text = re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.S)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"\[\[[^\]|]*\|([^\]]*)\]\]", r"\1", text)
    text = re.sub(r"\[\[([^\]]*)\]\]", r"\1", text)
    text = text.replace("'''", "").replace("''", "")
    text = re.sub(r"\{\{[^{}]*\}\}", "", text)
    text = re.sub(r"^\[\[[^\]]*\]\]\s*$", "", text, flags=re.M)
    return text


def split_sections(text):
    """返回 [(篇名, [段...]), ...]"""
    secs = []
    cur_name = None
    cur = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        m = re.match(r"^=+\s*(.+?)\s*=+$", line)
        if m:
            if cur_name is not None and cur:
                secs.append((cur_name, cur))
            cur_name = m.group(1)
            cur = []
            continue
        if any(line.startswith(p) for p in DROP_LINE_PREFIX):
            continue
        if line.startswith("*") or line.startswith("#") or line.startswith(":"):
            continue
        if cur_name is None:
            cur_name = "正文"
        cur.append(line)
    if cur_name is not None and cur:
        secs.append((cur_name, cur))
    return secs


def main():
    data = {}
    stat = []
    for name, files in BOOKS:
        secs = []
        for fn in files:
            p = os.path.join(SRC, fn)
            if not os.path.exists(p):
                print("缺文件", fn)
                continue
            raw = io.open(p, encoding="utf-8").read()
            for sname, paras in split_sections(clean(raw)):
                if sname in ("目录", "目錄"):
                    continue
                paras = [zhconv.convert(x, "zh-cn") for x in paras]
                secs.append({"篇": zhconv.convert(sname, "zh-cn"), "段": paras})
        data[name] = secs
        chars = sum(len("".join(s["段"])) for s in secs)
        stat.append((name, len(secs), chars))
    with io.open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    for n, c, ch in stat:
        print("%-8s 篇/计 %3d  字数 %6d" % (n, c, ch))
    print("total chars", sum(s[2] for s in stat), "->", OUT)


if __name__ == "__main__":
    main()
