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

# ----- the library + the (currently single) book -----
LIBRARY = {
    "brand": "ปรัชญาปัญญาประดิษฐ์",
    "tagline": "ห้องสมุดว่าด้วยปรัชญาปัญญาประดิษฐ์ — การให้เหตุผลและการอยู่ร่วมกันของมนุษย์กับ AI",
}
BOOK = {
    "slug": "person-reasoning",
    "brand": "ปรัชญาปัญญาประดิษฐ์",
    "title": "Person Reasoning Design Foundation and Protocol",
    "title_th": "รากฐานและระเบียบการของการให้เหตุผลของบุคคล",
    "author": "Yaoharee",
    "year": 2026,
    "accent": "#0ea5e9",
    "summary": ("หนังสือที่กลั่นรากฐานการให้เหตุผลของบุคคลเป็นฐานปรัชญา สมการ และหลักการ "
                "— สำหรับให้มนุษย์และ AI เชื่อมโยงและทำงานร่วมกันอย่างมีบริบท"),
    "seed": "PRDFP.seed.yaml",
    "repo": "https://github.com/morrocwi/cpg_bookweb",
    "source_repo": "https://github.com/morrocwi/cpg_book",
    "seed_url": "https://morrocwi.github.io/cpg_bookweb/books/person-reasoning/PRDFP.seed.yaml",
    # what the book is + the problem it solves (problems = Thai gloss of PRF human_multi_ai_bridge.problem)
    "overview": {
        "what": ("กลั่นรากฐานการให้เหตุผลของบุคคล (Person Reasoning) เป็น สมการ + pseudo-schema "
                 "ไฟล์เดียวที่กระชับและเบา ให้ AI อ่านเป็นไฟล์แรกก่อนทำงานร่วมกับบุคคล"),
        "problems": [
            "AI แต่ละตัวเห็นบุคคลเดียวกันแค่บางบทบาท จึงเข้าใจไม่ตรงกัน",
            "คุยกันคนละรอบ ทำให้สรุปลำดับความสำคัญของบุคคลเพี้ยนไปคนละทาง",
            "memory ที่แยกตามงาน ทำให้ความต่อเนื่องของการให้เหตุผลแตกเป็นเสี่ยง",
            "การปรับแต่งสไตล์อย่างเดียว ไม่รักษามาตรฐานการตัดสินของบุคคล",
        ],
        "solves": ("ให้ AI อ่านไฟล์ตั้งต้นนี้ก่อน แล้วเชื่อมกับบุคคลได้ลงตัวทั้ง การซิงโครไนซ์ "
                   "(ความหมายร่วม) และ รีทึม (จังหวะร่วม) โดยไม่ลดทอนบุคคลให้เหลือเพียงแบบจำลอง (PR_t ≠ Person)"),
    },
}

