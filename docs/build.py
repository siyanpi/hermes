#!/usr/bin/env python3
"""
应天周报门户 v3 — 4个独立Tab页面
- 主页：4个卡片，点击跳转独立页面
- 每个简报独立HTML页面
- DOI和来源可点击
"""

import os, re, shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

BRIEFING_DIR = Path("/Users/cc/Desktop/Hermes")
PORTAL_DIR = Path.home() / "Desktop/Infinitus/weekly_portal/docs"
ARCHIVE_DIR = PORTAL_DIR / "archive"
TEMPLATE_PATH = PORTAL_DIR / "template.html"

NOW = datetime.now()
WEEK_LABEL = NOW.strftime("%Y-W%U")
DATE_CN = NOW.strftime("%Y年%m月%d日")

PUBLICATION_URLS = {
    "MIT Technology Review": "https://www.technologyreview.com",
    "Business Insider": "https://www.businessinsider.com",
    "Nature Medicine": "https://www.nature.com/nm/",
    "Nature Aging": "https://www.nature.com/nataging/",
    "Nature": "https://www.nature.com",
    "Science": "https://www.science.org",
    "Cell": "https://www.cell.com",
    "Cell Metabolism": "https://www.cell.com/cell-metabolism",
    "Neuron": "https://www.cell.com/neuron",
    "Cell Stem Cell": "https://www.cell.com/cell-stem-cell",
    "Longevity.Technology": "https://longevity.technology",
    "New York Times": "https://www.nytimes.com",
    "Science Advances": "https://www.science.org/journal/sciadv",
    "Pharmacological Research": "https://www.journals.elsevier.com/pharmacological-research",
}

BRIEFINGS = {
    "academic": {
        "id": "academic", "title": "抗衰老学术前沿",
        "subtitle": "线粒体 · 细胞衰老 · 中草药 · 表观遗传 · 检测工具",
        "icon": "🔬", "pattern": "briefing1_academic_",
        "bg": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        "file": "academic.html",
    },
    "industry": {
        "id": "industry", "title": "抗衰老产业进展",
        "subtitle": "逆龄疗法 · 药物管线 · 产业融资 · 中草药产业",
        "icon": "🏭", "pattern": "briefing2_industry_",
        "bg": "linear-gradient(135deg, #11998e 0%, #38ef7d 100%)",
        "file": "industry.html",
    },
    "ai_aging": {
        "id": "ai_aging", "title": "AI × 抗衰老",
        "subtitle": "AI药物发现 · 衰老时钟 · 中草药AI · 蛋白质组学",
        "icon": "🤖", "pattern": "briefing3_AI_aging_",
        "bg": "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
        "file": "ai_aging.html",
    },
    "ai_apps": {
        "id": "ai_apps", "title": "AI 抗衰应用落地",
        "subtitle": "AI药物临床 · 长寿委员会 · 大模型 · 数字孪生 · 投融资",
        "icon": "⚡", "pattern": "briefing4_ai_apps_",
        "bg": "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
        "file": "ai_apps.html",
    },
}


def find_latest(pattern: str) -> Optional[Path]:
    files = sorted(BRIEFING_DIR.glob(f"{pattern}*.md"), reverse=True)
    return files[0] if files else None


