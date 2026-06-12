#!/usr/bin/env python3
"""
build_articles.py — transform the REAL cpg_book content into article records.

Reads the actual files in the cpg_book repository:
  - README.md                                       (library manifesto, Thai)
  - personal_reasoning/00_PERSONAL_REASONING_FOUNDATION_AND_PROTOCOL.yaml
        -> 10 core principles, 6 equations, 7 philosophical foundations

and emits articles.json (consumed by the website + upserted into Supabase).
NO content is invented here: principle statements, rationales, counterexamples,
scopes, equations, and philosophical principles are taken verbatim from source.
Thai display titles are faithful translations of the English statements; the
verbatim English source is always shown in the article body (per the library's
own rule: "keep provenance before adding interpretation").

Usage:
  python build_articles.py --book-dir <path-to-cpg_book> --out ../articles.json
  python build_articles.py --book-dir <path> --push-supabase   # uses env creds
"""
import argparse, json, os, re, sys, html, datetime
import yaml

# Windows consoles default to cp1252 and choke on Thai in print(); force UTF-8.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ----- the book -----
BOOK = {
    "brand": "ปรัชญาปัญญาประดิษฐ์",
    "title": "Person Reasoning Design Foundation and Protocol",
    "title_th": "รากฐานและระเบียบการของการให้เหตุผลของบุคคล",
}

# ----- category metadata = the parts of the single book (drives the chips/TOC) -----
CATEGORIES = {
    "about":      {"label": "บทนำ",       "accent": "#f59e0b"},
    "philosophy": {"label": "ฐานปรัชญา",  "accent": "#10b981"},
    "equation":   {"label": "สมการหลัก",  "accent": "#8b5cf6"},
    "principle":  {"label": "หลักการ",    "accent": "#0ea5e9"},
}

# faithful Thai titles for the 10 principles (summaries of the verbatim English statement)
PRINCIPLE_TITLE_TH = {
    "PR-001": "แยกสิ่งที่สังเกต ออกจากการตีความและกฎที่กำกับ",
    "PR-002": "ความมั่นใจไม่ใช่หลักฐาน และความสามารถไม่ใช่อำนาจ",
    "PR-003": "ข้อสรุปยังเป็นชั่วคราว ตราบที่ยังมีความไม่แน่นอน",
    "PR-004": "คุณค่าของคน ไม่ได้ลดทอนเหลือแค่ความเหมาะกับบทบาทหรือผลงาน",
    "PR-005": "ผลกระทบต่อผู้เกี่ยวข้อง ต้องอยู่ในกรอบการให้เหตุผล",
    "PR-006": "ความสามารถแก้ไขกลับ คือส่วนหนึ่งของการตัดสินที่รับผิดชอบ",
    "PR-007": "เมื่อคำวิจารณ์ชี้จุดผิด ให้แก้แบบจำลองก่อนปกป้องคำตอบเดิม",
    "PR-008": "หลักการร่วมช่วยให้ทำงานร่วมกันได้ โดยไม่ต้องสรุปเหมือนกัน",
    "PR-009": "หลักคิดควรชี้นำการตีความ ไม่ใช่กำหนดการกระทำล่วงหน้า",
    "PR-010": "เอกสารต้องแก้ไขได้ ระบุที่มาได้ และมีขอบเขต",
}
STABILITY_TH = {"constitutional": "รากฐาน", "high": "สูง", "medium": "ปานกลาง", "experimental": "ทดลอง"}
PR_SRC = "personal_reasoning/00_PERSONAL_REASONING_FOUNDATION_AND_PROTOCOL.yaml"


def esc(s):
    return html.escape(str(s), quote=False)


def read_minutes(*texts):
    words = sum(len(re.findall(r"\S+", t or "")) for t in texts)
    return max(1, round(words / 180))


def gh_blob(src, sub=None):
    base = "https://github.com/morrocwi/cpg_book/blob/main/" + src
    return base + (("#" + sub) if sub else "")


