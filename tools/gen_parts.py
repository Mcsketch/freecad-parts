"""Generate the starter parts as .FCStd files. Headless:

    FreeCADCmd.exe tools/gen_parts.py            (writes into <FreeCAD config>/Mod/parts_library)
    PARTS_OUT=<dir> FreeCADCmd.exe tools/gen_parts.py

Each file holds one Part::Feature solid, origin at the part's natural mounting datum (boards:
corner, bottom of PCB; round parts: axis = Z, bottom face at Z=0). doc.Comment carries the key
dimensions and doc.Meta the machine-readable ones; tools/catalog.py turns them into CATALOG.md.
Thumbnails are rendered separately in the GUI (tools/thumbs.py). Re-running overwrites.
"""
import math
import os
import FreeCAD
import Part
from FreeCAD import Vector as V

OUT = os.environ.get("PARTS_OUT") or os.path.join(FreeCAD.getUserAppDataDir(), "Mod", "parts_library")
PARTS = []  # (folder, name, label, comment, meta, shape_fn)


def part(folder, name, label, comment, **meta):
    def deco(fn):
        PARTS.append((folder, name, label, comment, {k: str(v) for k, v in meta.items()}, fn))
        return fn
    return deco


# ---- helpers ------------------------------------------------------------------------------
def cyl(d, h, z=0):
    return Part.makeCylinder(d / 2.0, h, V(0, 0, z))


def tube(od, idm, h, z=0):
    return cyl(od, h, z).cut(cyl(idm, h, z))


def box(l, w, h, x=0, y=0, z=0):
    return Part.makeBox(l, w, h, V(x, y, z))


def rbox(l, w, h, r):
    """Box with the four vertical edges rounded (fans, boards)."""
    b = box(l, w, h)
    edges = [e for e in b.Edges if abs(e.tangentAt(e.FirstParameter).z) > 0.99]
    return b.makeFillet(r, edges)


def chamfer_ends(shape, size):
    try:
        edges = [e for e in shape.Edges if e.Curve.__class__.__name__ == "Circle" and abs(e.tangentAt(e.FirstParameter).z) < 1e-6]
        return shape.makeChamfer(size, edges)
    except Exception:
        return shape


def holes(shape, d, pts, h=100, z=-50):
    for x, y in pts:
        shape = shape.cut(Part.makeCylinder(d / 2.0, h, V(x, y, z)))
    return shape


def hexprism(af, h, bore=0):
    r = af / math.sqrt(3)
    pts = [V(r * math.cos(math.radians(60 * i)), r * math.sin(math.radians(60 * i)), 0) for i in range(6)]
    s = Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(V(0, 0, h))
    return s.cut(cyl(bore, h)) if bore else s


# ---- inserts (heat-set, brass) ------------------------------------------------------------
for m, od, L in ((2, 3.2, 4.0), (2.5, 3.5, 4.0), (3, 4.0, 4.0), (3, 4.0, 5.7), (4, 5.6, 8.1), (5, 6.4, 9.5)):
    def _ins(od=od, L=L, m=m):
        s = tube(od, m - 0.3, L)
        return chamfer_ends(s, 0.15)
    part("inserts", "Insert_M%g_%gx%g" % (m, od, L), "Heat-set insert M%g %g×%g" % (m, od, L),
         "Heat-set insert M%g, OD %g mm, length %g mm. Print hole: %g mm dia, %g mm deep (+1 mm)." % (m, od, L, od, L),
         thread="M%g" % m, od=od, length=L, hole=od)(_ins)

# ---- bearings -----------------------------------------------------------------------------
for name, idm, od, w in (("623", 3, 10, 4), ("MR105", 5, 10, 4), ("625", 5, 16, 5), ("688", 8, 16, 5),
                         ("608", 8, 22, 7), ("6001", 12, 28, 8), ("6805", 25, 37, 7)):
    def _brg(idm=idm, od=od, w=w):
        wall = (od - idm) / 4.5
        outer = chamfer_ends(tube(od, od - 2 * wall, w), 0.3)
        inner = chamfer_ends(tube(idm + 2 * wall, idm, w), 0.3)
        shield = tube(od - 2 * wall + 0.4, idm + 2 * wall - 0.4, w * 0.5, w * 0.25)
        return outer.fuse([inner, shield]).removeSplitter()
    part("bearings", "Bearing_%s" % name, "Bearing %s (%g×%g×%g)" % (name, idm, od, w),
         "Ball bearing %s: bore %g mm, OD %g mm, width %g mm. Press-fit pocket: OD −0.1 mm." % (name, idm, od, w),
         bore=idm, od=od, width=w)(_brg)

