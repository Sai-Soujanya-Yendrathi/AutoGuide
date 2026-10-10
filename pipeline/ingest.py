"""Compliance-first NHTSA ingestion: URL allowlist, robots, throttle, HTML/PDF/table preservation."""
import argparse, hashlib, json, time
from datetime import datetime,timezone
from urllib.parse import urljoin,urlparse
from urllib.robotparser import RobotFileParser
import requests
from bs4 import BeautifulSoup
from .common import ROOT,DATA,doc_id,clean,save_jsonl
USER_AGENT='AutoGuideAI-AcademicResearch/1.0 (contact: replace-with-team-email@example.edu)'
def approved(url):
    u=urlparse(url)
    return u.scheme=='https' and u.hostname and (u.hostname=='nhtsa.gov' or u.hostname.endswith('.nhtsa.gov'))
def extract_html(body,url):
    soup=BeautifulSoup(body,'html.parser')
    for e in soup(['script','style','nav','footer','header','aside']):e.decompose()
    title=clean(soup.title.get_text(' ',strip=True)) if soup.title else url
    main=soup.find('main') or soup.find('article') or soup.body or soup
    blocks=[]; headings=[]; tables=[]
    for el in main.find_all(['h1','h2','h3','h4','p','li','table']):
        if el.name.startswith('h'):
            headings=[clean(el.get_text(' ',strip=True))]
            blocks.append('## '+headings[-1])
        elif el.name=='table':
            rows=[[clean(x.get_text(' ',strip=True)) for x in tr.find_all(['td','th'])] for tr in el.find_all('tr')]
            rows=[r for r in rows if r]
            if rows:
                tables.append(rows)
                blocks.append('\n'.join(' | '.join(r) for r in rows))
        elif not el.find_parent('table'):
            t=clean(el.get_text(' ',strip=True))
            if t and len(t)>20: blocks.append(t)
    return title,'\n'.join(blocks),tables

def extract_pdf(body):
    import fitz
    doc=fitz.open(stream=body,filetype='pdf')
    pages=[]
    for page in doc:
        pages.append(f'## PDF page {page.number+1}\n'+page.get_text('text'))
    tables=[]
    try:
        import pdfplumber,io
        with pdfplumber.open(io.BytesIO(body)) as pdf:
            for i,page in enumerate(pdf.pages):
                for t in page.extract_tables() or []:
                    if t:tables.append({'page':i+1,'rows':t})
    except Exception:pass
    return 'PDF document','\n'.join(pages),tables

def crawl(seeds,max_pages=180,delay=1.,email=None):
    if email:
        global USER_AGENT
        USER_AGENT=f'AutoGuideAI-AcademicResearch/1.0 (contact: {email})'
    if 'replace-with' in USER_AGENT:raise ValueError('Supply --email with a real team contact before crawling.')
    s=requests.Session();s.headers['User-Agent']=USER_AGENT
    queue=list(dict.fromkeys(seeds));visited=set();documents=[];logs=[];robots={};last=0
    while queue and len(documents)<max_pages:
        url=queue.pop(0)
        if url in visited or not approved(url):continue
        visited.add(url)
        base=f'https://{urlparse(url).hostname}'
        if base not in robots:
            rp=RobotFileParser()
            try:
                r=s.get(base+'/robots.txt',timeout=20);r.raise_for_status();rp.parse(r.text.splitlines());robots[base]=rp
            except Exception as ex:
                logs.append({'url':url,'reason':f'robots unavailable: {ex}'})
                robots[base]=None
        rp=robots[base]
        if rp is None or not rp.can_fetch(USER_AGENT,url):
            logs.append({'url':url,'reason':'robots blocked/unavailable'});continue
        time.sleep(max(0,delay-(time.monotonic()-last)))
        try:
            r=s.get(url,timeout=35,allow_redirects=True);last=time.monotonic();r.raise_for_status()
            if not approved(r.url):continue
            ctype=r.headers.get('Content-Type','').lower()
            if not ('pdf' in ctype or 'html' in ctype or r.url.lower().endswith('.pdf')):continue
            is_pdf='pdf' in ctype or r.url.lower().endswith('.pdf')
            title,txt,tables=extract_pdf(r.content) if is_pdf else extract_html(r.content,r.url)
            if len(txt)<150:continue
            key=doc_id(r.url);digest=hashlib.sha256(r.content).hexdigest();ext='pdf' if is_pdf else 'html'
            raw=DATA/'raw'/f'{key}.{ext}';raw.parent.mkdir(parents=True,exist_ok=True);raw.write_bytes(r.content)
            documents.append({'document_id':key,'version':'v1','url':r.url,'title':title,'type':ext,'text':txt,'tables':tables,'heading_path':[],'crawl_date':datetime.now(timezone.utc).isoformat(),'effective_date':None,'sha256':digest,'raw_file':str(raw.relative_to(ROOT))})
            if not is_pdf:
                soup=BeautifulSoup(r.text,'html.parser')
                for a in soup.select('a[href]'):
                    next_url=urljoin(r.url,a['href']).split('#')[0]
                    if approved(next_url) and next_url not in visited and next_url not in queue and len(queue)<max_pages*8:queue.append(next_url)
        except Exception as ex:logs.append({'url':url,'reason':str(ex)})
    save_jsonl(DATA/'documents.jsonl',documents)
    (DATA/'crawl_log.json').write_text(json.dumps({'documents':len(documents),'pdfs':sum(d['type']=='pdf' for d in documents),'table_documents':sum(bool(d['tables']) for d in documents),'skipped':logs},indent=2),encoding='utf8')
    return documents

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--seeds',default='config/seed_urls.txt');parser.add_argument('--email',required=True);parser.add_argument('--max-pages',type=int,default=180)
    args=parser.parse_args();seeds=[s.strip() for s in (ROOT/args.seeds).read_text().splitlines() if s.strip() and not s.startswith('#')]
    print('Ingested',len(crawl(seeds,args.max_pages,email=args.email)),'documents; review data/crawl_log.json')
