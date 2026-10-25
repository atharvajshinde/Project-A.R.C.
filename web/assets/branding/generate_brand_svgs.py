import os, math, subprocess

DIR = os.path.dirname(os.path.abspath(__file__))
os.makedirs(DIR, exist_ok=True)

# Shared A.R.C. Stencil Definition (Vector Paths, Zero External Font Dependency)
ARC_GLYPHS = '''
    <!-- LETTER A -->
    <polygon points="42,7 48,7 80,83 66,83 55,57 42,26" />
    <polygon points="42,7 34,26 40,29 46,15" />
    <path d="M 31 33 L 10 83 L 24 83 L 33 61 L 53 61 L 53 50 L 29 50 L 37 31 Z" />
    <!-- PERIOD 1 -->
    <rect x="86" y="71" width="12" height="12" />
    <!-- LETTER R -->
    <rect x="108" y="7" width="12" height="76" />
    <path d="M 126 7 L 152 7 C 166 7, 175 16, 175 30 C 175 42, 166 50, 154 51 L 176 83 L 161 83 L 141 53 L 126 53 L 126 42 L 150 42 C 158 42, 163 37, 163 30 C 163 22, 158 18, 150 18 L 126 18 Z" />
    <!-- PERIOD 2 -->
    <rect x="182" y="71" width="12" height="12" />
    <!-- LETTER C -->
    <path d="M 247 7.5 L 247 19 C 224 21, 211 32, 211 45 C 211 58, 224 69, 247 71 L 247 82.5 C 217 80, 199 65, 199 45 C 199 25, 217 10, 247 7.5 Z" />
    <path d="M 253 8.7 C 263 11, 270 17, 275 24 L 265 31 C 262 26, 257 21, 253 19.8 Z" />
    <path d="M 253 81.3 L 253 70.2 C 257 69, 262 64, 265 59 L 275 66 C 270 73, 263 79, 253 81.3 Z" />
    <!-- PERIOD 3 -->
    <rect x="282" y="71" width="12" height="12" />
'''

def circular_text_elements(text, cx, cy, r, start_angle_deg, end_angle_deg, font_size=15, font_family="'Inter', sans-serif", font_weight='600', fill='#ffffff', flip=False):
    n = len(text)
    if n == 0: return ''
    angles = [start_angle_deg + (end_angle_deg - start_angle_deg) * i / max(1, n - 1) for i in range(n)]
    out = []
    for char, ang in zip(text, angles):
        if char == ' ': continue
        rad = math.radians(ang)
        x = cx + r * math.sin(rad)
        y = cy - r * math.cos(rad)
        rot = ang + 180 if flip else ang
        out.append(f'<text x="{x:.2f}" y="{y:.2f}" font-family="{font_family}" font-size="{font_size}" font-weight="{font_weight}" fill="{fill}" text-anchor="middle" dominant-baseline="central" transform="rotate({rot:.2f}, {x:.2f}, {y:.2f})">{char}</text>')
    return '\n    '.join(out)

