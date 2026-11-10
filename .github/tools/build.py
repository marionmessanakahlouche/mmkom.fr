"""Validate and stage only public files for GitHub Pages. No third-party dependencies."""
import argparse
import json
import shutil
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ('index.html', 'mentions-legales.html', '404.html', 'style.css',
          'script.js', 'logo.svg', 'favicon.svg', 'robots.txt',
          'sitemap.xml', 'site.webmanifest', 'CNAME')
parser = argparse.ArgumentParser()
parser.add_argument('--production', action='store_true', help='Refuse uncompleted legal information.')
parser.add_argument('--check', action='store_true', help='Validate without producing _site/.')
args = parser.parse_args()
errors = []


class PageCheck(HTMLParser):
    def __init__(self, filename):
        super().__init__(convert_charrefs=True)
        self.filename, self.ids, self.references, self.fragments = filename, set(), [], []
        self.jsonld = False
        self.jsonparts = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            if attrs['id'] in self.ids:
                errors.append(f'{self.filename}: duplicate id {attrs["id"]}')
            self.ids.add(attrs['id'])
        if tag == 'img' and 'alt' not in attrs:
            errors.append(f'{self.filename}: image missing alt')
        for key in ('href', 'src'):
            if key in attrs:
                self.references.append(attrs[key])
        for candidate in attrs.get('srcset', '').split(','):
            if candidate.strip():
                self.references.append(candidate.strip().split()[0])
        if tag == 'script' and attrs.get('type') == 'application/ld+json':
            self.jsonld = True
            self.jsonparts = []

    def handle_data(self, data):
        if self.jsonld:
            self.jsonparts.append(data)

    def handle_endtag(self, tag):
        if tag == 'script' and self.jsonld:
            try:
                json.loads(''.join(self.jsonparts))
            except ValueError as error:
                errors.append(f'Invalid JSON-LD: {error}')
            self.jsonld = False


for filename in PUBLIC:
    if not (ROOT / filename).is_file():
        errors.append(f'Missing public file: {filename}')
for filename in ('index.html', 'mentions-legales.html', '404.html'):
    page = PageCheck(filename)
    page.feed((ROOT / filename).read_text())
    for reference in page.references:
        url = urlsplit(reference)
        if url.scheme or url.netloc:
            continue
        if not url.path:
            if url.fragment and url.fragment not in page.ids:
                errors.append(f'{filename}: unknown anchor {reference}')
        elif not (ROOT / url.path).exists():
            errors.append(f'{filename}: missing asset {url.path}')

manifest = json.loads((ROOT / 'site.webmanifest').read_text())
for icon in manifest['icons']:
    if not (ROOT / icon['src']).is_file():
        errors.append(f'Missing manifest icon: {icon["src"]}')
for filename in ('logo.svg', 'favicon.svg', 'sitemap.xml'):
    ET.parse(ROOT / filename)
for filename in ('inter-latin.woff2', 'caveat-latin.woff2'):
    if not (ROOT / 'assets/fonts' / filename).is_file():
        errors.append(f'Missing local font: {filename}')
if 'À RENSEIGNER' in (ROOT / 'mentions-legales.html').read_text():
    message = 'Complete the À RENSEIGNER fields in mentions-legales.html before publication.'
    if args.production:
        errors.append(message)
    else:
        print('WARNING:', message)
if errors:
    print('\n'.join(errors), file=sys.stderr)
    sys.exit(1)
if not args.check:
    target = ROOT / '_site'
    # Remove only this script’s generated output, never sources or artwork.
    if target.is_symlink():
        raise RuntimeError('_site must not be a symlink')
    if target.exists():
        shutil.rmtree(target)
    target.mkdir()
    for filename in PUBLIC:
        shutil.copy2(ROOT / filename, target / filename)
    shutil.copytree(ROOT / 'assets', target / 'assets')
    print('Public files staged in _site/. Sources, print files and originals are excluded.')
print('Static checks passed.')