# ---------------------------------------------------------------- README (about)
def build_about(book_dir):
    path = os.path.join(book_dir, "README.md")
    md = open(path, encoding="utf-8").read()

    # §3 distinctions: "### 3.x หัวข้อ" + the fenced code line "A ≠ B"
    dist = []
    for m in re.finditer(r"### 3\.\d+\s+(.+?)\n(.*?)```text\n(.+?)\n```", md, re.S):
        dist.append((m.group(1).strip(), m.group(3).strip()))

    # final statement (blockquote after "## Final statement")
    fm = re.search(r"## Final statement\s*\n+>\s*(.+?)(?:\n\n|\Z)", md, re.S)
    final = re.sub(r"\s+", " ", fm.group(1)).strip() if fm else ""

    intro = ("บทนำของหนังสือ Person Reasoning Design Foundation and Protocol — "
             "รวมรากฐานปรัชญา สมการ และหลักการของการให้เหตุผลของบุคคลไว้ในเล่มเดียว")

    body = ['<p>หนังสือเล่มนี้รวบรวมรากฐานการให้เหตุผลของบุคคล (Person Reasoning) ไว้ในเล่มเดียว — '
            'ฐานปรัชญา สมการหลัก และหลักการ — เพื่อให้มนุษย์และ AI หลายตัวเข้าใจวิธีตีความ ตัดสิน '
            'และแก้ไขของบุคคลได้อย่างสอดคล้องและมีบริบท โดยไม่ลดทอนบุคคลให้เหลือเพียงข้อมูลหรือแบบจำลอง '
            'เนื้อหาเรียบเรียงจากห้องสมุดความรู้ cpg_book ของ Yaoharee Lahtee และ Walancha</p>']
    if dist:
        body.append("<h2>หลักการของห้องสมุด</h2>")
        for title, eqn in dist:
            body.append(f'<p><strong>{esc(title)}</strong></p>')
            body.append(f'<blockquote><p>{esc(eqn)}</p></blockquote>')
    if final:
        body.append("<h2>คำแถลงสุดท้าย</h2>")
        body.append(f'<blockquote><p>{esc(final)}</p></blockquote>')
    body.append(f'<p style="font-family:\'Noto Sans Thai\',sans-serif;font-size:13px;color:#9aa5b1;">'
                f'ที่มา: <a href="{gh_blob("README.md")}" target="_blank" rel="noopener" '
                f'style="color:#0ea5e9;">cpg_book/README.md</a></p>')
    body_html = "\n".join(body)

    return {
        "id": "about-cpg-book", "cat": "about", "featured": True, "sort": 0,
        "title": "บทนำ: เกี่ยวกับหนังสือเล่มนี้",
        "excerpt": intro,
        "body_html": body_html,
        "tags": ["ห้องสมุด", "ความรู้", "AI"],
        "read_minutes": read_minutes(md[:4000]),
        "source": "README.md", "source_id": "README", "lang": "th",
    }


