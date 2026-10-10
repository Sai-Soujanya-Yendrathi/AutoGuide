import os
import html
from pathlib import Path
from urllib.parse import urlparse

import streamlit as st
from dotenv import load_dotenv
from chatbot import answer_question

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / '.env')
st.set_page_config(page_title='AutoGuide AI | Safety Intelligence', page_icon='🚙', layout='wide', initial_sidebar_state='expanded')
DEMO = os.getenv('AUTOGUIDE_DEMO','1') == '1'
MODEL = os.getenv('OPENAI_MODEL','gpt-4o-mini')

st.markdown('''
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
.stApp {background:#f3f6fb;color:#172a46;font-family:Inter,Arial,sans-serif}
[data-testid="stMainBlockContainer"] {max-width:1540px;padding:1.4rem 2rem 4rem}
[data-testid="stSidebar"] {background:#0b1c38;border-right:1px solid #29415f}
[data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] p,
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2 {color:#e8f0ff!important}
[data-testid="stSidebar"] button {border:1px solid #3f5577!important;background:#192f52!important;color:#fff!important}
.hero-copy {background:linear-gradient(115deg,#fff,#eaf2ff);border:1px solid #e2eaf4;border-radius:17px;padding:30px;min-height:260px}
.hero-copy .eyebrow{color:#4269a6;font-size:12px;letter-spacing:1.3px;font-weight:800}
.hero-copy h1 {color:#142d51;font-size:46px;line-height:1.07;margin:16px 0 12px;font-weight:800}
.hero-copy h1 span {color:#1769e4}
.hero-copy p {font-size:15px;color:#526883;line-height:1.7;max-width:560px}
.surface {background:#fff;border:1px solid #e0e7f1;border-radius:14px;padding:18px;margin:8px 0 18px;box-shadow:0 3px 12px rgba(18,45,85,.035)}
.topic {min-height:92px;border-radius:0 0 12px 12px;padding:13px 12px;background:white;border:1px solid #e3ebf7;border-top:0;margin-top:-5px}
.topic strong{font-size:13px;color:#153254}
.topic small{display:block;font-size:11px;color:#667992;line-height:1.6;padding-top:6px}
.sec-title{font-size:21px;color:#172d4b;font-weight:800;margin:12px 0 8px}
.subtle {font-size:12px;color:#72829a}
[data-testid="stChatMessage"]{border:1px solid #e1e8f1;border-radius:13px;background:white;padding:8px}
[data-testid="stMetric"]{background:#f8fbff;border:1px solid #e8eef6;border-radius:11px;padding:11px}
.stButton>button{border-radius:9px;border:1px solid #d5e1f1;font-weight:650}
[data-testid="stImage"] img{border-radius:12px 12px 0 0} .topic small{min-height:40px} .stApp{background:#f4f7fb} .sec-title{font-size:22px} [data-testid="stSidebar"]{background:#071c37} .hero-copy{background:linear-gradient(120deg,#fdfdff,#ecf4ff)}
@media(max-width:900px){.hero-copy h1{font-size:32px}.hero-copy{min-height:0;padding:20px}}
</style>
''', unsafe_allow_html=True)

if 'messages' not in st.session_state: st.session_state.messages=[]
if 'pending' not in st.session_state: st.session_state.pending=None

def nhtsa_link(url):
    try:
        u=urlparse(str(url)); h=u.hostname or ''
        return u.scheme=='https' and (h=='nhtsa.gov' or h.endswith('.nhtsa.gov'))
    except (TypeError, ValueError): return False

def show_sources(sources):
    for n,source in enumerate(sources,1):
        if not isinstance(source,dict): continue
        url=source.get('url','')
        if nhtsa_link(url): st.link_button(f'{n}. {source.get("title","NHTSA reference")}',url,use_container_width=True)

with st.sidebar:
    st.markdown('## 🚘 AutoGuide AI')
    st.caption('SAFETY INTELLIGENCE PLATFORM')
    st.divider()
    st.markdown('**WORKSPACE**')
    st.markdown('**▣ Safety Assistant**')
    st.markdown('📄 NHTSA Resources')
    st.markdown('🛡️ Safety Features')
    st.markdown('🚨 Vehicle Recalls')
    st.divider()
    if st.button('＋ New Conversation',use_container_width=True):
        st.session_state.messages=[];st.session_state.pending=None;st.rerun()
    transcript='\n\n'.join(f'{m["role"].upper()}: {m["content"]}' for m in st.session_state.messages)
    st.download_button('↓ Export Chat',transcript or 'No conversation yet','autoguide_chat.txt','text/plain',use_container_width=True)
    st.divider()
    st.markdown('**SYSTEM DETAILS**')
    st.caption('Knowledge source: NHTSA (planned)')
    st.caption(f'Generation model: {MODEL}')
    st.caption('Mode: DEMO — sample passages' if DEMO else 'Mode: LIVE — backend required')
    st.divider()
    st.caption('MSAI 633 • Automotive Safety RAG')

st.caption('AUTOGUIDE  /  INTELLIGENCE WORKSPACE')
st.title('Vehicle Safety Intelligence')
st.caption('An evidence-grounded assistant for understanding automotive safety technologies.')

