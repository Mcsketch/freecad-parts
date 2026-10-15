# freecad-parts

My FreeCAD parts library: the off-the-shelf things I design around (heat-set inserts,
bearings, magnets, cells, dev boards, fans, switches, nuts, stock). Every part is one
`.FCStd` with a single solid, origin on its natural mounting datum, and its key dimensions
in the document Comment (visible in the browser and in [CATALOG.md](CATALOG.md)).

## Use
Clone into the FreeCAD config dir so the browser and the FreeCADMCP addon both find it:

    git clone https://github.com/Mcsketch/freecad-parts "%APPDATA%\FreeCAD\v1-1\Mod\parts_library"

Then in FreeCAD (with [Mcsketch/freecad](https://github.com/Mcsketch/freecad) config restored):
**Shop toolbar → Parts library** or **Ctrl+Alt+L**, filter, pick, **Insert**. The part is
merged into the active document as a `Part::Feature`; move it with Placement or drop it into
an assembly. **Open** loads the file itself for editing. Another library folder:
`Folder…` in the dialog (stored in Preferences/Mod/PartsLibrary/Path).

## Layout
| Folder | Contents |
|---|---|
| `inserts/` | heat-set inserts M2–M5 (hole = OD, depth = length + 1) |
| `bearings/` | 623, MR105, 625, 688, 608, 6001, 6805 |
| `magnets/` | discs 5×2 … 12×3, 5 mm cube |
| `cells/` | AAA, AA, 18650, 21700, CR2032, 9 V |
| `boards/` | Pi 4, Pi Pico, Arduino Uno, ESP32 DevKitC, 0.96" OLED (outline + holes only) |
| `fans/` | 25, 30, 40, 60, 80, 120 mm axial |
| `electronics/` | KCD1 rocker, 6×6 tactile, 5 mm LED, DC jack, buzzer, SG90, NEMA 17 |
| `hardware/` | hex nuts M3–M5, M3 square nut, washers (nut-trap sizing) |
| `stock/` | 2020/2040 extrusion, 2×4, 1×4, 12/18 mm ply, dowels |
| `thumbs/` | 256 px renders, one per part (`tools/thumbs.py`) |
| `tools/` | `gen_parts.py` (regenerates every starter part headless), `thumbs.py`, `catalog.py` |

Screws and bolts are not here: the Fasteners addon does those parametrically.

## Add a part
1. Model it (or import a STEP from the vendor), one solid, sensible origin, millimetres.
2. Set the document Label and write the dimensions in the document Comment
   (`File → Project information`), save as `<folder>/<Name>.FCStd`.
3. `tools/thumbs.py` inside FreeCAD, `python3 tools/catalog.py`, commit.

Starter parts come from `tools/gen_parts.py`:
`FreeCADCmd.exe tools/gen_parts.py` regenerates them all (edit the tables in that file).
Dimensions are nominal datasheet values; check press fits against your printer.
