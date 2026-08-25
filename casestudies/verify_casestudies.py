#!/usr/bin/env python3
"""Guard against silently orphaned case studies.

WHY THIS EXISTS
---------------
On 2026-08-03 a routine Cowork render batch (commit b91406e) regenerated
casestudies/index.html, sitemap.xml and llms.txt from Airtable Published rows.
Nine case studies that had been added to the repo by hand on 2026-07-29
(commit 9602e59) were never in Airtable, so they vanished from all three
discovery files in one commit. The pages stayed live and returned 200, so
nothing failed and nothing alerted. They were orphaned for 22 days.

Every prior audit compared sitemap URLs against Search Console. Both agreed,
because both derived from the same shrunken list. Nothing compared what is on
DISK against what is in the SITEMAP. That set-difference is the whole bug.

Run this after any case-study render, before committing.
Exit 0 = clean, exit 1 = at least one check failed.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKIP_DIRS = {'assets'}


def read(path):
    with open(path, encoding='utf-8') as fh:
        return fh.read()


def main():
    failures = []

    slugs = sorted(
        d for d in os.listdir(HERE)
        if os.path.isdir(os.path.join(HERE, d))
        and d not in SKIP_DIRS
        and os.path.exists(os.path.join(HERE, d, 'index.html'))
    )
    sitemap = read(os.path.join(HERE, 'sitemap.xml'))
    index = read(os.path.join(HERE, 'index.html'))
    llms = read(os.path.join(HERE, 'llms.txt'))

    print(f'case-study pages on disk: {len(slugs)}')
    print(f'urls in sitemap.xml:      {sitemap.count("<loc>")}')
    print('-' * 68)

    # 1. every page on disk must be discoverable
    for slug in slugs:
        missing = [
            name for name, blob in
            (('sitemap.xml', sitemap), ('index.html', index), ('llms.txt', llms))
            if slug not in blob
        ]
        if missing:
            failures.append(f'{slug}: absent from {", ".join(missing)}')

    # 2. every page must reference an og:image that exists on disk
    for slug in slugs:
        page = read(os.path.join(HERE, slug, 'index.html'))
        m = re.search(r'<meta property="og:image" content="([^"]+)"', page)
        if not m:
            failures.append(f'{slug}: no og:image meta tag')
            continue
        fname = m.group(1).rsplit('/', 1)[-1]
        if not os.path.exists(os.path.join(HERE, 'assets', fname)):
            failures.append(f'{slug}: og:image references missing file assets/{fname}')

    # 3. no sitemap entry may point at a page that does not exist
    for loc in re.findall(r'<loc>https://reachsocial\.co/casestudies/([^/<]+)/</loc>', sitemap):
        if loc and loc not in slugs:
            failures.append(f'sitemap lists /{loc}/ but no such directory exists')

    if failures:
        print('FAIL\n')
        for f in failures:
            print('  -', f)
        print(f'\n{len(failures)} problem(s). Do not commit this render.')
        return 1

    print('PASS - every case study on disk is in sitemap.xml, index.html and')
    print('       llms.txt, and every og:image resolves to a real file.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
