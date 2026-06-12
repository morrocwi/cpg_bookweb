# ปรัชญาปัญญาประดิษฐ์ — Web Hub

`cpg_bookweb` คือ **hub รวมหลายเว็บไซต์** ของโปรเจกต์ — **1 โฟลเดอร์ = 1 เว็บไซต์**
ทุกเว็บใช้มาตรฐานเดียวกัน: **notify ─ supabase ─ git** + deploy บน GitHub Pages

> **สำหรับ AI เซสชั่นอื่น:** อ่านไฟล์นี้ + `sites.json` + สกิล `/WebForge`
> (`cpq_skill/webops/WebForge_v0_1_0.yaml`) แล้วสร้าง/อัปเดตเว็บได้ตามมาตรฐานเลย

## โครงสร้าง

```
cpg_bookweb/
├─ index.html, library.json, books/   # เว็บ #1 (ไลบรารี) — อยู่ที่ root, URL เดิม
├─ sites/                              # เว็บใหม่ทั้งหมด — 1 โฟลเดอร์ = 1 เว็บ
│  ├─ _TEMPLATE/                       # ต้นแบบสำหรับสร้างเว็บใหม่
│  └─ <slug>/                          # เว็บหนึ่งตัว: index.html + site.json + content.json
├─ shared/                             # เครื่องมือใช้ร่วมทุกเว็บ
│  ├─ new_site.py                      # scaffolder: สร้างเว็บใหม่จาก _TEMPLATE + ลงทะเบียน
│  └─ notify.py                        # แจ้งเตือน Discord/Telegram/LINE (fail-soft)
├─ sites.json                          # ทะเบียนเว็บทั้งหมด (registry)
└─ WEBHUB.md                           # ไฟล์นี้
```

## มาตรฐานหนึ่งเว็บ (notify-supabase-git)

- **git** = source of truth (โค้ด + `content.json`) — push แล้ว GitHub Pages redeploy อัตโนมัติ
- **supabase** = ฐานข้อมูล content (อ่านสดด้วย anon key, กรองด้วย `site` / ตารางของเว็บ) → fallback `content.json`
- **notify** = แจ้งเตือนเมื่อ sync/deploy ผ่าน `shared/notify.py`
- **deploy** = GitHub Pages; เว็บใหม่เสิร์ฟที่ `…/cpg_bookweb/sites/<slug>/`

## สร้างเว็บใหม่

```bash
python shared/new_site.py <slug> "<ชื่อเว็บ>"     # สร้าง sites/<slug>/ + เพิ่มใน sites.json
# แก้ sites/<slug>/content.json (หรือต่อ supabase) แล้ว:
git add sites/<slug> sites.json && git commit -m "feat(site): <slug>" && git push
```

หรือในเซสชั่น AI: `/WebForge new <slug> "<ชื่อ>"`

## อัปเดตเว็บที่มีอยู่

แก้ไฟล์ใน `sites/<slug>/` (`content.json` / `index.html`) → commit + push → Pages redeploy
ถ้าเว็บใช้ supabase: อัปเดต row ในตารางของเว็บนั้น (หรือ re-sync จาก content.json)

## ทะเบียน (sites.json)

ทุกเว็บมี entry: `slug · title · path · url · data · supabase_table? · status`
`new_site.py` อัปเดตให้อัตโนมัติ — แก้มือก็ได้

## ขอบเขต / กฎ (สอดคล้อง PROJECT_RULES)

- การ **deploy / publish** = การกระทำออกสู่สาธารณะ → **ต้องมีมนุษย์อนุมัติก่อน**
- **anon key** ใส่ใน frontend ได้ (ปลอดภัยด้วย Supabase RLS) — **service key ห้ามคอมมิต** อยู่ใน GitHub Secrets เท่านั้น
- **1 โฟลเดอร์ = 1 เว็บ** — อย่าปนเนื้อหาข้ามเว็บ; เว็บใหม่ไม่แตะของเว็บอื่น
- เนื้อหาที่มาจาก repo อื่น (เช่น `cpg_book`) ให้ **รักษาที่มา** + ลิงก์กลับต้นทาง

## ขอบเขตระหว่างสองเว็บ (ISSUE-0119 · human_pi 2026-06-12 — แยกแต่จัดระเบียบ)

| | **cpg_bookweb** (hub นี้) | **projects/araya-platform** |
|---|---|---|
| ประเภท | เว็บเนื้อหา **static** | **แอป dynamic** (auth/SSR/API/connector) |
| Stack / deploy | static + vanilla JS → **GitHub Pages** | Next.js + Supabase SSR → **Netlify** |
| สกิล | `/WebForge` | (devteam / actor-connector) |

- **Supabase = โปรเจกต์เดียว** (`ckvxuvkxctssyozscfbm`) แต่ **แต่ละเว็บเป็นเจ้าของตารางของตัวเองในรีโปของตัวเอง** —
  ตารางเนื้อหาของ hub นี้ (เช่น `articles`) นิยามใน `supabase/schema.sql` ของ cpg_bookweb เท่านั้น ไม่ปนกับตารางของ araya-platform
- งานเว็บที่เป็น **แอป/auth/connector → ไปที่ araya-platform** (ไม่ใช่ที่นี่)
- คลังสกิล/ติดตั้ง/อ่าน อยู่จุดเดียวที่ `cpq_skill/SKILLS.md` (`python cpq_skill/skills.py …`)
