#!/usr/bin/env python3
"""Reproduce the Chapter 37 core-profile scope/storage figure.
Requires Python 3 and svgwrite. Optional PNG/PDF rendering: Inkscape.
All geometry, type and illustrations are original vector primitives.
"""
from pathlib import Path
import sys
import svgwrite

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2] / 'book/images/mechanisms/scope-storage.svg'
W, H = 1360, 1180
C = dict(bg='#F7F5EF', ink='#172B3A', muted='#586B79', line='#C8D1D2', teal='#00777A', teal_light='#D8EFEB', orange='#B65018', orange_light='#F8E6D6', blue='#365FA8', blue_light='#E3EAF8', pale='#ECEFEA', white='#FFFFFF')
D = svgwrite.Drawing(str(OUT), size=(W,H), viewBox=f'0 0 {W} {H}')
D.set_desc(title='A symbol row can be reused; its frame slot cannot', desc='Three compiler snapshots show inner x, block exit, and a subsequent y declaration. The live row count changes from 2 to 1 to 2, but the next-slot counter changes from 2 to 2 to 3. Lookup for x returns the inner row B+1 before exit and the outer row B afterward. y reuses row B+1 but gets slot 2 at RBP minus 24. A separate runtime timeline shows the inner object lifetime ending at its block exit while the entire 256-byte frame remains reserved until the epilogue.')
D.add(D.rect((0,0),(W,H),fill=C['bg']))
FONT='DejaVu Sans, Arial, sans-serif'; MONO='DejaVu Sans Mono, monospace'

def txt(x,y,s,size=22,fill=None,weight=400,anchor='start',mono=False):
    el=D.text(s,insert=(x,y),font_size=size,font_family=MONO if mono else FONT,font_weight=weight,fill=fill or C['ink'],text_anchor=anchor)
    D.add(el); return el

def line(x1,y1,x2,y2,color=None,width=2,dash=None):
    kw=dict(stroke=color or C['line'],stroke_width=width)
    if dash: kw['stroke_dasharray']=dash
    D.add(D.line((x1,y1),(x2,y2),**kw))

def path(d,color=None,width=2,dash=None):
    kw=dict(fill='none',stroke=color or C['ink'],stroke_width=width,stroke_linecap='round',stroke_linejoin='round')
    if dash: kw['stroke_dasharray']=dash
    D.add(D.path(d=d,**kw))

def arrow(x1,y1,x2,y2,color=None,width=2.6):
    color=color or C['ink']; line(x1,y1,x2,y2,color,width)
    import math
    a=math.atan2(y2-y1,x2-x1); sz=8
    pts=[(x2,y2),(x2-sz*math.cos(a)+sz*.55*math.sin(a),y2-sz*math.sin(a)-sz*.55*math.cos(a)),(x2-sz*math.cos(a)-sz*.55*math.sin(a),y2-sz*math.sin(a)+sz*.55*math.cos(a))]
    D.add(D.polygon(pts,fill=color))

def shape(kind,x,y,color,filled=True,r=8):
    kw=dict(fill=color if filled else C['bg'],stroke=color,stroke_width=2.4)
    if kind=='circle': D.add(D.circle((x,y),r,**kw))
    elif kind=='triangle': D.add(D.polygon([(x,y-r-2),(x-r-1,y+r),(x+r+1,y+r)],**kw))
    elif kind=='square': D.add(D.rect((x-r,y-r),(2*r,2*r),rx=1,**kw))

def rounded_rect(x,y,w,h,fill,stroke=None,dash=None):
    kw=dict(fill=fill,stroke=stroke or 'none',stroke_width=1.6)
    if dash: kw['stroke_dasharray']=dash
    D.add(D.rect((x,y),(w,h),rx=5,**kw))

# The removed declaration's slot stays claimed. Hatching denotes a past
# assignment, not a surviving C object or a promise about its byte contents.
hatch=D.pattern(id='past-claim',size=(9,9),patternUnits='userSpaceOnUse')
hatch.add(D.rect((0,0),(9,9),fill='#EDF0ED'))
hatch.add(D.path(d='M -2,2 L 2,-2 M 0,9 L 9,0 M 7,11 L 11,7',stroke='#C2CBCB',stroke_width=1))
D.defs.add(hatch)

