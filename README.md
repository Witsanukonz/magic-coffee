# MAGIC COFFEE

**BREWED FOR EVERY MOMENT.**

เว็บร้านกาแฟสำหรับโปรเจกต์รายวิชา ใช้ Django Templates พร้อมระบบสั่งซื้อจำลองและ Custom Admin Dashboard ที่ `/dashboard/` ไม่มีการชำระเงินจริง

## เปิดเดโมอย่างเร็วบน Windows

ติดตั้ง Python 3.12 ขึ้นไป แล้วดับเบิลคลิก **START_MAGIC_COFFEE.bat** หรือรัน:

```powershell
powershell -ExecutionPolicy Bypass -File .\run.ps1
```

เปิด **http://127.0.0.1:8000/**

สคริปต์สร้าง `.venv` และติดตั้ง dependencies เมื่อยังไม่มี จากนั้น migrate, seed แบบไม่ทับข้อมูลเดิม และเปิด development server ใช้ Python ใน `.venv` โดยตรง **ไม่ได้ activate terminal ของผู้ใช้** กด Ctrl+C เพื่อหยุด ถ้าพอร์ต 8000 ถูกใช้ ให้เพิ่ม `-Port 8001`

## Clone แล้วเปิดใช้งาน

หลัง clone โปรเจกต์จาก GitHub ให้เปิด PowerShell ในโฟลเดอร์โปรเจกต์ แล้วใช้เพียงคำสั่งนี้:

```powershell
powershell -ExecutionPolicy Bypass -File .\run.ps1
```

