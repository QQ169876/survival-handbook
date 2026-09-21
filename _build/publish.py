# -*- coding: utf-8 -*-
"""《穿越生存手册》一键发布脚本：提交 → 双端推送（Gitee + GitHub）→ 双端发行版（只留最新）

用法：
    python publish.py -m "提交说明"      # 提交 + 推送 + 生成发行版（完整流程）
    python publish.py                    # 无改动时只推送并刷新发行版
    python publish.py --no-push          # 只提交，不推送不发行
    python publish.py --dry              # 只打印将要执行的操作

流程约定（以后每次版本更新都走这个脚本）：
1. 版本号与发行说明自动取自 README「## 更新日志」的第一条
2. 推送到 Gitee（origin）与 GitHub（github）两个远端
3. 两端都只保留一个发行版：先删旧的全部 release（GitHub 连 tag 一起删），再按当前版本新建
"""
import os, sys, json, re, glob, subprocess, urllib.parse
import urllib.request, urllib.error

ROOT = r"D:\穿越生存手册"
TOKEN_GITEE = r"C:\Users\maker\.gitee_token.json"
TOKEN_GITHUB = r"C:\Users\maker\.github_token.json"
GITEE_OWNER, GITEE_REPO = "big_head_mk", "survival-handbook"
GITHUB_OWNER, GITHUB_REPO = "QQ169876", "survival-handbook"
GITHUB_API = "https://api.github.com"
GITEE_API = "https://gitee.com/api/v5"


# ---------- 基础工具 ----------
def sh(args, cwd=ROOT, env=None):
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="ignore", env=env)
    return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()


def gitee_token():
    return json.load(open(TOKEN_GITEE, encoding="utf-8"))["token"]


def github_conf():
    d = json.load(open(TOKEN_GITHUB, encoding="utf-8"))
    return d["token"], d.get("proxy")


def gitee(method, path, data=None):
    url = GITEE_API + path + "?access_token=" + gitee_token()
    body = urllib.parse.urlencode(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, method=method)
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            raw = r.read().decode("utf-8")
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        print("  [Gitee HTTP %s] %s" % (e.code, e.read().decode("utf-8", "ignore")[:300]))
        return None


def github(method, path, data=None):
    tok, proxy = github_conf()
    url = GITHUB_API + path
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", "token " + tok)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "survival-handbook-publisher")
    opener = urllib.request.build_opener()
    if proxy:
        try:
            import socks
            from sockshandler import SocksiPyHandler  # 不一定存在，走下面 requests 兜底
        except Exception:
            pass
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read().decode("utf-8")
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        print("  [GitHub HTTP %s] %s" % (e.code, e.read().decode("utf-8", "ignore")[:300]))
        return None


def gh_requests(method, path, data=None):
    """GitHub 走 SOCKS5 代理时用 requests 更稳，作为 urllib 的兜底/主通道"""
    import requests
    tok, proxy = github_conf()
    proxies = {"http": proxy, "https": proxy} if proxy else None
    h = {"Authorization": "token " + tok, "Accept": "application/vnd.github+json",
         "User-Agent": "survival-handbook-publisher"}
    r = requests.request(method, GITHUB_API + path, headers=h, json=data, proxies=proxies, timeout=60)
    if r.status_code >= 400:
        print("  [GitHub HTTP %s] %s" % (r.status_code, r.text[:300]))
        return None
    return r.json() if r.text else None


# ---------- 版本与说明 ----------
def read_changelog():
    s = open(os.path.join(ROOT, "README.md"), encoding="utf-8").read()
    seg = s.split("## 更新日志", 1)[1].strip().split("\n")
    first = []
    for idx, ln in enumerate(seg):
        if idx > 0 and ln.startswith("- "):
            break
        first.append(ln)
    block = "\n".join(first).strip()
    m = re.search(r"v(\d+\.\d+)", block)
    ver = "v" + m.group(1) if m else "vX.Y"
    return ver, block.split("\n")[0].lstrip("- ").strip(), block


def stats():
    books = len(glob.glob(os.path.join(ROOT, "分册", "*.docx")))
    imgs = len(glob.glob(os.path.join(ROOT, "图片", "*.png")))
    txt = (len(glob.glob(os.path.join(ROOT, "诗词", "*.txt"))) +
           len(glob.glob(os.path.join(ROOT, "小说", "*.txt"))))
    return books, imgs, txt


