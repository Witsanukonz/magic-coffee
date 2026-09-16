"""Original local demo illustrations. No network or external assets required."""
import hashlib
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def make_placeholder(path, name, category='Coffee'):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return
    seed = int(hashlib.sha256(name.encode()).hexdigest()[:8], 16)
    backgrounds = ['#e9dfd0', '#e3d9ca', '#e5ddd0', '#e9e3d7', '#e0d6c6', '#e9dfd3']
    image = Image.new('RGB', (800, 880), backgrounds[seed % len(backgrounds)])
    draw = ImageDraw.Draw(image)
    # A restrained still-life composition, with a soft plate and individual food shapes.
    draw.polygon([(0, 0), (560, 0), (800, 300), (800, 880), (620, 880), (0, 240)], fill='#eee7dc')
    draw.ellipse((145, 607, 670, 737), fill='#d2c4b2')
    if category in ['Coffee', 'Non-Coffee', 'Tea']:
        cold = 'Iced' in name or name in ['Cold Brew', 'Dirty Coffee', 'Strawberry Milk', 'Thai Tea', 'Peach Tea', 'Lemon Tea', 'Matcha Lemon']
        liquid = '#694432'
        if 'Matcha' in name: liquid = '#89905a'
        elif 'Strawberry' in name: liquid = '#d5a0a0'
        elif 'Vanilla' in name: liquid = '#e9d7b7'
        elif 'Cocoa' in name or name == 'Mocha': liquid = '#80513c'
        elif name in ['Thai Tea', 'Peach Tea', 'Lemon Tea']: liquid = '#c58340'
        elif any(x in name for x in ['Latte', 'Cappuccino', 'Macchiato']): liquid = '#bd946c'
        if cold:
            draw.polygon([(245, 270), (558, 270), (526, 660), (280, 660)], fill='#f3efdf', outline='#c7bba8', width=4)
            draw.polygon([(255, 317), (549, 317), (520, 637), (287, 637)], fill=liquid)
            if name in ['Iced Latte', 'Dirty Coffee', 'Strawberry Milk']:
                draw.polygon([(270, 443), (538, 443), (520, 637), (287, 637)], fill='#ecdfc4')
            for x,y,r in [(294,341,-8),(401,375,6),(330,471,3),(430,515,-3)]:
                draw.rounded_rectangle((x,y,x+69,y+61), radius=10, fill='#e4d6b5', outline='#f4e9d7', width=3)
            draw.ellipse((245, 243, 558, 298), fill='#f0e5d4', outline='#c8bba4', width=3)
            draw.ellipse((257, 253, 547, 285), fill=liquid)
            draw.line((497,178,445,482), fill='#8f795e', width=10)
            draw.line((286,319,306,602), fill='#f5edda', width=5)
        else:
            draw.ellipse((135, 526, 649, 738), fill='#f4efe5', outline='#e2d8c8', width=4)
            draw.ellipse((193, 566, 591, 692), outline='#e0d4c1', width=4)
            draw.ellipse((482, 351, 642, 537), fill='#f7f2e7', outline='#e1d4c0', width=5)
            draw.ellipse((508, 377, 612, 509), fill=backgrounds[seed % len(backgrounds)])
            draw.rounded_rectangle((212, 308, 543, 613), radius=75, fill='#f7f2e7', outline='#e1d4c0', width=4)
            draw.ellipse((212, 269, 543, 399), fill='#fff9ed', outline='#e3d5bf', width=4)
            draw.ellipse((232, 288, 524, 377), fill=liquid)
            if name not in ['Espresso', 'Americano']:
                for i in range(7):
                    y=307+i*6
                    radius=63-i*7
                    draw.ellipse((378-radius,y,378+radius,y+17), fill='#f6e8cd')
                draw.line((378,305,385,362),fill=liquid,width=4)
            else:
                draw.arc((242,295,515,368),0,330,fill='#c59c68',width=5)
            draw.arc((280,180,320,267),90,260,fill='#f6f1e8',width=5)
            draw.arc((356,159,400,246),90,260,fill='#f6f1e8',width=5)
    else:
        draw.ellipse((109, 377, 695, 731), fill='#f6f1e7', outline='#e0d4c0', width=4)
        draw.ellipse((150, 409, 655, 698), outline='#e4d8c5', width=3)
        if 'Croissant' in name:
            for i in range(7):
                angle=(i-3)*.28
                x=400+math.sin(angle)*212
                y=490- math.cos(angle)*35
                w=53+(3-abs(i-3))*8
                draw.ellipse((x-w,y-70,x+w,y+85),fill=['#bb793b','#cc8b47','#da9c56'][i%3],outline='#ad7138',width=3)
                draw.arc((x-w+12,y-55,x+w-7,y+65),220,320,fill='#efd09a',width=7)
            if 'Chocolate' in name:
                for x in range(265,551,48):draw.line((x,402,x+40,539),fill='#603c2b',width=7)
        elif 'Muffin' in name:
            draw.polygon([(275,477),(541,477),(502,652),(314,652)],fill='#b7956c')
            for x in range(315,507,25):draw.line((x,499,x+6,644),fill='#d1b691',width=6)
            draw.ellipse((252,330,560,540),fill='#c38e4e')
            for x,y in [(308,394),(390,367),(468,404),(347,454),(445,469)]:draw.ellipse((x,y,x+28,y+25),fill='#555165')
        elif category=='Dessert' or 'Brownie' in name:
            base='#ead3a6' if name=='Basque Cheesecake' else '#704633'
            draw.polygon([(245,448),(460,351),(572,482),(367,593)],fill=base)
            draw.polygon([(245,448),(367,526),(367,642),(245,554)],fill='#d4b683' if name=='Basque Cheesecake' else '#553827')
            draw.polygon([(367,526),(572,425),(572,552),(367,642)],fill=base)
            draw.polygon([(245,448),(449,346),(572,425),(367,526)],fill='#945b37' if name=='Basque Cheesecake' else '#543527')
            if name in ['Tiramisu','Chocolate Cake']:
                for offset in [33,76]:draw.line((368,526+offset,568,429+offset),fill='#e4caa2' if name=='Tiramisu' else '#9b6949',width=20)
            if name=='Chocolate Brownie':
                for x,y in [(350,432),(406,388),(460,429),(398,477)]:draw.rectangle((x,y,x+18,y+14),fill='#c29564')
        else:
            draw.rounded_rectangle((231,381,501,616),radius=27,fill='#ae7339',outline='#8c5d30',width=5)
            draw.rounded_rectangle((244,394,488,600),radius=21,fill='#e7c287')
            if name=='Ham & Cheese Sandwich':
                draw.polygon([(248,403),(484,403),(484,590)],fill='#f0cc65')
                draw.polygon([(244,411),(478,410),(470,583)],fill='#cfa198')
                draw.polygon([(251,381),(489,388),(487,561)],fill='#d5ab6b',outline='#ae7339',width=5)
            else:
                draw.ellipse((256,409,473,582),fill='#fff6e0')
                draw.ellipse((324,454,405,531),fill='#dea449')
                draw.ellipse((337,461,390,499),fill='#eebe61')
                if name=='Breakfast Set':
                    draw.rounded_rectangle((523,437,570,599),radius=22,fill='#a75f37')
                    draw.rounded_rectangle((578,429,615,584),radius=20,fill='#b57648')
    try:
        regular=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
        title=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',24)
    except OSError:
        regular=ImageFont.load_default(size=18)
        title=ImageFont.load_default(size=24)
    draw.text((45,45),'MAGIC COFFEE / EVERYDAY COLLECTION',fill='#756452',font=regular)
    draw.text((45,775),name.upper(),fill='#5c4033',font=title)
    draw.text((45,816),'DEMO MENU ILLUSTRATION',fill='#887663',font=regular)
    image.save(path,quality=88,optimize=True)
