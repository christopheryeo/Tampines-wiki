#!/usr/bin/env python3
"""Materialize retained Set B source evidence into raw crawl inputs."""
from __future__ import annotations
import hashlib, html, json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'runs/2026-09-15/artifacts/topic-crawls/SEP2026-B01/setB'
ITEMS=[
 ('2026-08','Enlistment Compliance','NS Registration','Ministry of Defence','https://www.mindef.gov.sg/national-service/additional-info/ns-registration/','mindef-ns-registration.html'),
 ('2026-09','Enlistment Compliance','Oral Answer to PQ on Protection for National Servicemen Against Workplace Discrimination','Ministry of Manpower','https://www.mom.gov.sg/newsroom/parliament-questions-and-replies/2026/0909-oral-answer-to-pq-on-protection-for-national-servicemen-against-workplace-discrimination','mom-ns-workplace.html'),
]
def clean(raw:str)->str:
 raw=re.sub(r'<(script|style)[^>]*>.*?</\\1>',' ',raw,flags=re.I|re.S)
 text=html.unescape(re.sub(r'<[^>]+>',' ',raw)); return re.sub(r'\\s+',' ',text).strip()
def slug(s): return re.sub('[^a-z0-9]+','-',s.lower()).strip('-')[:100]
def write(month,topic,title,outlet,url,body):
 aid='crawl-'+hashlib.sha256(url.encode()).hexdigest(); path=ROOT/'Inputs/articles'/month/f'{aid}-{slug(title)}.md'; path.parent.mkdir(parents=True,exist_ok=True)
 text = "\n".join(["---", f"articleId: {json.dumps(aid)}", f"articleTitle: {json.dumps(title)}", f"publishedDate: {json.dumps(month+'-01')}", "category: Non-institutional", f"topic: {json.dumps(topic)}", "tone: Factual", "toneSentiment: Neutral", "eventType: Unfacilitated", "tags: ['#source']", f"outlets: [{json.dumps(outlet)}]", "countries: []", "coverageCount: 1", "mediaCount: 0", "sourceType: crawl", f"url: {json.dumps(url)}", "---", "", body, ""])
 path.write_text(text,encoding='utf-8'); return path
out=[]
for item in ITEMS: out.append(str(write(*item[:-1],clean((RUN/item[-1]).read_text(encoding='utf-8',errors='ignore'))).relative_to(ROOT)))
info=json.loads((RUN/'article-1.json').read_text())['b-9465692373']['info']
out.append(str(write('2026-09','Emerging Weapons Technology',info['title'],info['source']['title'],info['url'],info['body']).relative_to(ROOT)))
(RUN/'accepted-normalized.json').write_text(json.dumps({'normalized':out},indent=2)+'\n'); print(json.dumps({'normalized':len(out)}))