# ----- category metadata = the parts of the single book (drives the chips/TOC) -----
CATEGORIES = {
    "about":      {"label": "บทนำ",            "accent": "#f59e0b"},
    "position":   {"label": "นิยาม & ตำแหน่ง", "accent": "#6366f1"},
    "philosophy": {"label": "ฐานปรัชญา",       "accent": "#10b981"},
    "equation":   {"label": "สมการหลัก",       "accent": "#8b5cf6"},
    "principle":  {"label": "หลักการ",         "accent": "#0ea5e9"},
    "protocol":   {"label": "กระบวนการ",       "accent": "#ec4899"},
    "example":    {"label": "ตัวอย่างใช้งาน",  "accent": "#14b8a6"},
    "schema":     {"label": "สคีมาผลลัพธ์",    "accent": "#0891b2"},
    "reference":  {"label": "บทอ้างอิง",       "accent": "#64748b"},
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

    seed_path = "books/%s/%s" % (BOOK["slug"], BOOK["seed"])
    intro = ("หนังสือเล่มนี้กลั่นรากฐานการให้เหตุผลของบุคคล (Person Reasoning) เป็นสมการและ pseudo-schema "
             "— ไฟล์ตั้งต้นที่กระชับและเบา ให้ AI อ่านเป็นไฟล์แรกก่อนทำงานร่วมกับบุคคล")

    body = ['<p><strong>สิ่งที่หนังสือเล่มนี้ต้องการสื่อ:</strong> รวบรวมรากฐานการให้เหตุผลของบุคคล '
            '(Person Reasoning) แล้วแปลเป็น <strong>สมการ</strong> และ <strong>pseudo-schema</strong> '
            'ให้กลายเป็น <strong>ไฟล์ตั้งต้น</strong> ไฟล์เดียวที่กระชับและเบา — เพื่อให้ AI อ่านไฟล์นี้ '
            '<strong>เป็นไฟล์แรก</strong> แล้วทำงานร่วมกับบุคคลผู้นั้นได้อย่างลงตัว ทั้งทาง '
            '<strong>การซิงโครไนซ์</strong> (ความหมายร่วม) และ <strong>รีทึม</strong> (จังหวะร่วม) '
            'โดยไม่ลดทอนบุคคลให้เหลือเพียงข้อมูลหรือแบบจำลอง (PR_t ≠ Person)</p>',
            '<blockquote><p>📄 ไฟล์ตั้งต้นสำหรับ AI: '
            '<a href="%s" target="_blank" rel="noopener">PRDFP.seed.yaml</a> — ให้ AI อ่านก่อนเริ่มงาน</p>'
            '</blockquote>' % seed_path,
            '<p>ส่วนที่เหลือของหนังสือคือเนื้อหาที่ไฟล์ตั้งต้นนี้กลั่นมา — ฐานปรัชญา สมการหลัก และหลักการ '
            'เรียบเรียงจากห้องสมุดความรู้ cpg_book ของ Yaoharee Lahtee และ Walancha</p>']
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


# ----------------------------------------------------- PRF-derived narrative chapters
def _mk(cid, cat, sort, title, excerpt, parts, tags, updated=""):
    parts = parts + ['<p style="font-family:\'Noto Sans Thai\',sans-serif;font-size:13px;color:#9aa5b1;">'
                     'ที่มา: <a href="%s" target="_blank" rel="noopener" style="color:#0ea5e9;">PRF-001 · %s</a></p>'
                     % (gh_blob(PR_SRC), cid)]
    body_html = "\n".join(parts)
    return {
        "id": cid, "cat": cat, "featured": False, "sort": sort, "title": title, "excerpt": excerpt,
        "body_html": body_html, "tags": tags,
        "read_minutes": read_minutes(re.sub(r"<[^>]+>", " ", body_html)),
        "source": PR_SRC, "source_id": "PRF-001/" + cid, "lang": "th-en", "updated_at": updated,
    }


def _ul(items):
    return "<ul>" + "".join("<li>%s</li>" % esc(x) for x in (items or [])) + "</ul>"


def prf_identity(data):
    idy = data.get("identity", {})
    bridge = data.get("human_multi_ai_bridge", {})
    p = ['<p>%s</p>' % esc(idy.get("thai_definition", "")),
         '<blockquote><p><strong>Definition.</strong> %s</p></blockquote>' % esc(idy.get("definition", "")),
         '<h2>ทำไมต้องเป็นไฟล์แรกที่มนุษย์สร้างเพื่อคุยกับ AI</h2>',
         '<p>AI แต่ละตัวเห็นบุคคลเดียวกันเพียงบางบทบาท ถ้าไม่มีจุดอ้างอิงร่วม การตีความจะแตกกระจายและไม่ต่อเนื่อง '
         'ไฟล์นี้จึงควรถูกสร้างและอ่าน <strong>ก่อน</strong> งานใด ๆ เพื่อวางพื้นความเข้าใจร่วม ก่อนที่ AI จะเริ่มตีความหรือทำงาน '
         '— เป็น “ไฟล์ตั้งต้น” ที่มนุษย์เขียนถึงหลักคิดของตนเองในแบบที่ AI หลายตัวอ่านแล้วเข้าใจตรงกัน</p>']
    if idy.get("purpose"):
        p += ['<h2>ไฟล์นี้มีไว้เพื่อ</h2>', _ul(idy["purpose"])]
    if bridge.get("function"):
        p += ['<h2>หน้าที่ในการเชื่อมมนุษย์กับ AI หลายตัว</h2>', _ul(bridge["function"])]
    p += ['<h2>ตำแหน่งของไฟล์: ไฟล์นี้ “ไม่ใช่” อะไร</h2>', _ul(idy.get("not_a")),
          '<blockquote><p>ไฟล์นี้เป็น <strong>การอ้างอิงเชิงตีความ</strong> (interpretive reference) ไม่มีอำนาจสั่งการ '
          'และไม่ใช่ตัวบุคคล: <code>PR_t ≠ Person</code></p></blockquote>']
    return _mk("identity", "position", 1, "ไฟล์นี้คืออะไร และทำไมต้องเป็นไฟล์แรก",
               "ตำแหน่งของไฟล์: เป็นการอ้างอิงเชิงตีความ ไม่ใช่คำสั่ง — และเหตุผลที่มนุษย์ควรสร้างไฟล์นี้ก่อนคุยกับ AI",
               p, ["ตำแหน่ง", "นิยาม", "ไฟล์แรก"], str(data.get("document", {}).get("last_reviewed_at", "")))


def prf_distinctions(data):
    cd = data.get("conceptual_distinctions", {})
    label = {"prompt": "prompt (คำสั่งงาน)", "workflow": "workflow (ลำดับงาน)", "skill": "skill (ความสามารถ)",
             "memory": "memory (ความจำ)", "persona": "persona (โทน/บทบาท)", "policy": "policy (นโยบาย)",
             "knowledge_base": "knowledge base (คลังความรู้)"}
    p = ['<p>Personal Reasoning มักถูกสับสนกับสิ่งเหล่านี้ แต่ละอย่างทำหน้าที่คนละชั้น — แยกให้ชัดเพื่อไม่ให้ '
         '“หลักคิด” กลายเป็น “คำสั่ง” โดยไม่ตั้งใจ (แสดงคำอธิบายต้นฉบับ)</p>']
    for k, v in cd.items():
        p += ['<h2>ต่างจาก %s</h2>' % esc(label.get(k, k)),
              '<p><strong>คืออะไร.</strong> %s</p>' % esc(v.get("definition", "")),
              '<p><strong>ต่างกันตรงไหน.</strong> %s</p>' % esc(v.get("difference", ""))]
    return _mk("distinctions", "position", 2, "ต่างจาก prompt · skill · workflow · persona อย่างไร",
               "ความต่างที่ชัดเจนระหว่าง Personal Reasoning กับ prompt, workflow, skill, memory, persona, policy และ knowledge base",
               p, ["prompt", "skill", "workflow", "persona"], str(data.get("document", {}).get("last_reviewed_at", "")))


def prf_protocol(data):
    ip, ep, rp = (data.get("interpretation_protocol", {}), data.get("extension_protocol", {}),
                  data.get("revision_protocol", {}))
    p = ['<h2>กระบวนการตีความ (interpretation protocol)</h2>',
         '<p>บทบาท: <code>%s</code> — ตีความและสะท้อนเท่านั้น ไม่สั่งการ</p>' % esc(ip.get("role", ""))]
    if ip.get("input"): p += ['<p><strong>รับเข้า</strong></p>', _ul(ip["input"])]
    if ip.get("output"): p += ['<p><strong>ให้ผลเป็น</strong></p>', _ul(ip["output"])]
    if ip.get("must_not_output"): p += ['<p><strong>ต้องไม่ทำ</strong></p>', _ul(ip["must_not_output"])]
    if ip.get("pseudocode"):
        p.append('<blockquote><p style="font-family:ui-monospace,monospace;">'
                 + "<br>".join(esc(x) for x in ip["pseudocode"]) + '</p></blockquote>')
    p.append('<h2>การต่อยอด (extension protocol)</h2>')
    if ep.get("allowed_extensions"): p += ['<p><strong>ต่อยอดได้</strong></p>', _ul(ep["allowed_extensions"])]
    if ep.get("prohibited_extensions"): p += ['<p><strong>ห้าม</strong></p>', _ul(ep["prohibited_extensions"])]
    if ep.get("new_principle_requirements"):
        p += ['<p><strong>เพิ่มหลักการใหม่ต้องมี</strong></p>', _ul(ep["new_principle_requirements"])]
    p.append('<h2>การทบทวนและยกระดับ (revision protocol)</h2>')
    if rp.get("review_triggers"): p += ['<p><strong>ทบทวนเมื่อ</strong></p>', _ul(rp["review_triggers"])]
    if rp.get("change_types"):
        p.append('<p><strong>ชนิดการเปลี่ยน:</strong> %s</p>' % esc(", ".join(rp["change_types"])))
    if rp.get("required_change_record"):
        p.append('<p><strong>บันทึกการเปลี่ยนต้องมี:</strong> %s</p>' % esc(", ".join(rp["required_change_record"])))
    if rp.get("deprecation_rule"):
        p.append('<p>%s</p>' % esc(rp["deprecation_rule"]))
    return _mk("protocol", "protocol", 30, "กระบวนการ: ตีความ · ต่อยอด · ทบทวน",
               "interpretation / extension / revision protocol — กระบวนการครบสำหรับใช้ ต่อยอด และยกระดับไฟล์อย่างมีวินัย",
               p, ["protocol", "กระบวนการ", "ทบทวน"], str(data.get("document", {}).get("last_reviewed_at", "")))


def prf_examples(data):
    exs = data.get("application_examples", [])
    p = ['<p>ไฟล์เดียวกัน ถูกตีความต่างกันตามโดเมน โดยยังอิงหลักการร่วมเดียวกัน — และไม่กลายเป็นคำสั่ง (แสดงต้นฉบับ)</p>']
    for e in exs:
        p += ['<h2>%s</h2>' % esc(e.get("domain", "")),
              '<p><strong>สถานการณ์.</strong> %s</p>' % esc(e.get("situation", ""))]
        if e.get("relevant_principles"):
            p.append('<p><strong>หลักการที่เกี่ยว.</strong> %s</p>' % esc(", ".join(e["relevant_principles"])))
        p += ['<p><strong>ใช้เชิงตีความ.</strong> %s</p>' % esc(e.get("interpretive_use", "")),
              '<p><strong>ไม่ใช่คำสั่ง.</strong> %s</p>' % esc(e.get("not_an_instruction", ""))]
    return _mk("examples", "example", 40, "ตัวอย่างการใช้งานข้ามโดเมน",
               "ไฟล์เดียวกัน ตีความต่างกันตามโดเมน — HR · COO · ที่ปรึกษาศาสนา · วิจัย · multi-agent",
               p, ["ตัวอย่าง", "โดเมน"], str(data.get("document", {}).get("last_reviewed_at", "")))


def prf_output_schema(data):
    ws, qc = data.get("writing_standard", {}), data.get("quality_checks", [])
    tfs, sl = ws.get("target_file_size", {}), ws.get("section_limits", {})
    p = ['<p>เมื่อทำครบกระบวนการ ผลลัพธ์ควรเป็น <strong>ไฟล์ Personal Reasoning Foundation</strong> '
         'ที่ตรวจสอบได้ด้วย <code>personal_reasoning_foundation.schema.yaml</code> — ฉบับเต็มสำหรับเก็บถาวร '
         'และฉบับกลั่น (seed) สำหรับให้ AI อ่านก่อน</p>',
         '<h2>ส่วนที่ไฟล์ schema ควรมี</h2>',
         '<ul>'
         '<li><code>document</code> — เมตา (id, version, status, owner, review_cycle)</li>'
         '<li><code>identity</code> — นิยาม + purpose + not_a (ตำแหน่งของไฟล์)</li>'
         '<li><code>philosophical_foundation</code> — ฐานปรัชญา</li>'
         '<li><code>core_equations</code> — สมการเชิงตีความ</li>'
         '<li><code>core_principles</code> — หลักการ (id, statement, rationale, scope, counterexample, revision_trigger, stability)</li>'
         '<li><code>conceptual_distinctions</code> — ต่างจาก prompt/skill/workflow/...</li>'
         '<li><code>interpretation_protocol</code> + <code>revision_protocol</code> — กระบวนการ</li>'
         '</ul>',
         '<h2>รูปร่างของรายการ (pseudo-schema)</h2>',
         '<blockquote><p style="font-family:ui-monospace,monospace;">'
         'principle: { id, statement, rationale, scope[], counterexample, revision_trigger, stability }<br>'
         'equation:&nbsp; { id, name, expression, terms, meaning }<br>'
         'stability: [constitutional, high, medium, experimental]</p></blockquote>']
    if tfs or sl:
        items = []
        if tfs.get("recommended_words"):
            items.append("ความยาว ~%s คำ (%s บรรทัด · %s)" % (tfs.get("recommended_words"),
                          tfs.get("recommended_lines"), tfs.get("recommended_file_bytes")))
        if sl.get("core_principles"):
            items.append("หลักการ %s ข้อ · สมการ %s · ตัวอย่าง %s" % (sl.get("core_principles"),
                          sl.get("core_equations"), sl.get("application_examples")))
        p += ['<h2>ขนาดและขอบเขตที่แนะนำ</h2>', _ul(items)]
    if qc:
        p += ['<h2>เกณฑ์คุณภาพ (peer-review checklist)</h2>', _ul(qc)]
    p.append('<blockquote><p>ฉบับกลั่นที่ AI อ่านก่อน: '
             '<a href="books/person-reasoning/PRDFP.seed.yaml" target="_blank" rel="noopener">PRDFP.seed.yaml</a></p></blockquote>')
    return _mk("output-schema", "schema", 50, "ผลลัพธ์: ไฟล์ schema ที่ควรได้ตอนจบ",
               "เมื่อครบกระบวนการ ควรได้ไฟล์ schema รูปแบบนี้ — โครงสร้าง รูปร่างรายการ ขนาด และเกณฑ์คุณภาพ",
               p, ["schema", "ผลลัพธ์", "peer-review"], str(data.get("document", {}).get("last_reviewed_at", "")))


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
        "id": "philosophical-foundation", "cat": "philosophy", "featured": False, "sort": 3,
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
        "id": "core-equations", "cat": "equation", "featured": False, "sort": 4,
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
    # peer-reviewed elevation: position/distinctions before, protocol/examples/output-schema after
    return ([prf_identity(data), prf_distinctions(data)] + out
            + [prf_protocol(data), prf_examples(data), prf_output_schema(data)])


def build_references():
    """The closing chapter — cites every source back to its git origin."""
    seed_path = "books/%s/%s" % (BOOK["slug"], BOOK["seed"])
    body = [
        '<p>หนังสือเล่มนี้เรียบเรียงจากแหล่งต้นทางบน git ทั้งหมด ตามหลักของห้องสมุด — '
        '<strong>“รักษาที่มา ก่อนเพิ่มการตีความ”</strong> ทุกบทอ้างอิงกลับไปยังไฟล์ต้นทางได้</p>',
        '<h2>แหล่งต้นทาง (git)</h2>',
        '<ul>',
        '<li><strong>หนังสือต้นทาง</strong> — '
        '<a href="%s" target="_blank" rel="noopener">morrocwi/cpg_book</a> '
        '· ห้องสมุดความรู้ของ Yaoharee Lahtee และ Walancha</li>' % BOOK["source_repo"],
        '<li><strong>ไฟล์รากฐาน (PRF-001)</strong> — '
        '<a href="%s" target="_blank" rel="noopener">personal_reasoning/00_PERSONAL_REASONING_FOUNDATION_AND_PROTOCOL.yaml</a> '
        '· ที่มาของ 7 ฐานปรัชญา · 6 สมการ · 10 หลักการ</li>' % gh_blob(PR_SRC),
        '<li><strong>เว็บ + ไฟล์ตั้งต้น</strong> — '
        '<a href="%s" target="_blank" rel="noopener">morrocwi/cpg_bookweb</a></li>' % BOOK["repo"],
        '<li><strong>ไฟล์ตั้งต้นสำหรับ AI (seed)</strong> — '
        '<a href="%s" target="_blank" rel="noopener">PRDFP.seed.yaml</a> '
        '· สมการ + pseudo-schema ที่ให้ AI อ่านก่อน</li>' % seed_path,
        '</ul>',
        '<h2>ติดตั้ง / ดึงผ่าน git</h2>',
        '<p>โคลนหนังสือต้นทาง หรือดึงเฉพาะไฟล์ตั้งต้นสำหรับ AI:</p>',
        '<blockquote><p><code>git clone %s.git</code><br>'
        '<code>curl -O %s</code></p></blockquote>' % (BOOK["source_repo"], BOOK["seed_url"]),
        '<h2>ผู้เขียน & เจ้าของบริบท</h2>',
        '<p><strong>ผู้เขียน:</strong> %s, %s</p>' % (BOOK["author"], BOOK["year"]),
        '<p>Yaoharee Lahtee · Walancha — เจ้าของประสบการณ์ บริบท และความหมายที่ถูกกลั่นเป็นองค์ความรู้นี้ '
        '(บุคคลไม่เท่ากับแบบจำลอง: <code>PR_t ≠ Person</code>)</p>',
        '<h2>วิธีอ้างอิง</h2>',
        '<blockquote><p>%s, %s. <em>Person Reasoning Design Foundation and Protocol.</em> '
        'ปรัชญาปัญญาประดิษฐ์ (cpg_bookweb). เรียบเรียงจาก morrocwi/cpg_book · PRF-001.</p></blockquote>'
        % (BOOK["author"], BOOK["year"]),
    ]
    return {
        "id": "references", "cat": "reference", "featured": False, "sort": 900,
        "title": "บทอ้างอิง — ที่มาทั้งหมดบน git",
        "excerpt": "แหล่งที่มาทั้งหมดของหนังสือ อ้างอิงกลับไปยัง git ต้นทาง พร้อมวิธีติดตั้งผ่าน git",
        "body_html": "\n".join(body),
        "tags": ["อ้างอิง", "git", "ที่มา"],
        "read_minutes": 1,
        "source": "README.md", "source_id": "REFERENCES", "lang": "th-en",
    }


def build(book_dir):
    articles = [build_about(book_dir)] + build_from_prf(book_dir) + [build_references()]
    articles.sort(key=lambda a: a.get("sort", 999))
    for a in articles:
        a["book_id"] = BOOK["slug"]
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
            "id", "book_id", "cat", "title", "excerpt", "body_html", "tags",
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


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--book-dir", default=os.environ.get("CPG_BOOK_DIR", "."))
    ap.add_argument("--web-root", default=os.path.join(os.path.dirname(__file__), ".."),
                    help="cpg_bookweb root; writes books/<slug>/book.json and library.json")
    ap.add_argument("--push-supabase", action="store_true")
    args = ap.parse_args()

    bundle = build(args.book_dir)
    web_root = os.path.abspath(args.web_root)
    slug = BOOK["slug"]

    # one folder = one book
    book_json = os.path.join(web_root, "books", slug, "book.json")
    write_json(book_json, bundle)

    # library index (lists the books; currently one)
    library = {
        "generated_at": bundle["generated_at"],
        "library": LIBRARY,
        "books": [{
            "slug": slug,
            "title": BOOK["title"],
            "title_th": BOOK["title_th"],
            "accent": BOOK["accent"],
            "summary": BOOK["summary"],
            "chapters": len(bundle["articles"]),
            "data": f"books/{slug}/book.json",
            "seed": f"books/{slug}/{BOOK['seed']}",
            "source_repo": "morrocwi/cpg_book",
        }],
    }
    write_json(os.path.join(web_root, "library.json"), library)

    print(f"[build] library '{LIBRARY['brand']}' · 1 book · {len(bundle['articles'])} chapters")
    print(f"   -> {book_json}")
    print(f"   -> {os.path.join(web_root, 'library.json')}")
    for a in bundle["articles"]:
        print(f"   - [{a['cat']:10}] {a['id']:24} {a['title']}")

    if args.push_supabase:
        push_supabase(bundle["articles"])


if __name__ == "__main__":
    main()
