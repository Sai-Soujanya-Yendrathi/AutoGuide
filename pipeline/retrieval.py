"""BM25, 384-d normalized MiniLM dense, RRF hybrid, cross-encoder reranking."""
from functools import lru_cache
from .common import DATA,read_jsonl

def _rows(strategy):
    return read_jsonl(DATA/f'chunks_{strategy}.jsonl')

@lru_cache(maxsize=2)
def _model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

@lru_cache(maxsize=2)
def _reranker():
    from sentence_transformers import CrossEncoder
    return CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

def search(question,mode='hybrid',strategy='structure',candidate_k=20,top_k=5,rerank=True,page_type=None):
    rows=_rows(strategy)
    if page_type:rows=[r for r in rows if r.get('type')==page_type]
    if not rows:return []
    from rank_bm25 import BM25Okapi
    import numpy as np
    bm=BM25Okapi([r['text'].lower().split() for r in rows])
    bs=bm.get_scores(question.lower().split())
    bm_rank=list(np.argsort(-np.array(bs)))[:candidate_k]
    dense_rank=[]
    if mode in ('dense','hybrid'):
        import chromadb
        cli=chromadb.PersistentClient(path=str(DATA/'chromadb'))
        col=cli.get_collection(f'nhtsa_{strategy}')
        q=_model().encode([question],normalize_embeddings=True).tolist()
        result=col.query(query_embeddings=q,n_results=min(len(rows),max(candidate_k,20)),include=['distances'])
        by_id={r['id']:i for i,r in enumerate(rows)}
        dense_rank=[by_id[k] for k in result['ids'][0] if k in by_id]
    if mode=='bm25':selected=bm_rank
    elif mode=='dense':selected=dense_rank
    else:
        scores={}
        for ranking in (bm_rank,dense_rank):
            for pos,i in enumerate(ranking):scores[i]=scores.get(i,0)+1/(60+pos+1)
        selected=sorted(scores,key=scores.get,reverse=True)[:candidate_k]
    candidates=[]
    for rank,i in enumerate(selected):
        v=dict(rows[i]);v['score']=float(bs[i]) if mode=='bm25' else float(1/(rank+1));candidates.append(v)
    if rerank and candidates:
        values=_reranker().predict([(question,c['text']) for c in candidates])
        for c,v in zip(candidates,values):c['rerank_score']=float(v)
        candidates.sort(key=lambda x:x['rerank_score'],reverse=True)
    return candidates[:top_k]