# ---- magnets ------------------------------------------------------------------------------
for d, h in ((5, 2), (6, 3), (8, 3), (10, 2), (10, 3), (12, 3)):
    part("magnets", "Magnet_%gx%g" % (d, h), "Magnet disc %g×%g" % (d, h),
         "Neodymium disc magnet %g mm dia × %g mm. Press pocket: +0.1–0.2 mm dia." % (d, h), dia=d, height=h)(
        lambda d=d, h=h: cyl(d, h))
part("magnets", "Magnet_Cube_5", "Magnet cube 5 mm", "Neodymium cube magnet 5×5×5 mm.", size=5)(lambda: box(5, 5, 5, -2.5, -2.5))

# ---- cells ----------------------------------------------------------------------------------
for name, d, h in (("AAA", 10.5, 44.5), ("AA", 14.5, 50.5), ("18650", 18.4, 65.0), ("21700", 21.2, 70.2)):
    part("cells", "Cell_%s" % name, "Cell %s (%g×%g)" % (name, d, h),
         "%s cell %g mm dia × %g mm incl. button top. Holder bore: +0.4 mm." % (name, d, h), dia=d, length=h)(
        lambda d=d, h=h: cyl(d, h - 1.0).fuse(cyl(d * 0.35, 1.0, h - 1.0)))
part("cells", "Cell_CR2032", "Coin cell CR2032", "CR2032 coin cell 20 mm dia × 3.2 mm.", dia=20, height=3.2)(lambda: cyl(20, 3.2))
part("cells", "Cell_9V", "9 V block", "9 V block 26.5 × 17.5 × 48.5 mm (snap terminals excluded).", l=26.5, w=17.5, h=48.5)(
    lambda: box(26.5, 17.5, 48.5))

# ---- boards (origin = bottom-left corner, PCB bottom face at Z=0) ------------------------------
BOARDS = (
    ("RaspberryPi_4", "Raspberry Pi 4 B", 85, 56, 1.6, 2.7, [(3.5, 3.5), (61.5, 3.5), (3.5, 52.5), (61.5, 52.5)], 3.0),
    ("RaspberryPi_Pico", "Raspberry Pi Pico", 51, 21, 1.0, 2.1, [(2, 4.8), (2, 16.2), (49, 4.8), (49, 16.2)], 1.0),
    ("Arduino_Uno", "Arduino Uno R3", 68.6, 53.3, 1.6, 3.2, [(14.0, 2.5), (15.3, 50.7), (66.1, 7.6), (66.1, 35.5)], 2.0),
    ("ESP32_DevKitC", "ESP32 DevKitC", 55, 28, 1.6, 0, [], 1.0),
    ("OLED_0.96_SSD1306", "OLED 0.96\" SSD1306 module", 27.3, 27.8, 1.2, 2.0, [(2.0, 2.0), (25.3, 2.0), (2.0, 25.8), (25.3, 25.8)], 1.0),
)
for name, label, l, w, t, hd, pts, r in BOARDS:
    def _board(l=l, w=w, t=t, hd=hd, pts=pts, r=r):
        s = rbox(l, w, t, r) if r else box(l, w, t)
        return holes(s, hd, pts) if pts else s
    hole_txt = (", %d holes %g mm at %s" % (len(pts), hd, ", ".join("(%g, %g)" % p for p in pts))) if pts else ", no mounting holes"
    part("boards", name, label, "%s PCB outline %g × %g × %g mm%s. Origin: corner, PCB underside." % (label, l, w, t, hole_txt),
         l=l, w=w, t=t, hole=hd, holes=";".join("%g,%g" % p for p in pts))(_board)

