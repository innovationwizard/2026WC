#!/usr/bin/env python3
"""
Generate the favicon / app-icon / OG images from the Lucide 'trophy' glyph in our gold
(#d4af37) on brand navy, using cairosvg. Reproducible — re-run to regenerate.

Run:  .venv/bin/python web/scripts/build_icons.py
"""
import os
import cairosvg

STATIC = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))

# Lucide "trophy" (MIT), 24×24 stroke glyph.
TROPHY = '''
  <path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/>
  <path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/>
  <path d="M4 22h16"/>
  <path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"/>
  <path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"/>
  <path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"/>'''

GOLD, NAVY, BG, GREEN, INK, MUTE = '#d4af37', '#00063d', '#0a0e17', '#9eff1f', '#e2e8f0', '#94a3b8'


def icon_svg():
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">
  <rect width="512" height="512" rx="104" fill="{NAVY}"/>
  <g transform="translate(106,103) scale(12.5)" fill="none" stroke="{GOLD}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{TROPHY}
  </g>
</svg>'''


def og_svg():
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <rect width="1200" height="630" fill="{BG}"/>
  <rect width="1200" height="8" fill="{GOLD}"/>
  <g transform="translate(150,188) scale(11)" fill="none" stroke="{GOLD}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{TROPHY}
  </g>
  <text x="478" y="272" font-family="Helvetica, Arial, sans-serif" font-size="74" font-weight="bold" fill="{INK}">¿Puede la <tspan fill="{GREEN}">IA</tspan></text>
  <text x="478" y="360" font-family="Helvetica, Arial, sans-serif" font-size="74" font-weight="bold" fill="{INK}">ganar quinielas?</text>
  <text x="480" y="430" font-family="Helvetica, Arial, sans-serif" font-size="32" fill="{MUTE}">Predicción del Mundial 2026 · 4 modelos en vivo</text>
  <text x="480" y="486" font-family="Helvetica, Arial, sans-serif" font-size="21" letter-spacing="3" fill="#dc2626">ARTIFICIAL INTELLIGENCE DEVELOPMENTS</text>
</svg>'''


def render(svg, name, w, h=None):
    cairosvg.svg2png(bytestring=svg.encode('utf-8'),
                     write_to=os.path.join(STATIC, name),
                     output_width=w, output_height=h or w)
    print('  wrote', name)


def main():
    for size, name in [(32, 'favicon-32.png'), (180, 'apple-touch-icon.png'),
                       (192, 'icon-192.png'), (512, 'icon-512.png')]:
        render(icon_svg(), name, size)
    render(og_svg(), 'og.png', 1200, 630)
    print('done →', STATIC)


if __name__ == '__main__':
    main()
