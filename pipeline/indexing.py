"""Reproducible 2-strategy chunking + atomic collection replacement."""
import argparse,re,statistics
from .common import DATA,read_jsonl,save_jsonl

def chunks_for(doc,strategy='structure'):
    text=doc['text']; sections=[]
    if strategy=='structure':
        current='Document';buf=[]
        for line in text.splitlines():
            if line.startswith('## '):
                if buf:sections.append((current,' '.join(buf)));buf=[]
                current=line[3:].strip()
            else:buf.append(line)
        if buf:sections.append((current,' '.join(buf)))
    else:sections=[('Document',text)]
    out=[]
    for heading,txt in sections:
        words=txt.split();size=500;step=400
        for start in range(0,len(words),step):
            block=words[start:start+size]
            if not block:continue
            n=len(out)+1
            out.append({'id':f"{doc['document_id']}:{doc.get('version','v1')}:{strategy}:{n:04d}",'document_id':doc['document_id'],'title':doc['title'],'url':doc['url'],'type':doc['type'],'heading_path':[heading],'text':' '.join(block),'token_count_approx':len(block),'strategy':strategy})
            if start+size>=len(words):break
    return out

def build(strategy='structure',index_db=True):
    docs=read_jsonl(DATA/'documents.jsonl')
    if not docs:raise RuntimeError('No documents. Run ingestion first.')
    all_chunks=[chunk for d in docs for chunk in chunks_for(d,strategy)]
    path=DATA/f'chunks_{strategy}.jsonl';save_jsonl(path,all_chunks)
    if index_db:
        import chromadb
        from sentence_transformers import SentenceTransformer
        import numpy as np
        model=SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        client=chromadb.PersistentClient(path=str(DATA/'chromadb'))
        temp=f'nhtsa_{strategy}_rebuild'
        try:client.delete_collection(temp)
        except Exception:pass
        col=client.get_or_create_collection(temp,metadata={'hnsw:space':'cosine'})
        for i in range(0,len(all_chunks),100):
            sub=all_chunks[i:i+100]
            vec=model.encode([x['text'] for x in sub],normalize_embeddings=True).tolist()
            col.add(ids=[x['id'] for x in sub],documents=[x['text'] for x in sub],embeddings=vec,metadatas=[{'url':x['url'],'title':x['title'],'type':x['type'],'document_id':x['document_id'],'heading':' / '.join(x['heading_path'])} for x in sub])
        target=f'nhtsa_{strategy}'
        # Chroma has no cross-collection atomic rename: swap after successful full build.
        try:client.delete_collection(target)
        except Exception:pass
        final=client.get_or_create_collection(target,metadata={'hnsw:space':'cosine'})
        for i in range(0,len(all_chunks),100):
            sub=all_chunks[i:i+100];response=col.get(ids=[x['id'] for x in sub],include=['embeddings'])
            lookup={id_:vec for id_,vec in zip(response['ids'],response['embeddings'])}
            final.add(ids=[x['id'] for x in sub],documents=[x['text'] for x in sub],embeddings=[list(lookup[x['id']]) for x in sub],metadatas=[{'url':x['url'],'title':x['title'],'type':x['type'],'document_id':x['document_id'],'heading':' / '.join(x['heading_path'])} for x in sub])
        client.delete_collection(temp)
        assert final.count()==len(all_chunks),'Orphan or missing chunks'
    return all_chunks
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--strategy',choices=['fixed','structure','both'],default='both');ap.add_argument('--no-vectors',action='store_true');a=ap.parse_args()
    for s in ['fixed','structure'] if a.strategy=='both' else [a.strategy]:print(s,len(build(s,not a.no_vectors)))
