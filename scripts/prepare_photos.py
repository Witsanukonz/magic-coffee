"""One-time developer asset preparation; seeded demo runs completely offline."""
import urllib.request
from pathlib import Path
from io import BytesIO
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
PHOTOS = {
    'hero.jpg': 'photo-1514432324607-a09d9b4aefdd',
    'cafe.jpg': 'photo-1501339847302-ac426a4a7cbb',
    'menu/cafe-latte.jpg': 'photo-1541167760496-1628856ab772',
    'menu/iced-latte.jpg': 'photo-1517701604599-bb29b565090c',
    'menu/butter-croissant.jpg': 'photo-1555507036-ab1f4038808a',
}
for name, photo in PHOTOS.items():
    dest=ROOT/'static/images'/name
    if dest.exists():
        continue
    url=f'https://images.unsplash.com/{photo}?auto=format&fit=crop&w=1400&q=85'
    try:
        data=urllib.request.urlopen(url,timeout=30).read()
        image=Image.open(BytesIO(data)).convert('RGB')
        image.thumbnail((1400,1400))
        dest.parent.mkdir(parents=True,exist_ok=True)
        image.save(dest,quality=85,optimize=True)
        print(f'{name}: {image.size}')
    except Exception as exc:
        print(f'{name}: download failed: {exc}')
