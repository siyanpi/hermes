#!/usr/bin/env python3
"""应天周报门户 v4 — 修复链接+Markdown渲染+摘要+归档搜索"""

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
    "academic": {"title":"抗衰老学术前沿","subtitle":"线粒体·细胞衰老·中草药·表观遗传·检测","icon":"🔬","pattern":"briefing1_academic_","bg":"linear-gradient(135deg,#667eea 0%,#764ba2 100%)","file":"academic.html"},
    "industry": {"title":"抗衰老产业进展","subtitle":"逆龄疗法·药物管线·融资·中草药产业","icon":"🏭","pattern":"briefing2_industry_","bg":"linear-gradient(135deg,#11998e 0%,#38ef7d 100%)","file":"industry.html"},
    "ai_aging": {"title":"AI × 抗衰老","subtitle":"AI药物·衰老时钟·中草药AI·蛋白质组学","icon":"🤖","pattern":"briefing3_AI_aging_","bg":"linear-gradient(135deg,#f093fb 0%,#f5576c 100%)","file":"ai_aging.html"},
    "ai_apps": {"title":"AI 抗衰应用落地","subtitle":"AI药物临床·长寿委员会·大模型·数字孪生","icon":"⚡","pattern":"briefing4_ai_apps_","bg":"linear-gradient(135deg,#fa709a 0%,#fee140 100%)","file":"ai_apps.html"},
    "competitor_food": {"title":"延衰健食 · 竞对","subtitle":"安利·汤臣倍健·Swisse·同仁堂·正官庄等","icon":"🍵","pattern":"briefing5_competitor_food_","bg":"linear-gradient(135deg,#43e97b 0%,#38f9d7 100%)","file":"competitor_food.html"},
    "competitor_beauty": {"title":"延衰美妆 · 竞对","subtitle":"欧莱雅·资生堂·雅诗兰黛·爱茉莉等","icon":"💄","pattern":"briefing6_competitor_beauty_","bg":"linear-gradient(135deg,#a18cd1 0%,#fbc2eb 100%)","file":"competitor_beauty.html"},
    "competitor_women": {"title":"女性健康 · 竞对","subtitle":"月神·BIOCARE·Swisse·生命花园等","icon":"🌸","pattern":"briefing7_competitor_women_","bg":"linear-gradient(135deg,#ffecd2 0%,#fcb69f 100%)","file":"competitor_women.html"},
}

TAG_PATTERNS = {
    "临床": ["临床","clinical trial","人体试验","FDA","NMPA","III期","II期"],
    "融资": ["融资","funding","IPO","投资","收购","并购","估值"],
    "成分": ["成分","ingredient","提取物","多酚","肽","胶原蛋白","益生菌","NAD","NMN"],
    "新品": ["新品","launch","推出","发布","上市"],
    "法规": ["法规","regulatory","监管","审批","GRAS"],
    "AI制药": ["AI","机器学习","深度学习","大模型","生成式"],
    "中草药": ["中草药","TCM","herbal","人参","黄芪","枸杞","灵芝"],
    "衰老机制": ["衰老","aging","senescence","senolytic","长寿","longevity"],
}


def find_latest(pattern: str) -> Optional[Path]:
    files = sorted(BRIEFING_DIR.glob(f"{pattern}*.md"), reverse=True)
    return files[0] if files else None


