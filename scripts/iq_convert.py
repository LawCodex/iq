#!/usr/bin/env python3
"""Convert archived iraqld.hjc.iq LoadLawBook pages (see iq_fetch.py) to Markdown.

Usage: iq_convert.py [RAW_DIR] [OUT_DIR]
"""
import collections
import glob
import json
import os
import re
import sys
from datetime import date

import yaml
from bs4 import BeautifulSoup, NavigableString

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "..", "_raw", "iq")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..")
RETRIEVED = os.environ.get("RETRIEVED", date.today().isoformat())

TYPE_DIRS = [
    ("دستور", "constitution", "constitution"),
    ("قانون", "laws", "law"),
    ("امر", "orders", "order"),
    ("أمر", "orders", "order"),
    ("نظام", "regulations", "regulation"),
    ("تعليمات", "instructions", "instructions"),
    ("قرار", "decisions", "decision"),
    ("بيان", "statements", "statement"),
    ("مرسوم", "decrees", "decree"),
]

META_KEYS = {
    "التصنيف": "classification",
    "الجهة المصدرة": "issuer",
    "نوع التشريع": "type_ar",
    "رقم التشريع": "number",
    "تاريخ التشريع": "date",
    "سريان التشريع": "status_ar",
    "عنوان التشريع": "title",
}


def load(fn):
    b = open(fn, "rb").read()
    try:
        return b.decode("utf-8")
    except UnicodeDecodeError:
        return b.decode("windows-1256", "replace")


def norm(s):
    s = s.replace("\xa0", " ").replace("‌", "").replace("‏", "").replace("‎", "")
    return re.sub(r"[ \t]+", " ", s).strip()


def parse_meta(html):
    m = re.search(r'<span id="Label3">(.*?)</span>', html, re.S)
    if not m:
        return None
    parts = re.split(r"</?br\s*/?>", m.group(1), flags=re.I)
    meta = {"gazette": []}
    for p in parts:
        t = norm(BeautifulSoup(p, "html.parser").get_text(" "))
        if not t:
            continue
        m = re.match(r"^([^:]+?)\s*:\s*(.*)$", t)
        if m and m.group(1).strip() in META_KEYS:
            meta[META_KEYS[m.group(1).strip()]] = m.group(2).strip()
        elif t.startswith("المصدر") or "رقم العدد" in t or "رقم الصفحة" in t:
            meta["gazette"].append(re.sub(r"^المصدر\s*:\s*", "", t).strip(" |"))
        elif t.startswith("ملاحظة"):
            n = t.split(":", 1)[1].strip() if ":" in t else ""
            if n:
                meta["note"] = n
    return meta


def page_count(soup):
    lab = soup.find(id="Label8")
    if not lab:
        return 1
    nums = [int(x) for x in re.findall(r"page=(\d+)", str(lab))]
    return max(nums) if nums else 1


def parse_body(soup):
    lab = soup.find(id="Label2")
    if lab is None:
        return None
    for a in lab.find_all("a"):
        if "VerdictsLstResults" in (a.get("href") or ""):
            a.decompose()
    for p in lab.find_all("p", id="ddd2"):
        p.replace_with(NavigableString("\n\x01H" + norm(p.get_text(" ")) + "\n"))
    for p in lab.find_all("p", id="ddd"):
        p.replace_with(NavigableString("\n\x01A" + norm(p.get_text(" ")) + "\n"))
    for br in lab.find_all("br"):
        br.replace_with(NavigableString("\n"))
    for t in lab.find_all(["p", "div", "tr"]):
        t.insert_after(NavigableString("\n"))
    text = lab.get_text("")
    blocks = []  # (kind, text)
    for ln in text.split("\n"):
        ln = norm(ln)
        if not ln:
            continue
        if ln.startswith("\x01H"):
            blocks.append(("H", ln[2:].strip()))
        elif ln.startswith("\x01A"):
            blocks.append(("A", ln[2:].strip()))
        else:
            blocks.append(("T", ln))
    return blocks


ENUM_RE = re.compile(r"^(?:\(?[0-9٠-٩]+\s*[-\)\.–]|\(?[أ-ي]{1,2}\s*[-\)\.–‌]|[-•*]\s)")


def esc(line):
    if re.match(r"^(#|>|\d+\.\s|[-+*]\s|={3,}|-{3,})", line):
        return "\\" + line
    return line


def render(blocks):
    out = []
    prev = None
    for kind, t in blocks:
        if not t:
            continue
        if kind == "H":
            out += ["", f"### {t}", ""]
        elif kind == "A":
            out += ["", f"##### {t}", ""]
        else:
            if prev == "T" and ENUM_RE.match(t):
                out.append("")
            out.append(esc(t))
        prev = kind
    s = "\n".join(out)
    return re.sub(r"\n{3,}", "\n\n", s).strip() + "\n"


