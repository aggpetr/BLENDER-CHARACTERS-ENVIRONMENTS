from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table,
                                TableStyle, PageBreak, Image, KeepTogether)
import sys

OUT = sys.argv[1]
SHEET = sys.argv[2]

INK = colors.HexColor("#1f2937")
ACCENT = colors.HexColor("#8b2e2e")
MUTED = colors.HexColor("#6b7280")
HEAD_BG = colors.HexColor("#2b2b2b")
ROW_ALT = colors.HexColor("#f3f1ee")
OK = colors.HexColor("#2f6b3a")
WARN = colors.HexColor("#9a5b00")

ss = getSampleStyleSheet()
body = ParagraphStyle("body", parent=ss["Normal"], fontName="Helvetica", fontSize=9.5, leading=13.2, textColor=INK, spaceAfter=5)
small = ParagraphStyle("small", parent=body, fontSize=8.3, leading=11, spaceAfter=2)
cell = ParagraphStyle("cell", parent=body, fontSize=8.4, leading=10.8, spaceAfter=0)
cellb = ParagraphStyle("cellb", parent=cell, fontName="Helvetica-Bold")
cellh = ParagraphStyle("cellh", parent=cell, fontName="Helvetica-Bold", textColor=colors.white)
h1 = ParagraphStyle("h1", parent=ss["Heading1"], fontName="Helvetica-Bold", fontSize=15.5, leading=19, textColor=ACCENT, spaceBefore=12, spaceAfter=6)
h2 = ParagraphStyle("h2", parent=ss["Heading2"], fontName="Helvetica-Bold", fontSize=11.2, leading=14, textColor=INK, spaceBefore=8, spaceAfter=4)
title = ParagraphStyle("title", parent=ss["Title"], fontName="Helvetica-Bold", fontSize=26, leading=30, textColor=INK, alignment=0, spaceAfter=4)
subtitle = ParagraphStyle("subtitle", parent=body, fontSize=12, leading=16, textColor=MUTED, spaceAfter=10)
bullet = ParagraphStyle("bullet", parent=body, leftIndent=14, bulletIndent=3, spaceAfter=2.5)

def P(t, s=body): return Paragraph(t, s)
def B(items): return [Paragraph(i, bullet, bulletText="•") for i in items]