# ── FIXED: URL regex that allows dots ──
def linkify(line: str) -> str:
    """Convert DOIs/URLs/sources to clickable HTML. FIXED: dots allowed in URLs."""
    # DOI
    line = re.sub(r'DOI:?\s*(10\.\d{4,}/[^\s)\]<>]+)', r'<a href="https://doi.org/\1" target="_blank">DOI: \1</a>', line)
    line = re.sub(r'🔗\s*DOI:?\s*(10\.\d{4,}/[^\s)\]<>]+)', r'<a href="https://doi.org/\1" target="_blank">🔗 DOI: \1</a>', line)
    # Bare URL — allow dots, commas, semicolons
    line = re.sub(r'(?<!href=")(?<!">)(https?://[^\s)\]<>]+)', r'<a href="\1" target="_blank">\1</a>', line)
    # Source mentions
    def src_link(m):
        pub = m.group(1).strip()
        date = m.group(2).strip() if m.lastindex and m.lastindex >= 2 else ""
        url = PUBLICATION_URLS.get(pub, "")
        if url:
            return f'<span class="src">（来源：<a href="{url}" target="_blank">{pub}</a>{", "+date if date else ""}）</span>'
        return f'<span class="src">（来源：{pub}{", "+date if date else ""}）</span>'
    line = re.sub(r'（来源[：:]\s*([^，,）]+)(?:[,，]\s*([^）]+))?）', src_link, line)
    return line


# ── Full Markdown → HTML renderer ──
def md_to_html(content: str) -> str:
    """Full markdown to HTML: bold, italic, tables, blockquotes, lists, code."""
    lines = content.split("\n")
    html = []
    i = 0
    in_table = False
    in_list = False

    while i < len(lines):
        l = lines[i].rstrip()

        # Skip H1
        if l.startswith("# ") and i < 2:
            i += 1; continue

        # H2
        if l.startswith("## "):
            if in_list: html.append("</ul>"); in_list = False
            if in_table: html.append("</table>"); in_table = False
            html.append(f'<h3 class="sec">{linkify(l[3:].strip())}</h3>')
            i += 1; continue

        # H3
        if l.startswith("### "):
            if in_list: html.append("</ul>"); in_list = False
            if in_table: html.append("</table>"); in_table = False
            title = linkify(l[4:].strip())
            # Collect body until next heading
            i += 1
            body_lines = []
            while i < len(lines):
                ll = lines[i].rstrip()
                if ll.startswith(("## ","### ","---","# ")): break
                body_lines.append(ll)
                i += 1
            body_html = _render_block(body_lines)
            html.append(f'<div class="item"><h4>{title}</h4><div class="body">{body_html}</div></div>')
            continue

        # Table
        if "|" in l and l.strip().startswith("|"):
            if in_list: html.append("</ul>"); in_list = False
            if not in_table:
                in_table = True
                html.append('<table class="md-table">')
            cells = [c.strip() for c in l.split("|")[1:-1]]
            if all(c.startswith("---") or c.startswith(":--") for c in cells if c):
                i += 1; continue  # skip separator row
            tag = "th" if i+1 < len(lines) and "---" in lines[i+1] else "td"
            html.append("<tr>" + "".join(f"<{tag}>{linkify(c)}</{tag}>" for c in cells) + "</tr>")
            i += 1; continue

        # List item
        if re.match(r'^[-*]\s', l):
            if in_table: html.append("</table>"); in_table = False
            if not in_list: html.append("<ul>"); in_list = True
            stripped = re.sub(r'^[-*]\s','',l)
            html.append(f"<li>{_render_inline(linkify(stripped))}</li>")
            i += 1; continue

        # Blockquote
        if l.startswith("> "):
            if in_list: html.append("</ul>"); in_list = False
            if in_table: html.append("</table>"); in_table = False
            html.append(f'<blockquote>{_render_inline(linkify(l[2:].strip()))}</blockquote>')
            i += 1; continue

        # Separator
        if l.startswith("---"):
            if in_list: html.append("</ul>"); in_list = False
            if in_table: html.append("</table>"); in_table = False
            html.append("<hr>")
            i += 1; continue

        # Bold-only line (like **覆盖周期**: ...)
        if l.strip():
            if in_list: html.append("</ul>"); in_list = False
            if in_table: html.append("</table>"); in_table = False
            html.append(f"<p>{_render_inline(linkify(l))}</p>")

        i += 1

    if in_table: html.append("</table>")
    if in_list: html.append("</ul>")
    return "\n".join(html)


