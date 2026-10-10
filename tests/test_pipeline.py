from pipeline.indexing import chunks_for
from pipeline.evaluate import metrics
from pipeline.validate import report
from chatbot import prepare_evidence,valid_public_url

def test_chunk_ids_and_strategies():
    d={'document_id':'X1','version':'v1','title':'Test','url':'https://www.nhtsa.gov/test','type':'html','text':'## Header\n'+('words '*600)}
    assert all(c['id'].startswith('X1:v1:') for c in chunks_for(d,'fixed'))
    assert chunks_for(d,'structure')[0]['heading_path']==['Header']
def test_metrics():
    r=metrics(['a','b'],['b']);assert r['recall_at_5']==1 and r['mrr']==.5
def test_url_safety():
    assert valid_public_url('https://www.nhtsa.gov/recalls')
    assert not valid_public_url('https://nhtsa.gov.evil.example/path')
def test_demo_is_not_cited():
    assert prepare_evidence([{'url':'https://example.com','text':'x'}])==[]
