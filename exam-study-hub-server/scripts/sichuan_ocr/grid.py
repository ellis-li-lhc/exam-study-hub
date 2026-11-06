from pathlib import Path
from PIL import Image
import json,re,bisect
from collections import Counter
ROOT=Path('scraped-data/sources/sichuan')
def groups(values):
 out=[]
 for v in values:
  if not out or v>out[-1][-1]+1:out.append([v])
  else:out[-1].append(v)
 return [round(sum(g)/len(g))for g in out]
def grid(path):
 im=Image.open(path).convert('L');w,h=im.size
 bw=im.point(lambda v:0 if v<100 else 255)
 ys=groups([i for i,v in enumerate(bw.resize((1,h),Image.Resampling.BOX).get_flattened_data())if v<40])
 if len(ys)<3:raise ValueError(('Missing row borders',path.name,ys))
 cropped=bw.crop((0,ys[0],w,ys[-1]))
 xs=groups([i for i,v in enumerate(cropped.resize((w,1),Image.Resampling.BOX).get_flattened_data())if v<50])
 return w,h,xs,ys
if __name__=='__main__':
 allrows=[];issues=[];grids={}
 for path in sorted(ROOT.glob('catalog-2026-*.png')):
  w,h,xs,ys=grid(path);grids[path.name]=dict(width=w,height=h,xs=xs,ys=ys)
  if len(xs)!=13:issues.append((path.name,'column_count',len(xs)));continue
  ocr=path.with_suffix('.ocr.json')
  if not ocr.exists():continue
  rows=[[[]for _ in range(12)]for _ in range(len(ys)-1)]
  for token in json.loads(ocr.read_text()):
   x=(token['x']+token['w']/2)*w;y=(1-token['y']-token['h']/2)*h
   col=bisect.bisect_right(xs,x)-1;row=bisect.bisect_right(ys,y)-1
   if not(0<=row<len(rows)and 0<=col<12):continue
   rows[row][col].append(dict(**token,cx=x,cy=y))
  for idx,cells in enumerate(rows[1:],1):
   text=[''.join(t['text']for t in sorted(c,key=lambda t:t['cy']))for c in cells]
   text=[re.sub(r'\s+','',c)for c in text]
   record=dict(page=int(re.search(r'(\d{3})\.png',path.name)[1]),row=idx,cells=text,confidence=[min((t['confidence']for t in c),default=1)for c in cells])
   allrows.append(record)
   for j in range(9):
    if not text[j]:issues.append((path.name,idx,'empty',j,text))
   if not re.fullmatch(r'\d{3}',text[0])or not re.fullmatch(r'\d{6}',text[2])or text[2][:3]!=text[0]:issues.append((path.name,idx,'codes',text))
 print('grid pages',len(grids),'parsed rows',len(allrows),'issues',len(issues));print('issues sample',issues[:12]);print('schools',Counter(r['cells'][1]for r in allrows));print('categories',Counter(r['cells'][4]for r in allrows));print('durations',Counter(r['cells'][5]for r in allrows));print('lowconfidence',sum(any(c<.9 for c in r['confidence'][:9])for r in allrows))
 (ROOT/'grid-metadata.json').write_text(json.dumps(grids,ensure_ascii=False,indent=2));(ROOT/'grid-rows.json').write_text(json.dumps(allrows,ensure_ascii=False,indent=2));(ROOT/'grid-issues.json').write_text(json.dumps(issues,ensure_ascii=False,indent=2))
