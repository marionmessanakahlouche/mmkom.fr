"""Generate responsive photos, local fonts, favicons and social sharing image.

Install .github/tools/requirements.txt in a virtual environment before running.
Runtime website files have no Python dependency. Existing originals stay intact.
"""
from io import BytesIO
from pathlib import Path
from urllib.request import urlopen

import cairosvg
from PIL import Image, ImageDraw, ImageFont, ImageOps
from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / 'assets'
CACHE = Path(__file__).resolve().parent / '.cache'
for directory in ('images', 'fonts', 'icons'):
    (ASSETS / directory).mkdir(parents=True, exist_ok=True)
CACHE.mkdir(exist_ok=True)


def download(url, target):
    if not target.exists():
        with urlopen(url, timeout=45) as response:
            target.write_bytes(response.read())


base = 'https://raw.githubusercontent.com/google/fonts/main/ofl/'
for family, filename in [('inter', 'Inter%5Bopsz,wght%5D.ttf'), ('caveat', 'Caveat%5Bwght%5D.ttf')]:
    source = CACHE / f'{family}.ttf'
    download(base + family + '/' + filename, source)
    download(base + family + '/OFL.txt', ASSETS / 'fonts' / f'{family}-OFL.txt')
    font = TTFont(source)
    options = subset.Options()
    options.layout_features = ['*']
    subsetter = subset.Subsetter(options=options)
    subsetter.populate(unicodes=list(range(0x250)) + list(range(0x1e00, 0x1f00)) + list(range(0x2000, 0x2070)))
    subsetter.subset(font)
    font.flavor = 'woff2'
    font.save(ASSETS / 'fonts' / f'{family}-latin.woff2')

photo = ImageOps.exif_transpose(Image.open(ROOT / 'photo.jpeg')).convert('RGB')
for width in (400, 800, 1200):
    image = ImageOps.fit(photo, (width, width), method=Image.Resampling.LANCZOS)
    # No EXIF/GPS metadata is copied into public images.
    image.save(ASSETS / 'images' / f'marion-{width}.webp', quality=82, method=6)
    image.save(ASSETS / 'images' / f'marion-{width}.jpg', quality=84, optimize=True, progressive=True)

for size, filename in [(32, 'favicon-32.png'), (180, 'apple-touch-icon.png'), (192, 'icon-192.png'), (512, 'icon-512.png')]:
    cairosvg.svg2png(url=str(ROOT / 'favicon.svg'), write_to=str(ASSETS / 'icons' / filename), output_width=size, output_height=size)

company_logo = Image.new('RGB', (512, 512), '#FDFBEC')
logo = Image.open(BytesIO(cairosvg.svg2png(url=str(ROOT / 'logo.svg'), output_width=432))).convert('RGBA')
company_logo.paste(logo, ((512 - logo.width) // 2, (512 - logo.height) // 2), logo)
company_logo.save(ASSETS / 'icons' / 'company-logo.png', optimize=True)

front = Image.open(ROOT / 'print' / 'mmkom-recto-rose.png').convert('RGB')
card = Image.new('RGB', (1200, 630), front.getpixel((0, 0)))
front = ImageOps.contain(front, card.size, method=Image.Resampling.LANCZOS)
card.paste(front, ((card.width - front.width) // 2, (card.height - front.height) // 2))
card.save(ASSETS / 'images' / 'og-mmkom.jpg', quality=90, optimize=True)
print('Photos, polices locales, icônes et aperçu social générés dans assets/.')