# ---- fans (origin = corner, frame on Z=0) ----------------------------------------------------------
for size, depth, hd, pitch in ((25, 10, 2.9, 20), (30, 10, 3.0, 24), (40, 10, 4.3, 32), (60, 15, 4.3, 50), (80, 25, 4.3, 71.5), (120, 25, 4.3, 105)):
    def _fan(size=size, depth=depth, hd=hd, pitch=pitch):
        o = (size - pitch) / 2.0
        frame = rbox(size, size, depth, 3.0)
        frame = frame.cut(Part.makeCylinder(size * 0.47, depth, V(size / 2.0, size / 2.0, 0)))
        hub = Part.makeCylinder(size * 0.17, depth, V(size / 2.0, size / 2.0, 0))
        return holes(frame.fuse(hub), hd, [(o, o), (size - o, o), (o, size - o), (size - o, size - o)])
    part("fans", "Fan_%dx%dx%d" % (size, size, depth), "Fan %d×%d×%d" % (size, size, depth),
         "Axial fan %d × %d × %d mm, 4 holes %g mm on %g mm square. Grill cutout: %g mm dia." % (size, size, depth, hd, pitch, size * 0.94),
         size=size, depth=depth, hole=hd, pitch=pitch)(_fan)

# ---- electronics -----------------------------------------------------------------------------
part("electronics", "Rocker_KCD1", "Rocker switch KCD1", "KCD1 rocker: body 19 × 13 mm below a 21 × 15 × 2 mm bezel, 12 mm deep. Panel cutout 19.2 × 13.2 mm.",
     cutout="19.2x13.2")(lambda: box(19, 13, 12, 1, 1, -12).fuse(box(21, 15, 2)))
part("electronics", "Tactile_6x6x5", "Tactile switch 6×6×5", "Tactile button 6 × 6 mm, 5 mm tall incl. 3.5 mm dia plunger (1.5 mm above body).", size=6, height=5)(
    lambda: box(6, 6, 3.5, -3, -3).fuse(cyl(3.5, 1.5, 3.5)))
part("electronics", "LED_5mm", "LED 5 mm", "5 mm LED: 5 mm dome, 8.6 mm tall, 5.8 × 1 mm flange at the base. Panel hole 5.1 mm.", dia=5, height=8.6)(
    lambda: cyl(5.8, 1.0).fuse(cyl(5, 6.1, 1.0)).fuse(Part.makeSphere(2.5, V(0, 0, 7.1))))
part("electronics", "DC_Jack_5.5x2.1_Panel", "DC jack 5.5×2.1 panel", "Panel-mount DC barrel jack 5.5 × 2.1: M8 bushing (8 mm hole, 10 mm long), 14 mm body behind the panel.",
     hole=8)(lambda: cyl(8, 10).fuse(cyl(11, 14, -14)))
part("electronics", "Buzzer_12mm", "Buzzer 12 mm", "Piezo/active buzzer 12 mm dia × 9.5 mm, pins 7.6 mm apart.", dia=12, height=9.5)(lambda: cyl(12, 9.5))
part("electronics", "Servo_SG90", "Servo SG90", "SG90 micro servo: body 22.5 × 12.2 × 22.7 mm, ears 32.2 mm wide, 2 mm holes 27.5 mm apart at 16.5 mm up. Origin: body corner.",
     l=22.5, w=12.2, h=22.7, ear=32.2, hole=2, pitch=27.5)(
    lambda: holes(box(22.5, 12.2, 22.7).fuse(box(32.2, 12.2, 2.5, -4.85, 0, 16.5)), 2.0, [(-2.5, 6.1), (25.0, 6.1)]))
part("electronics", "Stepper_NEMA17_40", "Stepper NEMA 17 (40 mm)", "NEMA 17 stepper: 42.3 mm square × 40 mm, 4× M3 on 31 mm square, 22 mm × 2 mm boss, 5 mm shaft 24 mm long. Origin: body corner, shaft up.",
     size=42.3, length=40, pitch=31, boss=22, shaft=5)(
    lambda: holes(rbox(42.3, 42.3, 40, 5.0), 3.0, [(5.65, 5.65), (36.65, 5.65), (5.65, 36.65), (36.65, 36.65)], h=5, z=40 - 4.5)
    .fuse(Part.makeCylinder(11, 2, V(21.15, 21.15, 40))).fuse(Part.makeCylinder(2.5, 24, V(21.15, 21.15, 40))))

