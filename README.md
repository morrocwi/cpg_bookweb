# cpg_bookweb · ปรัชญาปัญญาประดิษฐ์

เว็บไซต์ของหนังสือ **Person Reasoning Design Foundation and Protocol**
(รากฐานและระเบียบการของการให้เหตุผลของบุคคล) — **หนังสือเล่มเดียว** ที่รวมฐานปรัชญา
สมการ และหลักการไว้ด้วยกัน แบ่งเป็นบท (chapters) เรียบเรียงจาก
[`cpg_book`](https://github.com/morrocwi/cpg_book) ห้องสมุดความรู้ของ
**Yaoharee Lahtee** และ **Walancha**

> โฟลเดอร์นี้คือ "ที่รวบรวมเว็บ" (web collection) ที่เชื่อม **notify ─ supabase ─ git** เข้าด้วยกัน

## โครงสร้าง

```
cpg_bookweb/                          # ห้องสมุด: library → book → chapter
├─ index.html               # ตัวเว็บ (static, vanilla JS — ไม่ต้อง build)
├─ library.json             # รายชื่อหนังสือในห้องสมุด (ตอนนี้ 1 เล่ม)
├─ books/                   # 1 โฟลเดอร์ = 1 เล่ม
│  └─ person-reasoning/
│     ├─ book.json          # ข้อมูลบท (chapters) ของหนังสือ สร้างจาก cpg_book
│     └─ PRDFP.seed.yaml    # ไฟล์ตั้งต้นสำหรับ AI (สมการ + pseudo-schema · อ่านก่อน)
├─ tools/
│  ├─ build_articles.py     # cpg_book (README + PRF yaml) -> books/<slug>/book.json + library.json
│  └─ notify.py             # แจ้งเตือน Discord / Telegram / LINE (fail-soft)
├─ supabase/
│  └─ schema.sql            # ตาราง articles (มี book_id) + RLS (อ่านสาธารณะ)
├─ .github/workflows/
│  └─ sync.yml              # git -> build -> supabase -> notify
└─ _design_extracted/       # ดีไซน์ต้นฉบับที่สกัดจาก .dc.html (provenance)
```

## โครงสร้าง: ห้องสมุด → หนังสือ → บท

- **ห้องสมุด** = `ปรัชญาปัญญาประดิษฐ์` (เว็บนี้) — รวมหนังสือหลายเล่มได้ ตอนนี้มี **1 เล่ม**
- **1 โฟลเดอร์ = 1 เล่ม** ที่ `books/<slug>/`
- **หนังสือเล่มแรก** = *Person Reasoning Design Foundation and Protocol* ซึ่ง **“คือ” ไฟล์ตั้งต้น**:
  กลั่น Person Reasoning เป็น **สมการ + pseudo-schema** (ดู `PRDFP.seed.yaml`) ให้ AI อ่านก่อน
  เพื่อเชื่อมกับบุคคลทั้ง **การซิงโครไนซ์** (ความหมายร่วม) และ **รีทึม** (จังหวะร่วม)

## เนื้อหา = ของจริงจาก cpg_book เท่านั้น

`book.json` ถูกสร้างโดย `tools/build_articles.py` ซึ่งอ่านไฟล์จริงใน `cpg_book`:

- `README.md` → บท "บทนำ"
- `personal_reasoning/00_…FOUNDATION….yaml` → ฐานปรัชญา 7 ด้าน · สมการหลัก 6 สมการ ·
  หลักการ 10 ข้อ (PR-001…PR-010)

หลักการ/เหตุผล/ตัวอย่าง/สมการ ถูกนำมา **ตามต้นฉบับ** และทุกบทลิงก์กลับไปยังไฟล์ต้นทาง
(รักษาที่มา ก่อนเพิ่มการตีความ) ชื่อหัวข้อภาษาไทยเป็นคำแปลที่ซื่อตรงของต้นฉบับภาษาอังกฤษ
ซึ่งยังแสดงคู่กันในเนื้อหา

สร้างใหม่:

```bash
python tools/build_articles.py --book-dir /path/to/cpg_book --web-root .
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