def table(rows, widths, header=True, zebra=True, bold_first=False):
    data = []
    for ri, r in enumerate(rows):
        out = []
        for ci, c in enumerate(r):
            if isinstance(c, str):
                st = cellh if (header and ri == 0) else (cellb if (bold_first and ci == 0) else cell)
                out.append(Paragraph(c, st))
            else:
                out.append(c)
        data.append(out)
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    style = [("VALIGN", (0, 0), (-1, -1), "TOP"),
             ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
             ("TOPPADDING", (0, 0), (-1, -1), 3.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
             ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#d6d3ce"))]
    if header: style.append(("BACKGROUND", (0, 0), (-1, 0), HEAD_BG))
    if zebra:
        for i in range(1 if header else 0, len(rows)):
            if i % 2 == 0: style.append(("BACKGROUND", (0, i), (-1, i), ROW_ALT))
    t.setStyle(TableStyle(style))
    return t

def on_page(c, doc):
    c.saveState()
    c.setFont("Helvetica", 7.8); c.setFillColor(MUTED)
    c.drawString(2 * cm, 1.2 * cm, "Edo Village House Kit - Deliverables Specification")
    c.drawRightString(A4[0] - 2 * cm, 1.2 * cm, "Page %d" % doc.page)
    c.setStrokeColor(colors.HexColor("#d6d3ce")); c.setLineWidth(0.5)
    c.line(2 * cm, 1.6 * cm, A4[0] - 2 * cm, 1.6 * cm)
    c.restoreState()

doc = BaseDocTemplate(OUT, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.9 * cm, bottomMargin=2.1 * cm,
                      title="Edo Village House Kit - Deliverables Specification", author="Claude Code",
                      subject="What the finished modular house kit will contain")
frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")
doc.addPageTemplates([PageTemplate(id="p", frames=[frame], onPage=on_page)])
W = doc.width
s = []

# ---------------------------------------------------------------- cover
s += [Spacer(1, 1.2 * cm), P("Edo Village House Kit", title),
      P("Deliverables specification: everything the finished result will contain", subtitle),
      table([["Source scene", "Feudal_Japan4 - Copy.blend (Blender 5.2.2), 94 procedural houses, 17 designs"],
             ["Target engine", "Unreal Engine 5.8, PC, Nanite meshes, no LODs"],
             ["Style", "Edo-period Japanese village: tile hip roofs, thatched gable roofs, timber frame, plaster walls, stilted foundations"],
             ["Quality goal", "Game-ready, heavily optimized, as realistic as procedural + CC0 photo textures allow"],
             ["Status", "Built: 86 modules, GN_EdoKitHouse, all 17 designs, whole village rebuilt in place. Unreal side untested. See kit/KIT_REPORT.md."]],
            [3.2 * cm, W - 3.2 * cm], header=False, zebra=True, bold_first=True),
      Spacer(1, 0.5 * cm),
      P("<b>How to read this document.</b> Items marked <b>Agreed</b> were confirmed by you. Items marked <b>Proposed</b> are my defaults "
        "(you asked me to use my recommendations) and can still change. Section 9 lists what I can and cannot verify from this cloud "
        "container, and section 10 lists open risks. Nothing here has been built yet, so no figure for the finished kit is a measurement; "
        "figures about the existing scene are measured and come from the analysis report."),
      Spacer(1, 0.3 * cm), Image(SHEET, width=W, height=W * 0.75),
      P("One house of each type, rendered from the source scene (numbers are how many of each exist in the village).", small),
      PageBreak()]

# ---------------------------------------------------------------- 1 summary
s += [P("1. What you will receive", h1),
      P("The result is a modular kit that rebuilds your village houses from a small set of reusable, grid-snapped pieces, "
        "with real textures and clean UVs, exported for Unreal Engine 5.8. It replaces the current box-based procedural geometry "
        "(unoptimized, no UVs, no textures) with properly modelled, texture-based pieces."),
      table([["#", "Deliverable", "Format / location", "Notes"],
             ["1", "Modular kit scene", ".blend (Blender 5.2), repo folder <i>kit/</i>", "All modules in one organized scene: collections per module family, named, origin-set, grid-snapped."],
             ["2", "Per-module meshes", ".fbx, one file per module, <i>export/fbx/</i>", "Unreal-ready scale and axes, Nanite-friendly. No LODs. Collision added later."],
             ["3", "Kit geometry nodes (new)", "Node group <i>GN_EdoKitHouse</i> + helpers, inside the kit .blend",
              "New geometry nodes built from the kit meshes from the start. Same style of inputs as your generator (Bays X/Y, Floors, Roof style, Shopfront, Engawa, Balcony, Lanterns, Gate, Fence, Props) plus a variant seed. Instances the kit modules. Your existing <i>GN_EdoHouse</i> is not modified."],
             ["4", "Textures", "PNG, <i>kit/textures/</i> (and <i>export/textures/</i>)", "Shared 4K sets for the main materials, 2K for minor ones. BaseColor, Normal (DirectX), packed ORM, plus emissive where needed."],
             ["5", "Assembly manifest", ".json, <i>export/manifest.json</i>", "For each of the 94 houses: which modules, where, rotation. Rebuilds the village from the kit."],
             ["6", "Unreal import helper", ".py script for the UE Python console", "Imports FBX/textures and (optionally) places houses from the manifest. <b>Untested</b>: I have no Unreal here."],
             ["7", "Preview renders", ".png, <i>previews/</i>", "Cycles renders of each module and each finished house type, for your review."],
             ["8", "Technical report", ".md in repo", "Measured triangle counts, UV/texel-density checks, texture list, naming, how to use the kit."],
             ["9", "Source scripts", ".py, <i>tools/</i>", "Everything used to build, bake and export, so it can be re-run."]],
            [0.7 * cm, 3.4 * cm, 5.1 * cm, W - 9.2 * cm]),
      P("Not included: collision meshes (to be done at the end, see section 6), LODs (not needed with Nanite), "
        "terrain, roads, fields, bridges and other non-house assets in the scene, the village layout solver (<i>GN_EdoVillage</i>, not rebuilt unless you ask), and any Unreal project or Blueprint files.", small),

      P("2. Houses covered", h1),
      P("The 94 houses are only 17 designs (the generator's parameters match exactly per design; the seed only jitters the footprint). "
        "The kit has to cover all 17. The first prototype is <b>dwellA</b>, then <b>kura</b>, then the thatched types, then the rest."),
      table([["Design", "Count", "Bays", "Floors", "Roof", "Extras"],
             ["kura", "14", "2x2", "2", "Tile + pent", "-"],
             ["shopA", "13", "3x3", "1", "Tile hip", "Shopfront, lanterns"],
             ["dwellA (prototype 1)", "11", "4x3", "1", "Tile hip", "Engawa, fence"],
             ["farmhouse", "9", "5x3", "1", "Thatch gable", "Engawa, fence"],
             ["dwellB", "9", "4x3", "2", "Tile + pent", "Balcony, fence"],
             ["barn", "8", "3x4", "1", "Thatch gable", "-"],
             ["dwellC", "7", "3x3", "1", "Tile + pent", "Engawa, fence"],
             ["hutA / hutB / hutC", "2 / 3 / 2", "3x3 / 4x3 / 3x2", "1", "Thatch gable", "Engawa, fence, lanterns (varies)"],
             ["restA / restB", "3 / 2", "5x4 / 6x4", "1 / 2", "Tile", "Shopfront, engawa, balcony, lanterns"],
             ["shopB", "3", "3x4", "2", "Tile + pent", "Shopfront, balcony, lanterns"],
             ["tea", "3", "3x3", "1", "Thatch gable", "Engawa, lanterns"],
             ["row (rowhouse)", "2", "7x2", "1", "Tile + pent", "-"],
             ["inn", "2", "9x6", "2", "Tile hip", "Engawa, balcony, lanterns, gate, stone compound wall"]],
            [4.0 * cm, 1.8 * cm, 2.9 * cm, 1.5 * cm, 2.6 * cm, W - 12.8 * cm]),
      P("Roof values confirmed from renders in stage 1: 0 = no roof (open frame), 1 = tile hip, 2 = thatch gable, 3 = tile hip with a slightly different ridge cap. Every two-floor house also gets a pent tier between the floors.", small),
      ]

# ---------------------------------------------------------------- 3 modules
s += [P("3. Module families in the kit", h1),
      P("Derived from the architecture of the <i>GN_EdoHouse</i> node group: each spawner builds one family. "
        "Every family becomes one or more clean, grid-snapped modules."),
      table([["Family", "Pieces (planned)", "Replaces generator part"],
             ["Foundation", "Stone pier / footing, stilt post (stilted houses)", "EDO_PierSet"],
             ["Timber frame", "Corner post, wall post, tie beam, floor beam, bracing", "Timber Frame"],
             ["Wall bays", "Plaster panel, paper/lattice panel, door panel, window variants, corner (one set per bay width, 1 ken)", "Wall Modules + Wall Placement (11 box types)"],
             ["Interior", "Partition panels (visible through openings only)", "Interior Partitions (6 types)"],
             ["Tile roof", "Hip roof sections (sized by bays), corner/hip ridges, eave edge, ridge cap, end tiles", "Main Roof Surface, Smooth Roof"],
             ["Pent roof", "Tile pent tier between floors (2-floor designs)", "Pent Roof Surface"],
             ["Thatch roof", "Gable roof sections, ridge log, crossed ridge finials, thick eave edge", "Thatched Gable Roof"],
             ["Entrance", "Engawa deck, steps, deck posts and bracing, railings", "Entrance (Engawa + Steps)"],
             ["Balcony", "Outer beam, railing sections", "Balconies"],
             ["Shopfront", "Noren (cloth) rod, sign arm, sign board, lantern", "Shopfront"],
             ["Plot", "Fence segment, fence corner, gate (posts, beams, small roof, lanterns), stone compound wall (inn)", "Plot: Fence + Gate"],
             ["Props", "Barrel, firewood stack, jar, rack, rice bale", "Props"],
             ["Weathering", "Not geometry: moss, dirt, wear, sag handled in materials and decals", "Wear (sag, lean, moss, dirt)"]],
            [2.6 * cm, 9.0 * cm, W - 11.6 * cm], bold_first=True),
      P("Modules come in sizes matching the existing bay counts (1 to 9 bays) by combining pieces on the grid, not by stretching meshes, so textures keep a constant scale.", small),

      P("4. Technical specification", h1),
      table([["Item", "Specification", "Status"],
             ["Grid", "1 ken = 1.818 m per bay (measured from the generator: 1.81 m per bay)", "Agreed (from analysis)"],
             ["Storey height", "About 3.14 m per floor (measured)", "Agreed (from analysis)"],
             ["Unreal scale", "FBX exported at Unreal scale (1 Blender unit = 1 m = 100 cm), Z up, forward -Y, applied transforms", "Proposed"],
             ["Origins / pivots", "Grid-aligned origin at the module's bottom corner or centre-bottom, documented per family", "Proposed"],
             ["Naming", "SM_Edo_&lt;family&gt;_&lt;piece&gt;_&lt;variant&gt;, materials M_Edo_&lt;name&gt;, textures T_Edo_&lt;set&gt;_&lt;map&gt;", "Proposed"],
             ["Meshes", "Quads/clean triangles, smooth shading with hard edges only where needed, no n-gons, no hidden interior faces", "Proposed"],
             ["Built for geometry nodes", "Every module is authored to be instanced by the new geometry nodes: fixed 1 ken bay width, origin on a grid corner, consistent facing, pieces that tile along X and Y, separate corner and end pieces. The seed only picks between variants; it never changes sizes.", "Agreed (new goal)"],
             ["Supported parameters", "Bays X/Y, Floors, Roof style, Shopfront, Engawa, Balcony, Lanterns, Gate, Fence, Props, variant seed. Bay Scale and Raise are fixed (the village only uses 1.0 and 1.12). The 17 existing designs are the guaranteed set; the tested range beyond them will be reported.", "Proposed"],
             ["Placement", "Every house keeps its original position: x, y and rotation about Z (0, 90, 180, -90 degrees); z = 0 and scale 1 for all 94 houses, stored in analysis/data/placements.json and used by the manifest.", "Agreed"],
             ["Ground adaptation", "The original generator reads the terrain under each house and adapts floor level and stilt length. The kit foundation uses a variable-length post and the new geometry nodes sample the same Ground object, so houses meet the terrain as before.", "Proposed (needed to keep houses in place)"],
             ["LODs", "None. Nanite meshes.", "Agreed"],
             ["UVs", "UV set 0: tiling/trim layout, consistent texel density across the kit, no overlapping islands except intentional trim reuse. UV set 1 (lightmap) only if you ask for it; not needed with Lumen", "Proposed"],
             ["Vertex colour", "Dropped. The current vertex-colour masks are replaced by texture-based materials and decals", "Proposed"],
             ["Materials", "Few materials per module (target 2-3) to keep draw/material cost low", "Proposed"],
             ["Seed variation", "Fixed modules. Variety comes from module variants and material tint, not geometry jitter", "Agreed (my recommendation)"]],
            [3.0 * cm, W - 7.3 * cm, 4.3 * cm], bold_first=True),
      ]

# ---------------------------------------------------------------- 5 budgets + 6 collisions
s += [P("5. Triangle budgets", h1),
      table([["Part", "Budget", "Status"],
             ["One storey (frame, walls, openings, doors)", "2,000 - 5,000 triangles", "Agreed"],
             ["Roof (tile or thatch)", "up to 10,000 triangles", "Agreed"],
             ["Engawa + steps", "up to 3,000", "Proposed"],
             ["Gate", "up to 5,000", "Proposed"],
             ["Fence segment", "up to 400", "Proposed"],
             ["Prop (barrel, jar, rack, bale, ...)", "about 500 each", "Proposed"],
             ["Pent roof tier (2-floor designs)", "up to 5,000 each", "Proposed (not yet discussed)"]],
            [8.4 * cm, 4.6 * cm, W - 13.0 * cm], bold_first=True),
      P("A typical one-storey house lands around 12,000 - 22,000 triangles, close to today's median of about 19,000 (current houses: min 5,208, max 81,442, "
        "total 1.84 million for 94 houses). The difference is where they go: today the roof tiles are real geometry and the walls are boxes; in the kit, "
        "tile and wood detail comes mostly from normal maps and textures on modelled silhouettes. With Nanite these budgets are conservative; "
        "hero details (eave edges, bracket ends, ridge ornaments) may use the headroom where it helps the silhouette. "
        "I will report the real measured counts per module."),

      P("6. Collisions", h1),
      P("<b>Agreed:</b> the current scene has no collision meshes and the generator has no collision output, so none can be copied. "
        "Collisions are done at the end of the project: simple boxes/convex hulls per module, exported as UCX_ meshes alongside the FBX files. "
        "If you want them to match a specific setup from your Unreal project, send a screenshot or description at that stage."),

      P("7. Textures and materials", h1),
      P("<b>Photo-based CC0 sets</b> (downloaded by you from Poly Haven / ambientCG into <i>textures/</i>; I cannot download them here):"),
      table([["Material", "Planned source set", "Role"],
             ["Roof tile", "Poly Haven: Roof Tiles (recoloured to dark grey in stage 1); grey_roof_01 kept as colour/weathering reference", "Tile roofs"],
             ["Thatch", "Poly Haven: Reed Roof 03 (alternative: Thatch Roof Angled)", "Thatched gable roofs"],
             ["Timber (dark)", "Poly Haven: Dark Wooden Planks", "Posts, plank walls, fences"],
             ["Timber (beams)", "Poly Haven: Rough Wood", "Beams, rails, railings"],
             ["Plaster", "Poly Haven: White Stucco", "Wall plaster (warm off-white)"],
             ["Stone", "Poly Haven: Stacked Stone Wall (alternative: Rock Wall 05)", "Footings, compound walls"],
             ["Moss overlay", "ambientCG: Moss 001 (licence to be verified)", "Moss on roofs, stone, timber"]],
            [2.6 * cm, 8.4 * cm, W - 11.0 * cm], bold_first=True),
      P("<b>Procedural (made and baked in Blender):</b> paper (shoji), cloth (noren), lanterns, signs, dirt/grime and edge wear, and any gap where the photo sets do not cover a need.", small),
      Spacer(1, 3),
      table([["Texture spec", "Value"],
             ["Resolution", "4K for the five main materials (tile, thatch, timber, plaster, stone); 2K for minor ones (cloth, paper, lantern, sign, props). Unreal streams lower mips by distance automatically. Status: Agreed (4K); minor-set 2K proposed"],
             ["Sharing", "Shared tileable / trim sets used by every house, not unique 4K textures per house. A full 4K set is roughly 50-65 MB"],
             ["Maps", "BaseColor (sRGB), Normal (DirectX / Unreal convention), packed ORM (Occlusion, Roughness, Metallic), Emissive for lanterns"],
             ["Format", "Sources are the JPG/EXR downloads; outputs are PNG: BaseColor, Normal_DX, packed ORM. Texture preparation script tested in stage 1 on all 8 sets"],
             ["Licence", "CC0 sets are free for commercial use. I will confirm each set's licence on its own page before using it, and list them in the report"]],
            [3.4 * cm, W - 3.4 * cm], bold_first=True),
      P("Realism: photo-based CC0 sets plus modelled detail give a good semi-realistic to realistic result. It will not match hand-sculpted or fully photoscanned AAA assets up close; "
        "final judgement needs your eye in Unreal under real lighting.", small),
      ]

# ---------------------------------------------------------------- 8 process
s += [P("8. How the work will be done", h1),
      table([["Stage", "What", "Model / effort", "You review"],
             ["0", "Analysis of the .blend (done): 17 designs, grid, triangle costs, architecture, contact sheet", "Sonnet 5.5", "Report in <i>analysis/</i>"],
             ["1", "DONE: roof values confirmed, 94 placements recorded, ground behaviour checked, texture preparation tested on all 8 sets", "Sonnet 5.5", "-"],
             ["2", "DONE: dwellA prototype, kit geometry nodes, textures, previews, FBX; placed on the 11 original dwellA spots (floor within 1 cm)", "Opus 5.5, extra-high", "Renders, tri counts, FBX"],
             ["3", "DONE: pent roof, two storeys, balcony", "Opus 5.5, extra-high", "Renders"],
             ["4", "DONE: thatched gable roof (farmhouse, barn, huts, tea)", "Opus 5.5, extra-high", "Renders"],
             ["5", "DONE: shopfront, lanterns, stone compound wall, gate; all 17 designs build", "Opus 5.5 / Sonnet 5.5", "Renders"],
             ["6", "DONE: 4K JPG textures in the repo, all FBX, village manifest (94 houses), Unreal import helper (untested)", "Sonnet 5.5", "Files in repo"],
             ["7", "DONE: UCX convex collisions, whole village rebuilt in place (floor within 1.5 cm), kit/KIT_REPORT.md", "Sonnet 5.5", "Report"]],
            [1.3 * cm, 8.2 * cm, 3.4 * cm, W - 12.9 * cm]),
      P("Work is delivered in stages to the repo branch so you can stop or redirect after each one. Stage 2 is the main checkpoint: if the prototype quality is not what you want, we adjust before the other 16 designs.", small),

      P("Budget plan", h2),
      P("Using the model prices I have (Opus 5.5: $4 input / $20 output per million tokens; Sonnet 5.5: $2 / $10; cache reads $0.20) and my assumptions about "
        "turn size, a full build of roughly 300-500 turns comes to about <b>$35-60</b> (this includes roughly 50-100 extra turns, my estimate, for the new geometry nodes) with the split above (Opus at high effort; extra-high, which you chose, costs more and could push toward the upper end or beyond), "
        "versus about $18-30 on Sonnet alone and about $50-110 on Opus at max effort. These are estimates, not measurements: the real figure depends on how many "
        "render-check-fix loops are needed. I will report spending trends after stage 2 so you can decide whether to continue."),

      P("9. What I can and cannot verify", h1),
      table([["I can verify here", "I cannot verify here"],
             [Paragraph("<br/>".join(["- Triangle counts per module and per assembled house", "- Modules sit on the 1 ken grid, correct dimensions and pivots",
                                      "- UV validity, overlap, texel density consistency", "- Texture maps generated, sizes, channel packing",
                                      "- FBX exports open and match the .blend (re-import test)", "- Preview renders (CPU Cycles)", "- Geometry nodes: parameter sweeps (bays, floors, toggles), no gaps or overlaps, grid alignment, triangle counts vs the original footprints"]), cell),
              Paragraph("<br/>".join(["- How it looks in Unreal under Lumen/Nanite lighting", "- Nanite behaviour, material compatibility (translucent paper/lanterns), performance",
                                      "- The Unreal import script (no Unreal available)", "- Collision behaviour in your game",
                                      "- Whether textures downloaded by you match the exact picks (you provide them)"]), cell)]],
            [W / 2, W / 2], zebra=False),

      P("10. Risks and open items", h1)]
s += B(["<b>No Unreal here.</b> Everything engine-side is untested until you import it. Paper shoji and lanterns may need opaque/masked + emissive treatment to stay Nanite-friendly; I will flag this per material.",
        "<b>Roofs are the hardest part to make modular.</b> The current roof is a generated surface with curved eaves. A kit roof has to be assembled from pieces that tile for any bay count and still look right at the corners. Stage 2 tests this on dwellA at several sizes; if a fully instanced roof does not hold up, the fallback is roof sections generated by the geometry nodes using the same textures and UVs. I will report which one is used.",
        "<b>Thatch texture is not seamless.</b> reed_roof_03 has a ridge band along its top edge; I will use the straw area for the roof and the band as trim.",
        "<b>Realism ceiling.</b> CC0 photo textures + modelled detail is good but not AAA photoscan quality.",
        "<b>Repo size.</b> Textures and FBX files add up; GitHub rejects any file over 100 MB. Git LFS is recommended for <i>textures/</i> and <i>export/</i>.",
        "<b>Texture downloads depend on you.</b> This container cannot reach Poly Haven / ambientCG. Licences must be confirmed on each page (Poly Haven states CC0; ambientCG not confirmed by me).",
        "<b>Roof style mapping</b> (Roof 1 / 2 / 3) is inferred from renders and must be confirmed in stage 1.",
        "<b>Balcony</b> showed no change in my test on a single-floor house (probably needs two floors); to be confirmed when building dwellB.",
        "<b>Pent roof budget</b> (5,000) is a new proposal you have not yet seen; tell me if you disagree.",
        "<b>Credits.</b> Costs above are estimates; Opus max effort is not planned because it could use most of the budget."])
s += [P("11. Decisions recorded", h1),
      table([["Question", "Decision"],
             ["Triangle budget per module", "About 2-5K per storey, roof up to 10K. Engawa, gate, fence, props budgeted separately (proposed values above)"],
             ["Texture resolution", "4K, optimized for games; Unreal handles distance mip lowering"],
             ["Module split", "Taken from the node-group architecture (section 3)"],
             ["LODs / collisions", "No LODs (Nanite). Collisions at the end"],
             ["Seed variation", "Fixed modules, variety via variants and material tint"],
             ["Existing geometry nodes", "The kit does not need to work with GN_EdoHouse, which is not modified. It must work with new geometry nodes built from the kit meshes from the start"],
             ["First prototype", "dwellA, then kura"],
             ["Texture source", "Real CC0 photo sets downloaded by the user from Poly Haven / ambientCG, plus procedural materials for the rest"],
             ["Model plan", "Sonnet 5.5 for analysis and mechanical steps; Opus 5.5 at extra-high for the hard modelling stages"]],
            [4.6 * cm, W - 4.6 * cm], bold_first=True),
      Spacer(1, 6),
      P("Source analysis (measured): see <i>analysis/KIT_ANALYSIS.md</i> in the repository.", small)]

doc.build(s)
print("built", OUT)
