#!/usr/bin/env python3
"""Original mechanism illustration. Run: python3 generate_process.py [output.svg].
Requires svgwrite. Render: inkscape OUTPUT.svg --export-filename=OUTPUT.png.
"""
from pathlib import Path
import sys
import svgwrite

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2] / 'book/images/mechanisms/process-handoff.svg'
W, H = 800, 1350
C = dict(bg='#F7F5EF', ink='#172B3A', teal='#006B6E', orange='#9F4518', muted='#40535F', rule='#5D7074', white='#FFFFFF', pale='#E7F2F0', peach='#F8EADC', red='#A64335', gray='#EEF0EF')
d = svgwrite.Drawing(str(OUT), size=(f'{W}px',f'{H}px'), viewBox=f'0 0 {W} {H}')
d.set_desc(title='Fork, redirect, exec, and publish only after success', desc='A host Linux process trace. Fork makes two processes with separate descriptor tables. In child 202, open returns 3; dup2 makes descriptors 0 and 3 refer to the same open file description A with one offset. Closing 3 leaves 0 connected. Exec replaces the child program while its PID and descriptor 0 survive. The parent waits for exactly child 202. Only a matching returned PID and stored status zero let the controller rename unit.o to the unit object path.')
d.add(d.rect((0,0),(W,H),fill=C['bg']))
for name, color in [('ink','ink'),('teal','teal'),('orange','orange'),('muted','muted'),('red','red')]:
    m=d.marker(id=f'arrow-{name}', insert=(8,4), size=(9,8), orient='auto', markerUnits='userSpaceOnUse')
    m.add(d.path(d='M 0 0 L 8 4 L 0 8 z', fill=C[color])); d.defs.add(m)

def text(s,x,y,size=16,fill='ink',weight='normal',anchor='start',mono=False,opacity=1):
    d.add(d.text(s,insert=(x,y),fill=C.get(fill,fill),font_size=size,font_family='DejaVu Sans Mono' if mono else 'DejaVu Sans',font_weight=weight,text_anchor=anchor,opacity=opacity))
def rect(x,y,w,h,fill='white',stroke='rule',r=10,sw=1.4,**kw):
    z=d.rect((x,y),(w,h),rx=r,fill=C.get(fill,fill),stroke=C.get(stroke,stroke),stroke_width=sw,**kw); d.add(z); return z

def line(x1,y1,x2,y2,color='ink',sw=2,arrow=False,dash=None):
    kw=dict(stroke=C[color],stroke_width=sw,fill='none')
    if arrow: kw['marker_end']=f'url(#arrow-{color})'
    if dash: kw['stroke_dasharray']=dash
    d.add(d.line((x1,y1),(x2,y2),**kw))
def path(p,color='ink',sw=2,arrow=False,dash=None):
    kw=dict(stroke=C[color],stroke_width=sw,fill='none',stroke_linejoin='round',stroke_linecap='round')
    if arrow: kw['marker_end']=f'url(#arrow-{color})'
    if dash: kw['stroke_dasharray']=dash
    d.add(d.path(d=p,**kw))
def circle(x,y,r,fill='white',stroke='ink',sw=1.5):
    d.add(d.circle((x,y),r,fill=C[fill],stroke=C[stroke],stroke_width=sw))
def step(n,x,y):
    circle(x,y,13,'ink','ink'); text(str(n),x,y+5,14,'white','bold','middle')
def fdtable(x,y,w=180,initial=True):
    rect(x,y,w,99,'white','rule',6)
    for i in range(3):
        if i: line(x,y+33*i,x+w,y+33*i,'rule',1)
        rect(x,y+33*i,35,33,'gray','rule',r=0,sw=0)
        text(str(i),x+17,y+23+33*i,17,'ink','bold','middle',True)
        text(['stdin','stdout','stderr'][i],x+49,y+23+33*i,16,'muted',mono=True)
    line(x+35,y,x+35,y+99,'rule',1)
def document(x,y,w,h,title,fill='white'):
    # Folded corner plus lines gives the object a file shape, not a prose card.
    fold=16
    d.add(d.path(d=f'M{x} {y} H{x+w-fold} L{x+w} {y+fold} V{y+h} H{x} Z',fill=C[fill],stroke=C['ink'],stroke_width=1.7))
    path(f'M{x+w-fold} {y} V{y+fold} H{x+w}','ink',1.3)
    text(title,x+w/2,y+31,16,'ink','bold','middle',True)
    for yy,ww in [(y+47,w-28),(y+58,w-41),(y+69,w-33)]:
        line(x+14,yy,x+ww,yy,'rule',3)

