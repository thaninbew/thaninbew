# Usage: python3 -I timeline.py index.html
# Generates the scene timeline as CSS @keyframes over one 12 s loop and writes it into index.html.
import re,sys
LOOP=12000
EXIT='cubic-bezier(.3,0,1,1)'
STEP='step-end'
def pct(ms): return f"{ms/LOOP*100:.3f}".rstrip('0').rstrip('.')+'%'
anims=[]
def kf(name,sel,pts):
    # pts: list of (ms, css, easing-for-next-segment or None)
    if pts[0][0]!=0: pts=[(0,pts[0][1],None)]+pts
    if pts[-1][0]!=LOOP: pts=pts+[(LOOP,pts[-1][1],None)]
    body=''.join(f"{pct(ms)}{{{css}{';animation-timing-function:'+e if e else ''}}}" for ms,css,e in pts)
    anims.append(f"@keyframes {name}{{{body}}}\n{sel}{{animation-name:{name}}}")
ON='opacity:1;transform:translateY(0)'; OFF='opacity:0;transform:translateY(0)'; LOW='opacity:0;transform:translateY(8px)'
def fade(name,sel,ins,outs,rise=True,start_on=False):
    """ins/outs: lists of (start,dur). Builds opacity (+rise on entry) keyframes."""
    ev=sorted([(t,d,'in') for t,d in ins]+[(t,d,'out') for t,d in outs])
    cur=ON if start_on else (LOW if rise else OFF)
    pts=[(0,cur,None)]
    for t,d,k in ev:
        if k=='in':
            pts.append((t-1,LOW if rise else OFF,None)); pts.append((t,LOW if rise else OFF,None)); pts.append((t+d,ON,None)); cur=ON
        else:
            pts.append((t,ON,EXIT)); pts.append((t+d,OFF,None)); cur=OFF
    pts.append((LOOP,cur,None))
    # drop duplicate/back-to-back times
    out=[];seen=set()
    for p in pts:
        if p[0] in seen or p[0]<0: continue
        seen.add(p[0]); out.append(p)
    kf(name,sel,out)
OUT=(1700,200); BACK=(7800,200)
# Headlines
fade('h-a','.h-a',[(7950,300)],[OUT],start_on=True)
fade('h-b','.h-b',[(1850,300)],[BACK])
# Reply card: ticket ID, question, sentences, skeleton, outcome badges
fade('id-a','.id-a',[(8100,200)],[OUT],rise=False,start_on=True)
fade('id-b','.id-b',[(1900,200)],[BACK],rise=False)
fade('ask-a','.ask-a',[(8100,200)],[OUT],start_on=True)
fade('ask-b','.ask-b',[(1900,200)],[BACK])
fade('s1','.s1',[(9350,200)],[OUT],rise=False,start_on=True)
fade('s2','.s2',[(9900,200)],[OUT],rise=False,start_on=True)
fade('skel','.skel',[(8400,200)],[(9200,150)],rise=False)
fade('nodraft','.none',[(2500,200)],[BACK],rise=False)
fade('ok','.ok',[(10500,200)],[OUT],rise=False,start_on=True)
fade('esc','.esc',[(2500,200)],[BACK],rise=False)
# AI strip sweep only while the reply is generating (sd-sweep), 8.4 s to 10.1 s
kf('sweep','.reply .strip',[(0,'background-size:100% 100%;background-position:0% 0',None),(8399,'background-size:100% 100%;background-position:0% 0',None),
   (8400,'background-size:200% 100%;background-position:0% 0',None),(10100,'background-size:200% 100%;background-position:100% 0',None),
   (10101,'background-size:100% 100%;background-position:0% 0',None)])
# Engineer inbox: list makes room, the ticket ID flies in (320 ms), the row tints once (900 ms)
kf('rows','.rows',[(0,'transform:translateY(0)',None),(3000,'transform:translateY(0)',None),(3200,'transform:translateY(68px)',None),
   (8000,'transform:translateY(68px)',None),(8200,'transform:translateY(0)',None)])
fade('nrow','.nrow',[(3400,200)],[BACK],rise=False)
kf('nid','.nid',[(0,'opacity:0',None),(3519,'opacity:0',None),(3520,'opacity:1',None),(LOOP,'opacity:1',None)])
kf('tint','.tint',[(0,'opacity:0',None),(3519,'opacity:0',None),(3520,'opacity:1',None),(4420,'opacity:0',None)])
G='translate(-269.6px,-66.8px) scale(1.2258)'
kf('ghost','.ghost',[(0,f'opacity:0;transform:{G}',None),(3199,f'opacity:0;transform:{G}',None),(3200,f'opacity:1;transform:{G}',None),
   (3520,'opacity:1;transform:translate(0,0) scale(1)',None),(3521,f'opacity:0;transform:{G}',None)])
fade('brief','.brief',[(4600,200)],[BACK])
css='\n'.join(anims)
p=sys.argv[1]; s=open(p).read()
s=re.sub(r'/\*ANIM\*/.*?/\*END\*/|/\*ANIM\*/',lambda m:'/*ANIM*/\n'+css+'\n/*END*/',s,flags=re.S)
open(p,'w').write(s)
print(len(anims),'animations')
