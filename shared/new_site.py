#!/usr/bin/env python3
"""
new_site.py — scaffold a new website in the hub (1 folder = 1 site) and register it.

Usage:
  python shared/new_site.py <slug> "<Title>" [--title-th "..."] [--accent "#0ea5e9"]

Creates sites/<slug>/ from sites/_TEMPLATE/, fills site.json, and appends an entry
to sites.json. Idempotent-ish: refuses to overwrite an existing site folder.
"""
import argparse, json, os, re, shutil, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))   # cpg_bookweb/
TEMPLATE = os.path.join(ROOT, "sites", "_TEMPLATE")
SITES_JSON = os.path.join(ROOT, "sites.json")


def slugify(s):
    s = re.sub(r"[^a-z0-9-]+", "-", s.strip().lower()).strip("-")
    return re.sub(r"-{2,}", "-", s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("title")
    ap.add_argument("--title-th", default="")
    ap.add_argument("--accent", default="#0ea5e9")
    args = ap.parse_args()

    slug = slugify(args.slug)
    if not slug:
        sys.exit("error: empty/invalid slug")
    dest = os.path.join(ROOT, "sites", slug)
    if os.path.exists(dest):
        sys.exit(f"error: sites/{slug} already exists")

    shutil.copytree(TEMPLATE, dest)
    os.remove(os.path.join(dest, "README.md"))  # template-only readme

    # fill site.json
    sj_path = os.path.join(dest, "site.json")
    sj = json.load(open(sj_path, encoding="utf-8"))
    sj.update({"slug": slug, "title": args.title, "title_th": args.title_th, "accent": args.accent})
    json.dump(sj, open(sj_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    # register in sites.json
    reg = json.load(open(SITES_JSON, encoding="utf-8"))
    base = reg.get("hub", {}).get("base_url", "").rstrip("/")
    if any(s.get("slug") == slug for s in reg.get("sites", [])):
        sys.exit(f"error: slug '{slug}' already registered in sites.json")
    reg.setdefault("sites", []).append({
        "slug": slug,
        "title": args.title,
        "kind": "site",
        "path": f"sites/{slug}",
        "url": f"{base}/sites/{slug}/",
        "data": "content.json",
        "supabase_table": sj["supabase"]["table"] or None,
        "status": "draft",
    })
    json.dump(reg, open(SITES_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    print(f"[new_site] created sites/{slug}/ and registered in sites.json")
    print( "  next:")
    print(f"    1) edit sites/{slug}/content.json (or set supabase in site.json)")
    print(f"    2) git add sites/{slug} sites.json && git commit -m 'feat(site): {slug}' && git push")
    print(f"    3) live at {base}/sites/{slug}/ after Pages redeploys")


if __name__ == "__main__":
    main()
