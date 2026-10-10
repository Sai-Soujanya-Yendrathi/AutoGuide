"""Adapter shared with the Streamlit chatbot; use demo or the local RAG pipeline."""
import os,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def retrieve(question:str,top_k:int=5)->list[dict]:
    if os.getenv('AUTOGUIDE_DEMO','1')=='1':
        chunks=json.loads((ROOT/'data/sample_chunks.json').read_text(encoding='utf8'))
        terms={w.lower().strip('.,?!') for w in question.split() if len(w)>3}
        matches=[c for c in chunks if any(t in (c.get('title','')+' '+c.get('text','')).lower() for t in terms)]
        return matches[:top_k]
    from pipeline.retrieval import search
    return search(question,mode=os.getenv('AUTOGUIDE_MODE','hybrid'),strategy=os.getenv('AUTOGUIDE_CHUNKING','structure'),candidate_k=20,top_k=min(top_k,5),rerank=True)