# Header.
txt(48,44,'CHAPTER 37  /  CORE PROFILE · NO PARAMETERS',17,C['muted'],600)
txt(48,92,'A row can be reused. Its slot cannot.',37,weight=700)
txt(48,130,'Block exit changes lookup. The function’s frame stays reserved.',25)
shape('circle',60,173,C['teal']); txt(80,181,'Start with int x = 1;',21,mono=True)
txt(397,181,'row B → slot 0.  B = file-scope row count, including this function.',20,C['muted'])
line(48,205,1312,205)

txt(48,244,'COMPILE TIME',18,C['teal'],700)
txt(245,244,'Live symbol records → assigned frame locations',23,weight=500)
txt(1312,244,'8 bytes each · lower addresses ↓',17,C['muted'],anchor='end')
# Arrows across snapshot headers make the parse direction explicit.
for x in (434,866): arrow(x,290,x+28,290,C['muted'],2)

COLS=[48,480,912]
STATES=[
    dict(n='1',title='Enter the inner block',code='{ int x = 2;',rows=2,nxt=2,lookup=1,kind='inner',action='push: save count B+1'),
    dict(n='2',title='Close the inner block',code='}',rows=1,nxt=2,lookup=0,kind='closed',action='pop: restore count B+1'),
    dict(n='3',title='Declare y afterward',code='int y = 3;',rows=2,nxt=3,lookup=0,kind='reuse',action='add: write row B+1 again'),
]
for x,s in zip(COLS,STATES):
    # Small-multiple background is deliberately open: aligned records,
    # pointers and address cells carry the explanation, not prose boxes.
    D.add(D.circle((x+16,287),16,fill=C['ink']))
    txt(x+16,294,s['n'],19,C['bg'],700,'middle')
    txt(x+44,295,s['title'],22,weight=600)
    txt(x+36,335,s['code'],25,mono=True)
    # Name lookup probe; the actual selected row changes after scope pop.
    txt(x+39,380,'lookup x',20,weight=600)
    target_y=525 if s['lookup']==1 else 460
    path(f'M {x+26},374 L {x+12},374 L {x+12},{target_y} L {x+29},{target_y}',C['ink'],2.5)
    arrow(x+27,target_y,x+35,target_y,C['ink'],2.5)
    txt(x+36,417,'SYMBOL ROW',17,C['muted'],600)
    txt(x+237,417,'FRAME SLOT',17,C['muted'],600)
    # Persistent outer x record.
    selected=s['lookup']==0
    rounded_rect(x+36,433,152,54,C['teal_light'],C['teal'] if selected else '#9FC9C6')
    txt(x+48,468,'B',21,mono=True)
    shape('circle',x+111,460,C['teal'])
    txt(x+135,469,'x',26,weight=600,mono=True)
    # Explicit symbol-to-slot edge. Geometry is stable until the reused row
    # points diagonally at a fresh slot in the final state.
    arrow(x+194,460,x+230,460,C['teal'],2.7)
    if s['kind']=='inner':
        rounded_rect(x+36,498,152,54,C['orange_light'],C['orange'])
        txt(x+48,533,'B+1',20,mono=True)
        shape('triangle',x+111,525,C['orange'])
        txt(x+135,534,'x',26,weight=600,mono=True)
        arrow(x+194,525,x+230,525,C['orange'],2.7)
        # Saved symbol-count boundary is between outer and inner rows.
        line(x+36,492,x+188,492,C['orange'],1.4,'4 3')
    elif s['kind']=='closed':
        rounded_rect(x+36,498,152,54,C['bg'],C['line'],'5 4')
        txt(x+46,532,'B+1',18,C['muted'],mono=True)
        txt(x+103,532,'out',19,C['muted'])
        # A count cut excludes the former row without pretending its
        # backing bytes have been erased.
        line(x+36,492,x+188,492,C['ink'],3)
    else:
        rounded_rect(x+36,498,152,54,C['blue_light'],C['blue'])
        txt(x+48,533,'B+1',20,mono=True)
        shape('square',x+111,525,C['blue'])
        txt(x+135,534,'y',26,weight=600,mono=True)
        arrow(x+194,525,x+231,581,C['blue'],3)
    # Three concrete eight-byte locations, always at the same coordinates.
    for k,cy in enumerate((460,525,590)):
        if k==0: fill=C['teal_light']; stroke='#9FC9C6'
        elif k==1 and s['kind']=='inner': fill=C['orange_light']; stroke=C['orange']
        elif k==1: fill='url(#past-claim)'; stroke='#ABB7B9'
        elif s['kind']=='reuse': fill=C['blue_light']; stroke=C['blue']
        else: fill=C['bg']; stroke=C['line']
        rounded_rect(x+236,cy-27,164,54,fill,stroke)
        txt(x+247,cy-5,f'slot {k}',16,C['muted'])
        txt(x+247,cy+18,f'RBP−{8*(k+1)}',21,mono=True)
        if k==0: shape('circle',x+380,cy,C['teal'],r=7)
        elif k==1 and s['kind']=='inner': shape('triangle',x+380,cy,C['orange'],r=7)
        elif k==1:
            # A short bar means allocation history, no living-object glyph.
            line(x+373,cy,x+387,cy,C['muted'],3)
        elif s['kind']=='reuse': shape('square',x+380,cy,C['blue'],r=7)
    # Ghost row explains reuse directly where it occurs.
    if s['kind']=='inner':
        txt(x+37,590,'x is shadowed',19,C['teal'])
        txt(x+37,616,'in row B',19,C['teal'])
    elif s['kind']=='closed':
        txt(x+37,590,'B+1 is outside',19,C['muted'])
        txt(x+37,616,'the live table',19,C['muted'])
    else:
        txt(x+37,590,'same row',20,C['blue'],600)
        txt(x+37,616,'new slot →',20,C['blue'],600)
    # Constant omitted region: the figure shows offsets, not a proportional
    # 32-cell memory picture. Mark the break explicitly.
    path(f'M {x+236},638 l 5,-5 l 6,10 l 6,-10 l 5,5 M {x+378},638 l 5,-5 l 6,10 l 6,-10 l 5,5',C['line'],1.8)
    txt(x+236,670,'slots 3–31 omitted',17,C['muted'])
    txt(x+36,710,s['action'],18,C['muted'],mono=True)
    # Counters occupy two invariant columns. Their differing trajectories
    # reveal precisely what is and is not restored.
    line(x+36,731,x+400,731)
    txt(x+36,760,'local rows',19,C['muted'])
    txt(x+145,763,str(s['rows']),28,weight=700)
    txt(x+236,760,'next slot',19,C['muted'])
    txt(x+375,763,str(s['nxt']),28,C['blue'] if s['kind']=='reuse' else C['ink'],700)

