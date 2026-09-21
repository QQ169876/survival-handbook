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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOME = os.path.expanduser("~")
# 凭据一律放在仓库外，脚本内不写死任何令牌、代理地址或用户名；
# 支持用环境变量覆盖：GITEE_TOKEN / GITHUB_TOKEN / GITEE_TOKEN_FILE / GITHUB_TOKEN_FILE / GITHUB_PROXY
TOKEN_GITEE = os.environ.get("GITEE_TOKEN_FILE") or os.path.join(HOME, ".gitee_token.json")
TOKEN_GITHUB = os.environ.get("GITHUB_TOKEN_FILE") or os.path.join(HOME, ".github_token.json")
GITEE_OWNER, GITEE_REPO = "big_head_mk", "survival-handbook"
GITHUB_OWNER, GITHUB_REPO = "QQ169876", "survival-handbook"
GITHUB_API = "https://api.github.com"
GITEE_API = "https://gitee.com/api/v5"


# ---------- 基础工具 ----------
def sh(args, cwd=ROOT, env=None):
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="ignore", env=env)
    return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()


# ---------- 凭据与脱敏 ----------
def _load(path, key="token"):
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception as e:
        print("[错误] 读取凭据文件失败：%s（%s）" % (path, e))
        return {}


def gitee_token():
    return os.environ.get("GITEE_TOKEN") or _load(TOKEN_GITEE).get("token", "")


def github_conf():
    tok = os.environ.get("GITHUB_TOKEN") or _load(TOKEN_GITHUB).get("token", "")
    proxy = os.environ.get("GITHUB_PROXY") or _load(TOKEN_GITHUB).get("proxy")
    return tok, proxy


def mask(text):
    """输出前抹掉任何可能混进日志的令牌与代理串，避免终端/日志泄露凭据"""
    if not text:
        return ""
    out = str(text)
    for secret in filter(None, [os.environ.get("GITEE_TOKEN"), gitee_token(),
                                os.environ.get("GITHUB_TOKEN")]):
        out = out.replace(secret, "***")
    try:
        _, proxy = github_conf()
        if proxy:
            out = out.replace(proxy, "***")
    except Exception:
        pass
    out = re.sub(r"(https?://)[^/@\s]+@", r"\1***@", out)
    return out


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
PROJECT_NAME = "穿越生存手册"

# 属于仓库/脚本维护的条目不进发行说明，发行说明只讲内容本身
MAINTENANCE_KEYWORDS = ["脚本", "publish.py", "release.py", "gitignore", "__pycache__",
                        "凭据", "脱敏", "自检", "发行版", "推送", "仓库维护", "readme"]


def changelog_blocks():
    """解析「更新日志」章节，返回 [(版本号, 条目原文), ...]（按行首的 ## 与 - 定位）"""
    lines = open(os.path.join(ROOT, "README.md"), encoding="utf-8").read().split("\n")
    start = None
    for i, ln in enumerate(lines):
        if ln.strip() == "## 更新日志":
            start = i + 1
            break
    if start is None:
        return []
    blocks, cur = [], []
    for ln in lines[start:]:
        if ln.startswith("- "):
            if cur:
                blocks.append("\n".join(cur).strip())
            cur = [ln]
        elif ln.strip().startswith("## "):
            break
        elif cur:
            cur.append(ln)
    if cur:
        blocks.append("\n".join(cur).strip())
    out = []
    for b in blocks:
        m = re.search(r"v(\d+\.\d+)", b)
        out.append(("v" + m.group(1) if m else "vX.Y", b))
    return out


def pick_content_block(blocks):
    """发行说明用最近一条「内容类」条目；工程维护类条目不写进发行说明"""
    for ver, b in blocks:
        if not any(k.lower() in b.lower() for k in MAINTENANCE_KEYWORDS):
            return ver, b
    return blocks[0] if blocks else ("vX.Y", "（更新日志为空）")


def read_changelog():
    """当前版本号取自更新日志第一条；内容说明另行挑选"""
    blocks = changelog_blocks()
    if not blocks:
        return "vX.Y", "更新说明缺失", "（未在 README 中找到「## 更新日志」章节）"
    ver, block = blocks[0]
    return ver, block.split("\n")[0].lstrip("- ").strip(), block


def stats():
    books = len(glob.glob(os.path.join(ROOT, "分册", "*.docx")))
    imgs = len(glob.glob(os.path.join(ROOT, "图片", "*.png")))
    txt = (len(glob.glob(os.path.join(ROOT, "诗词", "*.txt"))) +
           len(glob.glob(os.path.join(ROOT, "小说", "*.txt"))))
    return books, imgs, txt


