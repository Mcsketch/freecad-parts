"""Render thumbs/<folder>/<name>.png for every part and embed the same image in the .FCStd.
Needs the GUI: run inside FreeCAD (Macro editor, or `python3 themes/rpc.py tools/thumbs.py`
from the config repo). Skips parts whose png is newer than the FCStd unless FORCE = True.
Closes nothing of yours: it only opens/closes the library documents.
"""
import os
import FreeCAD
import FreeCADGui

ROOT = os.path.join(FreeCAD.getUserAppDataDir(), "Mod", "parts_library")
FORCE = False
SIZE = 256


def main():
    n = 0
    for d, dirs, files in os.walk(ROOT):
        dirs[:] = [x for x in dirs if not x.startswith(".") and x not in ("tools", "thumbs")]
        for f in files:
            if not f.lower().endswith(".fcstd"):
                continue
            src = os.path.join(d, f)
            rel = os.path.relpath(src, ROOT)[:-6]
            png = os.path.join(ROOT, "thumbs", rel + ".png")
            if not FORCE and os.path.exists(png) and os.path.getmtime(png) > os.path.getmtime(src):
                continue
            os.makedirs(os.path.dirname(png), exist_ok=True)
            doc = FreeCAD.openDocument(src)
            FreeCADGui.ActiveDocument = FreeCADGui.getDocument(doc.Name)
            for o in doc.Objects:
                o.Visibility = True
            v = FreeCADGui.ActiveDocument.ActiveView
            v.viewIsometric()
            v.fitAll()
            FreeCADGui.updateGui()
            v.saveImage(png, SIZE, SIZE, "Current")
            doc.save()  # SaveThumbnail is on: embeds thumbnails/Thumbnail.png too
            FreeCAD.closeDocument(doc.Name)
            n += 1
    print("rendered %d thumbnails" % n)


main()
