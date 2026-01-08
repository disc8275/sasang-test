# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# ==========================================
# [설정] 이메일 발송 정보 (보안 적용)
# ==========================================
try:
    SENDER_EMAIL = st.secrets["SENDER_EMAIL"]
    SENDER_PASSWORD = st.secrets["SENDER_PASSWORD"]
except:
    # 로컬 테스트용 더미 값 (실제 배포시 secrets 설정 필수)
    SENDER_EMAIL = "test@example.com"
    SENDER_PASSWORD = "password"

RECEIVER_EMAIL = "ds1lih@naver.com" 
# ==========================================
# 1. 페이지 설정 및 스타일
# ==========================================
st.set_page_config(page_title="사상체질 자가진단", layout="centered")

st.markdown("""
    <style>
    /* [화면 표시용 스타일] */
    h1 { 
        font-size: 1.5rem; 
        font-weight: 700;
    }
    h3 { 
        color: #16a085; 
        font-size: 1.2rem; 
    }
    .stButton button {
        height: 3rem;
        font-size: 1.2rem;
        border-radius: 10px;
    }
    div[data-testid="stRadio"] label {
        font-size: 1.1rem !important;
        padding: 10px 0;
        cursor: pointer;
        color: var(--text-color) !important; 
    }
    .question-text {
        font-size: 1.3rem;
        font-weight: bold;
        color: var(--text-color); 
        margin-bottom: 20px;
        line-height: 1.5;
    }
    
    /* [공통 테이블 스타일] */
    .guide-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
        margin-bottom: 20px;
        font-size: 1rem;
    }
    .guide-table th {
        background-color: #f0f2f6;
        color: #333;
        padding: 12px;
        border: 1px solid #ddd;
        text-align: center;
        font-weight: bold;
    }
    .guide-table td {
        padding: 10px;
        border: 1px solid #ddd;
        vertical-align: top;
        color: var(--text-color);
    }
    
    @media (prefers-color-scheme: dark) {
        .guide-table th {
            background-color: #444;
            color: #fff;
            border-color: #666;
        }
        .guide-table td {
            border-color: #666;
        }
    }

    /* ============================================================ */
    /* [인쇄 전용 스타일]                                            */
    /* ============================================================ */
    @media print {
        * { 
            color: black !important; 
            background-color: white !important;
            -webkit-print-color-adjust: exact !important; 
            print-color-adjust: exact !important; 
        }

        .guide-table th {
            background-color: #eee !important;
            color: black !important;
            border: 1px solid black !important;
        }
        .guide-table td {
            color: black !important;
            border: 1px solid black !important;
        }

        .page-break { 
            page-break-before: always !important; 
            display: block !important;
            height: 1px;
        }

        @page {
            margin: 0mm !important; 
            size: auto;
        }

        html, body {
            margin: 0 !important;
            padding: 0 !important;
            height: auto !important;
            min-height: 0 !important;
            overflow: visible !important;
        }
        
        .stApp {
            min-height: 0 !important;
            height: auto !important;
            overflow: visible !important;
            background-color: white !important;
        }

        .block-container {
            margin: 15mm 15mm 0 15mm !important;
            padding-top: 0 !important;
            padding-bottom: 0 !important;
            width: auto !important;
        }

        section[data-testid="stSidebar"], 
        header, 
        footer, 
        .stAppDeployButton, 
        button, 
        .stButton, 
        div[data-testid="stHorizontalBlock"], 
        .stProgress,
        iframe {
            display: none !important;
            height: 0 !important;
            width: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
            opacity: 0 !important;
            visibility: hidden !important;
        }
        
        iframe[title="streamlit.components.v1.components.html"] {
            display: none !important;
            height: 0 !important;
        }
    }
    /* [추가] 체질 명칭 가로 배열 및 검정색 설정 */
    .constitution-container {
        display: flex;
        justify-content: space-around;
        align-items: center;
        background-color: #ffffff; /* 배경 흰색 */
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #dddddd;
        margin: 20px 0;
    }
    .constitution-box {
        text-align: center;
        flex: 1;
    }
    .constitution-label {
        font-size: 1.2rem;
        font-weight: bold;
        color: #000000 !important; /* 글자색 검정 고정 */
        display: block;
        margin-bottom: 5px;
    }
    .constitution-score {
        font-size: 1.1rem;
        color: #333333 !important;
    }
    </style>
    """, unsafe_allow_html=True)

TYPE_MAP = {'TY': '태양인', 'SY': '소양인', 'TE': '태음인', 'SE': '소음인'}