# ---- hardware (plain solids for nut traps / washers) --------------------------------------------
for m, af, h in ((3, 5.5, 2.4), (4, 7.0, 3.2), (5, 8.0, 4.7)):
    part("hardware", "Nut_M%d_Hex" % m, "Hex nut M%d" % m, "Hex nut M%d: %g mm across flats, %g mm thick. Nut trap: AF +0.3 mm." % (m, af, h),
         thread="M%d" % m, af=af, height=h)(lambda m=m, af=af, h=h: hexprism(af, h, m))
part("hardware", "Nut_M3_Square", "Square nut M3", "Square nut M3 DIN 562: 5.5 × 5.5 × 1.8 mm. Trap: 5.8 mm.", size=5.5, height=1.8)(
    lambda: box(5.5, 5.5, 1.8, -2.75, -2.75).cut(cyl(3, 1.8)))
for m, od, t in ((3, 7, 0.5), (4, 9, 0.8), (5, 10, 1.0)):
    part("hardware", "Washer_M%d" % m, "Washer M%d" % m, "Washer M%d DIN 125: %g mm OD × %g mm thick." % (m, od, t), od=od, t=t)(
        lambda m=m, od=od, t=t: tube(od, m + 0.3, t))

# ---- stock ------------------------------------------------------------------------------------
def extrusion(w, h, L):
    s = box(w, h, L, -w / 2.0, -h / 2.0)
    for cx in [i * 20 - (w / 2.0 - 10) for i in range(int(w / 20))]:
        s = s.cut(box(6, 6, L, cx - 3, h / 2.0 - 6)).cut(box(6, 6, L, cx - 3, -h / 2.0))
        s = s.cut(Part.makeCylinder(2.1, L, V(cx, 0, 0)))
    for cy in [i * 20 - (h / 2.0 - 10) for i in range(int(h / 20))]:
        s = s.cut(box(6, 6, L, w / 2.0 - 6, cy - 3)).cut(box(6, 6, L, -w / 2.0, cy - 3))
    return s

part("stock", "Extrusion_2020_100", "2020 extrusion 100 mm", "20 × 20 aluminium extrusion, 100 mm, 6 mm slots (simplified), 4.2 mm core hole. Axis = Z.", w=20, h=20, L=100)(lambda: extrusion(20, 20, 100))
part("stock", "Extrusion_2040_100", "2040 extrusion 100 mm", "20 × 40 aluminium extrusion, 100 mm, 6 mm slots (simplified). Axis = Z.", w=20, h=40, L=100)(lambda: extrusion(20, 40, 100))
part("stock", "Lumber_2x4_300", "2×4 lumber 300 mm", "Nominal 2×4: 38 × 89 mm actual, 300 mm long. Axis = Z.", w=38, h=89, L=300)(lambda: box(38, 89, 300))
part("stock", "Lumber_1x4_300", "1×4 lumber 300 mm", "Nominal 1×4: 19 × 89 mm actual, 300 mm long. Axis = Z.", w=19, h=89, L=300)(lambda: box(19, 89, 300))
part("stock", "Ply_18_100x100", "Plywood 18 mm", "18 mm plywood offcut 100 × 100 mm.", t=18)(lambda: box(100, 100, 18))
part("stock", "Ply_12_100x100", "Plywood 12 mm", "12 mm plywood offcut 100 × 100 mm.", t=12)(lambda: box(100, 100, 12))
for d in (6, 8):
    part("stock", "Dowel_%d_100" % d, "Dowel %d mm" % d, "Hardwood dowel %d mm dia, 100 mm. Hole: %g mm." % (d, d + 0.2), dia=d, L=100)(lambda d=d: cyl(d, 100))


# ---- write ---------------------------------------------------------------------------------------
def main():
    n = 0
    for folder, name, label, comment, meta, fn in PARTS:
        d = os.path.join(OUT, folder)
        os.makedirs(d, exist_ok=True)
        doc = FreeCAD.newDocument(name)
        doc.Label = label
        doc.Comment = comment
        try:
            doc.Meta = meta
        except Exception:
            pass
        obj = doc.addObject("Part::Feature", name)
        obj.Label = label
        obj.Shape = fn()
        obj.Visibility = True  # headless default is hidden, which would also hide the part on insert
        doc.recompute()
        path = os.path.join(d, name + ".FCStd")
        doc.saveAs(path)
        FreeCAD.closeDocument(doc.Name)
        n += 1
    print("wrote %d parts under %s" % (n, OUT))


main()