# -----------------------------------------------------------------------------
# 1. 01 HORIZONTAL INLINE
# -----------------------------------------------------------------------------
svg_01_inline = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 540 100" width="540" height="100">
  <defs>
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap');
      .project-txt {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 26px;
        font-weight: 500;
        letter-spacing: 0.36em;
        fill: #f8fafc;
      }}
      .arc-fill {{ fill: #ffffff; }}
      .divider {{ stroke: #475569; stroke-width: 1.5; }}
    </style>
    <g id="arc-symbol">{ARC_GLYPHS}
    </g>
  </defs>
  
  <!-- "PROJECT" Label -->
  <text x="12" y="59" class="project-txt">PROJECT</text>
  
  <!-- Divider Line -->
  <line x1="210" y1="16" x2="210" y2="84" class="divider" />
  
  <!-- Stencil A.R.C. Symbol -->
  <g transform="translate(225, 5)" class="arc-fill">
    <use href="#arc-symbol" />
  </g>
</svg>'''

# -----------------------------------------------------------------------------
# 2. 01 AEROSPACE TECHNICAL FRAME
# -----------------------------------------------------------------------------
svg_01_frame = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 220" width="600" height="220">
  <defs>
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&amp;family=JetBrains+Mono:wght@400;500&amp;display=swap');
      .frame-border {{
        fill: #0c0d0e;
        stroke: #ffffff;
        stroke-width: 2;
        stroke-linejoin: miter;
      }}
      .project-lbl {{
        font-family: 'Inter', sans-serif;
        font-size: 24px;
        font-weight: 500;
        letter-spacing: 0.44em;
        fill: #e2e8f0;
        text-anchor: middle;
      }}
      .tech-meta {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        font-weight: 500;
        letter-spacing: 0.22em;
        fill: #94a3b8;
      }}
      .tech-subtle {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 10px;
        font-weight: 400;
        letter-spacing: 0.25em;
        fill: #475569;
      }}
      .arc-fill {{ fill: #ffffff; }}
    </style>
    <g id="arc-symbol">{ARC_GLYPHS}
    </g>
  </defs>

  <!-- Technical Chamfered Placard Frame -->
  <path d="M 28 6 
           L 572 6 
           L 594 28 
           L 594 192 
           L 572 214 
           L 28 214 
           L 6 192 
           L 6 28 Z" class="frame-border" />

  <!-- Top metadata -->
  <text x="32" y="32" class="tech-subtle">TECHFEST // AUTONOMY</text>

  <!-- Center typography -->
  <text x="300" y="78" class="project-lbl">PROJECT</text>
  <g transform="translate(145, 95)" class="arc-fill">
    <use href="#arc-symbol" />
  </g>

  <!-- Bottom metadata -->
  <text x="32" y="196" class="tech-meta">THANE, IND</text>
  <text x="568" y="196" class="tech-meta" text-anchor="end">V2.0</text>
</svg>'''

# -----------------------------------------------------------------------------
# 3. 02 HARDWARE BADGE (Industrial Placard / Die-Cut Chassis Badge)
# -----------------------------------------------------------------------------
svg_02_badge = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 520 280" width="520" height="280">
  <defs>
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@500;600;700&amp;family=JetBrains+Mono:wght@500&amp;display=swap');
      .badge-bg {{
        fill: #08090a;
        stroke: #ffffff;
        stroke-width: 3.5;
        stroke-linejoin: miter;
      }}
      .badge-meta {{
        font-family: 'Inter', 'JetBrains Mono', -apple-system, sans-serif;
        font-size: 16px;
        font-weight: 600;
        letter-spacing: 0.24em;
        fill: #f1f5f9;
      }}
      .arc-fill {{ fill: #ffffff; }}
    </style>
    <g id="arc-symbol">{ARC_GLYPHS}
    </g>
  </defs>

  <!-- 45-degree chamfered chassis plate (32px chamfers) -->
  <path d="M 38 8 
           L 482 8 
           L 512 38 
           L 512 242 
           L 482 272 
           L 38 272 
           L 8 242 
           L 8 38 Z" class="badge-bg" />

  <!-- Top Metadata Row -->
  <text x="42" y="48" class="badge-meta">IIT x OLL</text>
  <text x="478" y="48" class="badge-meta" text-anchor="end">TECHFEST</text>

  <!-- Massive Central Stencil A.R.C. -->
  <g transform="translate(68, 85) scale(1.24)" class="arc-fill">
    <use href="#arc-symbol" />
  </g>

  <!-- Bottom Metadata Row -->
  <text x="42" y="244" class="badge-meta">GANTRY SYSTEM</text>
  <text x="478" y="244" class="badge-meta" text-anchor="end">V1.0</text>
</svg>'''

# -----------------------------------------------------------------------------
# 4. 03 CIRCULAR SEAL (NASA/DARPA-Grade Round Mission Patch)
# -----------------------------------------------------------------------------
top_seal_chars = circular_text_elements('IIT x OLL • TECHFEST', 210, 210, 156, -65, 65, font_size=15.5, font_weight='700')
bot_seal_chars = circular_text_elements('GANTRY SYSTEM • V1.0', 210, 210, 156, 242, 118, font_size=14.5, font_weight='700', flip=True)

svg_03_seal = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 420" width="420" height="420">
  <defs>
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@600;700&amp;display=swap');
      .seal-bg {{ fill: #0a0b0c; }}
      .ring-outer {{ fill: none; stroke: #ffffff; stroke-width: 2.2; }}
      .ring-thick {{ fill: none; stroke: #ffffff; stroke-width: 4; }}
      .arc-fill {{ fill: #ffffff; }}
      .dot-accent {{ fill: #ffffff; }}
    </style>
    <g id="arc-symbol">{ARC_GLYPHS}
    </g>
  </defs>

  <!-- Circular Badge Background -->
  <circle cx="210" cy="210" r="202" class="seal-bg" />

  <!-- Double Outer Concentric Rings -->
  <circle cx="210" cy="210" r="198" class="ring-outer" />
  <circle cx="210" cy="210" r="186" class="ring-thick" />

  <!-- Top Arc Text: IIT x OLL • TECHFEST -->
  {top_seal_chars}

  <!-- Inner Concentric Boundary Ring Arcs -->
  <path d="M 85 160 A 136 136 0 0 1 335 160" fill="none" stroke="#ffffff" stroke-width="2.5" />
  <path d="M 85 260 A 136 136 0 0 0 335 260" fill="none" stroke="#ffffff" stroke-width="2.5" />

  <!-- Left Accent Dot -->
  <circle cx="92" cy="210" r="5" class="dot-accent" />

  <!-- Center Stencil A.R.C. -->
  <g transform="translate(104, 178) scale(0.68)" class="arc-fill">
    <use href="#arc-symbol" />
  </g>

  <!-- Right Accent Dot -->
  <circle cx="328" cy="210" r="5" class="dot-accent" />

  <!-- Bottom Arc Text: GANTRY SYSTEM • V1.0 -->
  {bot_seal_chars}
</svg>'''

# -----------------------------------------------------------------------------
# 5. 03 CIRCULAR SEAL (MINIMAL PV GANTRY VARIANT WITH STARS)
# -----------------------------------------------------------------------------
pv_gantry_chars = circular_text_elements('PV GANTRY', 210, 210, 152, 215, 145, font_size=20, font_weight='600', flip=True)

svg_03_minimal = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 420" width="420" height="420">
  <defs>
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@600;700&amp;display=swap');
      .seal-bg {{ fill: #070809; }}
      .ring-single {{ fill: none; stroke: #ffffff; stroke-width: 2.5; }}
      .arc-fill {{ fill: #ffffff; }}
      .sparkle {{ fill: #ffffff; }}
    </style>
    <g id="arc-symbol">{ARC_GLYPHS}
    </g>
  </defs>

  <!-- Circular Body -->
  <circle cx="210" cy="210" r="198" class="seal-bg" />
  <circle cx="210" cy="210" r="194" class="ring-single" />

  <!-- Left Accent Dot -->
  <circle cx="82" cy="195" r="6.5" class="sparkle" />

  <!-- Center Stencil A.R.C. -->
  <g transform="translate(98, 160) scale(0.72)" class="arc-fill">
    <use href="#arc-symbol" />
  </g>

  <!-- Right Accent Dot -->
  <circle cx="338" cy="195" r="6.5" class="sparkle" />

  <!-- Bottom Curved Text: PV GANTRY -->
  {pv_gantry_chars}

  <!-- Four-Pointed Star Sparkles (Bot Right) -->
  <path d="M 370 290 Q 370 305 385 305 Q 370 305 370 320 Q 370 305 355 305 Q 370 305 370 290 Z" class="sparkle" opacity="0.9" />
  <path d="M 395 340 Q 395 352 407 352 Q 395 352 395 364 Q 395 352 383 352 Q 395 352 395 340 Z" class="sparkle" opacity="0.75" />
</svg>'''

# -----------------------------------------------------------------------------
# 6. MASTER DIE-CUT STICKER SHEET (Ready for Sticker Mule / StickerApp / Printing)
# -----------------------------------------------------------------------------
svg_sticker_sheet = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 800" width="1200" height="800">
  <defs>
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;family=JetBrains+Mono:wght@400;500&amp;display=swap');
      .sheet-bg {{ fill: #121316; }}
      .sheet-header {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 13px;
        font-weight: 500;
        letter-spacing: 0.28em;
        fill: #64748b;
      }}
      .sheet-title {{
        font-family: 'Inter', sans-serif;
        font-size: 22px;
        font-weight: 700;
        letter-spacing: 0.12em;
        fill: #f8fafc;
      }}
      .cut-line {{
        fill: none;
        stroke: #ef4444;
        stroke-width: 1.5;
        stroke-dasharray: 4, 4;
      }}
      .reg-mark {{
        fill: none;
        stroke: #64748b;
        stroke-width: 1.2;
      }}
      .frame-border {{ fill: #0c0d0e; stroke: #ffffff; stroke-width: 2; }}
      .project-lbl {{ font-family: 'Inter', sans-serif; font-size: 24px; font-weight: 500; letter-spacing: 0.44em; fill: #e2e8f0; text-anchor: middle; }}
      .tech-meta {{ font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 500; letter-spacing: 0.22em; fill: #94a3b8; }}
      .tech-subtle {{ font-family: 'JetBrains Mono', monospace; font-size: 10px; font-weight: 400; letter-spacing: 0.25em; fill: #475569; }}
      .badge-bg {{ fill: #08090a; stroke: #ffffff; stroke-width: 3.5; }}
      .badge-meta {{ font-family: 'Inter', sans-serif; font-size: 16px; font-weight: 600; letter-spacing: 0.24em; fill: #f1f5f9; }}
      .seal-bg {{ fill: #0a0b0c; }}
      .ring-outer {{ fill: none; stroke: #ffffff; stroke-width: 2.2; }}
      .ring-thick {{ fill: none; stroke: #ffffff; stroke-width: 4; }}
      .ring-single {{ fill: none; stroke: #ffffff; stroke-width: 2.5; }}
      .project-txt {{ font-family: 'Inter', sans-serif; font-size: 26px; font-weight: 500; letter-spacing: 0.36em; fill: #f8fafc; }}
      .divider {{ stroke: #475569; stroke-width: 1.5; }}
      .arc-fill {{ fill: #ffffff; }}
      .dot-accent {{ fill: #ffffff; }}
      .sparkle {{ fill: #ffffff; }}
    </style>
    <g id="arc-symbol">{ARC_GLYPHS}
    </g>
  </defs>

  <!-- Sheet Background -->
  <rect width="100%" height="100%" class="sheet-bg" />

  <!-- Sheet Header / Technical Metadata -->
  <g transform="translate(60, 50)">
    <text x="0" y="0" class="sheet-header">PROJECT A.R.C. // DIE-CUT STICKER &amp; CHASSIS BADGE PACK</text>
    <text x="0" y="30" class="sheet-title">IIT x OLL TECHFEST • OFFICIAL MERCH &amp; HARDWARE IDENTIFIERS</text>
    <text x="1080" y="0" class="sheet-header" text-anchor="end">VECTOR SPEC: 300 DPI</text>
    <text x="1080" y="30" class="sheet-header" text-anchor="end">CUT CONTOUR: 2.0 mm OFFSET</text>
  </g>

  <!-- Registration Marks (Corners) -->
  <g class="reg-mark">
    <circle cx="30" cy="30" r="12" /><line x1="12" y1="30" x2="48" y2="30" /><line x1="30" y1="12" x2="30" y2="48" />
    <circle cx="1170" cy="30" r="12" /><line x1="1152" y1="30" x2="1188" y2="30" /><line x1="1170" y1="12" x2="1170" y2="48" />
    <circle cx="30" cy="770" r="12" /><line x1="12" y1="770" x2="48" y2="770" /><line x1="30" y1="752" x2="30" y2="788" />
    <circle cx="1170" cy="770" r="12" /><line x1="1152" y1="770" x2="1188" y2="770" /><line x1="1170" y1="752" x2="1170" y2="788" />
  </g>

  <!-- Item 1: 01 HORIZONTAL INLINE BADGE (Top Left) -->
  <g transform="translate(60, 130)">
    <text x="0" y="-14" class="sheet-header">01 // HORIZONTAL INLINE VINYL STRIP</text>
    <rect x="-8" y="-8" width="556" height="116" rx="10" class="cut-line" />
    <rect width="540" height="100" fill="#08090a" rx="8" />
    <text x="12" y="59" class="project-txt">PROJECT</text>
    <line x1="210" y1="16" x2="210" y2="84" class="divider" />
    <g transform="translate(225, 5)" class="arc-fill">
      <use href="#arc-symbol" />
    </g>
  </g>

  <!-- Item 2: 01 AEROSPACE TECHNICAL FRAME (Bottom Left) -->
  <g transform="translate(60, 310)">
    <text x="0" y="-14" class="sheet-header">01 // AEROSPACE CHASSIS PLACARD (V2.0)</text>
    <path d="M 22 -2 L 578 -2 L 602 22 L 602 198 L 578 222 L 22 222 L -2 198 L -2 22 Z" class="cut-line" />
    <path d="M 28 6 L 572 6 L 594 28 L 594 192 L 572 214 L 28 214 L 6 192 L 6 28 Z" class="frame-border" />
    <text x="32" y="32" class="tech-subtle">TECHFEST // AUTONOMY</text>
    <text x="300" y="78" class="project-lbl">PROJECT</text>
    <g transform="translate(145, 95)" class="arc-fill"><use href="#arc-symbol" /></g>
    <text x="32" y="196" class="tech-meta">THANE, IND</text>
    <text x="568" y="196" class="tech-meta" text-anchor="end">V2.0</text>
  </g>

  <!-- Item 3: 02 HARDWARE BADGE (Top Right) -->
  <g transform="translate(640, 130)">
    <text x="0" y="-14" class="sheet-header">02 // INDUSTRIAL HARDWARE RATING BADGE</text>
    <path d="M 32 0 L 488 0 L 520 32 L 520 248 L 488 280 L 32 280 L 0 248 L 0 32 Z" class="cut-line" />
    <g transform="scale(0.96)">
      <path d="M 38 8 L 482 8 L 512 38 L 512 242 L 482 272 L 38 272 L 8 242 L 8 38 Z" class="badge-bg" />
      <text x="42" y="48" class="badge-meta">IIT x OLL</text>
      <text x="478" y="48" class="badge-meta" text-anchor="end">TECHFEST</text>
      <g transform="translate(68, 85) scale(1.24)" class="arc-fill"><use href="#arc-symbol" /></g>
      <text x="42" y="244" class="badge-meta">GANTRY SYSTEM</text>
      <text x="478" y="244" class="badge-meta" text-anchor="end">V1.0</text>
    </g>
  </g>

  <!-- Item 4: 03 CIRCULAR SEAL (Bottom Center) -->
  <g transform="translate(680, 470)">
    <text x="0" y="-14" class="sheet-header">03 // CIRCULAR MISSION PATCH</text>
    <circle cx="150" cy="150" r="154" class="cut-line" />
    <g transform="scale(0.71)">
      <circle cx="210" cy="210" r="202" class="seal-bg" />
      <circle cx="210" cy="210" r="198" class="ring-outer" />
      <circle cx="210" cy="210" r="186" class="ring-thick" />
      {top_seal_chars}
      <path d="M 85 160 A 136 136 0 0 1 335 160" fill="none" stroke="#ffffff" stroke-width="2.5" />
      <path d="M 85 260 A 136 136 0 0 0 335 260" fill="none" stroke="#ffffff" stroke-width="2.5" />
      <circle cx="92" cy="210" r="5" class="dot-accent" />
      <g transform="translate(104, 178) scale(0.68)" class="arc-fill"><use href="#arc-symbol" /></g>
      <circle cx="328" cy="210" r="5" class="dot-accent" />
      {bot_seal_chars}
    </g>
  </g>

  <!-- Item 5: 03 MINIMAL PV GANTRY SEAL (Bottom Right) -->
  <g transform="translate(940, 490)">
    <text x="0" y="-14" class="sheet-header">03 // PV GANTRY DIE-CUT SEAL</text>
    <circle cx="130" cy="130" r="134" class="cut-line" />
    <g transform="scale(0.62)">
      <circle cx="210" cy="210" r="198" class="seal-bg" />
      <circle cx="210" cy="210" r="194" class="ring-single" />
      <circle cx="82" cy="195" r="6.5" class="sparkle" />
      <g transform="translate(98, 160) scale(0.72)" class="arc-fill"><use href="#arc-symbol" /></g>
      <circle cx="338" cy="195" r="6.5" class="sparkle" />
      {pv_gantry_chars}
      <path d="M 370 290 Q 370 305 385 305 Q 370 305 370 320 Q 370 305 355 305 Q 370 305 370 290 Z" class="sparkle" opacity="0.9" />
      <path d="M 395 340 Q 395 352 407 352 Q 395 352 395 364 Q 395 352 383 352 Q 395 352 395 340 Z" class="sparkle" opacity="0.75" />
    </g>
  </g>
</svg>'''

files = {
    "01_horizontal_inline.svg": svg_01_inline,
    "01_aerospace_frame.svg": svg_01_frame,
    "02_hardware_badge.svg": svg_02_badge,
    "03_circular_seal.svg": svg_03_seal,
    "03_circular_seal_minimal.svg": svg_03_minimal,
    "arc_sticker_sheet.svg": svg_sticker_sheet,
}

for name, content in files.items():
    p = os.path.join(DIR, name)
    with open(p, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Generated: {name}")

# Re-render PNGs for verification
for k in files.keys():
    base = k.replace('.svg', '')
    svg_p = os.path.join(DIR, k)
    png_p = os.path.join(DIR, f"{base}.png")
    subprocess.run(['rsvg-convert', svg_p, '-o', png_p])
    print(f"Rendered PNG: {base}.png")

print("All branding SVG assets and PNG previews generated successfully!")
