#!/usr/bin/env python3
"""Original SVG: scratch allocations and data movement for legacy SQUARE(ROWS)."""
from pathlib import Path
import sys
from html import escape
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2] / 'book/images/mechanisms/macro-scratch-lifetime.svg'
W,H=1200,1130
C={'paper':'#F7F5EF','ink':'#172B3A','teal':'#007F82','orange':'#D16B26','muted':'#637585','rule':'#C8D1D4','tealbg':'#D4EBE7','orangebg':'#F4DFCD','graybg':'#E3E8E8','white':'#FFFFFF','outbg':'#E1EFE4','out':'#286D4B'}
a=[]
def raw(x): a.append(x)
def rect(x,y,w,h,fill,stroke=None,r=0,sw=1.5,extra=''):
    raw(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}"'+(f' stroke="{stroke}" stroke-width="{sw}"' if stroke else '')+f' {extra}/>')
def line(x1,y1,x2,y2,color=None,sw=2,extra=''):
    raw(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color or C["rule"]}" stroke-width="{sw}" {extra}/>')
def path(d,color,sw=2.5,extra=''):
    raw(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round" {extra}/>')
def txt(x,y,s,size=20,color=None,weight='400',anchor='start',mono=False,extra=''):
    raw(f'<text x="{x}" y="{y}" font-family="{("DejaVu Sans Mono, monospace" if mono else "DejaVu Sans, sans-serif")}" font-size="{size}" fill="{color or C["ink"]}" font-weight="{weight}" text-anchor="{anchor}" {extra}>{escape(s)}</text>')
def arrow(d,color,sw=2.5):
    mark='teal' if color==C['teal'] else 'orange' if color==C['orange'] else 'out' if color==C['out'] else 'ink'
    path(d,color,sw,f'marker-end="url(#{mark}-arrow)"')
raw(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">')
raw('<title id="title">Keep scratch bytes until the replacement rescan returns</title>')
raw('<desc id="desc">Time runs left to right through a top-level legacy SQUARE(ROWS) expansion. Argument records and an expanded argument are retained in scratch. Two arrows copy the argument 4 into a replacement ((4) * (4)). Rescanning that retained replacement emits a separate copy into cc-src-buf. Only after the scan returns does the scratch cursor reset to saved S; the output copy survives. A second memory drawing shows that temp-end only shrinks a 64 KiB reservation to the used text, without releasing that text. Separator blanks are omitted in the main token view.</desc>')
raw('<defs>')
for n in ['ink','teal','orange','out']:
    raw(f'<marker id="{n}-arrow" markerWidth="8" markerHeight="8" refX="6.8" refY="4" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L8,4 L0,8 Z" fill="{C[n]}"/></marker>')
raw(f'<pattern id="reuse" patternUnits="userSpaceOnUse" width="10" height="10"><rect width="10" height="10" fill="{C["paper"]}"/><path d="M-2,2 L2,-2 M0,10 L10,0 M8,12 L12,8" stroke="#D2D8D7" stroke-width="1.3"/></pattern>')
raw('</defs>')
rect(0,0,W,H,C['paper'])
txt(42,54,'Keep the bytes until the rescan returns',34,weight='700')
txt(42,86,'Top-level call · legacy profile · token view (separator blanks omitted)',20,C['muted'])
# Concrete source, without a paragraph card.
line(42,111,1158,111)
txt(42,145,'#define ROWS 4',22,mono=True)
txt(42,179,'#define SQUARE(x) ((x) * (x))',22,mono=True)
txt(782,140,'CALL IN cc-in-buf',17,C['muted'],weight='700')
txt(782,178,'SQUARE(ROWS)',28,weight='700',mono=True)
# Time and phases.
arrow('M245,220 H1148',C['ink'],2)
txt(42,227,'TIME →',18,C['muted'],weight='700')
for x,n,label in [(270,'1','Prescan'),(500,'2','Substitute'),(735,'3','Rescan'),(987,'4','Resume')]:
    raw(f'<circle cx="{x}" cy="220" r="15" fill="{C["ink"]}"/>')
    txt(x,226,n,18,C['white'],'700','middle')
    txt(x-5,265,label,22,weight='700')
# A narrow read-position rail, distinct from memory.
line(269,287,953,287,C['muted'],1.7,'stroke-dasharray="4 5"')
txt(500,310,'Call site waits after the closing “)”',18,C['muted'])
arrow('M955,287 H1138',C['muted'],1.7)
txt(990,310,'read on',18,C['muted'])
# Scratch lifetime bands: rows are allocations, widths are elapsed lifetime.
txt(42,357,'SCRATCH',18,C['muted'],weight='700')
txt(42,386,'above saved S',20,weight='700')
txt(42,417,'Records',20)
txt(42,492,'Argument',20)
txt(42,628,'Replacement',20)
# Allocation backgrounds, same reset boundary.
rect(245,373,710,60,C['graybg'],C['rule'],5)
txt(269,410,'argument records',21,C['muted'])
rect(270,455,685,60,C['tealbg'],C['teal'],5)
txt(297,495,'4',32,C['teal'],'700',mono=True)
txt(746,491,'still allocated',20,C['teal'])
rect(500,587,455,65,C['orangebg'],C['orange'],5)
# Token-by-token positioning makes the two copy targets explicit.
body='((4) * (4))'
start=522; step=20
for i,ch in enumerate(body):
    if ch=='4': rect(start+i*step-3,598,23,40,C['white'],None,3)
    txt(start+i*step,632,ch,28,C['orange'] if ch=='4' else C['ink'],'700' if ch=='4' else '400',mono=True)
txt(773,627,'kept for scan',19,C['orange'])
# Movement of bytes; no arrow implies moving an allocation.
arrow('M309,516 V545 H570 V585',C['teal'],2.7)
arrow('M309,545 H690 V585',C['teal'],2.7)
txt(349,537,'copy into both x positions',20,C['teal'])
# Future scratch: available, not erased.
for y,h in [(373,60),(455,60),(587,65)]:
    rect(955,y,190,h,'url(#reuse)',C['rule'],4)
txt(1050,403,'reusable',20,C['muted'],'700','middle')
txt(1050,486,'reusable',20,C['muted'],'700','middle')
txt(1050,627,'reusable',20,C['muted'],'700','middle')
# Restore mark is the end of all allocations, not an erase operation.
line(955,338,955,671,C['ink'],2.8,'stroke-dasharray="8 6"')
txt(951,351,'reset top → S',18,C['ink'],'700','end')
# Separate durable output, only gets new bytes after restored sink is active.
line(42,691,1158,691)
txt(42,729,'CALLER OUTPUT',18,C['muted'],weight='700')
txt(42,762,'cc-src-buf',21,weight='700',mono=True)
rect(245,727,490,64,'none',C['rule'],5,1.5,'stroke-dasharray="7 5"')
txt(271,766,'sink parked while temporaries are built',19,C['muted'])
rect(735,727,410,64,C['outbg'],C['out'],5)
txt(753,766,'((4) * (4))',25,C['out'],'700',mono=True)
arrow('M962,759 H1127',C['out'],2.8)
txt(1047,819,'copy survives',20,C['out'],'700','middle')
# Rescan reads scratch, emits to a distinct destination.
arrow('M825,653 V725',C['orange'],3)
txt(837,677,'scan → emit',18,C['orange'],weight='700')
txt(245,819,'Records + texts remain allocated until the scan returns.',20,weight='700')
# Allocator inset: capacity vs retained bytes, with geometrical shrink.
line(42,848,1158,848)
txt(42,886,'Finishing a temporary shrinks its reservation',26,weight='700')
txt(42,920,'While building: 64 KiB reserved',20,mono=True)
txt(650,920,'temp-end: retain u bytes',20,mono=True)
for x in [42,650]:
    rect(x,947,465,59,'url(#reuse)',C['rule'],4)
    rect(x,947,88,59,C['tealbg'],C['teal'],4)
    txt(x+44,984,'4',29,C['teal'],'700','middle',mono=True)
    txt(x,1035,'A',20,mono=True)
# Reserved but unwritten before finish; free again after finish.
rect(130,947,377,59,'#F0F1EB',C['rule'],0)
txt(318,982,'reserved room',20,C['muted'],anchor='middle')
txt(926,982,'unused room returned',20,C['muted'],anchor='middle')
line(507,936,507,1017,C['ink'],2.5)
line(738,936,738,1017,C['ink'],2.5)
txt(507,1035,'top = A + 65,536',18,C['ink'],anchor='end',mono=True)
txt(745,1035,'top = A + u',18,C['ink'],mono=True)
arrow('M543,975 H613',C['ink'],2.5)
txt(650,1070,'The completed text stays at A.',20,C['teal'],weight='700')
txt(42,1104,'S = call’s saved cursor. A = temporary start. u = used bytes. Time and byte sizes are schematic.',17,C['muted'])
raw('</svg>')
(OUT).write_text('\n'.join(a)+'\n')
print(OUT)