# A terse shared legend tells the reader how to interpret symbols and hatch.
shape('circle',60,808,C['teal'],r=6); txt(77,814,'outer x',18)
shape('triangle',193,808,C['orange'],r=6); txt(211,814,'inner x',18)
shape('square',325,808,C['blue'],r=6); txt(343,814,'y',18)
rounded_rect(396,796,29,22,'url(#past-claim)','#ABB7B9'); txt(438,814,'previously claimed; not reusable',18,C['muted'])

line(48,841,1312,841)

# Runtime is a distinct, later timeline. Only the inner object's lifetime
# is drawn; automatic non-VLA object lifetime must not be confused with
# the point at which its initializer executes.
txt(48,880,'RUN TIME',18,C['teal'],700)
txt(245,880,'One invocation of the emitted function',23,weight=500)
txt(150,923,'prologue',19,C['muted'],anchor='middle')
txt(545,923,'inner {',20,anchor='middle',mono=True)
txt(790,923,'}',24,anchor='middle',mono=True)
txt(1235,923,'epilogue',19,C['muted'],anchor='middle')
# Time arrow and fixed footprint, no growth at scalar declarations.
arrow(150,940,1250,940,C['line'],1.7)
rounded_rect(150,960,1085,45,C['teal_light'])
line(150,960,150,1005,C['teal'],3)
line(1235,960,1235,1005,C['teal'],3)
txt(692,990,'256 bytes reserved throughout',23,C['teal'],600,'middle')
line(545,942,545,1047,C['line'],1.5,'4 5')
line(790,942,790,1085,C['orange'],1.7,'4 5')
# Filled capsule has a decisive terminal cap at block exit.
shape('triangle',353,1038,C['orange'],r=7)
txt(373,1046,'inner x lifetime',20)
line(545,1038,790,1038,C['orange'],10)
line(790,1026,790,1050,C['orange'],3)
txt(812,1046,'ends here',22,C['orange'],600)
txt(812,1076,'Reserved bytes do not keep it alive.',20)
txt(48,1131,'Parsing } emits no stack adjustment. The epilogue restores RSP from RBP.',23)
D.save(pretty=True)
print(OUT)
