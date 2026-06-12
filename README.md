# cpg_bookweb · ห้องสมุดสบายๆ

เว็บไซต์เผยแพร่ความรู้จาก [`cpg_book`](https://github.com/morrocwi/cpg_book) —
ห้องสมุดของ **Yaoharee Lahtee** และ **Walancha** ที่รวบรวมแนวคิดเรื่องความรู้
การให้เหตุผล และการอยู่ร่วมกันระหว่างมนุษย์กับ AI

> โฟลเดอร์นี้คือ "ที่รวบรวมเว็บ" (web collection) ที่เชื่อม **notify ─ supabase ─ git** เข้าด้วยกัน

## โครงสร้าง

```
cpg_bookweb/
├─ index.html               # ตัวเว็บ (static, vanilla JS — ไม่ต้อง build)
├─ articles.json            # ข้อมูลบทความจริง สร้างจาก cpg_book
├─ tools/
│  ├─ build_articles.py     # cpg_book (README + PRF yaml) -> articles.json (+ upsert Supabase)
│  └─ notify.py             # แจ้งเตือน Discord / Telegram / LINE (fail-soft)
├─ supabase/
│  └─ schema.sql            # ตาราง articles + RLS (อ่านสาธารณะ)
├─ .github/workflows/
│  └─ sync.yml              # git -> build -> supabase -> notify
└─ _design_extracted/       # ดีไซน์ต้นฉบับที่สกัดจาก .dc.html (provenance)
```

## เนื้อหา = ของจริงจาก cpg_book เท่านั้น

`articles.json` ถูกสร้างโดย `tools/build_articles.py` ซึ่งอ่านไฟล์จริงใน `cpg_book`:

- `README.md` → บทความ "เกี่ยวกับห้องสมุด"
- `personal_reasoning/00_…FOUNDATION….yaml` → ฐานปรัชญา 7 ด้าน · สมการหลัก 6 สมการ ·
  หลักการให้เหตุผล 10 ข้อ (PR-001…PR-010)

หลักการ/เหตุผล/ตัวอย่าง/สมการ ถูกนำมา **ตามต้นฉบับ** และทุกบทความลิงก์กลับไปยังไฟล์ต้นทาง
(รักษาที่มา ก่อนเพิ่มการตีความ) ชื่อหัวข้อภาษาไทยเป็นคำแปลที่ซื่อตรงของต้นฉบับภาษาอังกฤษ
ซึ่งยังแสดงคู่กันในเนื้อหา

สร้างใหม่:

```bash
python tools/build_articles.py --book-dir /path/to/cpg_book --out articles.json
```

## รันในเครื่อง

```bash
python -m http.server 4178            # แล้วเปิด http://localhost:4178
```

## notify ─ supabase ─ git

```
cpg_book (push) ──dispatch──► cpg_bookweb (Action: sync.yml)
                                  │ build_articles.py  (README + PRF yaml → articles.json)
                                  │ upsert ──► Supabase  table public.articles
                                  │ commit articles.json ──► GitHub Pages redeploy
                                  └ notify ──► Discord / Telegram / LINE
เว็บ index.html ──fetch──► Supabase (anon key)  ─fallback→ articles.json
```

### Secrets ที่ต้องตั้ง (Settings → Secrets → Actions)

| secret | ใช้ทำอะไร | จำเป็น |
|--------|-----------|--------|
| `SUPABASE_URL` | `https://ckvxuvkxctssyozscfbm.supabase.co` | ถ้าจะ push เข้า DB |
| `SUPABASE_SERVICE_KEY` | service-role key (เขียน DB, **อย่าใส่ในโค้ด/เว็บ**) | ถ้าจะ push เข้า DB |
| `DISCORD_WEBHOOK_URL` *(หรือ)* `TELEGRAM_BOT_TOKEN`+`TELEGRAM_CHAT_ID` *(หรือ)* `LINE_CHANNEL_ACCESS_TOKEN`+`LINE_TO` | ช่องทางแจ้งเตือน | ถ้าจะแจ้งเตือน |

> **anon key** (อ่านอย่างเดียว) ใส่ใน `index.html` (`SUPABASE.anonKey`) ได้อย่างปลอดภัย —
> ความปลอดภัยมาจาก RLS ใน `supabase/schema.sql` ไม่ใช่การซ่อนคีย์ ส่วน **service key อยู่ใน
> GitHub Secrets เท่านั้น** ห้ามคอมมิตลง repo สาธารณะ

## ที่มาของดีไซน์

`index.html` สกัดและประกอบใหม่จาก Claude design-code artifact `ห้องสมุดสบายๆ.dc.html`
ดู `DESIGN_SOURCE.md` สำหรับรายละเอียดการถอดรหัส bundle
