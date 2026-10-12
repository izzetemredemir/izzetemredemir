"""Refresh the Writing list in README.md from the blog's RSS feed.

Stdlib only. On any failure (network, bad XML, empty feed, missing markers)
it exits non-zero without touching README.md, so a broken feed can never
wipe the list.
"""

import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from pathlib import Path

FEED = os.environ.get('FEED_URL', 'https://izzetemredemir.com/rss.xml')
README = Path(__file__).resolve().parents[2] / 'README.md'
LIMIT = 5
START, END = '<!-- WRITING:START -->', '<!-- WRITING:END -->'

# Cloudflare answers the default "Python-urllib" user agent with a 403.
UA = 'izzetemredemir-profile-readme (+https://github.com/izzetemredemir/izzetemredemir)'


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=30) as res:
        return res.read()


def entries(xml):
    items = []
    for item in ET.fromstring(xml).iter('item'):
        title = (item.findtext('title') or '').strip()
        link = (item.findtext('link') or '').strip()
        date = parsedate_to_datetime(item.findtext('pubDate'))
        if title and link:
            items.append((date, title, link))
    items.sort(key=lambda i: i[0], reverse=True)
    return items[:LIMIT]


def line(date, title, link):
    title = re.sub(r'([\\\[\]])', r'\\\1', title)
    # UTC, same "2026 Aug 07" format as formatPostDate on the site.
    return f'- [{title}]({link}) <sub>{date.strftime("%Y %b %d")}</sub>'


def main():
    items = entries(fetch(FEED))
    if not items:
        sys.exit(f'No items in {FEED}, leaving README.md alone.')

    text = README.read_text()
    if text.count(START) != 1 or text.count(END) != 1:
        sys.exit('WRITING markers missing or duplicated in README.md.')

    head, rest = text.split(START)
    _, tail = rest.split(END)
    body = '\n'.join(line(*i) for i in items)
    new = f'{head}{START}\n{body}\n{END}{tail}'

    if new != text:
        README.write_text(new)
        print(f'Updated with {len(items)} post(s).')
    else:
        print('No change.')


if __name__ == '__main__':
    main()
