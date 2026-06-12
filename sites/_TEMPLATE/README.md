# _TEMPLATE — ต้นแบบเว็บไซต์ (1 โฟลเดอร์ = 1 เว็บ)

อย่าแก้โฟลเดอร์นี้โดยตรง — ใช้เป็นต้นแบบสำหรับสร้างเว็บใหม่

## สร้างเว็บใหม่จากต้นแบบนี้
```bash
python shared/new_site.py <slug> "<ชื่อเว็บ>"
```
จะได้ `sites/<slug>/` (index.html + site.json + content.json) + ลงทะเบียนใน `sites.json` ให้อัตโนมัติ

## ไฟล์ในเว็บหนึ่งตัว
- `index.html` — static, vanilla JS, ไม่ต้อง build; อ่าน `site.json` + `content.json` และเชื่อม Supabase ได้
- `site.json` — config: title, accent, `supabase{ url, anonKey, table }`
- `content.json` — เนื้อหา fallback (ใช้เมื่อไม่ต่อ Supabase หรือ Supabase ล่ม)

## ต่อ Supabase (ตัวเลือก)
ใส่ `supabase.anonKey` + `supabase.table` ใน `site.json` → เว็บจะอ่านสดจากตารางนั้น
(ตารางควรมีคอลัมน์อย่างน้อย: `heading`, `body_html`, `sort`) — anon key ปลอดภัยด้วย RLS

ดูภาพรวมที่ `../../WEBHUB.md`