hero_l,hero_r=st.columns([1.25,1],gap='medium')
with hero_l:
    st.markdown('''<div class="hero-copy"><div class="eyebrow">DRIVE SMARTER. STAY SAFER.</div>
<h1>Auto<span>Guide</span> AI</h1><p>Ask clear questions about airbags, automatic emergency braking, driver assistance and NHTSA vehicle safety information.</p>
<p>Safety Features &nbsp; • &nbsp; Recalls &nbsp; • &nbsp; Ratings</p></div>''',unsafe_allow_html=True)
with hero_r:
    st.image(str(ROOT/'assets'/'vehicle_hero.jpg'),use_container_width=True)

main,side=st.columns([2.25,1],gap='medium')
with main:
    st.markdown('<div class="sec-title">Explore vehicle safety</div>',unsafe_allow_html=True)
    topics=[
        ('braking.jpg','🛑','Braking Systems','ABS and emergency braking technologies','How does automatic emergency braking work?'),
        ('airbags.jpg','🛡️','Airbag Safety','Passenger protection and airbag systems','How do airbags protect passengers?'),
        ('driver_assistance.jpg','📡','Driver Assistance','Blind spots, lane alerts and driver support','What does blind spot monitoring do?'),
        ('safety_ratings.jpg','⭐','Safety Ratings','Crash tests and NHTSA safety scores','How are vehicle safety ratings determined?')
    ]
    cols=st.columns(4,gap='small')
    for i,(picture,emoji,title,desc,question) in enumerate(topics):
        with cols[i]:
            st.image(str(ROOT/'assets'/picture),use_container_width=True)
            st.markdown(f'<div class="topic"><strong>{emoji} {html.escape(title)}</strong><small>{html.escape(desc)}</small></div>',unsafe_allow_html=True)
            if st.button('Explore →',key=f'topic{i}',use_container_width=True):
                st.session_state.pending=question;st.rerun()
    st.markdown('<div class="sec-title">Chat with AutoGuide AI</div>',unsafe_allow_html=True)
    if DEMO:
        st.info('Demo mode: responses show unverified sample passages only. Connect the team retriever for real NHTSA-grounded answers.')
    if not st.session_state.messages:
        with st.chat_message('assistant',avatar='🚘'):
            st.markdown('**Welcome to AutoGuide AI.** Ask about vehicle safety systems or choose a topic above.')
        st.caption('TRY A QUESTION')
        q1,q2=st.columns(2)
        for i,(label,prompt) in enumerate([('Automatic braking','How does automatic emergency braking work?'),('Airbag operation','How do airbags protect passengers?'),('Blind spot monitoring','What does blind spot monitoring do?'),('Vehicle ratings','How are vehicle safety ratings determined?')]):
            with (q1 if i%2==0 else q2):
                if st.button(label,key=f'suggest{i}',use_container_width=True):st.session_state.pending=prompt;st.rerun()
    for m in st.session_state.messages:
        with st.chat_message(m['role'],avatar='🚘' if m['role']=='assistant' else '👤'):
            st.markdown(m['content'])
            if m.get('sources'):show_sources(m['sources'])
    typed=st.chat_input('Ask about vehicle safety...')
    question=typed or st.session_state.pending
    if question:
        st.session_state.pending=None
        history=st.session_state.messages.copy()
        st.session_state.messages.append({'role':'user','content':question})
        try:
            with st.spinner('Searching knowledge and preparing answer...'):
                response=answer_question(question,history=history)
            st.session_state.messages.append({'role':'assistant','content':response.get('answer','No answer available.'),'sources':response.get('sources',[]),'trace':response.get('trace',[]),'refused':response.get('refused',False)})
        except Exception as error:
            st.session_state.messages.append({'role':'assistant','content':f'Unable to answer. Check backend configuration. ({type(error).__name__})','sources':[],'trace':[],'refused':True})
        st.rerun()
with side:
    st.markdown('<div class="sec-title">Session overview</div>',unsafe_allow_html=True)
    count=sum(m['role']=='user' for m in st.session_state.messages)
    cited=sum(bool(m.get('sources')) for m in st.session_state.messages if m['role']=='assistant')
    used=sum(len(m.get('sources',[])) for m in st.session_state.messages if m['role']=='assistant')
    a,b,c=st.columns(3)
    a.metric('Questions',count);b.metric('Cited',cited);c.metric('Sources',used)
    st.caption('NHTSA source corpus • model: '+MODEL)
    st.divider()
    st.markdown('**Evidence inspector**')
    latest=next((m for m in reversed(st.session_state.messages) if m['role']=='assistant'),None)
    if latest:
        if latest.get('refused'):st.warning('Insufficient evidence / answer unavailable')
        st.caption(f'Sources: {len(latest.get("sources",[]))}')
        show_sources(latest.get('sources',[]))
        trace=latest.get('trace',[])
        if trace:
            with st.expander(f'Retrieved passages ({len(trace)})'):
                for c in trace:
                    if not isinstance(c,dict):continue
                    st.markdown('**'+str(c.get('title','Document'))+'**')
                    st.caption(f'Score: {c.get("score","N/A")}  •  Rerank: {c.get("rerank_score","N/A")}')
                    st.write(str(c.get('text',''))[:500])
                    st.divider()
    else:st.info('Ask a question to inspect retrieved evidence.')
    st.divider()
    st.markdown('**NHTSA Quick Links**')
    for label,url in [('Vehicle safety ratings','https://www.nhtsa.gov/ratings'),('Recall information','https://www.nhtsa.gov/recalls'),('Driver assistance technologies','https://www.nhtsa.gov/vehicle-safety/driver-assistance-technologies'),('Research & Reports','https://www.nhtsa.gov/research-data')]:
        st.link_button(label+' ↗',url,use_container_width=True)
    st.caption('Educational information only; not professional mechanical advice.')