# 질문 목록 정의
QUESTIONS = [
    {"q": "오래 서 있거나 걷는 게 유난히 힘들고 다리에 힘이 없나요?", "type": "TY"},
    {"q": "가슴이 넓고 딱 벌어졌지만, 엉덩이 쪽은 빈약한 편인가요?", "type": "SY"},
    {"q": "배와 허리 부위가 굵고, 전체적으로 뼈대가 굵고 살집이 있나요?", "type": "TE"},
    {"q": "전체적으로 체구가 작고 마른 편이며, 엉덩이가 발달했나요?", "type": "SE"},
    {"q": "눈매가 날카롭고 강렬해서, 남들이 쳐다보기 어려워하나요?", "type": "TY"},
    {"q": "눈매가 날렵하고 입술이 얇으며, 턱이 뾰족한 편인가요?", "type": "SY"},
    {"q": "이목구비가 큼직하고 입술이 두툼해서 점잖은 인상인가요?", "type": "TE"},
    {"q": "인상이 부드럽고 얌전하며 오밀조밀하게 생겼나요?", "type": "SE"},
    {"q": "추진력이 강하고 결단력이 있지만, 남의 말을 잘 안 듣나요?", "type": "TY"},
    {"q": "성격이 급하고 활발하며 솔직하지만, 싫증을 잘 내나요?", "type": "SY"},
    {"q": "느긋하고 변화를 싫어하며, 속마음을 잘 드러내지 않나요?", "type": "TE"},
    {"q": "꼼꼼하고 내성적이며, 작은 일에도 걱정이 많은 편인가요?", "type": "SE"},
    {"q": "화가 나면 확 폭발했다가도 금방 풀리는 편인가요?", "type": "SY"},
    {"q": "새로운 일을 벌이는 것을 좋아하고 사람 사귀는 걸 즐기나요?", "type": "TY"},
    {"q": "겁이 많고 가슴이 자주 두근거리나요?", "type": "TE"},
    {"q": "불안한 마음이 자주 들고 질투심이 좀 있는 편인가요?", "type": "SE"},
    {"q": "음식을 먹으면 자꾸 토하거나 체하는 증상이 심한가요?", "type": "TY"},
    {"q": "소화가 아주 잘 돼서 과식하는 편이고, 배고픔을 못 참나요?", "type": "SY"},
    {"q": "무엇이든 잘 먹고, 많이 먹어도 소화에 큰 문제가 없나요?", "type": "TE"},
    {"q": "입이 짧고 소화가 잘 안 되며, 조금만 많이 먹어도 불편한가요?", "type": "SE"},
    {"q": "찬물이나 아이스크림을 먹어도 배탈이 잘 안 나나요?", "type": "SY"},
    {"q": "찬 음식을 먹으면 바로 설사를 하거나 배가 아픈가요?", "type": "SE"},
    {"q": "평소 땀이 잘 안 나고, 땀을 흘리면 오히려 개운한가요?", "type": "TE"},
    {"q": "조금만 움직여도 땀이 나고, 땀 흘리면 기운이 쏙 빠지나요?", "type": "SE"},
    {"q": "머리나 얼굴, 가슴 쪽에만 유독 땀이 많이 나나요?", "type": "SY"},
    {"q": "운동으로 땀을 흠뻑 흘려야 몸이 가볍고 컨디션이 좋나요?", "type": "TE"},
    {"q": "소변을 시원하게 잘 보면 몸이 건강하다고 느끼나요?", "type": "TY"},
    {"q": "변비가 있어서 며칠 화장실을 못 가도 배가 안 아프나요?", "type": "TE"},
    {"q": "변비가 생기면 가슴이 답답하고 무척 괴롭나요?", "type": "SY"},
    {"q": "대변이 묽지 않고 모양 있게 잘 나오면 속이 편한가요?", "type": "SY"},
    {"q": "설사를 하면 기운이 쫙 빠지고 배가 아픈가요?", "type": "SE"},
    {"q": "추위를 아주 많이 타고 손발이 차며, 여름에도 이불을 덮나요?", "type": "SE"},
    {"q": "더위를 못 참아서 찬물을 벌컥벌컥 마시나요?", "type": "SY"},
    {"q": "이유 없이 다리에 힘이 풀려서 걷기 힘들 때가 있나요?", "type": "TY"},
    {"q": "피부나 코, 기관지가 건조하고 뻑뻑한 느낌이 드나요?", "type": "TE"},
    {"q": "오후나 밤이 되면 몸에 열이 확 오르는 느낌이 있나요?", "type": "SY"},
    {"q": "피곤하면 눈이 쉽게 충혈되고 건조해지나요?", "type": "TE"},
]

OPTIONS = ["전혀 아니다", "아니다", "보통이다", "그렇다", "매우 그렇다"]

# ==========================================
# 세션 상태 초기화
# ==========================================
if 'step' not in st.session_state:
    st.session_state['step'] = 0  
if 'user_info' not in st.session_state:
    st.session_state['user_info'] = {}
if 'answers_score' not in st.session_state:
    st.session_state['answers_score'] = [2] * len(QUESTIONS) 
if 'answers_log' not in st.session_state:
    st.session_state['answers_log'] = [""] * len(QUESTIONS)
if 'symptom_answers' not in st.session_state:
    st.session_state['symptom_answers'] = {}
if 'final_result' not in st.session_state:
    st.session_state['final_result'] = None

# ==========================================
# 로직 함수 (이메일 및 추천)
# ==========================================
def send_email_result(info, constitution, scores, recommendation, answers_summary):
    try:
        subject = f"[사상체질진단 결과] {info['name']}님 ({info['birth']})"
        scores_str = ", ".join([f"{TYPE_MAP[k]}: {v:.1f}점" for k, v in scores.items()])

        body = f"""
[사용자 기본 정보]
- 이름: {info['name']}
- 생년월일: {info['birth']}
- 키/몸무게: {info.get('height','')}cm / {info.get('weight','')}kg
- 진단 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

[건강 상세 정보]
- 약: {info.get('meds','')}
- 병력: {info.get('history','')}
- 코멘트: {info.get('comment','')}

[진단 결과]
- 체질: {TYPE_MAP.get(constitution, '알수없음')}
- 점수: {scores_str}

[추천 처방 및 병증]
- 병증: {recommendation['condition']}
- 처방: {recommendation['prescription']}
- 설명: {recommendation['desc']}

[설문 응답 상세]
{answers_summary}
        """
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Email Fail: {e}")
        return False

def get_recommendation(constitution, symptoms):
    pain = symptoms.get('pain')
    sweat = symptoms.get('sweat')
    stool = symptoms.get('stool')
    
    if constitution == 'SE':
        if pain == "몸살 기운 (으슬으슬 춥고 열이 남)":
            if sweat == "땀이 거의 나지 않는다":
                return {"condition": "소음인 울광체질 (내부 양기가 갇힌 상태)", "desc": "대변이 잘 나오지 않거나 몸에 열감이 느껴지며, 심할 경우 불안함이나 조급함이 나타날 수 있습니다.", "prescription": "천궁계지탕, 궁귀향소산, 향부자팔물탕 등"}
            else: 
                return {"condition": "소음인 망양체질 (양기가 허약해 땀으로 빠지는 상태)", "desc": "식은땀이 잘 나며 잘 지치고 피로를 자주 느낄 수 있습니다", "prescription": "황기계지탕, 보중익기탕, 승양익기탕 등"}
        else: 
            if stool == "설사를 하거나 묽다":
                return {"condition": "소음인 태음병 (속이 냉하고 배탈이 잦음)", "desc": "배가 차갑고 복통 또는 설사가 잘 나며, 소화 기능 약합니다.", "prescription": "백하오이중탕, 곽향정기산 등"}
            else:
                return {"condition": "소음인 태음병 (위장이 차갑고 막힘)", "desc": "명치 밑이 답답하고 소화가 안 됩니다.", "prescription": "곽향정기산, 향사양위탕 등"}

    elif constitution == 'SY':
        if pain == "몸살 기운 (으슬으슬 춥고 열이 남)":
            if stool == "설사를 하거나 묽다":
                return {"condition": "소양인 망음병 (겉은 열, 속은 냉)", "desc": "위로는 열이나고 답답하지만, 아래는 차거나 설사가 나기 쉽고 몸이 피곤합니다.", "prescription": "형방지황탕, 저령차전자탕, 활석고삼탕 등"}
            else: 
                return {"condition": "소양인 소양상풍병 (열기가 갇힘)", "desc": "머리가 아프고 몸에 열이 나며, 가슴이 답답하고 아픈 증상으로 발전하기 쉽습니다.", "prescription": "형방패독산, 형방도적산, 형방사백산 등"}
        else: 
            if stool == "변비가 있거나 잘 안 나온다":
                return {"condition": "소양인 흉격열병 (가슴에 열이 꽉 참)", "desc": "변비가 심하고 얼굴이 붉어지며 갈증을 자주 느킵니다.", "prescription": "형방사백산, 지황백호탕, 양격산화탕 등"}
            else:
                return {"condition": "소양인 음허오열병 (신장 기운 약화)", "desc": "오후에 얼굴에 열이 오르거나 허리/다리가 약해진 느낌이에요.", "prescription": "독활지황탕, 숙지황고삼탕 등"}

    elif constitution == 'TE':
        if pain == "몸살 기운 (으슬으슬 춥고 열이 남)":
            return {"condition": "태음인 위완한병 (폐/대장이 차가움)", "desc": "목이 건조하고 답답하며, 가슴이 두근거리거나, 땀은 나지 않으면서 몸이 무겁게 느껴집니다.", "prescription": "태음조위탕, 조위승청탕, 녹용대보탕 등"}
        else: 
            return {"condition": "태음인 간열병 (간에 열이 많음)", "desc": "얼굴이 붉고 눈이 아프거나, 갈증이 심하고 변비가 잘 생깁니다.", "prescription": "갈근해기탕, 열다한소탕, 청폐사간탕 등"}

    elif constitution == 'TY':
        return {"condition": "태양인 특이 병증", "desc": "다리에 힘이 빠지거나(해역), 음식을 먹고 토하는 증상(열격)을 주의해야 해요.", "prescription": "오가피장척탕, 미후등식장탕"}
    
    return {"condition": "정보 부족", "desc": "", "prescription": ""}

