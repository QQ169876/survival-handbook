# -*- coding: utf-8 -*-
"""《穿越生存手册》Gitee 发行版同步脚本

用法：
    python release.py            # 按 README 更新日志的最新一条生成发行版，并删除旧发行版
    python release.py --dry      # 只打印将要执行的操作，不改动远端

约定：
- 版本号取自 README「## 更新日志」下第一条条目的 vX.Y
- 发行版说明 = 该条更新日志 + 当前册数/图数统计 + 仓库链接
- 每次只保留一个发行版（与最新 commit 对应）
"""
import os, sys, json, glob, re, urllib.request, urllib.parse

ROOT = r"D:\穿越生存手册"
TOKEN_FILE = r"C:\Users\maker\.gitee_token.json"
OWNER = "big_head_mk"
REPO = "survival-handbook"
API = "https://gitee.com/api/v5"


def token():
    d = json.load(open(TOKEN_FILE, encoding="utf-8"))
    return d["token"]


def api(method, path, data=None):
    url = API + path
    params = {"access_token": token()}
    if data:
        body = urllib.parse.urlencode(data).encode("utf-8")
        req = urllib.request.Request(url + "?" + urllib.parse.urlencode(params),
                                     data=body, method=method)
    else:
        req = urllib.request.Request(url + "?" + urllib.parse.urlencode(params), method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read().decode("utf-8")
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        print("HTTP", e.code, e.read().decode("utf-8", "ignore")[:400])
        raise


def read_changelog():
    s = open(os.path.join(ROOT, "README.md"), encoding="utf-8").read()
    i = s.find("## 更新日志")
    seg = s[i + len("## 更新日志"):].strip()
    lines = seg.split("\n")
    first, rest = [], []
    for idx, ln in enumerate(lines):
        if idx > 0 and ln.startswith("- "):
            rest = lines[:idx]
            break
        first.append(ln)
    block = "\n".join(first).strip()
    m = re.search(r"v(\d+\.\d+)", block)
    ver = "v" + m.group(1) if m else "vX.Y"
    title = block.split("\n")[0].lstrip("- ").strip()
    return ver, title, block


def stats():
    books = len(glob.glob(os.path.join(ROOT, "分册", "*.docx")))
    imgs = len(glob.glob(os.path.join(ROOT, "图片", "*.png")))
    txt = len(glob.glob(os.path.join(ROOT, "诗词", "*.txt"))) + \
          len(glob.glob(os.path.join(ROOT, "小说", "*.txt")))
    return books, imgs, txt


def main():
    dry = "--dry" in sys.argv
    ver, title, block = read_changelog()
    books, imgs, txt = stats()
    body = (block + "\n\n---\n\n"
            f"- 当前规模：技术分册 {books} 册、示意图 {imgs} 幅、纯文本资料 {txt} 册\n"
            f"- 仓库：https://gitee.com/{OWNER}/{REPO}\n"
            f"- 本发行版对应 main 分支最新提交\n\n"
            f"> 阅读前请先看仓库内的 `可信度说明.md`：本手册区分【史实】【科学】【经验】【存疑】四类内容，"
            f"未标注为史实或科学的数字一律视为经验值，须现场验证。")
    print("版本:", ver)
    print("标题:", title)
    print("说明长度:", len(body))
    if dry:
        print("[dry] 不执行远端操作")
        return

    old = api("GET", f"/repos/{OWNER}/{REPO}/releases") or []
    print("现有发行版:", [(r.get("id"), r.get("tag_name")) for r in old])
    for r in old:
        print("删除", r.get("tag_name"), r.get("id"))
        api("DELETE", f"/repos/{OWNER}/{REPO}/releases/{r.get('id')}")

    res = api("POST", f"/repos/{OWNER}/{REPO}/releases", {
        "tag_name": ver,
        "name": f"{ver} · {title[:40]}",
        "body": body,
        "target_commitish": "main",
    })
    print("已创建发行版:", res.get("tag_name"), res.get("id"))
    print("https://gitee.com/{}/{}/releases/{}".format(OWNER, REPO, res.get("tag_name")))


if __name__ == "__main__":
    main()