def _render_inline(text: str) -> str:
    """Render inline markdown: **bold**, *italic*, `code`, [text](url)."""
    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # Italic
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    # Inline code
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    # Markdown links [text](url) — only if not already HTML
    text = re.sub(r'\[([^\]]+)\]\((https?://[^\)]+)\)', r'<a href="\2" target="_blank">\1</a>', text)
    return text


def _render_block(lines: list) -> str:
    """Render a block of mixed markdown into HTML."""
    out = []
    in_list = False
    for l in lines:
        l = l.strip()
        if not l: continue
        if re.match(r'^[-*]\s', l):
            if not in_list: out.append("<ul>"); in_list = True
            stripped2 = re.sub(r'^[-*]\s','',l)
            out.append(f"<li>{_render_inline(linkify(stripped2))}</li>")
        elif l.startswith("> "):
            if in_list: out.append("</ul>"); in_list = False
            out.append(f"<blockquote>{_render_inline(linkify(l[2:].strip()))}</blockquote>")
        else:
            if in_list: out.append("</ul>"); in_list = False
            out.append(f"<p>{_render_inline(linkify(l))}</p>")
    if in_list: out.append("</ul>")
    return "".join(out)


def _extract_highlights(content: str) -> str:
    """Extract top 3 highlights from content as decision-layer summary."""
    lines = content.split("\n")
    highlights = []
    for line in lines:
        stripped = line.strip()
        # Look for key phrases
        if any(kw in stripped for kw in ["突破","首次","重大","关键","里程碑","里程碑","最重要","核心","重磅"]):
            if len(stripped) > 20 and len(stripped) < 300:
                highlights.append(stripped)
        if len(highlights) >= 3: break
    if not highlights:
        # Fallback: first 3 H3 titles
        for line in lines:
            if line.startswith("### "):
                highlights.append(line[4:].strip())
            if len(highlights) >= 3: break
    if not highlights:
        return ""
    items = "".join(f"<li>{_render_inline(linkify(h[:200]))}</li>" for h in highlights)
    return f'<div class="highlights"><h4>📌 本期要点</h4><ul>{items}</ul></div>'


def _extract_tags(content: str) -> list:
    """Extract tags from content based on keyword matching."""
    found = set()
    text_lower = content.lower()
    for tag, keywords in TAG_PATTERNS.items():
        for kw in keywords:
            if kw.lower() in text_lower:
                found.add(tag)
                break
    return sorted(found)


def _extract_text_snippet(path: Path, max_chars: int = 300) -> str:
    """Extract plain text from md/html file for search indexing."""
    try:
        raw = path.read_text(encoding="utf-8")
        if path.suffix == ".html":
            # Strip HTML tags
            raw = re.sub(r'<style[^>]*>.*?</style>', '', raw, flags=re.DOTALL)
            raw = re.sub(r'<[^>]+>', ' ', raw)
        # Strip markdown syntax
        raw = re.sub(r'[#*>`|\[\]()_~]', ' ', raw)
        raw = re.sub(r'\s+', ' ', raw).strip()
        return raw[:max_chars]
    except:
        return ""


