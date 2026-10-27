"""Export the actual tie drawing geometry as SVG without requiring a GPU context.

Run with Blender --background --factory-startup --python tools/preview_tie.py.
This is a shape/shading preview, not a GPU/editor screenshot.
"""
import sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
from node_zip_ties import rendering

elements=[]
defs=[]
def color(rgb):
    return '#'+''.join(f'{max(0,min(255,round(c*255))):02x}' for c in rgb[:3])
def polygon(points,rgb,shades=None):
    fill=color(rgb)
    if shades:
        ident=f'gradient{len(defs)}'
        bottom=max(range(len(points)),key=lambda i:points[i][1])
        top=min(range(len(points)),key=lambda i:points[i][1])
        defs.append(f'<linearGradient id="{ident}" gradientUnits="userSpaceOnUse" x1="0" y1="{points[top][1]}" x2="0" y2="{points[bottom][1]}"><stop offset="0" stop-color="{color([c*shades[top] for c in rgb[:3]])}"/><stop offset="1" stop-color="{color([c*shades[bottom] for c in rgb[:3]])}"/></linearGradient>')
        fill=f'url(#{ident})'
    xy=' '.join(f'{x:.3f},{y:.3f}' for x,y in points)
    elements.append(f'<polygon points="{xy}" fill="{fill}"/>')
def line(points,rgb,width=2):
    xy=' '.join(f'{x:.3f},{y:.3f}' for x,y in points)
    elements.append(f'<polyline points="{xy}" fill="none" stroke="{color(rgb)}" stroke-width="{width*2}" stroke-linejoin="round"/>')

rendering.polygon=polygon
rendering.line=line
tie=dict(pos=[0,0],angle=0,members=list('abcde'),color=[.65,.35,.33,1])
rendering.draw_tie(tie,8,8,lambda p:(120+9*p[0],420-9*p[1]),(.015,.015,.015,1),False)
assert len(elements)==10  # 3 body bands, body outline, 3 head fills/outlines.
svg='<svg xmlns="http://www.w3.org/2000/svg" width="240" height="620" viewBox="0 0 240 620"><rect width="100%" height="100%" fill="white"/><defs>'+''.join(defs)+'</defs>'+''.join(elements)+'</svg>'
destination=root/'docs'/'tie-style-preview.svg'
destination.write_text(svg,encoding='utf8')
print('TIE_STYLE_PREVIEW_PASS',destination)
