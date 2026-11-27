"""Builds MoodyFin's Kodi add-on repository (what GitHub Pages serves at https://moodyjim.github.io/moodyfin/).

    python tools/build_repo.py [out_dir]        (default: _site)

out_dir/
    addons.xml, addons.xml.md5                  the index Kodi reads (repository.moodyfin points at it)
    <id>/<id>-<version>.zip                     each add-on, one top folder named after its id
    <id>/<asset paths>                          icon / fanart, where Kodi looks for them in a zipped repo
    repository.moodyfin-<version>.zip           the same repository zip at the top, for Kodi's "Install from zip file"
    index.html                                  a plain link list (Kodi's file manager can browse it as a source)

Run by .github/workflows/pages.yml for every version tag. Leaves out __pycache__ and *.pyc.
"""
import hashlib
import os
import re
import shutil
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
ADDONS = ["repository.moodyfin", "skin.moodyfin", "script.moodyfin.helper"]
SKIP_DIRS = {"__pycache__", ".git"}
SKIP_EXT = (".pyc", ".pyo")


def addon_info(folder):
    tree = ET.parse(os.path.join(ROOT, folder, "addon.xml"))
    a = tree.getroot()
    assets = []
    for meta in a.iter("assets"):
        assets += [e.text.strip() for e in meta if e.text and e.text.strip()]
    return a.get("id"), a.get("version"), assets


def zip_addon(folder, aid, version, dest):
    path = os.path.join(dest, aid, "%s-%s.zip" % (aid, version))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    src = os.path.join(ROOT, folder)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for base, dirs, files in os.walk(src):
            dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
            for f in sorted(files):
                if f.endswith(SKIP_EXT):
                    continue
                full = os.path.join(base, f)
                z.write(full, os.path.join(aid, os.path.relpath(full, src)).replace(os.sep, "/"))
    return path


def addon_xml_body(folder):
    raw = open(os.path.join(ROOT, folder, "addon.xml"), encoding="utf-8").read()
    raw = re.sub(r"^\s*<\?xml[^>]*\?>\s*", "", raw)
    return raw.strip()


def main(out):
    out = os.path.abspath(out)
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(out)
    bodies, links = [], []
    for folder in ADDONS:
        aid, version, assets = addon_info(folder)
        z = zip_addon(folder, aid, version, out)
        for asset in assets:
            src = os.path.join(ROOT, folder, asset)
            if os.path.isfile(src):
                dst = os.path.join(out, aid, asset)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
        bodies.append(addon_xml_body(folder))
        links.append((aid, version, os.path.relpath(z, out).replace(os.sep, "/")))
        if aid == "repository.moodyfin":
            shutil.copy2(z, os.path.join(out, os.path.basename(z)))
        print("%-26s %-8s %7.1f MB" % (aid, version, os.path.getsize(z) / 1048576.0))
    xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<addons>\n%s\n</addons>\n' % "\n".join(bodies)
    with open(os.path.join(out, "addons.xml"), "w", encoding="utf-8", newline="\n") as f:
        f.write(xml)
    with open(os.path.join(out, "addons.xml.md5"), "w", encoding="utf-8", newline="\n") as f:
        f.write(hashlib.md5(xml.encode("utf-8")).hexdigest())
    repo = next(l for l in links if l[0] == "repository.moodyfin")
    # the repository zip is listed once (its top-level copy); the add-ons are installed through it
    rows = "\n".join('<li><a href="%s">%s</a> %s</li>' % (p, os.path.basename(p), v) for i, v, p in links
                     if i != "repository.moodyfin")
    html = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>MoodyFin for Kodi</title></head>
<body style="font-family:sans-serif;max-width:720px;margin:40px auto;padding:0 16px;background:#000;color:#f1f2f4">
<h1>MoodyFin</h1>
<p>The Jellyfin theme's look for Kodi 21. In Kodi: <i>Settings &gt; File manager &gt; Add source</i>, enter this page's
address, then <i>Add-ons &gt; Install from zip file</i> and pick
<b>{name}</b>. Then <i>Install from repository &gt; MoodyFin Repository</i>.</p>
<ul>
<li><a href="{repo}" style="color:#5CD8FA">{name}</a></li>
{rows}
</ul>
<p><a href="https://github.com/moodyjim/moodyfin" style="color:#5CD8FA">Source on GitHub</a></p>
</body></html>
""".format(repo=os.path.basename(repo[2]), name=os.path.basename(repo[2]), rows=rows)
    with open(os.path.join(out, "index.html"), "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    open(os.path.join(out, ".nojekyll"), "w").close()
    print("wrote", out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "_site"))