def archive_index() -> str:
    """Generate archive with full-text search, collapsible weeks, colored tags."""
    all_files = []
    for f in sorted(ARCHIVE_DIR.glob("**/*.md"), reverse=True):
        all_files.append(f)
    for f in sorted(ARCHIVE_DIR.glob("**/*.html"), reverse=True):
        if f.name != "index.html":
            all_files.append(f)

    if not all_files:
        return "<p class='empty'>暂无归档记录</p>"

    labels = {k: f"{v['icon']} {v['title']}" for k, v in BRIEFINGS.items()}
    mod_labels = {"academic":"学术","industry":"产业","ai_aging":"AI","ai_apps":"AI应用","competitor_food":"健食","competitor_beauty":"美妆","competitor_women":"女性"}
    tag_class = {"学术":"tag-academic","产业":"tag-industry","AI":"tag-ai","AI应用":"tag-ai","健食":"tag-food","美妆":"tag-beauty","女性":"tag-women"}

    weeks = {}
    for f in all_files:
        w = f.parent.name
        weeks.setdefault(w, []).append(f)

    groups = []
    for week in sorted(weeks.keys(), reverse=True):
        files = weeks[week]
        items = []
        for f in sorted(files):
            k = next((k for k in labels if k in f.stem), "")
            mod = mod_labels.get(k, "")
            tc = tag_class.get(mod, "")
            rel = str(f.relative_to(PORTAL_DIR))
            snippet = _extract_text_snippet(f).replace('"', "'")
            items.append(f'<div class="arch-item" data-week="{week}" data-module="{mod}" data-title="{f.name}" data-content="{snippet}"><span class="arch-mod-tag {tc}">{mod}</span><a href="{rel}">{labels.get(k, f.name)}</a></div>')
        if items:
            groups.append(f'<div class="arch-week-group"><div class="arch-week-header" onclick="toggleWeek(this)"><span class="arrow">▼</span>📅 {week} <span class="arch-week-count">({len(items)}篇)</span></div><div class="arch-week-items">{"".join(items)}</div></div>')

    return f"""<div class="archive-tools">
<input type="text" id="arch-search" placeholder="🔍 搜索归档标题+正文..." oninput="filterArchive()">
<select id="arch-module" onchange="filterArchive()"><option value="">全部模块</option>{"".join(f'<option value="{v}">{v}</option>' for v in sorted(set(mod_labels.values()))) if mod_labels else ""}</select>
</div>
<div id="arch-result-count" class="arch-result-count"></div>
<div id="arch-grid">{"".join(groups)}</div>
<div id="arch-empty" style="display:none" class="empty">无匹配结果</div>""" if groups else "<p class='empty'>暂无归档记录</p>"


def generate_page(content: str, title: str, icon: str) -> str:
    body = md_to_html(content)
    highlights = _extract_highlights(content)
    tags = _extract_tags(content)
    tag_html = "".join(f'<span class="tag">{t}</span>' for t in tags)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title} - 应天周报</title>
