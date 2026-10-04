"""Obsidian保管庫から読書ページ（1枚のHTML）を組み立てる。使い方: python3 tools/build_reader.py 出力先.html"""
import glob, html, json, re, sys

V = "腐らない森の菌糸体"
ORDER = ["柴崎恒", "感覚", "物差し", "右光", "苦い鎧", "丸い部屋と胞子", "石の柱", "薪の山", "葉の層", "外の何か", "板と紙", "拍と俺の範囲"]


def strip_links(s):
    s = re.sub(r"\[\[[^\]|]+\|([^\]]+)\]\]", r"\1", s)
    return re.sub(r"\[\[([^\]]+)\]\]", r"\1", s)


def inline(x):
    x = html.escape(x)
    x = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", x)
    x = re.sub(r"\*(.+?)\*", r"<em>\1</em>", x)
    return x.replace("\\|", "|")


def md2html(md):
    md = re.sub(r"^---\n.*?\n---\n", "", strip_links(md), flags=re.S)
    out, lines, i = [], md.split("\n"), 0
    while i < len(lines):
        l = lines[i]
        if l.startswith("目次") or not l.strip():
            i += 1
            continue
        if l.startswith("# "):
            out.append(f"<h3>{inline(l[2:])}</h3>")
        elif l.startswith("## "):
            out.append(f"<h4>{inline(l[3:])}</h4>")
        elif l.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append(lines[i])
                i += 1
            cells = lambda r: [c.strip() for c in re.split(r"(?<!\\)\|", r.strip()[1:-1])]
            head = "".join(f"<th>{inline(c)}</th>" for c in cells(rows[0]))
            body = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in cells(r)) + "</tr>" for r in rows[2:])
            out.append(f"<div class='tw'><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>")
            continue
        elif l.startswith("- "):
            items = []
            while i < len(lines) and (lines[i].startswith("- ") or lines[i].startswith("  - ")):
                items.append(inline(lines[i].lstrip(" -")))
                i += 1
            out.append("<ul>" + "".join(f"<li>{x}</li>" for x in items) + "</ul>")
            continue
        else:
            out.append(f"<p>{inline(l)}</p>")
        i += 1
    return "\n".join(out)


def episodes():
    eps = []
    for p in sorted(glob.glob(f"{V}/本文/第*.md")):
        s = open(p, encoding="utf-8").read()
        fm = dict(re.findall(r'^(話|題|章|経過夜露|先っぽ): "?(.*?)"?$', s.split("---")[1], re.M))
        summ = re.search(r"> \[!summary\]-.*\n> (.+)", s).group(1)
        body = s.split(summ, 1)[1].rsplit("\n---\n", 1)[0].strip("\n")
        blocks = []
        for b in re.split(r"\n\s*\n", body):
            ls = [l.rstrip() for l in b.split("\n") if l.strip()]
            if ls:
                blocks.append(["＊"] if ls[0].strip() == "＊" else ls)
        eps.append(dict(n=int(fm["話"]), t=fm["題"], ch=fm["章"], yo=fm["経過夜露"], tip=fm["先っぽ"], s=summ, p=blocks))
    return eps


data = dict(
    eps=episodes(),
    gloss=[dict(k=k, h=md2html(open(f"{V}/設定/{k}.md", encoding="utf-8").read())) for k in ORDER],
    syn=md2html(open(f"{V}/まとめ/これまでのあらすじ.md", encoding="utf-8").read()),
    myst=md2html(open(f"{V}/まとめ/謎の台帳.md", encoding="utf-8").read()),
)
tpl = open("tools/reader_template.html", encoding="utf-8").read()
out = tpl.replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
open(sys.argv[1] if len(sys.argv) > 1 else "reader.html", "w", encoding="utf-8").write(out)
