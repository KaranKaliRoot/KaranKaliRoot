import json, os, re, urllib.request
from datetime import datetime, timezone

USER = os.environ.get("GH_USER", "KaranKaliRoot")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
API = "https://api.github.com"


def get(path):
    req = urllib.request.Request(API + path, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "profile-readme-updater",
        **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}),
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def ago(iso):
    t = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    s = int((datetime.now(timezone.utc) - t).total_seconds())
    for n, u in ((86400, "d"), (3600, "h"), (60, "m")):
        if s >= n:
            return f"{s // n}{u} ago"
    return "just now"


def clean(msg):
    return msg.splitlines()[0].replace("|", "\\|")[:70]


def build():
    user = get(f"/users/{USER}")
    repos = [r for r in get(f"/users/{USER}/repos?sort=pushed&per_page=6&type=owner")
             if r["name"].lower() != USER.lower() and not r["fork"]][:5]
    rows = []
    for r in repos:
        try:
            c = get(f"/repos/{r['full_name']}/commits?per_page=1&author={USER}")
        except Exception:
            c = []
        if c:
            msg, url, when = clean(c[0]["commit"]["message"]), c[0]["html_url"], ago(c[0]["commit"]["author"]["date"])
            cell = f"[{msg}]({url})"
        else:
            cell, when = "—", ago(r["pushed_at"])
        rows.append(f"| [{r['name']}]({r['html_url']}) | {r['language'] or '—'} | {cell} | {when} |")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return "\n".join([
        f"**Public repos:** {user['public_repos']} · **Followers:** {user['followers']} · **Following:** {user['following']}",
        "",
        "| Repository | Language | Latest commit | When |",
        "|------------|----------|---------------|------|",
        *rows,
        "",
        f"<sub>Last synced: {now}</sub>",
    ])


def main():
    text = open("README.md", encoding="utf-8").read()
    new = re.sub(r"(<!--LIVE:START-->).*?(<!--LIVE:END-->)",
                 lambda m: f"{m.group(1)}\n{build()}\n{m.group(2)}", text, flags=re.S)
    open("README.md", "w", encoding="utf-8").write(new)


if __name__ == "__main__":
    main()