def release_body(block, content_ver=None, cur_ver=None):
    """发行说明只写内容更新：block 为挑选出的内容类条目"""
    books, imgs, txt = stats()
    body = re.sub(r"^\s*-\s*", "", block).strip() + "\n\n---\n\n"
    body += (f"- 当前规模：技术分册 {books} 册、示意图 {imgs} 幅、纯文本资料 {txt} 册\n"
             f"- Gitee：https://gitee.com/{GITEE_OWNER}/{GITEE_REPO}\n"
             f"- GitHub：https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}\n"
             f"- 本发行版对应 main 分支最新提交")
    if content_ver and cur_ver and content_ver != cur_ver:
        body += (f"\n\n> 说明：本版本（{cur_ver}）为仓库维护更新，内容分册无变化，"
                 f"上方为最近一次内容更新（{content_ver}）。")
    body += ("\n\n> 阅读前请先看仓库内的 `可信度说明.md`：本手册区分【史实】【科学】【经验】【存疑】四类内容，"
             "未标注为史实或科学的数字一律视为经验值，须现场验证。")
    return body


# ---------- 推送前自检：仓库内不得出现任何凭据/代理痕迹 ----------
SECRET_PATTERNS = [
    (r"gh[pousr]_[A-Za-z0-9]{20,}", "GitHub 令牌"),
    (r"github_pat_[A-Za-z0-9_]{20,}", "GitHub 细粒度令牌"),
    (re.escape("socks" + "5://") + r"[^\s\"']+", "SOCKS5 代理地址"),  # 拼接以免与自身源码匹配
    (r"https?://[^\s/@]+:[^\s/@]+@github\.com", "内嵌凭据的推送地址"),
    (r"access_token=[A-Za-z0-9]{8,}", "Gitee 令牌"),
]
SKIP_DIRS = {".git", "图片"}
TEXT_EXT = {".md", ".py", ".txt", ".json", ".yml", ".yaml", ".cfg", ".ini", ".bat", ".ps1", ".sh"}


def scan_secrets():
    """推送前扫描：命中即中止，避免把凭据/代理配置推上公开仓库"""
    bad = []
    for dp, dn, fn in os.walk(ROOT):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in fn:
            if os.path.splitext(f)[1].lower() not in TEXT_EXT:
                continue
            p = os.path.join(dp, f)
            try:
                s = open(p, encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            for pat, name in SECRET_PATTERNS:
                if re.search(pat, s):
                    bad.append((os.path.relpath(p, ROOT), name))
    return bad


# ---------- 推送 ----------
def push_gitee():
    code, out, err = sh(["git", "push", "origin", "main"])
    print("  Gitee push:", "OK" if code == 0 else "FAIL")
    if code != 0:
        print("   ", mask(err)[:300])
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
        print("   ", mask(err or out)[:400])
    return code == 0


# ---------- 发行版 ----------
def release_gitee(ver, body, dry=False):
    tag = ver
    old = gitee("GET", f"/repos/{GITEE_OWNER}/{GITEE_REPO}/releases") or []
    print("  Gitee 现有发行版:", [r.get("tag_name") for r in old])
    if dry:
        return
    for r in old:
        print("   删除旧发行版", r.get("tag_name"))
        gitee("DELETE", f"/repos/{GITEE_OWNER}/{GITEE_REPO}/releases/{r.get('id')}")
    res = gitee("POST", f"/repos/{GITEE_OWNER}/{GITEE_REPO}/releases", {
        "tag_name": tag, "name": f"{PROJECT_NAME} {ver}", "body": body, "target_commitish": "main"})
    if res:
        print("  已创建:", res.get("tag_name"), "|", res.get("name"))


def release_github(ver, body, dry=False):
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
        "tag_name": ver, "name": f"{PROJECT_NAME} {ver}", "body": body,
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

    print("== 0. 凭据自检 ==")
    bad = scan_secrets()
    if bad:
        print("  [中止] 仓库内发现疑似凭据/代理配置：")
        for f, name in bad:
            print("    -", f, "（%s）" % name)
        print("  请先清理再发布；令牌与代理只能放在仓库外的 ~/.gitee_token.json、~/.github_token.json 或环境变量。")
        return

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
    ver, _, _ = read_changelog()
    content_ver, content_block = pick_content_block(changelog_blocks())
    body = release_body(content_block, content_ver, ver)
    print("  版本:", ver, "| 名称:", f"{PROJECT_NAME} {ver}",
          "| 说明取自:", content_ver, "| 长度:", len(body))
    release_gitee(ver, body, dry)
    release_github(ver, body, dry)

    print("\n完成：https://gitee.com/{}/{}/releases/{}".format(GITEE_OWNER, GITEE_REPO, ver))
    print("      https://github.com/{}/{}/releases/{}".format(GITHUB_OWNER, GITHUB_REPO, ver))


if __name__ == "__main__":
    main()
