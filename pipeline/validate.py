"""Corpus minimum gate based on observed documents, never projected counts."""
import json
from .common import DATA,read_jsonl

def report():
    docs=read_jsonl(DATA/'documents.jsonl')
    counts={'web_pages':sum(d['type']=='html' for d in docs),'pdfs':sum(d['type']=='pdf' for d in docs),'pages_with_tables':sum(bool(d.get('tables')) for d in docs)}
    targets={'web_pages':150,'pdfs':5,'pages_with_tables':3}
    return {'observed':counts,'required':targets,'passed':all(counts[k]>=targets[k] for k in targets)}
if __name__=='__main__':print(json.dumps(report(),indent=2))
