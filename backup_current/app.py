import streamlit as st
import streamlit.web.cli as stcli
import sys
import PyPDF2
from io import BytesIO
from openai import OpenAI
from dotenv import load_dotenv
import os
import pandas as pd
import math
from resume_analysis import show_resume_analysis
from salary_negotiation import show_salary_negotiation
from resume_summarizer import summarize_resume

# 환경 변수 로드
load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# 세션 상태 초기화
if 'analysis_result' not in st.session_state:
    st.session_state['analysis_result'] = None
if 'interview_questions' not in st.session_state:
    st.session_state['interview_questions'] = None
if 'job_description' not in st.session_state:
    st.session_state['job_description'] = None

def main():
    # 페이지 설정
    st.set_page_config(
        page_title="HR-채용",
        layout="wide"
    )

    # 사이드바 스타일 수정 (기존 스타일 부분 교체)
    st.markdown("""
        <style>
            [data-testid="stSidebar"] {
                min-width: 520px !important;
                max-width: 520px !important;
                background-color: #f8f9fa;
            }
            [data-testid="stSidebar"] > div:first-child {
                padding: 2rem;
            }
            .sidebar-title {
                font-size: 24px;
                font-weight: bold;
                color: #333333;
                margin-bottom: 30px;
                padding-bottom: 10px;
                border-bottom: 2px solid #e0e0e0;
            }
        </style>
    """, unsafe_allow_html=True)

    # 사이드바 내용
    with st.sidebar:
        st.image("https://neurophethr.notion.site/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2Fe3948c44-a232-43dd-9c54-c4142a1b670b%2Fneruophet_logo.png?table=block&id=893029a6-2091-4dd3-872b-4b7cd8f94384&spaceId=9453ab34-9a3e-45a8-a6b2-ec7f1cefbd7f&width=410&userId=&cache=v2", 
                 width=120)
        
        st.markdown("<div class='sidebar-title'>HR-채용</div>", unsafe_allow_html=True)
        
        # 1. 이력서 첨부 섹션
        st.markdown("""
            <h4 style='color: #333333; margin-bottom: 20px;'>
                이력서 분석 및 면접 질문 TIP
            </h4>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "이력서(PDF 파일)를 선택해주세요",
            type=['pdf'],
            help="200MB 이하의 PDF 파일만 가능합니다"
        )
        
        if uploaded_file:
            st.markdown(f"<div style='padding: 5px 0px; color: #666666;'>{uploaded_file.name}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='upload-text'>Drag and drop file here<br>Limit 200MB per file • PDF</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        # 처우협상 메뉴 추가
        if st.button("💰 처우협상"):
            st.session_state.current_page = "salary"
        
        st.markdown("<br>", unsafe_allow_html=True)

    # 초기 페이지 상태 설정
    if 'current_page' not in st.session_state:
        st.session_state['current_page'] = 'resume'

    # 네비게이션 버튼
    if st.sidebar.button("📄 이력서 분석"):
        st.session_state['current_page'] = 'resume'
    if st.sidebar.button("💰 처우협상"):
        st.session_state['current_page'] = 'salary'

    # 페이지 라우팅
    if st.session_state['current_page'] == 'resume':
        show_resume_analysis()
    elif st.session_state['current_page'] == 'salary':
        show_salary_negotiation()

def show_resume_analysis():
    st.markdown("## 📄 이력서 분석 및 면접 질문 TIP")
    # 이력서 분석 관련 코드...

def show_salary_negotiation():
    st.markdown("## 💰 처우협상 분석")
    
    try:
        # 엑셀 파일 직접 로드
        df = pd.read_excel("salary_table.xlsx")
        
        # 직군 매핑 정의
        job_mapping = {
            "연구직": "직군1",
            "개발직": "직군2",
            "임상연구, QA": "직군2",
            "연구기획": "직군3",
            "디자인": "직군3",
            "인증(RA), SV, SCM": "직군3",
            "마케팅": "직군3",
            "기획": "직군3",
            "기술영업 / SE(5년 이상)": "직군3",
            "경영기획(전략,회계,인사,재무,법무,보안)": "직군3",
            "지원(연구, 기술, 경영 지원 등)": "직군4",
            "일반영업 /SE(5년 미만)": "직군4",
            "고객지원(CS)": "직군5",
            "레이블링": "직군5"
        }
        
        # 직군 상세 목록
        job_roles = list(job_mapping.keys())
        
        # 입력 폼 생성
        with st.form("salary_form"):
            # 1줄: 포지션명, 후보자명
            col1, col2 = st.columns(2)
            with col1:
                position = st.text_input("포지션명", "")
            with col2:
                candidate_name = st.text_input("후보자명", "")
            
            # 2줄: 직군선택
            job_role = st.selectbox("직군 선택", job_roles)
            
            # 3줄: 현재연봉, 기타 처우, 희망연봉
            col3, col4, col5 = st.columns(3)
            with col3:
                current_salary = st.number_input("현재연봉 (만원)", min_value=0, step=100)
            with col4:
                other_salary = st.number_input("기타 처우 (만원)", min_value=0, step=100)
            with col5:
                desired_salary = st.number_input("희망연봉 (만원)", min_value=0, step=100)
            
            # 4줄: 인정경력 연차, 학력특이사항
            col6, col7 = st.columns(2)
            with col6:
                years = st.number_input("인정경력 (년)", min_value=0.0, step=0.1, format="%.1f")
            with col7:
                education_notes = st.text_input("학력특이사항", "")
            
            # 5줄: 특이사항
            special_notes = st.text_area("특이사항 (성과, 스킬, 기타)", height=100)
            
            # 분석하기 버튼
            submitted = st.form_submit_button("분석하기")

            if submitted:
                # ... (기존 처우협상 분석 코드) ...

if __name__ == "__main__":
    sys.argv = ["streamlit", "run", "app.py"]
    sys.exit(stcli.main()) 