def go_shortcut(selected_type):
    if 'name' not in st.session_state['user_info']:
        st.session_state['user_info'] = {
            'name': '방문자', 'birth': '-', 
            'height': '-', 'weight': '-', 
            'meds': '-', 'history': '-', 'comment': '체질 바로보기 선택'
        }
    
    fake_scores = {'TY': 20, 'SY': 20, 'TE': 20, 'SE': 20}
    fake_scores[selected_type] = 100.0
    
    fake_symptoms = {}
    if selected_type == 'SE':
        fake_symptoms = {'pain': "몸살 기운 (으슬으슬 춥고 열이 남)", 'sweat': "땀이 거의 나지 않는다", 'stool': "설사를 하거나 묽다"}
    elif selected_type == 'SY':
        fake_symptoms = {'pain': "속 문제", 'stool': "변비가 있거나 잘 안 나온다", 'sweat': "보통"}
    elif selected_type == 'TE':
        fake_symptoms = {'pain': "몸살 기운 (으슬으슬 춥고 열이 남)", 'sweat': "보통", 'stool': "보통"}
    else: # TY
        fake_symptoms = {'pain': "보통", 'sweat': "보통", 'stool': "보통"}
        
    rec = get_recommendation(selected_type, fake_symptoms)
    
    st.session_state['final_result'] = {
        'code': selected_type,
        'scores': fake_scores,
        'rec': rec
    }
    st.session_state['step'] = 999
    st.rerun()

# ==========================================
# 화면 렌더링 함수
# ==========================================
def go_next():
    st.session_state['step'] += 1

def go_prev():
    if st.session_state['step'] > 0:
        st.session_state['step'] -= 1