# ----------------------------------------------------- PRF: philosophy + equations + principles
def build_from_prf(book_dir):
    path = os.path.join(book_dir, PR_SRC)
    data = yaml.safe_load(open(path, encoding="utf-8"))
    updated = str(data.get("document", {}).get("last_reviewed_at", ""))
    out = []

    # --- philosophy (7 foundations) ---
    pf = data.get("philosophical_foundation", {})
    pf_label = {
        "personhood": "ความเป็นบุคคล", "epistemology": "ญาณวิทยา",
        "hermeneutics": "การตีความ", "practical_wisdom": "ปัญญาเชิงปฏิบัติ",
        "relational_ethics": "จริยศาสตร์เชิงสัมพันธ์", "extended_mind": "จิตที่ขยายออก",
        "intersubjectivity": "ความเข้าใจร่วมระหว่างผู้คน",
    }
    pbody = ['<p>ฐานปรัชญาเจ็ดด้านที่รองรับวิธีการให้เหตุผล — แต่ละด้านมี "หลักการ" และ '
             '"นัยที่ตามมา" (แสดงต้นฉบับภาษาอังกฤษตามที่บันทึกไว้)</p>']
    for key, v in pf.items():
        name = pf_label.get(key, key)
        pbody.append(f'<h2>{esc(name)}</h2>')
        pbody.append(f'<p><strong>Principle.</strong> {esc(v.get("principle",""))}</p>')
        pbody.append(f'<p><strong>Implication.</strong> {esc(v.get("implication",""))}</p>')
    pbody.append(f'<p style="font-family:\'Noto Sans Thai\',sans-serif;font-size:13px;color:#9aa5b1;">'
                 f'ที่มา: <a href="{gh_blob(PR_SRC, "L37")}" target="_blank" rel="noopener" '
                 f'style="color:#0ea5e9;">PRF-001 · philosophical_foundation</a></p>')
    out.append({
        "id": "philosophical-foundation", "cat": "philosophy", "featured": False, "sort": 1,
        "title": "ฐานปรัชญา 7 ด้านของการให้เหตุผล",
        "excerpt": "ความเป็นบุคคล ญาณวิทยา การตีความ ปัญญาเชิงปฏิบัติ จริยศาสตร์เชิงสัมพันธ์ "
                   "จิตที่ขยายออก และความเข้าใจร่วม — รากฐานของ Personal Reasoning Foundation",
        "body_html": "\n".join(pbody),
        "tags": ["ปรัชญา", "ญาณวิทยา", "จริยศาสตร์"],
        "read_minutes": read_minutes(*[str(v) for v in pf.values()]),
        "source": PR_SRC, "source_id": "PRF-001/philosophy", "lang": "th-en", "updated_at": updated,
    })

    # --- equations (6) ---
    eqs = data.get("core_equations", [])
    ebody = ['<p>สมการช่วยให้เห็นความสัมพันธ์ระหว่างแนวคิด ไม่ใช่ข้อพิสูจน์ทางวิทยาศาสตร์ '
             '(ตามที่ระบุไว้ในมาตรฐานของห้องสมุด)</p>']
    for e in eqs:
        ebody.append(f'<h2>{esc(e.get("id"))} · {esc(e.get("name"))}</h2>')
        ebody.append('<blockquote><p style="font-family:ui-monospace,monospace;">'
                     f'{esc(e.get("expression"))}</p></blockquote>')
        terms = e.get("terms", {})
        if terms:
            ebody.append("<ul>" + "".join(
                f'<li><strong>{esc(k)}</strong> — {esc(v)}</li>' for k, v in terms.items()) + "</ul>")
        ebody.append(f'<p>{esc(e.get("meaning",""))}</p>')
    ebody.append(f'<p style="font-family:\'Noto Sans Thai\',sans-serif;font-size:13px;color:#9aa5b1;">'
                 f'ที่มา: <a href="{gh_blob(PR_SRC)}" target="_blank" rel="noopener" '
                 f'style="color:#0ea5e9;">PRF-001 · core_equations</a></p>')
    out.append({
        "id": "core-equations", "cat": "equation", "featured": False, "sort": 2,
        "title": "สมการหลัก 6 สมการของการให้เหตุผล",
        "excerpt": "ClaimStrength ≤ EvidenceStrength · PR(t+1) = Revise(...) · PR_t ≠ Person — "
                   "สมการเชิงตีความที่อธิบายความสัมพันธ์ ไม่ใช่ความแม่นยำทางคณิตศาสตร์ลวงตา",
        "body_html": "\n".join(ebody),
        "tags": ["สมการ", "การให้เหตุผล"],
        "read_minutes": read_minutes(*[str(e) for e in eqs]),
        "source": PR_SRC, "source_id": "PRF-001/equations", "lang": "th-en", "updated_at": updated,
    })

    # --- principles (10) ---
    for i, p in enumerate(data.get("core_principles", [])):
        pid = p.get("id")
        stab = p.get("stability", "")
        scopes = p.get("scope", []) or []
        pb = []
        pb.append(f'<span class="principle">{esc(pid)} · ความเสถียร: '
                  f'{esc(STABILITY_TH.get(stab, stab))} ({esc(stab)})</span>')
        pb.append("<h2>หลักการ (ต้นฉบับ)</h2>")
        pb.append(f'<blockquote><p>{esc(p.get("statement",""))}</p></blockquote>')
        pb.append("<h2>เหตุผล</h2>")
        pb.append(f'<p>{esc(p.get("rationale",""))}</p>')
        if p.get("counterexample"):
            pb.append("<h2>ตัวอย่างการใช้ผิด</h2>")
            pb.append(f'<p>{esc(p.get("counterexample"))}</p>')
        if p.get("revision_trigger"):
            pb.append("<h2>เงื่อนไขทบทวน</h2>")
            pb.append(f'<p>{esc(p.get("revision_trigger"))}</p>')
        if scopes:
            chips = "".join(
                f'<span style="font-family:\'Noto Sans Thai\',sans-serif;font-size:12.5px;color:#5d6b78;'
                f'background:#f1eee7;border:1px solid #e8e4db;padding:4px 11px;border-radius:99px;'
                f'margin:0 6px 6px 0;display:inline-block;">{esc(s)}</span>' for s in scopes)
            pb.append("<h2>ขอบเขต</h2>")
            pb.append(f'<div>{chips}</div>')
        pb.append(f'<p style="font-family:\'Noto Sans Thai\',sans-serif;font-size:13px;color:#9aa5b1;">'
                  f'ที่มา: <a href="{gh_blob(PR_SRC)}" target="_blank" rel="noopener" '
                  f'style="color:#0ea5e9;">PRF-001 · {esc(pid)}</a></p>')
        out.append({
            "id": pid.lower(), "cat": "principle", "featured": False, "sort": 10 + i,
            "title": PRINCIPLE_TITLE_TH.get(pid, p.get("statement", "")),
            "excerpt": p.get("rationale", ""),
            "body_html": "\n".join(pb),
            "tags": scopes[:4],
            "read_minutes": read_minutes(p.get("statement"), p.get("rationale"), p.get("counterexample")),
            "source": PR_SRC, "source_id": pid, "lang": "th-en", "updated_at": updated,
        })
    return out


