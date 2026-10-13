# Iraq — LawCodex (التشريعات العراقية)

Iraqi legislation as Markdown, in Arabic. The texts come from the **Iraqi Legislation
Database** (قاعدة التشريعات العراقية) of the Higher Judicial Council (مجلس القضاء الأعلى),
`iraqld.hjc.iq`. Part of [LawCodex](https://github.com/LawCodex): one repository per jurisdiction.

- Retrieved: **2026-10-13**, from **Internet Archive captures** of the database pages, mostly
  taken in 2021–2022.
- Version: as shown by the database at capture time. The database merges amendments into the
  text and adds editorial footnotes (الهوامش), and those footnotes are kept. Anything enacted
  or amended after the capture date is **not** included.

## Why Internet Archive copies

`iraqld.hjc.iq` and `hjc.iq` sit behind a Cloudflare block that answers automated clients with
"Sorry, you have been blocked". LawCodex does not work around bot protection, so the official
pages were read from the Wayback Machine instead. Each file lists the exact captures used in
`archived:`. The other starting points did not work either:

- `iraq-lg-law.org` (the Iraq Local Governance Law Library) now points to an unrelated site.
- The Ministry of Justice site (`moj.gov.iq`) offers the Official Gazette (الوقائع العراقية) as
  scanned PDF issues. These were not processed.
- `parliament.iq` sits behind a Cloudflare JavaScript challenge.

## Coverage

| Directory | Contents (نوع التشريع) | Files | `in_force` | incomplete |
| --- | --- | ---: | ---: | ---: |
| `ar/constitution/` | دستور — the 2005 Constitution (in force) and 6 historical constitutions (1925 Organic Law, 1958, 1964, 1967, 1968, 1970) | 7 | 1 | 0 |
| `ar/laws/<year>/` | قانون — laws | 1,940 | 1,049 | 22 |
| `ar/decisions/<year>/` | قرار مجلس قيادة الثورة (350), قرار (43), decisions of the Federal Supreme Court, Council of Ministers, Governing Council | 403 | 283 | 0 |
| `ar/regulations/<year>/` | نظام, نظام داخلي — regulations | 306 | 123 | 8 |
| `ar/instructions/<year>/` | تعليمات — instructions | 107 | 79 | 1 |
| `ar/orders/<year>/` | امر سلطة الائتلاف (Coalition Provisional Authority orders, 85), امر | 97 | 55 | 0 |
| `ar/statements/<year>/` | بيان — statements | 81 | 80 | 0 |
| `ar/decrees/<year>/` | مرسوم — decrees | 15 | 7 | 0 |
| `ar/other/<year>/` | اعلان, ارادة ملكية | 4 | 4 | 0 |
| **Total** | | **2,960** | **1,681** | **31** |

The texts date from 1917 to 2022. 2,926 are federal (`issuer: العراق - اتحادي`) and 34 come
from the Kurdistan Region (`اقليم كوردستان`).

**This is a partial set.** The Internet Archive holds captures of 2,968 distinct legislation
pages. The live database holds many more. Pre-2003 legislation is better covered than
recent legislation.

### Status

`status` follows the database's «سريان التشريع» field at capture time: `ساري` → `in_force`,
`غير ساري` → `repealed`. The Arabic value is kept in `status_ar`. Anything repealed after the
capture date can still show `in_force`.

### Incomplete texts

The database shows long texts across several pages, ten articles to a page. A law is complete
only if every one of its pages was archived. 31 laws are missing one or more pages. They are
marked `complete: false`, their front matter lists `missing_pages`, and a note at the top of
the text and a marker at each gap say so. Consecutive pages repeat the article on the page
boundary, and those repeats are removed. 7 captures were skipped: 4 had no metadata and 3 had
no first page.

## Structure

```
ar/constitution/<year>-<SC>.md
ar/<category>/<year>/<year>-<number>-<SC>.md      e.g. ar/laws/1959/1959-188-151220056661242.md  قانون الاحوال الشخصية
```

`<SC>` is the database's own identifier for the legislation (the `SC=` parameter of
`LoadLawBook.aspx`). `<year>` comes from the legislation date (تاريخ التشريع).

The front matter has `title`, `identifier` (`iraqld:<SC>`), `number`, `type`, `type_ar`,
`classification` (التصنيف), `issuer` (الجهة المصدرة), `date`, `status`, `status_ar`, `gazette`
(issue, date and page in al-Waqa'i' al-'Iraqiya), `note`, `complete`, `missing_pages`, `pages`,
`source` (original URL), `archived` (the captures used) and `retrieved`.

In the text, the database's section headings (الباب / الفصل …) are `###` and article labels
(المادة N, استناد, الاسباب الموجبة, الهوامش) are `#####`. Links to related court decisions
(«الاحكام المرتبطة بالماده») are removed. Cross-reference links are reduced to their text.
Nothing is translated or summarised.

## Licence / copyright

These are official legislative texts of the Republic of Iraq, published by the Higher Judicial
Council for public information. Official legislative texts are generally not subject to
copyright, and they are reproduced unchanged.

## Regenerate

```sh
python3 scripts/iq_fetch.py   ../_raw/iq     # Wayback CDX listing + captures (3 workers)
python3 scripts/iq_convert.py ../_raw/iq .
```
