#!/usr/bin/env python3
"""
应天周报门户 v2.1 — 修复版
- JS tab 修复
- 来源转可点击链接
- 完整报告转HTML格式
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

# Known publication URL mapping
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
        "file_label": "briefing1_academic",
    },
    "industry": {
        "id": "industry", "title": "抗衰老产业进展",
        "subtitle": "逆龄疗法 · 药物管线 · 产业融资 · 中草药产业 · 检测",
        "icon": "🏭", "pattern": "briefing2_industry_",
        "bg": "linear-gradient(135deg, #11998e 0%, #38ef7d 100%)",
        "file_label": "briefing2_industry",
    },
    "ai_aging": {
        "id": "ai_aging", "title": "AI × 抗衰老",
        "subtitle": "AI药物发现 · 衰老时钟 · 中草药AI · 蛋白质组学",
        "icon": "🤖", "pattern": "briefing3_AI_aging_",
        "bg": "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
        "file_label": "briefing3_AI_aging",
    },
    "ai_apps": {
        "id": "ai_apps", "title": "AI 抗衰应用落地",
        "subtitle": "AI药物临床 · 长寿委员会 · 大模型 · 数字孪生 · 投融资",
        "icon": "⚡", "pattern": "briefing4_ai_apps_",
        "bg": "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
        "file_label": "briefing4_ai_apps",
    },
}


def find_latest_briefing(pattern: str) -> Optional[Path]:
    files = sorted(BRIEFING_DIR.glob(f"{pattern}*.md"), reverse=True)
    return files[0] if files else None


def linkify_line(line: str) -> str:
    """Convert DOIs, URLs, and source references into clickable HTML links."""
    # DOI → doi.org link
    line = re.sub(
        r'DOI:?\s*(10\.\d{4,}/[^\s)\].,;]+)',
        r'<a href="https://doi.org/\1" target="_blank" class="source-link">DOI: \1</a>',
        line,
    )
    # Bare URL → clickable
    line = re.sub(
        r'(?<!href=")(?<!">)(https?://[^\s)\].,;]+)',
        r'<a href="\1" target="_blank" class="source-link">\1</a>',
        line,
    )
    # （来源：Publication, date）→ linked
    def source_link(m):
        pub = m.group(1).strip()
        date = m.group(2).strip() if m.lastindex >= 2 else ""
        # Try known publication URL
        url = PUBLICATION_URLS.get(pub, "")
        if url:
            return f'<span class="source-ref">（来源：<a href="{url}" target="_blank">{pub}</a>{(", " + date) if date else ""}）</span>'
        else:
            # Google search fallback
            q = f"{pub} anti-aging {date}".replace(" ", "+")
            return f'<span class="source-ref">（来源：<a href="https://www.google.com/search?q={q}" target="_blank">{pub}</a>{(", " + date) if date else ""}）</span>'

    line = re.sub(r'（来源[：:]\s*([^，,）]+)(?:[,，]\s*([^）]+))?）', source_link, line)

    # 🔗 DOI patterns from briefing3
    line = re.sub(
        r'🔗\s*DOI:?\s*(10\.\d{4,}/[^\s)\].,;]+)',
        r'<a href="https://doi.org/\1" target="_blank" class="source-link">🔗 DOI: \1</a>',
        line,
    )

    return line


def md_to_html(content: str) -> str:
    """Convert markdown briefing to HTML with clickable links."""
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

        # H2 → section header
        if line.startswith("## "):
            # Close previous section if any
            html.append(f'<div class="section"><h3>{linkify_line(line[3:].strip())}</h3>')
            i += 1
            continue

        # H3 → item
        if line.startswith("### "):
            html.append(f'<div class="item"><h4>{linkify_line(line[4:].strip())}</h4>')
            i += 1
            body = []
            while i < len(lines):
                l = lines[i].rstrip()
                if l.startswith("## ") or l.startswith("### ") or l.startswith("---") or l.startswith("# "):
                    break
                if l.strip():
                    body.append(linkify_line(l))
                i += 1
            if body:
                html.append(f'<div class="body">{" ".join(f"<p>{b}</p>" for b in body)}</div>')
            html.append("</div>")
            continue

        # --- separator
        if line.startswith("---"):
            i += 1
            continue

        # Bold text, bullet list, etc. — collect as body text
        if line.strip():
            html.append(f'<p>{linkify_line(line)}</p>')

        i += 1

    html.append("</div>")  # close last section
    return "\n".join(html)


def md_to_full_html(content: str, title: str) -> str:
    """Generate a standalone HTML full report page."""
    body_html = md_to_html(content)
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} - 应天周报</title>
<style>
body {{ font-family: -apple-system,"PingFang SC","Microsoft YaHei",sans-serif; max-width:900px; margin:0 auto; padding:20px; background:#0f1117; color:#e4e6eb; line-height:1.7; }}
h1 {{ background:linear-gradient(135deg,#667eea,#11998e,#f5576c); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }}
a {{ color:#667eea; }}
.back {{ display:inline-block; margin-bottom:20px; color:#667eea; text-decoration:none; }}
.section h3 {{ color:#f0c040; border-left:3px solid #f0c040; padding-left:12px; }}
.item {{ background:#252836; border-radius:10px; padding:16px 20px; margin:14px 0; }}
.item h4 {{ margin:0 0 8px; }}
.item .body p {{ color:#b0b3b8; font-size:0.93em; }}
.source-ref {{ color:#8b8fa3; font-size:0.85em; }}
.source-ref a,.source-link {{ color:#667eea; text-decoration:none; }}
</style>
</head>
<body>
<a href="index.html" class="back">← 返回周报首页</a>
<h1>{title}</h1>
{body_html}
<p style="margin-top:30px;color:#8b8fa3;font-size:0.85em;">应天AI研发系统 · 无限极全球科研中心 | 基于PubMed/Web/arXiv公开信息，仅供研究参考</p>
</body>
</html>"""