def smallcode(x,y,w,h,label,fill='white',opacity=1):
    # Fade only the old program's panel fill; its name and border stay legible.
    rect(x,y,w,h,fill,'rule',6,fill_opacity=opacity)
    text(label,x+w/2,y+25,16,'ink','bold','middle',mono=True)
    for yy,xx in [(y+43,w-20),(y+54,w-42),(y+65,w-31)]:
        line(x+12,yy,x+xx,yy,'rule',3)

# Head and time orientation.
text('Replace the program. Keep the input.',35,45,27,'ink','bold')
text('One successful compile-unit call on host Linux',35,75,17,'muted')
text('Assume fd 0/1/2 open (not close-on-exec); child open → 3.',35,102,15,'muted')
rect(345,127,110,42,'ink','ink',21)
text('fork()',400,155,20,'white','bold','middle',True)
path('M345 148 H145 V192','ink',2.5,True)
path('M455 148 H535 V192','ink',2.5,True)
text('PARENT',145,217,18,'orange','bold','middle')
text('fork returns 202',145,241,15,'ink',anchor='middle',mono=True)
text('CHILD 202',535,217,18,'teal','bold','middle')
text('fork returns 0',535,241,15,'ink',anchor='middle',mono=True)
text('controller',145,270,17,'ink','bold','middle',True)
text('controller',535,270,17,'ink','bold','middle',True)
fdtable(55,286,180); fdtable(445,286,180)
# Explicitly show inherited fd 0 references sharing an open-file description.
rect(256,286,166,99,'gray','rule',8)
text('inherited',339,308,15,'muted',anchor='middle')
text('stdin',339,331,18,'ink','bold','middle',True)
text('open-file',339,354,16,'muted',anchor='middle')
text('description',339,375,16,'muted',anchor='middle')
path('M235 302 H256','muted',1.7,True)
path('M445 302 H422','muted',1.7,True)
text('Separate tables; inherited open-file descriptions are shared.',35,412,15,'muted')

# Parent execution lane, held until the child terminates.
line(145,433,145,458,'orange',2.5,True)
rect(45,467,200,103,'peach','orange',12,1.8)
text('wait for this child',145,495,17,'ink','bold','middle')
text('wait4(202, &status,',145,521,13.5,'ink',anchor='middle',mono=True)
text('      0, 0)',145,542,13.5,'ink',anchor='middle',mono=True)
line(145,570,145,687,'orange',3,False,'7 7')
line(145,844,145,1007,'orange',3,False,'7 7')
# Pause icon and an untouched fd-table reference provide the parent state.
rect(130,701,9,37,'orange','orange',2,0); rect(151,701,9,37,'orange','orange',2,0)
text('waiting',145,768,17,'orange','bold','middle')
text('its fd table',145,800,15,'muted',anchor='middle')
text('stays unchanged',145,822,15,'muted',anchor='middle')

# Child descriptors: two arrows really terminate on ONE OFD.
line(535,433,535,450,'teal',2.5,True)
step(1,323,474); text('open → 3',345,480,18,'ink','bold',mono=True)
step(2,488,474); text('dup2(3, 0)',510,480,18,'ink','bold',mono=True)
text('Child’s bindings immediately after dup2',310,511,15,'muted')
text('fd table',343,541,14,'muted',anchor='middle')
rect(319,554,48,40,'pale','teal',4); text('0',343,581,21,'teal','bold','middle',True)
rect(319,620,48,40,'pale','teal',4); text('3',343,647,21,'teal','bold','middle',True)
path('M367 574 H492 V587 H568','teal',3,True)
path('M367 640 H492 V611 H568','teal',3,True)
text('stdin',388,562,15,'teal',mono=True)
text('opened fd',388,660,14,'muted')
# One open-file description stores the offset and points to one file.
rect(568,546,188,80,'white','teal',10,2)
circle(590,566,12,'teal','teal'); text('A',590,571,14,'white','bold','middle')
text('open-file',615,566,16,'ink','bold')
text('description',615,586,16,'ink','bold')
text('offset',583,614,13,'teal')
rect(634,602,106,15,'gray','rule',3,0)
d.add(d.polygon([(635,599),(644,599),(639.5,608)],fill=C['teal']))
text('0',650,614,12.5,'teal','bold',mono=True)
line(662,627,662,634,'teal',2,True)
# A folded-corner file is separate from the kernel's open-file description.
d.add(d.path(d='M584 634 H740 L752 646 V693 H584 Z',fill=C['white'],stroke=C['ink'],stroke_width=1.3))
path('M740 634 V646 H752','ink',1.1)
text('prepared input',668,655,14,'ink','bold','middle')
for xx,ww,col in [(596,51,'pale'),(649,30,'peach'),(681,58,'gray')]:
    rect(xx,665,ww,7,col,'rule',1,0)
