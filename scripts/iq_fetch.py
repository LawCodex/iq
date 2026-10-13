#!/usr/bin/env python3
"""Fetch Iraqi Legal Database (iraqld.hjc.iq) law pages from the Internet Archive.

iraqld.hjc.iq (Higher Judicial Council, قاعدة التشريعات العراقية) is behind a Cloudflare block
for automated clients, so this script uses the Wayback Machine copies of its official
"LoadLawBook.aspx" pages (full text of one legislation, paginated).

Usage: iq_fetch.py [RAW_DIR]
  1. lists archived captures with the Wayback CDX API (cached in RAW_DIR/cdx.txt);
  2. for every law (SC identifier) downloads the newest capture of each archived page
     into RAW_DIR/html/<SC>_p<page>.html (unmodified "id_" capture).
"""
import collections
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import requests

UA = "LawCodex/1.0 (+https://github.com/LawCodex)"
HERE = os.path.dirname(os.path.abspath(__file__))
CDX = ("https://web.archive.org/cdx/search/cdx?url=iraqld.hjc.iq&matchType=host"
       "&filter=statuscode:200&fl=original,timestamp&limit=200000")

S = requests.Session()
S.headers["User-Agent"] = UA


def get(url, tries=6):
    for a in range(tries):
        try:
            r = S.get(url, timeout=120)
            if r.status_code == 200:
                return r
            if r.status_code == 404:
                return None
            time.sleep(10 * (a + 1))
        except requests.RequestException:
            time.sleep(10 * (a + 1))
    return None


def captures(raw):
    fn = os.path.join(raw, "cdx.txt")
    if not os.path.exists(fn):
        r = get(CDX)
        open(fn, "w").write(r.text)
    caps = collections.defaultdict(dict)  # SC -> page -> (timestamp, url)
    for line in open(fn):
        parts = line.split()
        if len(parts) != 2 or "LoadLawBook.aspx" not in parts[0]:
            continue
        url, ts = parts
        m = re.search(r"[?&]SC=(\d+)", url)
        if not m:
            continue
        p = re.search(r"[?&]page=(\d+)", url)
        page = int(p.group(1)) if p else 1
        prev = caps[m.group(1)].get(page)
        if prev is None or ts > prev[0]:
            caps[m.group(1)][page] = (ts, url)
    return caps


def main():
    raw = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "..", "_raw", "iq")
    out = os.path.join(raw, "html")
    os.makedirs(out, exist_ok=True)
    caps = captures(raw)
    print(len(caps), "laws with captures", flush=True)
    jobs = []
    for sc, pages in sorted(caps.items()):
        for page, (ts, url) in sorted(pages.items()):
            fn = os.path.join(out, f"{sc}_p{page}.html")
            if not os.path.exists(fn):
                jobs.append((fn, ts, url))
    print(len(jobs), "pages to fetch", flush=True)
    n = [0]

    def job(j):
        fn, ts, url = j
        r = get(f"https://web.archive.org/web/{ts}id_/{url}")
        time.sleep(1.0)
        if r is None:
            print("MISS", fn, ts, flush=True)
            return
        open(fn + ".tmp", "wb").write(r.content)
        os.replace(fn + ".tmp", fn)
        n[0] += 1
        if n[0] % 100 == 0:
            print("fetched", n[0], flush=True)

    with ThreadPoolExecutor(3) as ex:
        list(ex.map(job, jobs))
    print("done", n[0], flush=True)


if __name__ == "__main__":
    main()