def release_body(block):
    books, imgs, txt = stats()
    return (block + "\n\n---\n\n"
            f"- 当前规模：技术分册 {books} 册、示意图 {imgs} 幅、纯文本资料 {txt} 册\n"
            f"- Gitee：https://gitee.com/{GITEE_OWNER}/{GITEE_REPO}\n"
            f"- GitHub：https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}\n"
            f"- 本发行版对应 main 分支最新提交\n\n"
            f"> 阅读前请先看仓库内的 `可信度说明.md`：本手册区分【史实】【科学】【经验】【存疑】四类内容，"
            f"未标注为史实或科学的数字一律视为经验值，须现场验证。")


# ---------- 推送 ----------
def push_gitee():
    code, out, err = sh(["git", "push", "origin", "main"])
    print("  Gitee push:", "OK" if code == 0 else "FAIL")
    if code != 0:
        print("   ", err[:300])
    return code == 0


def push_github():
    tok, proxy = github_conf()
    url = "https://%s@github.com/%s/%s.git" % (tok, GITHUB_OWNER, GITHUB_REPO)
    args = ["git"]
    if proxy:
        args += ["-c", "http.proxy=" + proxy, "-c", "https.proxy=" + proxy]
    args += ["push", url, "main"]
    code, out, err = sh(args)
    print("  GitHub push:", "OK" if code == 0 else "FAIL")
    if code != 0:
        print("   ", (err or out)[:400])
    return code == 0


# ---------- 发行版 ----------
def release_gitee(ver, title, body, dry=False):
    tag = ver
    old = gitee("GET", f"/repos/{GITEE_OWNER}/{GITEE_REPO}/releases") or []
    print("  Gitee 现有发行版:", [r.get("tag_name") for r in old])
    if dry:
        return
    for r in old:
        print("   删除旧发行版", r.get("tag_name"))
        gitee("DELETE", f"/repos/{GITEE_OWNER}/{GITEE_REPO}/releases/{r.get('id')}")
    res = gitee("POST", f"/repos/{GITEE_OWNER}/{GITEE_REPO}/releases", {
        "tag_name": tag, "name": f"{ver} · {title[:40]}", "body": body, "target_commitish": "main"})
    if res:
        print("  已创建:", res.get("tag_name"))


def release_github(ver, title, body, dry=False):
    path = f"/repos/{GITHUB_OWNER}/{GITHUB_REPO}"
    old = gh_requests("GET", path + "/releases") or []
    print("  GitHub 现有发行版:", [r.get("tag_name") for r in old])
    if dry:
        return
    for r in old:
        print("   删除旧发行版", r.get("tag_name"))
        gh_requests("DELETE", path + "/releases/" + str(r.get("id")))
        gh_requests("DELETE", path + "/git/refs/tags/" + urllib.parse.quote(r.get("tag_name"), safe=""))
    res = gh_requests("POST", path + "/releases", {
        "tag_name": ver, "name": f"{ver} · {title[:40]}", "body": body,
        "target_commitish": "main", "draft": False, "prerelease": False})
    if res:
        print("  已创建:", res.get("tag_name"), res.get("html_url"))


# ---------- 主流程 ----------
def main():
    args = sys.argv[1:]
    dry = "--dry" in args
    no_push = "--no-push" in args
    msg = None
    if "-m" in args:
        i = args.index("-m")
        msg = args[i + 1] if i + 1 < len(args) else None

    print("== 1. 提交 ==")
    code, out, _ = sh(["git", "status", "--porcelain"])
    dirty = bool(out.strip())
    if dirty and msg:
        print("  改动:", len(out.strip().split("\n")), "项")
        if not dry:
            sh(["git", "add", "-A"])
            c, o, e = sh(["git", "commit", "-m", msg])
            print("  commit:", "OK" if c == 0 else "FAIL", o[:120])
    elif dirty and not msg:
        print("  [警告] 工作区有改动但未给 -m，跳过提交（后续推送的将是不含这些改动的版本）")
    else:
        print("  工作区干净")

    if no_push:
        print("[--no-push] 到此为止")
        return

    print("== 2. 推送 ==")
    if not dry:
        push_gitee()
        push_github()
    else:
        print("  [dry] 跳过推送")

    print("== 3. 发行版 ==")
    ver, title, block = read_changelog()
    body = release_body(block)
    print("  版本:", ver, "| 说明长度:", len(body))
    release_gitee(ver, title, body, dry)
    release_github(ver, title, body, dry)

    print("\n完成：https://gitee.com/{}/{}/releases/{}".format(GITEE_OWNER, GITEE_REPO, ver))
    print("      https://github.com/{}/{}/releases/{}".format(GITHUB_OWNER, GITHUB_REPO, ver))


if __name__ == "__main__":
    main()