text('Forth + driver + C',668,687,12.3,'muted',anchor='middle')
text('Two descriptors. One stream and one shared offset.',310,710,15,'teal','bold')
text('Descriptors 1 and 2 are unchanged throughout.',310,733,14,'muted')

# Drop only one descriptor, then change only the program image.
step(3,323,775); text('close(3)',345,781,18,'ink','bold',mono=True)
rect(494,754,36,32,'gray','rule',4); text('3',512,777,17,'muted','bold','middle',True)
line(489,751,535,790,'red',2.5); line(535,751,489,790,'red',2.5)
text('0 still points to A',553,779,15,'teal','bold')
line(535,801,535,816,'teal',2.5,True)
rect(307,824,449,173,'white','teal',15,2.2)
rect(321,812,108,26,'teal','teal',7,0); text('PID 202',375,830,15,'white','bold','middle',True)
step(4,456,837); text('exec',478,844,19,'ink','bold',mono=True)
text('program image',463,868,14,'muted',anchor='middle')
smallcode(325,879,120,80,'controller','gray',0.52)
line(333,886,437,951,'muted',1.6)
path('M451 919 H480','ink',2.5,True)
smallcode(489,879,127,80,'seed-forth','pale')
text('fd table',686,868,14,'muted',anchor='middle')
for yy,n,lab in [(879,'0','→ A'),(908,'1','out'),(937,'2','err')]:
    rect(650,yy,82,28,'pale' if n=='0' else 'gray','rule',3,0)
    text(n,665,yy+20,15,'teal' if n=='0' else 'muted','bold','middle',True)
    text(lab,700,yy+20,15,'teal' if n=='0' else 'muted',anchor='middle',mono=True)
text('Same process. Fresh program. Input binding survives.',531,984,14,'teal','bold','middle')

# Exit synchronizes the lanes; no arbitrary cross-lane schedule is implied.
line(535,998,535,1030,'teal',2.5,True)
circle(535,1048,13,'teal','teal'); text('0',535,1053,14,'white','bold','middle')
text('exit',564,1054,17,'teal','bold')
text('reads fd 0',690,1018,14,'muted',anchor='middle')
text('writes unit.o',690,1041,14,'ink','bold','middle',True)
path('M522 1048 H145 V1069','orange',2.7,True)
text('child 202 terminates; wait completes',165,1037,14,'orange')

# wait4 has two outputs, and both checks must pass before rename.
text('TWO SEPARATE RESULTS',35,1100,14,'muted','bold')
rect(35,1113,170,47,'white','orange',6,1.7)
text('return PID = 202',120,1142,15,'ink','bold','middle',True)
rect(218,1113,178,47,'white','orange',6,1.7)
text('stored status = 0',307,1142,15,'ink','bold','middle',True)
path('M120 1113 V1105 H307 V1113','orange',1.7)

line(120,1160,120,1177,'orange',2,True)
line(307,1160,307,1177,'orange',2,True)
text('matches saved PID?',120,1200,14,'ink',anchor='middle')
text('normal exit 0?',307,1200,14,'ink',anchor='middle')
path('M120 1210 V1233 H197','teal',2.5,True)
path('M307 1210 V1213 H215 V1215','teal',2.5,True)
circle(215,1233,18,'teal','teal'); text('&',215,1240,21,'white','bold','middle')
line(233,1233,414,1233,'teal',3,True)
text('both pass',322,1258,14,'teal','bold','middle')
text('otherwise stop',215,1280,14,'red','bold','middle')
text('no rename',215,1301,14,'red',anchor='middle')
line(215,1251,215,1261,'red',1.5)
# Rename is a name change on the completed object; one object glyph.
text('rename',590,1137,19,'ink','bold','middle',True)
document(429,1162,110,104,'unit.o','white')
path('M550 1214 H620','ink',2.5,True)
text('name changes',584,1244,12,'muted',anchor='middle')
rect(631,1187,132,52,'pale','teal',7,1.7)
text('<unit>.o',697,1219,17,'teal','bold','middle',True)
text('Object already written by child',590,1281,14,'muted',anchor='middle')
text('Only now can the parent publish it.',590,1304,14,'ink','bold','middle')
# Small scope note, not an extra paragraph panel.
text('Manual, source-derived trace · execution order within lanes; no Linux scheduling order assumed',400,1334,11.8,'muted',anchor='middle')
d.save()
print(OUT)