def ymd(d):
    m = re.match(r"(\d{1,2})-(\d{1,2})-(\d{4})", d or "")
    if not m:
        return None, None
    return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}", int(m.group(3))


def tdir(type_ar):
    t = (type_ar or "").strip()
    for k, d, typ in TYPE_DIRS:
        if t.startswith(k):
            return d, typ
    return "other", "other"


def slug_num(n):
    n = re.sub(r"[^0-9A-Za-z]+", "-", n or "").strip("-")
    return n or "0"


def main():
    global CAPS
    sys.path.insert(0, HERE)
    from iq_fetch import captures
    CAPS = captures(RAW)
    pages = collections.defaultdict(dict)
    for fn in glob.glob(os.path.join(RAW, "html", "*_p*.html")):
        m = re.match(r"(\d+)_p(\d+)\.html$", os.path.basename(fn))
        pages[m.group(1)][int(m.group(2))] = fn
    counts = collections.Counter()
    seen_paths = set()
    report = {"skipped": [], "incomplete": []}
    for sc in sorted(pages):
        p1 = pages[sc].get(1)
        if not p1:
            report["skipped"].append([sc, "no page 1"])
            continue
        soup = BeautifulSoup(load(p1), "html.parser")
        meta = parse_meta(load(p1))
        if not meta or not meta.get("title"):
            report["skipped"].append([sc, "no metadata"])
            continue
        n = page_count(BeautifulSoup(load(p1), "html.parser"))
        blocks, missing = [], []
        for i in range(1, n + 1):
            fn = pages[sc].get(i)
            b = parse_body(BeautifulSoup(load(fn), "html.parser")) if fn else None
            if b is None:
                missing.append(i)
                blocks.append(("T", f"*[الصفحة {i} من {n} من هذا التشريع غير متوفرة في النسخة المؤرشفة]*"))
                continue
            blocks.extend(b)
        if not any(k == "T" for k, _ in blocks):
            report["skipped"].append([sc, "empty body"])
            continue
        iso, year = ymd(meta.get("date"))
        d, typ = tdir(meta.get("type_ar"))
        st = meta.get("status_ar") or ""
        status = "in_force" if st.startswith("ساري") else ("repealed" if ("ملغ" in st or "غير" in st) else "unknown")
        title = meta["title"]
        fm = {
            "title": title,
            "identifier": f"iraqld:{sc}",
            "number": meta.get("number") or None,
            "type": typ,
            "type_ar": meta.get("type_ar"),
            "classification": meta.get("classification"),
            "issuer": meta.get("issuer"),
            "jurisdiction": "iq",
            "language": "ar",
            "date": iso,
            "status": status,
            "status_ar": st or None,
            "gazette": " ; ".join(meta["gazette"]) or None,
            "note": meta.get("note"),
            "complete": not missing,
            "missing_pages": missing or None,
            "pages": n,
            "source": f"http://iraqld.hjc.iq/LoadLawBook.aspx?SC={sc}",
            "archived": [f"https://web.archive.org/web/{CAPS[sc][i][0]}/{CAPS[sc][i][1]}"
                         for i in sorted(pages[sc]) if i in CAPS.get(sc, {})] or None,
            "retrieved": RETRIEVED,
        }
        fm = {k: v for k, v in fm.items() if v is not None}
        if missing:
            report["incomplete"].append([sc, title, missing, n])
        yr = str(year) if year else "undated"
        if d == "constitution":
            rel = os.path.join("ar", d, f"{yr}-{sc}.md")
        else:
            rel = os.path.join("ar", d, yr, f"{yr}-{slug_num(meta.get('number'))}-{sc}.md")
        assert rel not in seen_paths
        seen_paths.add(rel)
        path = os.path.join(OUT, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        body = f"# {title}\n\n"
        if missing:
            body += ("> **ملاحظة:** هذا النص غير مكتمل؛ بعض صفحاته غير متوفرة في أرشيف الإنترنت "
                     f"(الصفحات: {', '.join(map(str, missing))} من {n}).\n\n")
        body += render(blocks)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write("---\n" + yaml.safe_dump(fm, allow_unicode=True, sort_keys=False, width=1000) + "---\n\n")
            f.write(body)
        counts[(d, status, "complete" if not missing else "partial")] += 1
    for k, v in sorted(counts.items()):
        print(k, v)
    json.dump(report, open(os.path.join(RAW, "convert_report.json"), "w"), ensure_ascii=False, indent=1)
    print("skipped", len(report["skipped"]), "incomplete", len(report["incomplete"]))


if __name__ == "__main__":
    main()
