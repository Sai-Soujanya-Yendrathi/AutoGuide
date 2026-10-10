"""Golden-set validation and retrieval metrics; no fabricated answers or human ratings."""
import argparse,json,math,statistics,time
from collections import Counter
from .common import ROOT,DATA

def metrics(ranked,relevant):
    rel=set(relevant);hits=[int(x in rel) for x in ranked]
    recall=lambda k:len(rel.intersection(ranked[:k]))/len(rel) if rel else None
    mrr=next((1/(i+1) for i,h in enumerate(hits) if h),0)
    dcg=sum(h/math.log2(i+2) for i,h in enumerate(hits[:10]))
    ideal=sum(1/math.log2(i+2) for i in range(min(10,len(rel))))
    return {'recall_at_5':recall(5),'recall_at_20':recall(20),'mrr':mrr,'ndcg_at_10':dcg/ideal if ideal else None}

def run(split='dev',out=None):
    from pipeline.retrieval import search
    data=json.loads((DATA/'golden_set.json').read_text(encoding='utf8'))
    questions=[q for q in data if q['split']==split]
    results=[]
    for q in questions:
        if q.get('verified') is not True:continue
        for name,mode,strategy,rerank in [('B1','bm25','fixed',False),('B2','dense','fixed',False),('B3','hybrid','structure',True)]:
            start=time.perf_counter();rows=search(q['question'],mode,strategy,candidate_k=20,top_k=20,rerank=rerank)
            result={'id':q['id'],'baseline':name,'latency_ms':round(1000*(time.perf_counter()-start),1),'retrieved_ids':[r['id'] for r in rows],**metrics([r['id'] for r in rows],q.get('relevant_chunk_ids',[]))}
            results.append(result)
    if out:out.write_text(json.dumps(results,indent=2),encoding='utf8')
    return results
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--split',choices=['dev','test'],default='dev');a=ap.parse_args();out=DATA/f'evaluation_{a.split}.json';print(f'Saved {len(run(a.split,out))} evaluated runs to {out}')