def generate_archive_index() -> str:
    weeks = {}
    for f in sorted(ARCHIVE_DIR.glob("**/*.md"), reverse=True):
        week_dir = f.parent.name
        if week_dir not in weeks:
            weeks[week_dir] = []
        weeks[week_dir].append(f)

    for f in sorted(ARCHIVE_DIR.glob("**/*.html"), reverse=True):
        week_dir = f.parent.name
        if week_dir not in weeks:
            weeks[week_dir] = []
        weeks[week_dir].append(f)

    if not weeks:
        return "<p class='empty'>暂无归档记录</p>"

    label_map = {
        "academic": "🔬 学术前沿",
        "industry": "🏭 产业进展",
        "ai_aging": "🤖 AI×抗衰老",
        "ai_apps": "⚡ AI应用落地",
    }

    html = '<div class="archive-list">'
    for week, files in sorted(weeks.items(), reverse=True):
        html += f'<div class="archive-week"><h4>📅 {week}</h4><ul>'
        for f in sorted(files):
            key = next((k for k in label_map if k in f.stem), None)
            display = label_map.get(key, f.stem)
            rel_path = f.relative_to(PORTAL_DIR)
            html += f'<li><a href="{rel_path}">{display}</a></li>'
        html += "</ul></div>"
    html += "</div>"
    return html


def build():
    briefing_data = {}

    for key, cfg in BRIEFINGS.items():
        f = find_latest_briefing(cfg["pattern"])
        if f:
            content = f.read_text(encoding="utf-8")
            briefing_data[key] = {
                "config": cfg,
                "path": str(f),
                "filename": f.name,
                "html": md_to_html(content),
                "full_html": md_to_full_html(content, cfg["title"]),
                "date": datetime.fromtimestamp(f.stat().st_mtime).strftime("%m/%d"),
            }

    # Generate full report HTML files
    for key, data in briefing_data.items():
        cfg = data["config"]
        html_path = PORTAL_DIR / f"{cfg['file_label']}.html"
        html_path.write_text(data["full_html"], encoding="utf-8")
        print(f"📄 HTML完整报告: {html_path}")

    # Build index page
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    for key, data in briefing_data.items():
        cfg = data["config"]
        html_file = f"{cfg['file_label']}.html"

        card_html = f"""
        <div class="module-card" id="{cfg['id']}">
            <div class="module-header" style="background: {cfg['bg']}">
                <div class="module-icon">{cfg['icon']}</div>
                <div class="module-title-group">
                    <h2>{cfg['title']}</h2>
                    <span class="module-subtitle">{cfg['subtitle']} · {data['date']}</span>
                </div>
            </div>
            <div class="module-body">
                <a href="{html_file}" class="full-report-link">📄 查看完整报告（HTML）</a>
                {data['html']}
            </div>
        </div>
        """
        template = template.replace(f"<!-- {key}_module -->", card_html)

    template = template.replace("<!-- archive -->", generate_archive_index())
    template = template.replace("{{date}}", DATE_CN)
    template = template.replace("{{week}}", WEEK_LABEL)

    output = PORTAL_DIR / "index.html"
    output.write_text(template, encoding="utf-8")
    print(f"✅ 门户页面已生成: {output}")

    # Archive
    week_archive = ARCHIVE_DIR / WEEK_LABEL
    week_archive.mkdir(parents=True, exist_ok=True)
    for key, data in briefing_data.items():
        src = Path(data["path"])
        dst = week_archive / f"{key}_{src.name}"
        if not dst.exists():
            shutil.copy2(src, dst)
            print(f"📁 已归档: {dst.name}")


def deploy():
    import subprocess
    repo = PORTAL_DIR.parent
    try:
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", f"weekly {WEEK_LABEL} - {DATE_CN}"],
            cwd=repo, capture_output=True,
        )
        r = subprocess.run(["git", "push"], cwd=repo, capture_output=True, text=True)
        if r.returncode == 0:
            print("🚀 已部署 https://siyanpi.github.io/hermes/")
        else:
            print(f"⚠️ push: {r.stderr[:200]}")
    except Exception as e:
        print(f"⚠️ {e}")


if __name__ == "__main__":
    build()
    deploy()