def linkify(line: str) -> str:
    """DOI/URL/来源 → clickable HTML"""
    # DOI → doi.org
    line = re.sub(
        r'DOI:?\s*(10\.\d{4,}/[^\s)\].,;]+)',
        r'<a href="https://doi.org/\1" target="_blank">DOI: \1</a>',
        line,
    )
    # 🔗 DOI
    line = re.sub(
        r'🔗\s*DOI:?\s*(10\.\d{4,}/[^\s)\].,;]+)',
        r'<a href="https://doi.org/\1" target="_blank">🔗 DOI: \1</a>',
        line,
    )
    # Bare URL
    line = re.sub(
        r'(?<!href=")(?<!">)(https?://[^\s)\].,;]+)',
        r'<a href="\1" target="_blank">\1</a>',
        line,
    )
    # （来源：Pub, date）
    def src_link(m):
        pub = m.group(1).strip()
        date = m.group(2).strip() if m.lastindex >= 2 else ""
        url = PUBLICATION_URLS.get(pub, "")
        if url:
            return f'<span class="src">（来源：<a href="{url}" target="_blank">{pub}</a>{(", " + date) if date else ""}）</span>'
        q = f"{pub} anti-aging {date}".replace(" ", "+")
        return f'<span class="src">（来源：<a href="https://www.google.com/search?q={q}" target="_blank">{pub}</a>{(", " + date) if date else ""}）</span>'

    line = re.sub(r'（来源[：:]\s*([^，,）]+)(?:[,，]\s*([^）]+))?）', src_link, line)
    return line


def md_to_body(content: str) -> str:
    """Convert markdown to article body HTML."""
    lines = content.split("\n")
    html = []
    i = 0
    skip_title = True

    while i < len(lines):
        line = lines[i].rstrip()

        if line.startswith("# ") and skip_title:
            skip_title = False
            i += 1
            continue
        skip_title = False

        if line.startswith("## "):
            html.append(f'<div class="section"><h3>{linkify(line[3:].strip())}</h3>')
            i += 1
            continue

        if line.startswith("### "):
            html.append(f'<div class="item"><h4>{linkify(line[4:].strip())}</h4>')
            i += 1
            body = []
            while i < len(lines):
                l = lines[i].rstrip()
                if l.startswith("## ") or l.startswith("### ") or l.startswith("---") or l.startswith("# "):
                    break
                if l.strip():
                    body.append(linkify(l))
                i += 1
            if body:
                html.append(f'<div class="body">{" ".join(f"<p>{b}</p>" for b in body)}</div>')
            html.append("</div>")
            continue

        if line.startswith("---"):
            i += 1
            continue

        if line.strip():
            html.append(f'<p>{linkify(line)}</p>')
        i += 1

    html.append("</div>")
    return "\n".join(html)


