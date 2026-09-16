# Local assets

## Photography

The following downloaded photographs are used under the [Unsplash License](https://unsplash.com/license), which permits downloading and using images in projects. Files are bundled locally; the app does not hotlink images at runtime. The photographs are illustrative stock cafe scenes, not a claim that MAGIC COFFEE is the photographed venue.

| File | Original image |
|---|---|
| `static/images/hero.jpg` | [Coffee in a ceramic cup](https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd) |
| `static/images/cafe.jpg` | [Cafe interior](https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb) |
| `static/images/menu/cafe-latte.jpg` | [Pouring milk into a latte](https://images.unsplash.com/photo-1541167760496-1628856ab772) |
| `static/images/menu/iced-latte.jpg` | [Iced coffee with milk](https://images.unsplash.com/photo-1517701604599-bb29b565090c) |
| `static/images/menu/butter-croissant.jpg` | [Butter croissants](https://images.unsplash.com/photo-1555507036-ab1f4038808a) |

`scripts/prepare_photos.py` records the download URLs and local processing. Photos were visually inspected before assignment; the iced coffee photograph contains milk and is assigned to Iced Latte.

## Demo illustrations

Other menu images are original procedural illustrations created by `apps/menu/placeholders.py`. Every menu receives its own named file and content, including tea, cocoa, matcha, pastry, cake and breakfast variants. They are explicitly labelled demo illustrations and can be replaced through the Dashboard. Seed data creates these locally without network access.

## Fonts

Manrope and Inter are bundled from their Fontsource packages. Their SIL Open Font License files are in `static/fonts/Manrope-LICENSE.txt` and `static/fonts/Inter-LICENSE.txt`. No external font request is made by the website.

## Brand mark

The small cup outline and favicon are original SVG assets for this demo project.