def build(book_dir):
    articles = [build_about(book_dir)] + build_from_prf(book_dir)
    articles.sort(key=lambda a: a.get("sort", 999))
    return {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0, tzinfo=None).isoformat() + "Z",
        "source_repo": "morrocwi/cpg_book",
        "book": BOOK,
        "categories": CATEGORIES,
        "articles": articles,
    }


def push_supabase(articles):
    import urllib.request
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY")
    if not (url and key):
        print("[supabase] SUPABASE_URL / SUPABASE_SERVICE_KEY not set — skipping upsert", file=sys.stderr)
        return False
    rows = []
    for a in articles:
        rows.append({k: a.get(k) for k in (
            "id", "cat", "title", "excerpt", "body_html", "tags",
            "read_minutes", "featured", "source", "source_id", "lang", "sort")})
    body = json.dumps(rows).encode("utf-8")
    req = urllib.request.Request(
        url.rstrip("/") + "/rest/v1/articles?on_conflict=id",
        data=body, method="POST",
        headers={"apikey": key, "Authorization": "Bearer " + key,
                 "Content-Type": "application/json",
                 "Prefer": "resolution=merge-duplicates,return=minimal"})
    with urllib.request.urlopen(req) as r:
        print(f"[supabase] upsert {len(rows)} rows -> HTTP {r.status}")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--book-dir", default=os.environ.get("CPG_BOOK_DIR", "."))
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "articles.json"))
    ap.add_argument("--push-supabase", action="store_true")
    args = ap.parse_args()

    bundle = build(args.book_dir)
    out = os.path.abspath(args.out)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(bundle, f, ensure_ascii=False, indent=2)
    print(f"[build] {len(bundle['articles'])} articles -> {out}")
    for a in bundle["articles"]:
        print(f"   - [{a['cat']:10}] {a['id']:24} {a['title']}")

    if args.push_supabase:
        push_supabase(bundle["articles"])


if __name__ == "__main__":
    main()