def main():
    current_step = st.session_state['step']
    total_q = len(QUESTIONS)
    
    # ----------------------------------
    # STEP 0: 기본 정보 입력
    # ----------------------------------
    if current_step == 0:
        st.markdown("<h1 style='text-align: center;'>사상체질 자가진단</h1>", unsafe_allow_html=True)
        st.info("이 프로그램은 디스코한의원에서 사상체질병증 한의표준임상진료지침을 바탕으로 제작했습니다. 모든 질문에 솔직하게 답변해 주세요.")
        
        with st.form("info_form"):
            name = st.text_input("이름 (필수)", placeholder="홍길동")
            birth = st.text_input("생년월일 (필수)", placeholder="예: 1980.01.01")
            col1, col2 = st.columns(2)
            with col1: height = st.text_input("키 (cm)", placeholder="175")
            with col2: weight = st.text_input("몸무게 (kg)", placeholder="70")
            
            meds = st.text_input("복용 중인 약 (선택)")
            history = st.text_input("과거 병력 (선택)")
            comment = st.text_area("증상 및 기타 (선택)", height=80)
            
            if st.form_submit_button("진단 시작하기", use_container_width=True):
                if not name or not birth:
                    st.error("이름과 생년월일은 필수입니다.")
                else:
                    st.session_state['user_info'] = {
                        'name': name, 'birth': birth, 'height': height,
                        'weight': weight, 'meds': meds, 'history': history, 'comment': comment
                    }
                    go_next()
                    st.rerun()

        st.write("")
        st.markdown("---")
        st.subheader("⚡ 체질별 결과 바로보기 (설문 건너뛰기)")
        st.caption("아래 버튼을 누르면 설문 없이 해당 체질의 상세 가이드와 처방 예시를 바로 확인합니다.")
        
        if name:
             st.session_state['user_info']['name'] = name
             st.session_state['user_info']['birth'] = birth

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            if st.button("☀️ 태양인", use_container_width=True):
                go_shortcut('TY')
        with c2:
            if st.button("🔥 소양인", use_container_width=True):
                go_shortcut('SY')
        with c3:
            if st.button("🌲 태음인", use_container_width=True):
                go_shortcut('TE')
        with c4:
            if st.button("💧 소음인", use_container_width=True):
                go_shortcut('SE')


    # ----------------------------------
    # STEP 1 ~ N: 개별 질문
    # ----------------------------------
    elif 1 <= current_step <= total_q:
        q_idx = current_step - 1
        q_data = QUESTIONS[q_idx]
        
        progress = q_idx / total_q
        st.progress(progress)
        st.caption(f"질문 {current_step} / {total_q}")
        
        st.markdown(f"<div class='question-text'>Q{current_step}.<br>{q_data['q']}</div>", unsafe_allow_html=True)
        
        default_idx = st.session_state['answers_score'][q_idx]
        
        choice = st.radio(
            "답변을 선택하세요",
            OPTIONS,
            index=default_idx,
            key=f"q_{q_idx}",
            horizontal=False,
            label_visibility="collapsed"
        )
        
        st.write("")
        st.write("")
        
        col_prev, col_next = st.columns(2)
        
        with col_prev:
            if st.button("⬅️ 이전", use_container_width=True):
                go_prev()
                st.rerun()
                
        with col_next:
            if st.button("다음 ➡️", use_container_width=True):
                score_val = OPTIONS.index(choice)
                st.session_state['answers_score'][q_idx] = score_val
                st.session_state['answers_log'][q_idx] = f"Q{current_step}. {q_data['q']} : {choice}"
                go_next()
                st.rerun()

    # ----------------------------------
    # STEP N+1 ~ N+3: 증상 질문
    # ----------------------------------
    elif current_step == total_q + 1:
        st.progress(1.0)
        st.markdown("<div class='question-text'>거의 다 왔습니다!<br>Q. 아플 때 주로 어떤 느낌인가요?</div>", unsafe_allow_html=True)
        ans = st.radio("통증 유형", ["몸살 기운 (으슬으슬 춥고 열이 남)", "속 문제 (소화가 안 되고, 가슴이 답답하거나 배가 아픔)"], key="sym_pain", horizontal=False)
        
        col_prev, col_next = st.columns(2)
        with col_prev:
            if st.button("⬅️ 이전", use_container_width=True):
                go_prev()
                st.rerun()
        with col_next:
            if st.button("다음 ➡️", use_container_width=True):
                st.session_state['symptom_answers']['pain'] = ans
                go_next()
                st.rerun()

    elif current_step == total_q + 2:
        st.progress(1.0)
        st.markdown("<div class='question-text'>Q. 아플 때 땀은 어떻게 나나요?</div>", unsafe_allow_html=True)
        ans = st.radio("땀 유형", ["땀이 거의 나지 않는다", "식은땀이 나거나 땀이 축축하게 난다"], key="sym_sweat", horizontal=False)
        
        col_prev, col_next = st.columns(2)
        with col_prev:
            if st.button("⬅️ 이전", use_container_width=True):
                go_prev()
                st.rerun()
        with col_next:
            if st.button("다음 ➡️", use_container_width=True):
                st.session_state['symptom_answers']['sweat'] = ans
                go_next()
                st.rerun()

    elif current_step == total_q + 3:
        st.progress(1.0)
        st.markdown("<div class='question-text'>Q. 대변 상태는 어떤가요?</div>", unsafe_allow_html=True)
        ans = st.radio("대변 유형", ["변비가 있거나 잘 안 나온다", "설사를 하거나 묽다", "평소와 비슷하다(보통)"], key="sym_stool", horizontal=False)
        
        col_prev, col_next = st.columns(2)
        with col_prev:
            if st.button("⬅️ 이전", use_container_width=True):
                go_prev()
                st.rerun()
        with col_next:
            if st.button("결과 보기", use_container_width=True):
                st.session_state['symptom_answers']['stool'] = ans
                
                raw_scores = {'TY': 0, 'SY': 0, 'TE': 0, 'SE': 0}
                type_counts = {'TY': 0, 'SY': 0, 'TE': 0, 'SE': 0}
                
                for i, score in enumerate(st.session_state['answers_score']):
                    q_type = QUESTIONS[i]['type']
                    raw_scores[q_type] += score
                    type_counts[q_type] += 1
                
                avg_scores = {k: (v / type_counts[k] if type_counts[k] > 0 else 0) for k, v in raw_scores.items()}
                max_score = max(avg_scores.values())
                result_types = [k for k, v in avg_scores.items() if v == max_score]
                my_type_code = result_types[0] 
                
                recommendation = get_recommendation(my_type_code, st.session_state['symptom_answers'])
                
                with st.spinner("결과 분석 및 전송 중..."):
                    answers_summary = "\n".join(st.session_state['answers_log'])
                    answers_summary += f"\n[증상] Pain: {st.session_state['symptom_answers']['pain']}"
                    answers_summary += f"\n[증상] Sweat: {st.session_state['symptom_answers']['sweat']}"
                    answers_summary += f"\n[증상] Stool: {st.session_state['symptom_answers']['stool']}"
                    
                    send_email_result(
                        st.session_state['user_info'], my_type_code, avg_scores, recommendation, answers_summary
                    )
                
                st.session_state['final_result'] = {
                    'code': my_type_code,
                    'scores': avg_scores,
                    'rec': recommendation
                }
                st.session_state['step'] = 999
                st.rerun()

    # ----------------------------------
    # [STEP 999] 통합 결과 화면 (순서 고정 버전)
    # ----------------------------------
    elif current_step == 999:
        res = st.session_state['final_result']
        my_code = res['code']
        scores = res['scores']

        st.balloons()
        
        # 제목 표시
        max_score = max(scores.values())
        tied_keys = [k for k, v in scores.items() if v == max_score]

        if len(tied_keys) > 1:
            tied_names = [TYPE_MAP[k] for k in tied_keys]
            title_text = " 또는 ".join(tied_names)
            st.title(f"🎉 [{title_text}] 확률이 동일합니다!")
        else:
            st.title(f"🎉 당신은 [{TYPE_MAP[my_code]}] 입니다!")

        # [요청사항 적용 1] 닥터 디스코의 한마디 (결과 상단 배치)
        st.info("""
        💡 **닥터 디스코의 한마디**
        
        이 결과는 건강 관리를 돕는 가벼운 길잡이로만 활용해 주시고, 정확한 체질 감별과 건강 상담은 전문 지식을 갖춘 한의사와의 따뜻한 진료를 통해 확인해 보세요.
        """)

        st.write("### 📊 체질별 분석 점수")
        
        # 1. 상단 요약 박스 (순서: TY -> TE -> SY -> SE)
        st.markdown(f"""
            <div class="constitution-container">
                <div class="constitution-box">
                    <span class="constitution-label">태양인</span>
                    <span class="constitution-score">{scores.get('TY', 0):.1f}점</span>
                </div>
                <div class="constitution-box">
                    <span class="constitution-label">태음인</span>
                    <span class="constitution-score">{scores.get('TE', 0):.1f}점</span>
                </div>
                <div class="constitution-box">
                    <span class="constitution-label">소양인</span>
                    <span class="constitution-score">{scores.get('SY', 0):.1f}점</span>
                </div>
                <div class="constitution-box">
                    <span class="constitution-label">소음인</span>
                    <span class="constitution-score">{scores.get('SE', 0):.1f}점</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.write("") 
        
        # 2. 하단 막대 차트 순서 고정 (태양 -> 태음 -> 소양 -> 소음)
        ordered_keys = ['TY', 'TE', 'SY', 'SE']
        ordered_names = [TYPE_MAP[k] for k in ordered_keys]
        
        chart_data = {
            '체질': ordered_names,
            '점수': [scores.get(k, 0) for k in ordered_keys]
        }
        chart_df = pd.DataFrame(chart_data)
        
        # [핵심 수정] 범주형(Categorical) 타입을 사용하여 정렬 순서를 강제로 고정합니다.
        chart_df['체질'] = pd.Categorical(chart_df['체질'], categories=ordered_names, ordered=True)
        
        # 차트 출력 (정렬된 상태 유지)
        st.bar_chart(chart_df.set_index('체질'))
        
        st.markdown('<div class="page-break"></div>', unsafe_allow_html=True)
        st.markdown("---")
        
        # =========================================================
        # 상세 건강 가이드 출력 (영문 표기 제거 완료)
        # =========================================================
        
        if my_code == 'TE': # 태음인
            st.header("📋 태음인 상세 가이드")
            
            st.markdown("""
            **1. 태음인의 특징**
            * 섭취한 에너지를 소모시키고 배설시키는 것이 취약합니다.
            * 체구가 큰 편이고, 식욕과 위장기능이 좋아 비만해지기 쉽습니다.
            """)
            st.subheader("🚨 건강이 안 좋아지면 나타나는 증상")
            st.warning("""
            * **체중/식욕:** 살이 찌고, 배가 부른데도 자꾸 먹게 됩니다.
            * **배설:** 대변이 굳거나 설사가 잦아지는 등 양상이 달라집니다.
            * **신체:** 땀이 잘 나지 않거나, 상체로만 진땀이 많이 납니다. 아침에 얼굴/손발이 붓습니다.
            * **피부:** 얼굴이 붉어지고 열감이 많으며, 피부 트러블이 잦습니다.
            """)
            st.info("""
            **💡 평소 생활 실천 사항**
            1. **관리:** 변비와 체중 증가를 항상 경계해야 합니다.
            2. **식사:** 과식/폭식/야식을 피하고, 천천히 먹습니다. 식후 바로 눕지 마세요.
            3. **운동:** 땀을 흘릴 정도의 유산소 운동(열량 소모 많은 운동)이 좋습니다.
            """)
            
            st.subheader("🍽️ 식품군별 권장 음식 상세")
            st.markdown("""
            <table class="guide-table">
            <thead>
                <tr><th>분류</th><th>권장 음식</th></tr>
            </thead>
            <tbody>
                <tr><td>곡류군</td><td>현미, 율무, 콩, 고구마, 옥수수, 토란, 밤, 마, 잣, 호두, 땅콩</td></tr>
                <tr><td>저지방 어육류</td><td>소고기(사태, 홍두깨), 대구, 조기, 명태, 민어, 오징어</td></tr>
                <tr><td>중지방 어육류</td><td>소고기(등심, 안심), 고등어, 꽁치, 갈치, 두부, 콩비지</td></tr>
                <tr><td>고지방 어육류</td><td>소갈비, 뱀장어, 유부, 치즈</td></tr>
                <tr><td>채소군</td><td>무, 호박, 콩나물, 고사리, 버섯, 김, 미역, 다시마, 도라지, 연근, 당근</td></tr>
                <tr><td>지방군/우유/과일</td><td>들기름, 올리브유, 우유, 두유 / 배, 매실, 자두, 살구</td></tr>
            </tbody>
            </table>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            # [수정됨] 
            st.subheader("🏥 태음인 체질 증상 및 질환")
            st.markdown("""
            **특성:** 간대폐소(肝大肺小). 흡수 기능은 강하나 발산과 배출 기능이 약해 노폐물이 잘 쌓이고, 호흡기와 심혈관이 취약함.

            * **노화 (대사/순환):** 혈액순환 장애, 고혈압, 당뇨, 고지혈증, 협심증, 중풍, 치매, 비만, 간암, 대장암
            * **수험생/청소년:** 지구력은 좋으나 비만하기 쉽고, 호흡기 약화로 인한 집중력 저하.
            * **여성:** 다낭성 난소 증후군, 비만형 생리불순.
            * **일반 (간/장):** 지방간, 변비, 과민성 대장(설사보다는 가스 참).

            ### 🥗 추천 약재·음식·영양제
            <table class="guide-table">
            <thead>
                <tr><th>분류</th><th>추천 목록 및 효능 요약</th></tr>
            </thead>
            <tbody>
                <tr>
                    <td style="font-weight:bold;">한약재</td>
                    <td>
                        녹용: 기혈 보강, 소아 성장 및 노인 항노화의 핵심 약재.<br>
                        맥문동·길경(도라지): 약한 폐/기관지를 윤택하게 하고 가래 배출.<br>
                        갈근(칡): 목덜미 긴장을 풀고(수험생), 갱년기 열감 해소.<br>
                        의이인(율무): 습담(노폐물) 제거, 다이어트 및 부종 완화.
                    </td>
                </tr>
                <tr>
                    <td style="font-weight:bold;">음식</td>
                    <td>
                        소고기: 양질의 단백질 공급원.<br>
                        무, 배, 연근: 폐 기운을 돕고 소화를 촉진.<br>
                        호두, 잣: 뇌 기능 활성화(치매/수험생) 및 변비 예방.
                    </td>
                </tr>
                <tr>
                    <td style="font-weight:bold;">영양제</td>
                    <td>
                        오메가-3: 혈행 개선, 고지혈증 예방 (태음인 필수).<br>
                        비타민 A/D: 호흡기 점막 보호 및 면역력 강화.<br>
                        밀크씨슬: 간의 해독 작용 보조 (간열이 많은 경우 주의).
                    </td>
                </tr>
            </tbody>
            </table>
            """, unsafe_allow_html=True)

        elif my_code == 'SY': # 소양인
            st.header("📋 소양인 상세 가이드")
            
            st.markdown("""
            **1. 소양인의 특징**
            * 몸에 열이 많습니다.
            * 신경이 예민하고, 피부, 장, 방광 등이 과민한 편입니다.
            """)
            st.subheader("🚨 건강이 안 좋아지면 나타나는 증상")
            st.warning("""
            * **수면/정서:** 잠들기 어렵고 자주 깨며, 마음이 조급하고 불안합니다.
            * **배설:** 소변을 자주 보거나 색이 진하며, 변비나 설사가 잦습니다.
            * **신체:** 얼굴이나 피부 트러블이 잦고, 입이 마르며 갈증이 납니다.
            * **소화:** 가슴이 답답하고 속이 쓰리거나 구역질을 합니다.
            """)
            st.info("""
            **💡 평소 생활 실천 사항**
            1. **수면/마음:** 충분한 수면을 취하고, 매사에 여유를 가지려 노력하세요.
            2. **식사:** 천천히 식사하며, 서늘한 성질의 음식/해물/채소가 좋습니다.
            3. **피할 것:** 맵고 짠 음식, 성질이 더운 음식을 피하세요.
            4. **운동:** 하체를 강화시켜 주는 운동(등산, 자전거 등)이 좋습니다.
            """)

            st.subheader("🍽️ 식품군별 권장 음식 상세")
            st.markdown("""
            <table class="guide-table">
            <thead>
                <tr><th>분류</th><th>권장 음식</th></tr>
            </thead>
            <tbody>
                <tr><td>곡류군</td><td>보리, 팥, 녹두 / (메밀, 고구마, 토란)</td></tr>
                <tr><td>저지방 어육류</td><td>돼지고기(살코기), 오리고기, 복어, 굴, 새우, 오징어, 낙지, 조개, 게, 해삼</td></tr>
                <tr><td>중지방 어육류</td><td>돼지고기(안심), 계란 / (두부, 고등어, 꽁치)</td></tr>
                <tr><td>고지방 어육류</td><td>삼겹살, 족발, 돼지갈비, 베이컨</td></tr>
                <tr><td>채소군</td><td>오이, 가지, 배추, 상추, 우엉, 숙주나물, 죽순</td></tr>
                <tr><td>지방군/우유/과일</td><td>참깨, 참기름, 우유 / 딸기, 수박, 바나나, 참외, 메론, 키위</td></tr>
            </tbody>
            </table>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            # [수정됨] 
            st.subheader("🏥 소양인 체질 증상 및 질환")
            st.markdown("""
            **특성:** 비대신소(脾大腎小). 소화력은 좋으나 신장/방광/자궁이 약함. 상체로 열이 잘 오르고(상열), 하체가 약하며 진액(수분)이 부족하기 쉬움.

            * **노화 (비뇨/골격):** 전립선 비대, 요실금, 골다공증, 안구건조, 뇌출혈, 심근경색
            * **수험생/청소년:** 성조숙증 주의, ADHD 성향(산만함), 열로 인한 두통.
            * **여성:** 질 건조증, 방광염, 상열감 심한 갱년기.
            * **일반 (위장/탈모):** 스트레스성 위염(속쓰림), 정수리 열로 인한 탈모.

            ### 🥗 추천 약재·음식·영양제
            <table class="guide-table">
            <thead>
                <tr><th>분류</th><th>추천 목록 및 효능 요약</th></tr>
            </thead>
            <tbody>
                <tr>
                    <td style="font-weight:bold;">한약재</td>
                    <td>
                        숙지황: 신장 기운 보강(생리, 뼈), 진액 보충(안구건조).<br>
                        구기자·산수유: 하체 강화, 정력 증진, 눈 피로 해소.<br>
                        복령: 소변을 잘 나오게 하고 마음을 안정시킴(불면증).
                    </td>
                </tr>
                <tr>
                    <td style="font-weight:bold;">음식</td>
                    <td>
                        돼지고기, 오리고기: 찬 성질로 몸의 화기를 내리고 보양.<br>
                        수박, 참외, 오이: 천연 이뇨작용 및 체내 열 배출.<br>
                        굴, 전복: 바다의 음기를 머금어 신장 보강 및 피부 미용.
                    </td>
                </tr>
                <tr>
                    <td style="font-weight:bold;">영양제</td>
                    <td>
                        알로에: 위장의 열을 내리고 배변 활동 보조.<br>
                        마그네슘: 신경 과흥분 조절(불면, 눈떨림) 및 근육 이완.<br>
                        콜라겐: 진액 부족으로 인한 피부 노화 및 관절 건조 예방.
                    </td>
                </tr>
            </tbody>
            </table>
            """, unsafe_allow_html=True)

        elif my_code == 'SE': # 소음인
            st.header("📋 소음인 상세 가이드")
            
            st.markdown("""
            **1. 소음인의 특징**
            * 몸이 찬 편입니다.
            * 전반적인 체력이 약한 편입니다.
            * 소화기의 기능이 약해지기 쉽습니다.
            """)
            st.subheader("🚨 건강이 안 좋아지면 나타나는 증상")
            st.warning("""
            * **전신:** 무리를 하지 않았는데도 피로감이 지속되고, 아침에 일어나기 힘듭니다.
            * **소화:** 식욕이 떨어지고 소화가 잘 안 되며, 배에 가스가 찹니다.
            * **배설:** 설사를 자주 하거나, 대변이 가늘면서 시원하지 않습니다.
            * **기타:** 손발과 배가 차고, 특별한 이유 없이 마음이 늘 불안합니다.
            """)
            st.info("""
            **💡 평소 생활 실천 사항**
            1. **보온:** 항상 몸을 따뜻하게 합니다.
            2. **휴식:** 과로를 피하고 적절한 휴식이 필요합니다.
            3. **식사:** 규칙적인 식사가 중요하며, 따뜻한 성질의 음식이나 약간의 자극성 있는 조미료가 좋습니다.
            """)

            st.subheader("🍽️ 식품군별 권장 음식 상세")
            st.markdown("""
            <table class="guide-table">
            <thead>
                <tr><th>분류</th><th>권장 음식</th></tr>
            </thead>
            <tbody>
                <tr><td>곡류군</td><td>백미, 차조, 찹쌀, 감자, 옥수수 / (떡, 누룽지)</td></tr>
                <tr><td>저지방 어육류</td><td>닭고기(껍질/기름 제거), 명태, 조기, 도미, 대구, 민어, 농어, 가자미, 멸치</td></tr>
                <tr><td>중지방 어육류</td><td>삼치, 갈치, 장어, 민어, 도루묵</td></tr>
                <tr><td>고지방 어육류</td><td>닭고기(껍질 포함), 개고기, 뱀장어</td></tr>
                <tr><td>채소군</td><td>깻잎, 냉이, 시금치, 양배추, 브로콜리, 마늘, 파, 고추, 양파, 부추, 쑥</td></tr>
                <tr><td>지방군/우유/과일</td><td>들깨, 참기름, 산양유 / 사과, 귤, 토마토, 복숭아, 대추, 유자</td></tr>
            </tbody>
            </table>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            # [수정됨] 
            st.subheader("🏥 소음인 체질 증상 및 질환")
            st.markdown("""
            **특성:** 신대비소(腎大脾小). 신장/생식기 기능은 좋으나 위장이 차고 소화력이 약함. 몸이 차고(냉증), 예민하며 체력이 약해지기 쉬움.

            * **노화 (기력/소화):** 소화 기능 저하, 근감소증, 수족냉증, 기력 감퇴, 위암
            * **수험생/청소년:** 체력 부족, 시험 불안, 예민성 복통.
            * **여성:** 심한 생리통(냉증), 빈혈, 수족냉증.
            * **일반 (면역/장):** 잦은 감기, 만성 설사, 멀미.

            ### 🥗 추천 약재·음식·영양제
            <table class="guide-table">
            <thead>
                <tr><th>분류</th><th>추천 목록 및 효능 요약</th></tr>
            </thead>
            <tbody>
                <tr>
                    <td style="font-weight:bold;">한약재</td>
                    <td>
                        인삼(홍삼): 원기 회복, 소화기 강화, 면역력 증진 (소음인 최고 약재).<br>
                        당귀·천궁: 혈액을 생성하고 순환시켜 생리통 및 빈혈 개선.<br>
                        계피(육계)·생강(건강): 뱃속을 따뜻하게 하여 소화 불량 및 냉증 개선.<br>
                        쑥(애엽): 자궁을 따뜻하게 하여 부인과 질환 예방.
                    </td>
                </tr>
                <tr>
                    <td style="font-weight:bold;">음식</td>
                    <td>
                        닭고기: 따뜻한 성질의 단백질로 기력 보충.<br>
                        마늘, 고추, 부추: 신진대사를 높이고 체온을 유지.<br>
                        꿀, 대추: 위장을 편안하게 하고 신경을 안정(불면증).
                    </td>
                </tr>
                <tr>
                    <td style="font-weight:bold;">영양제</td>
                    <td>
                        비타민 B군: 에너지 대사를 높여 만성 피로 회복.<br>
                        철분/엽산: 빈혈 예방 및 혈액 생성 보조.<br>
                        프로폴리스: 따뜻한 성질의 천연 항생제로 면역력 강화.
                    </td>
                </tr>
            </tbody>
            </table>
            """, unsafe_allow_html=True)

        elif my_code == 'TY': # 태양인
            st.header("📋 태양인 상세 가이드")
            
            st.markdown("""
            **1. 태양인의 특징**
            * 에너지를 축적하는 기능은 약하고, 발산/소모시키는 기능은 강합니다.
            * 머리와 목덜미가 발달한 반면, 허리나 하체가 빈약한 편입니다.
            """)
            st.subheader("🚨 건강이 안 좋아지면 나타나는 증상")
            st.warning("""
            * **신체:** 쉽게 몸살이 나고, 하체가 쉽게 피로하여 오래 걷기 힘듭니다.
            * **배설:** 소변 양과 횟수가 줄거나, 대변이 염소똥처럼 굳어집니다.
            * **입/소화:** 입 안에 맑은 침이나 거품이 고이고, 구역질을 합니다.
            * **정서:** 매사에 조급해지고 화가 잘 납니다.
            """)
            st.info("""
            **💡 평소 생활 실천 사항**
            1. **식사:** 매운 자극성 음식, 고지방 음식을 피하고 담백한 음식/해물/채소가 좋습니다.
            2. **운동:** 과격한 운동은 피하고, 허리/하체 근력 강화 운동을 하세요.
            3. **마음:** 조급해하지 말고 여유를 가지며, 원만한 인간관계를 유지하세요.
            """)

            st.subheader("🍽️ 식품군별 권장 음식 상세")
            st.markdown("""
            <table class="guide-table">
            <thead>
                <tr><th>분류</th><th>권장 음식</th></tr>
            </thead>
            <tbody>
                <tr><td>곡류군</td><td>메밀(국수, 묵, 밥) / (보리, 녹두, 팥)</td></tr>
                <tr><td>저지방 어육류</td><td>굴, 새우, 게, 오징어, 문어, 전복, 조개, 해삼, 홍합 / (흰살생선)</td></tr>
                <tr><td>중지방 어육류</td><td>(사용 가능) 고등어, 꽁치, 장어</td></tr>
                <tr><td>고지방 어육류</td><td>(해당 없음 / 육류는 피하는 것이 좋음)</td></tr>
                <tr><td>채소군</td><td>상추, 깻잎, 배추, 오이, 가지, 시금치, 우엉, 숙주나물, 죽순</td></tr>
                <tr><td>지방군/우유/과일</td><td>참깨 / 포도, 머루, 다래, 감, 키위, 파인애플, 오렌지</td></tr>
            </tbody>
            </table>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            # [수정됨] 
            st.subheader("🏥 태양인 체질 증상 및 질환")
            st.markdown("""
            **특성:** 폐대간소(肺大肝小). 폐 기능은 강하나 간 기능이 매우 약함. 기운이 위로 솟구쳐 하체가 약해지기 쉽고 구토 증상이 잦을 수 있음. (가장 드문 체질)

            * **노화 (근골격):** 하체 무력감, 다리에 힘이 풀림, 삼킴 장애(열격), 면역계 질환, 마비 질환
            * **수험생/청소년:** 독창적이나 화를 참지 못함.
            * **여성:** 원인 불명의 불임, 심한 입덧.
            * **일반 (간/피부):** 약물 과민 반응(간 해독력 저하), 아토피 등 피부 질환.

            ### 🥗 추천 약재·음식·영양제
            <table class="guide-table">
            <thead>
                <tr><th>분류</th><th>추천 목록 및 효능 요약</th></tr>
            </thead>
            <tbody>
                <tr>
                    <td style="font-weight:bold;">한약재</td>
                    <td>
                        오가피: 근골격을 튼튼하게 하여 하체 무력감 보강.<br>
                        모과: 근육의 경직을 풀고 위장 편안하게 함.<br>
                        다래(미후도): 위로 치솟는 기운을 내리고 열을 식힘.
                    </td>
                </tr>
                <tr>
                    <td style="font-weight:bold;">음식</td>
                    <td>
                        해산물(문어, 조개, 게): 타우린이 간 기능을 돕고 피로 회복.<br>
                        메밀: 몸의 열을 내리고 소화를 도움.<br>
                        포도, 키위: 진액을 생성하고 피로를 풂.
                    </td>
                </tr>
                <tr>
                    <td style="font-weight:bold;">영양제</td>
                    <td>
                        클로렐라/스피루리나: 엽록소가 풍부한 해조류로 간 해독 및 항산화.<br>
                        MSM (식이유황): 해독 작용 및 관절/연골 건강 보조.<br>
                        유산균: 육식보다는 채식 위주의 식단과 함께 장 건강 관리.
                    </td>
                </tr>
            </tbody>
            </table>
            """, unsafe_allow_html=True)
        
        # [요청사항 적용 2] 체질별 유명인 정보 (하단 배치)
        st.markdown("---")
        st.header(f"🌟 {TYPE_MAP[my_code]}으로 추정되는 유명인")
        st.caption("※ 알림: 이 내용은 인물의 대중적 이미지와 캐릭터를 바탕으로 한 재미 위주의 가상 분류입니다. 실제 의학적 체질 진단과는 다를 수 있으니 가볍게 즐겨주세요!")
        
        if my_code == 'TY':
             st.markdown("""
             **"카리스마 넘치는 직관의 리더"**
             
             태양인은 만 명 중 한두 명 있을 정도로 매우 드문 체질입니다. 강한 추진력과 카리스마, 남다른 직관력을 가졌으며, 남들이 범접하기 힘든 독보적인 아우라를 뿜어냅니다.
             
             * **배우:** 차승원, 김윤석 (강렬한 인상과 화면을 장악하는 남성미)
             * **가수:** 나훈아, 임재범 (폭발적인 성량과 무대 전체를 지배하는 쇼맨십)
             * **K-pop 아이돌:** 지드래곤(GD), 카리나(aespa), 전소연((G)I-DLE) (비현실적인 비주얼과 천재적인 프로듀싱 능력, 리더십)
             * **삼국지 장군:** **관우** (천하를 호령하는 위엄과 굽히지 않는 충절, 긴 수염을 휘날리는 압도적 풍채)
             * **우리나라 위인:** 이제마 (사상의학의 창시자), 박정희 (강력한 추진력)
             * **역사 속 위인:** 나폴레옹 (세상을 바꾸려는 강력한 영웅 심리)
             * **동물:** 사자, 용, 독수리 (백수의 왕, 하늘의 제왕처럼 비범함)
             """)
             
        elif my_code == 'SY':
             st.markdown("""
             **"재치 만점, 날렵한 분위기 메이커"**
             
             성격이 급하지만 뒤끝이 없고, 솔직담백하며 재치와 유머가 넘칩니다. 상체가 발달하고 하체가 약한 편이며, 톡톡 튀는 센스로 주변을 즐겁게 만듭니다.
             
             * **배우:** 김혜수, 전지현, 이병헌 (시원시원한 이목구비와 당당하고 솔직한 매력)
             * **가수:** 이선희, 윤수일, 싸이(PSY) (작은 체구에서 나오는 폭발적 고음과 열정적인 에너지)
             * **K-pop 아이돌:** 백현(EXO), 안유진(IVE), 하니(NewJeans) (예능감 넘치는 씩씩한 에너지와 엉뚱한 장난기)
             * **삼국지 장군:** **장비** (행동이 앞서는 불같은 성격, 호탕한 매력의 소유자)
             * **우리나라 위인:** 다산 정약용 (호기심이 많고 다방면에 능통함)
             * **역사 속 위인:** 스티브 잡스 (창의적이고 혁신적이나 성격이 급함)
             * **동물:** 원숭이, 돌고래 (재주가 많고 날렵하며 사교적임)
             """)

        elif my_code == 'TE':
             st.markdown("""
             **"듬직하고 끈기 있는 평화주의자"**
             
             한국인에게 가장 많은 체질입니다. 골격이 굵고 듬직하며, 인내심과 끈기가 강합니다. 변화보다는 안정을 추구하며, 겉은 유해 보이나 속은 단단한 외유내강형입니다.
             
             * **배우:** 마동석, 송강호, 최민식 (중후하고 묵직한 연기, 푸근한 인상 뒤의 파워)
             * **가수:** 송창식, 양희은, 성시경 (뱃속 깊은 곳에서 울리는 웅장하고 편안한 성량)
             * **K-pop 아이돌:** 창빈(Stray Kids), 휴닝카이(TXT), 신동 (탄탄한 피지컬과 팀의 중심을 잡는 무게감)
             * **삼국지 장군:** **유비** (넓은 덕으로 사람을 품는 인내심, 묵묵히 때를 기다리는 신중함)
             * **우리나라 위인:** 세종대왕 (고기를 좋아하고 앉아서 연구하기를 즐김), 김구
             * **역사 속 위인:** 윈스턴 처칠 (뚝심 있는 리더십, 풍채)
             * **동물:** 곰, 황소, 코끼리 (우직하고 힘이 세며 지구력이 좋음)
             """)

        elif my_code == 'SE':
             st.markdown("""
             **"섬세하고 완벽을 추구하는 전략가"**
             
             이목구비가 오밀조밀하고 단정합니다. 꼼꼼하고 내성적이며 완벽주의 성향이 있습니다. 체력이 약해 쉽게 피로를 느끼지만, 논리적이고 세심한 감수성을 가졌습니다.
             
             * **배우:** 박보검, 정유미, 한석규 (부드럽고 지적인 이미지, 섬세한 감정 연기)
             * **가수:** 심수봉, 김광석, 아이유(IU) (마음을 파고드는 애절한 감성과 철저한 자기관리)
             * **K-pop 아이돌:** 장원영(IVE), 민지(NewJeans), 설윤(NMIXX) (청순하고 고전적인 미인상, 차분하고 지적인 이미지)
             * **삼국지 장군:** **제갈량** (뛰어난 지략, 돌다리도 두들겨 보는 신중함과 꼼꼼함)
             * **우리나라 위인:** 이순신 장군 (철저한 기록과 신중한 전략), 퇴계 이황
             * **역사 속 위인:** 링컨 (사색적이고 신중하며 마른 체형)
             * **동물:** 사슴, 고양이 (예민하고 깔끔하며 독립적임)
             """)

        st.markdown("---")
        
        # 인쇄 버튼
        print_btn_code = """
        <script>function printPage() { window.parent.print(); }</script>
        <button onclick="printPage()" style="width:100%; padding:10px; background:white; border:1px solid #ddd; border-radius:5px; color:black; cursor:pointer;">🖨️ 결과 저장/인쇄</button>
        """
        components.html(print_btn_code, height=50)
        
        if st.button("🔄 처음부터 다시하기", use_container_width=True):
            st.session_state.clear()
            st.rerun()

if __name__ == '__main__':
    main()