<style>
body{{font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;max-width:900px;margin:0 auto;padding:20px;background:#0f1117;color:#e4e6eb;line-height:1.7}}
.hero{{text-align:center;padding:40px 20px 20px}}
.hero h1{{font-size:2em;font-weight:800;background:linear-gradient(135deg,#667eea,#11998e,#f5576c,#fa709a);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}}
.back{{display:inline-block;margin-bottom:14px;color:#667eea;text-decoration:none;font-weight:600}}.back:hover{{text-decoration:underline}}
.highlights{{background:#1a2733;border-left:3px solid #f0c040;padding:16px 20px;margin:16px 0 24px;border-radius:0 10px 10px 0}}
.highlights h4{{color:#f0c040;margin:0 0 8px;font-size:1em}}
.highlights ul{{margin:0;padding-left:18px;color:#b0b3b8}}
.tags{{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0 16px}}
.tag{{padding:3px 12px;background:#252836;border-radius:12px;font-size:.8em;color:#667eea}}
h3.sec{{color:#f0c040;border-left:3px solid #f0c040;padding-left:12px;margin:28px 0 16px;font-size:1.15em}}
.item{{background:#252836;border-radius:10px;padding:16px 20px;margin:14px 0}}
.item h4{{margin:0 0 10px;color:#e4e6eb;font-size:1em}}
.item .body p{{color:#b0b3b8;font-size:.93em;margin-bottom:6px;line-height:1.7}}
.item .body ul,.item .body ol{{color:#b0b3b8;padding-left:18px;margin:6px 0}}
.item .body li{{margin:2px 0}}
.item .body blockquote{{border-left:3px solid #667eea;padding-left:12px;margin:8px 0;color:#8b9fa3;font-style:italic}}
.item .body strong{{color:#e4e6eb}}
.item .body code{{background:#1a1d27;padding:2px 6px;border-radius:4px;font-size:.9em}}
.md-table{{width:100%;border-collapse:collapse;margin:8px 0;font-size:.9em}}
.md-table th,.md-table td{{border:1px solid #2d3142;padding:6px 10px;text-align:left}}
.md-table th{{background:#252836;color:#e4e6eb}}
.md-table td{{color:#b0b3b8}}
hr{{border:none;border-top:1px solid #2d3142;margin:16px 0}}
a{{color:#667eea;text-decoration:none}}a:hover{{text-decoration:underline}}
.src{{color:#8b8fa3;font-size:.85em}}.src a{{color:#667eea}}
.footer{{margin-top:40px;padding-top:16px;border-top:1px solid #2d3142;color:#8b8fa3;font-size:.85em;text-align:center}}
@media(max-width:600px){{body{{padding:12px}}.item{{padding:12px 14px}}}}
</style></head>
<body>
<a href="index.html" class="back">← 返回周报首页</a>
<div class="hero"><h1>{icon} {title}</h1><p>{DATE_CN}</p></div>
{tag_html}
{highlights}
{body}
<div class="footer"><p>应天AI研发系统 · 无限极全球科研中心 | 基于PubMed/Web/arXiv公开信息，仅供研究参考</p></div>
</body></html>"""


def build():
    data = {}
    for key, cfg in BRIEFINGS.items():
        f = find_latest(cfg["pattern"])
        if f:
            content = f.read_text(encoding="utf-8")
            data[key] = dict(cfg=cfg, date=datetime.fromtimestamp(f.stat().st_mtime).strftime("%m/%d"), content=content, path=str(f))

    for key, d in data.items():
        page = generate_page(d["content"], d["cfg"]["title"], d["cfg"]["icon"])
        (PORTAL_DIR / d["cfg"]["file"]).write_text(page, encoding="utf-8")
        print(f"📄 {d['cfg']['file']}")

    tpl = TEMPLATE_PATH.read_text(encoding="utf-8")
    for key, d in data.items():
        cfg = d["cfg"]
        card = f"""  <a class="card" href="{cfg['file']}">
    <div class="card-header" style="background:{cfg['bg']}"><div class="card-icon">{cfg['icon']}</div><div><div class="card-title">{cfg['title']}</div><div class="card-subtitle">{d['date']}</div></div></div>
    <div class="card-body">{cfg['subtitle']}</div>
    <div class="card-footer">查看详情 →</div></a>"""
        tpl = tpl.replace(f"<!-- {key}_card -->", card)

    tpl = tpl.replace("<!-- archive -->", archive_index())
    tpl = tpl.replace("{{date}}", DATE_CN).replace("{{week}}", WEEK_LABEL)
    (PORTAL_DIR / "index.html").write_text(tpl, encoding="utf-8")
    print("✅ index.html")

    wa = ARCHIVE_DIR / WEEK_LABEL
    wa.mkdir(parents=True, exist_ok=True)
    for key, d in data.items():
        src = Path(d["path"]); dst = wa / f"{key}_{src.name}"
        if not dst.exists(): shutil.copy2(src, dst)


def deploy():
    import subprocess
    r = PORTAL_DIR.parent
    try:
        subprocess.run(["git", "add", "-A"], cwd=r, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", f"v4 {WEEK_LABEL}"], cwd=r, capture_output=True)
        x = subprocess.run(["git", "push"], cwd=r, capture_output=True, text=True)
        print("🚀 https://siyanpi.github.io/hermes/" if x.returncode == 0 else f"⚠️ {x.stderr[:200]}")
    except Exception as e: print(f"⚠️ {e}")


if __name__ == "__main__":
    build()
    deploy()