def generate_page(content: str, title: str, icon: str, bg: str) -> str:
    """Generate a standalone briefing page."""
    body = md_to_body(content)
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} - 应天周报</title>
<style>
body {{ font-family: -apple-system,"PingFang SC","Microsoft YaHei",sans-serif; max-width:900px; margin:0 auto; padding:20px; background:#0f1117; color:#e4e6eb; line-height:1.7; }}
.hero {{ text-align:center; padding:40px 20px 30px; }}
.hero h1 {{ font-size:2em; font-weight:800; background:linear-gradient(135deg,#667eea,#11998e,#f5576c,#fa709a); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; margin-bottom:4px; }}
.hero p {{ color:#b0b3b8; }}
.back {{ display:inline-block; margin-bottom:20px; color:#667eea; text-decoration:none; font-weight:600; }}
.back:hover {{ text-decoration:underline; }}
.section h3 {{ color:#f0c040; border-left:3px solid #f0c040; padding-left:12px; margin:28px 0 16px; font-size:1.15em; }}
.item {{ background:#252836; border-radius:10px; padding:16px 20px; margin:14px 0; }}
.item h4 {{ margin:0 0 10px; color:#e4e6eb; font-size:1em; }}
.item .body p {{ color:#b0b3b8; font-size:0.93em; margin-bottom:6px; line-height:1.7; }}
a {{ color:#667eea; text-decoration:none; }}
a:hover {{ text-decoration:underline; }}
.src {{ color:#8b8fa3; font-size:0.85em; }}
.src a {{ color:#667eea; }}
.footer {{ margin-top:40px; padding-top:16px; border-top:1px solid #2d3142; color:#8b8fa3; font-size:0.85em; text-align:center; }}
@media (max-width:600px) {{ body {{ padding:12px; }} .item {{ padding:12px 14px; }} }}
</style>
</head>
<body>
<a href="index.html" class="back">← 返回周报首页</a>
<div class="hero">
  <h1>{icon} {title}</h1>
  <p>{DATE_CN}</p>
</div>
{body}
<div class="footer">
  <p>应天AI研发系统 · 无限极全球科研中心 | 基于PubMed/Web/arXiv公开信息，仅供研究参考</p>
</div>
</body>
</html>"""


def generate_archive_index() -> str:
    weeks = {}
    for f in sorted(ARCHIVE_DIR.glob("**/*.md"), reverse=True):
        w = f.parent.name
        weeks.setdefault(w, []).append(f)
    for f in sorted(ARCHIVE_DIR.glob("**/*.html"), reverse=True):
        w = f.parent.name
        weeks.setdefault(w, []).append(f)

    if not weeks:
        return "<p class='empty'>暂无归档记录</p>"

    label_map = {
        "academic": "🔬 学术前沿", "industry": "🏭 产业进展",
        "ai_aging": "🤖 AI×抗衰老", "ai_apps": "⚡ AI应用落地",
    }

    h = '<div class="archive-list">'
    for week, files in sorted(weeks.items(), reverse=True):
        h += f'<div class="archive-week"><h4>📅 {week}</h4><ul>'
        for f in sorted(files):
            k = next((k for k in label_map if k in f.stem), None)
            h += f'<li><a href="{f.relative_to(PORTAL_DIR)}">{label_map.get(k, f.stem)}</a></li>'
        h += "</ul></div>"
    return h + "</div>"


def build():
    briefing_data = {}

    for key, cfg in BRIEFINGS.items():
        f = find_latest(cfg["pattern"])
        if f:
            content = f.read_text(encoding="utf-8")
            briefing_data[key] = dict(
                config=cfg,
                path=str(f),
                date=datetime.fromtimestamp(f.stat().st_mtime).strftime("%m/%d"),
                content=content,
            )

    # Generate individual pages
    for key, data in briefing_data.items():
        cfg = data["config"]
        page = generate_page(data["content"], cfg["title"], cfg["icon"], cfg["bg"])
        (PORTAL_DIR / cfg["file"]).write_text(page, encoding="utf-8")
        print(f"📄 {cfg['file']}")

    # Build index
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    for key, data in briefing_data.items():
        cfg = data["config"]
        card = f"""
  <a class="card" href="{cfg['file']}">
    <div class="card-header" style="background:{cfg['bg']}">
      <div class="card-icon">{cfg['icon']}</div>
      <div>
        <div class="card-title">{cfg['title']}</div>
        <div class="card-subtitle">{cfg['subtitle']} · {data['date']}</div>
      </div>
    </div>
    <div class="card-body">{cfg['subtitle']}</div>
    <div class="card-footer">查看详情 →</div>
  </a>
"""
        template = template.replace(f"<!-- {key}_card -->", card)

    template = template.replace("<!-- archive -->", generate_archive_index())
    template = template.replace("{{date}}", DATE_CN)
    template = template.replace("{{week}}", WEEK_LABEL)

    (PORTAL_DIR / "index.html").write_text(template, encoding="utf-8")
    print(f"✅ index.html")

    # Archive
    wa = ARCHIVE_DIR / WEEK_LABEL
    wa.mkdir(parents=True, exist_ok=True)
    for key, data in briefing_data.items():
        src = Path(data["path"])
        dst = wa / f"{key}_{src.name}"
        if not dst.exists():
            shutil.copy2(src, dst)
            print(f"📁 {dst.name}")


def deploy():
    import subprocess
    r = PORTAL_DIR.parent
    try:
        subprocess.run(["git", "add", "-A"], cwd=r, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", f"v3 {WEEK_LABEL}"], cwd=r, capture_output=True)
        x = subprocess.run(["git", "push"], cwd=r, capture_output=True, text=True)
        print("🚀 https://siyanpi.github.io/hermes/" if x.returncode == 0 else f"⚠️ {x.stderr[:200]}")
    except Exception as e:
        print(f"⚠️ {e}")


if __name__ == "__main__":
    build()
    deploy()