หรือดับเบิลคลิก `START_MAGIC_COFFEE.bat` ได้เลย สคริปต์จะสร้าง virtual environment, ติดตั้ง dependencies, อัปเดตฐานข้อมูล และสร้างข้อมูลเดโมให้อัตโนมัติ โดยไม่ทับข้อมูลที่มีอยู่ จากนั้นเปิด [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

| บัญชีเดโม | Username | Password |
|---|---|---|
| Admin | `demo_admin` | `MagicDemo!2026` |
| Customer | `demo_customer` | `MagicDemo!2026` |

บัญชีเหล่านี้ใช้สำหรับเดโมในเครื่องเท่านั้น ตั้งรหัสอื่นก่อนสร้างข้อมูลครั้งแรกได้ด้วย environment variables `MAGIC_ADMIN_PASSWORD` และ `MAGIC_CUSTOMER_PASSWORD` การ seed ซ้ำจะไม่เปลี่ยนรหัสผ่านหรือข้อมูลที่แก้ไปแล้ว

## Features

- หน้าร้าน Modern / Minimal โทน Espresso Black, Coffee Brown, Cream ใช้ Manrope + Inter
- เมนูเดโม 28 รายการใน 6 หมวด ภาพอยู่ใน `media/menu/` และมี fallback สร้างแยกตามชื่อเมนู
- Search จากชื่อ คำอธิบาย หมวดหมู่, filter หมวด/ความพร้อม/ช่วงราคา, sort และ pagination
- Register, login, POST logout, profile และ reset password ผ่าน Django Authentication
- Role `admin` / `customer` ตรวจ permission ใน backend ทุกหน้า Dashboard
- ตะกร้าของ guest เก็บตาม session และรวมกับตะกร้าสมาชิกเมื่อ login/register
- ตัวเลือก Small/Medium/Large, Hot/Iced, ความหวาน 0/25/50/75/100 และจำนวน
- Checkout ต้อง login เลือก Dine In / Take Away พร้อมเบอร์โทรและหมายเหตุ
- บันทึกชื่อเมนู ราคา และตัวเลือกเป็น snapshot ไม่เปลี่ยนตามเมนูภายหลัง
- ตัดสต็อกใน transaction ด้วย conditional update ตรวจยอดรวมทุกตัวเลือกของเมนูเดียวกัน
- ป้องกันส่ง checkout ซ้ำด้วย token และ unique constraint
- My Orders แสดงเฉพาะเจ้าของออร์เดอร์
- MAGIC REWARDS: สะสมผ่านเบอร์โทร เมื่อออเดอร์เป็น Completed ครบ 10 ครั้ง รับสิทธิ์กาแฟฟรี 1 แก้ว
- ปุ่มเพิ่ม/ลดจำนวนในตะกร้าบันทึกและคำนวณยอดทันทีโดยไม่รีเฟรชหน้า
- Custom Dashboard: Overview, Low Stock, Menu CRUD, Category CRUD, User CRUD, Order Management
- Dashboard อัปเดต Live Orders และ Stock Alerts ใน sidebar อัตโนมัติ พร้อมป้ายแจ้งออเดอร์ใหม่ที่เมนู Live Orders
- Add Menu มี TextField, RadioButton, TextArea, CheckBox, DropdownList, DatePicker, FileBrowse และ image preview
- Delete ผ่าน confirmation modal และ POST + CSRF เท่านั้น
- ยกเลิกออร์เดอร์คืนสต็อกครั้งเดียว ออร์เดอร์จบแล้วไม่ย้อนสถานะ
- ป้องกัน Admin ลบ ปิดใช้งาน หรือลดสิทธิ์บัญชีตัวเอง
- สร้าง/เปลี่ยนรหัสผ่านด้วย Django validators + hashing ไม่แสดงรหัสผ่านเดิม
- รองรับ Desktop / Tablet / Mobile รวม sidebar แบบเปิดปิดได้และตารางเลื่อนภายในพื้นที่ตาราง
- CSS, fonts และรูปทั้งหมดใช้ไฟล์ในเครื่อง เปิดเดโมหลังติดตั้งแล้วได้โดยไม่ใช้อินเทอร์เน็ต

## Technology

- Python, Django 6.0, SQLite
- Django Templates, HTML5, Tailwind CSS 4, Vanilla JavaScript
- Pillow ตรวจไฟล์ภาพและสร้างภาพประกอบ fallback
- ไม่มี React, Next.js, Vue, Vite หรือ Bootstrap
- Node.js ใช้เฉพาะตอน build Tailwind หรือทดสอบ browser ไม่ต้องใช้ตอนเปิด Django เพราะมี compiled CSS ให้แล้ว

## โครงสร้าง

```text
config/                  settings, URL routing, WSGI
apps/
  accounts/              custom User, authentication, profile, user forms
  menu/                  Category, MenuItem, filters, image handling, seed_demo
  cart/                  session/member cart, options, quantity validation
  orders/                checkout, stock transaction, snapshots, status transitions
  dashboard/             permission checks, custom CRUD, backend tests
templates/               Django templates + shared partials
static/css/              input.css, compiled tailwind.css, site.css
static/js/               menu toggles, quantity, image preview, delete modal
static/fonts/            local Manrope / Inter + licenses
static/images/           bundled cafe photography
media/                   generated demo images and uploaded files
scripts/                 asset preparation, isolated browser workflow test
manage.py
requirements.txt
run.ps1 / START_MAGIC_COFFEE.bat
```

## ติดตั้งเอง

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

ถ้า activate ไม่ได้ ให้ใช้ `.\.venv\Scripts\python.exe` แทน `python` ได้เลย ไม่ต้องเปลี่ยน execution policy ของระบบ

Migration ถูกสร้างและรวมไว้แล้ว ไม่ต้อง `makemigrations` ทุกครั้ง ใช้คำสั่งนี้เฉพาะเมื่อแก้ models:

```powershell
python manage.py makemigrations
python manage.py migrate
```

`seed_demo` สร้างเฉพาะรายการที่ยังไม่มี รันซ้ำไม่เพิ่มข้อมูลซ้ำและไม่รีเซ็ต stock/price/บัญชี ถ้าเพิ่มเมนูโดยไม่อัปโหลดรูป ระบบสร้างภาพประกอบตามชื่อเมนูให้เอง หมวดที่มีเมนูอยู่จะลบไม่ได้จนกว่าจะย้ายหรือลบเมนูภายใน

## สร้าง Admin

ใช้ `demo_admin` เข้าหน้า `/dashboard/users/add/` แล้วเลือก Role = Admin หรือใช้:

```powershell
python manage.py createsuperuser
```

Superuser เข้า `/dashboard/` ได้เช่นกัน `/admin/` มีไว้สำหรับตรวจระบบเท่านั้น Admin ปกติไม่จำเป็นต้องมี `is_staff` และไม่ต้องเข้า Django Admin ในการสาธิต

## Reset Password

เปิด `/accounts/password-reset/` แล้วกรอกอีเมลบัญชีที่ active เช่น `demo_customer@example.com` ระบบใช้ **console email backend** ลิงก์จะพิมพ์ในหน้าต่าง terminal ที่รัน Django ไม่ได้ส่งอีเมลออกจริง เปิดลิงก์ดังกล่าวเพื่อตั้งรหัสผ่านใหม่ เมื่อใช้งานแล้วลิงก์เดิมจะใช้ซ้ำไม่ได้

## Flow สำหรับนำเสนอ

1. เปิด Home และ Menu สาธิต search, filter และเปลี่ยนหน้า
2. สมัครสมาชิกใหม่ หรือ login ด้วย `demo_customer`
3. เปิด Cafe Latte เลือก **Large / Iced / 50%** แล้ว Add to Cart
4. แก้จำนวน ทดลอง Remove แล้วเพิ่มกลับ
5. Checkout กรอกชื่อ เบอร์โทร เลือก Dine In / Take Away และหมายเหตุ
6. Place Order เห็น `MC00001` เมื่อเป็นออร์เดอร์แรก สถานะ Pending และราคา ฿85 ต่อแก้ว
7. เปิด My Orders และ Order Detail
8. Logout แล้ว login `demo_admin` ระบบพาไป Custom Dashboard
9. เปิดออร์เดอร์ใหม่และเปลี่ยน **Pending → Preparing → Ready**
10. กลับบัญชีลูกค้าแล้ว refresh Order Detail จะเห็น Ready
11. Admin เพิ่มเมนูใหม่ เลือก Radio/Checkbox/Date และอัปโหลดรูป ดู preview ก่อนบันทึก
12. แก้ราคาและ Stock แล้วเปิดเมนูนั้นที่หน้าร้านให้เห็นข้อมูลใหม่
13. สาธิต User และ Category Create / Read / Update / Delete
14. แสดง confirmation modal ก่อนลบ และลองกด Keep item
15. ใช้ Customer เปิด `/dashboard/` เพื่อสาธิตการปฏิเสธสิทธิ์

ขนาดเครื่องดื่มไม่มีค่าบวกเพิ่มในเดโมนี้ ราคาที่แสดงใช้กับทุกขนาด หน้าเมนูบอกเงื่อนไขนี้ไว้แล้ว สต็อกจองจริงตอน Place Order ไม่ใช่ตอน Add to Cart ถ้าเมนูถูกปิดหรือเปลี่ยนตัวเลือกระหว่างนั้น ระบบขอให้ปรับตะกร้าก่อน

## ทดสอบ

Backend:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Browser workflow + responsive screenshots:

```powershell
npm ci
npx playwright install chromium
npm run test:browser
```

สคริปต์เลือก Microsoft Edge ใน Windows ถ้ามี ไม่เช่นนั้นใช้ Playwright Chromium สร้างฐานข้อมูลและ media สำหรับทดสอบแยกใน `test-results/` ใช้พอร์ต 8011 ปิด test server หลังจบ ไม่แก้ `db.sqlite3` ของเดโม ผลอยู่ใน `test-results/browser-results.json` และภาพหน้าจอ `.png`

แก้ template utility classes แล้ว build Tailwind ใหม่:

```powershell
npm ci
npm run build:css
```

## รูปภาพและ licenses

ภาพถ่ายจาก Unsplash เก็บใน repository แล้ว รายละเอียดไฟล์และแหล่งที่มาอยู่ใน [ASSETS.md](ASSETS.md) ภาพเมนูที่เหลือเป็น **original demo illustrations** แยกตามเมนู ไม่ใช่ภาพถ่ายสินค้า ไม่มีโลโก้ภายนอกหรือ watermark

## ขอบเขตการใช้

โปรเจกต์นี้ตั้งค่าเป็น local development demo (`DEBUG=True`, SQLite, console email, secret key สำหรับเครื่องผู้พัฒนา) ไม่ใช่ระบบรับเงินจริง หากนำขึ้นบริการสาธารณะต้องตั้ง `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0`, `DJANGO_ALLOWED_HOSTS`, HTTPS, การเสิร์ฟ static/media, อีเมลจริง และฐานข้อมูลที่เหมาะกับการใช้งานหลายคน พร้อมเปลี่ยนรหัสบัญชีเดโมก่อน
