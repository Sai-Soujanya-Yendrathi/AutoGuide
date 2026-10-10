import hashlib, json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'
def read_jsonl(path):
    if not Path(path).exists(): return []
    return [json.loads(x) for x in Path(path).read_text(encoding='utf8').splitlines() if x.strip()]
def save_jsonl(path, rows):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf8')
def doc_id(url):return hashlib.sha256(url.encode()).hexdigest()[:16]
def clean(s):return re.sub(r'\s+',' ',s).strip()
