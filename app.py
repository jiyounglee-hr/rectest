import streamlit as st
import PyPDF2
from io import BytesIO
import os
import openai
from dotenv import load_dotenv
from datetime import datetime
import pandas as pd
import re
import base64

# 날짜 정규화 함수
def normalize_date(date_str):
    if pd.isna(date_str) or date_str == '':
        return None
    
    # 이미 datetime 객체인 경우
    if isinstance(date_str, (datetime, pd.Timestamp)):
        return date_str
    
    # 문자열인 경우
    if isinstance(date_str, str):
        # 공백 제거
        date_str = date_str.strip()
        
        # 빈 문자열 처리
        if not date_str:
            return None
            
        # 날짜 형식 변환 시도
        try:
            # YYYY-MM-DD 형식
            if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
                return datetime.strptime(date_str, '%Y-%m-%d')
            # YYYY.MM.DD 형식
            elif re.match(r'^\d{4}\.\d{2}\.\d{2}$', date_str):
                return datetime.strptime(date_str, '%Y.%m.%d')
            # YYYY/MM/DD 형식
            elif re.match(r'^\d{4}/\d{2}/\d{2}$', date_str):
                return datetime.strptime(date_str, '%Y/%m/%d')
            # YYYYMMDD 형식
            elif re.match(r'^\d{8}$', date_str):
                return datetime.strptime(date_str, '%Y%m%d')
        except ValueError:
            return None
    
    return None

def calculate_experience(experience_text):
    """경력기간을 계산하는 함수"""
    # 영문 월을 숫자로 변환하는 딕셔너리
    month_dict = {
        'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06',
        'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
    }
    
    total_months = 0
    experience_periods = []
    
    # 각 줄을 분리하여 처리
    lines = experience_text.split('\n')
    current_company = None
    
    for line in lines:
        # 공백과 탭 문자를 모두 일반 공백으로 변환하고 연속된 공백을 하나로 처리
        line = re.sub(r'[\s\t]+', ' ', line.strip())
        if not line:
            continue
            
        # 회사명 추출 (숫자나 특수문자가 없는 줄)
        if not any(c.isdigit() for c in line) and not any(c in '~-–./' for c in line):
            current_company = line
            continue
            
        # 영문 월 형식 패턴 (예: Nov 2021 – Oct 2024)
        en_pattern = r'([A-Za-z]{3})\s*(\d{4})\s*[–-]\s*([A-Za-z]{3})\s*(\d{4})'
        en_match = re.search(en_pattern, line)
        
        # 한국어 날짜 형식 패턴 (예: 2021 년 11월 – 2024 년 10월)
        kr_pattern = r'(\d{4})\s*년?\s*(\d{1,2})\s*월\s*[-–~]\s*(\d{4})\s*년?\s*(\d{1,2})\s*월'
        kr_match = re.search(kr_pattern, line)
        
        if en_match:
            start_month, start_year, end_month, end_year = en_match.groups()
            start_date = f"{start_year}-{month_dict[start_month]}-01"
            end_date = f"{end_year}-{month_dict[end_month]}-01"
            
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            
            months = (end.year - start.year) * 12 + (end.month - start.month) + 1
            total_months += months
            
            years = months // 12
            remaining_months = months % 12
            decimal_years = round(months / 12, 1)
            
            period_str = f"{start_year}-{month_dict[start_month]}~{end_year}-{month_dict[end_month]} ({years}년 {remaining_months}개월, {decimal_years}년)"
            if current_company:
                period_str = f"{current_company}: {period_str}"
            experience_periods.append(period_str)
            continue
            
        elif kr_match:
            start_year, start_month, end_year, end_month = kr_match.groups()
            start_date = f"{start_year}-{start_month.zfill(2)}-01"
            end_date = f"{end_year}-{end_month.zfill(2)}-01"
            
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            
            months = (end.year - start.year) * 12 + (end.month - start.month) + 1
            total_months += months
            
            years = months // 12
            remaining_months = months % 12
            decimal_years = round(months / 12, 1)
            
            period_str = f"{start_year}-{start_month.zfill(2)}~{end_year}-{end_month.zfill(2)} ({years}년 {remaining_months}개월, {decimal_years}년)"
            if current_company:
                period_str = f"{current_company}: {period_str}"
            experience_periods.append(period_str)
            continue
            
        # 날짜 패턴 처리
        # 1. 2023. 04 ~ 2024. 07 형식
        pattern1 = r'(\d{4})\.\s*(\d{1,2})\s*[~-–]\s*(\d{4})\.\s*(\d{1,2})'
        # 2. 2015.01.~2016.06 형식
        pattern2 = r'(\d{4})\.(\d{1,2})\.\s*[~-–]\s*(\d{4})\.(\d{1,2})'
        # 3. 2024.05 ~ 형식
        pattern3 = r'(\d{4})\.(\d{1,2})\s*[~-–]'
        # 4. 2024-05 ~ 형식
        pattern4 = r'(\d{4})-(\d{1,2})\s*[~-–]'
        # 5. 2024/05 ~ 형식
        pattern5 = r'(\d{4})/(\d{1,2})\s*[~-–]'
        # 6. 2024.05.01 ~ 형식 (일 부분 무시)
        pattern6 = r'(\d{4})\.(\d{1,2})\.\d{1,2}\s*[~-–]'
        # 7. 2024-05-01 ~ 형식 (일 부분 무시)
        pattern7 = r'(\d{4})-(\d{1,2})-\d{1,2}\s*[~-–]'
        # 8. 2024/05/01 ~ 형식 (일 부분 무시)
        pattern8 = r'(\d{4})/(\d{1,2})/\d{1,2}\s*[~-–]'
        # 9. 2023/05 - 2024.04 형식
        pattern9 = r'(\d{4})[/\.](\d{1,2})\s*[-]\s*(\d{4})[/\.](\d{1,2})'
        # 10. 2023-04-24 ~ 2024-05-10 형식
        pattern10 = r'(\d{4})-(\d{1,2})-(\d{1,2})\s*[~-–]\s*(\d{4})-(\d{1,2})-(\d{1,2})'
        # 11. 2021-03-2026-08 형식
        pattern11 = r'(\d{4})-(\d{1,2})-(\d{4})-(\d{1,2})'
        # 12. 2021-03~2022-08 형식
        pattern12 = r'(\d{4})-(\d{1,2})\s*[~-–]\s*(\d{4})-(\d{1,2})'
        
        # 패턴 매칭 시도
        match = None
        current_pattern = None
        
        # 먼저 패턴 10으로 시도 (2023-04-24 ~ 2024-05-10 형식)
        match = re.search(pattern10, line)
        if match:
            current_pattern = pattern10
        # 다음으로 패턴 12로 시도 (2021-03~2022-08 형식)
        elif re.search(pattern12, line):
            match = re.search(pattern12, line)
            current_pattern = pattern12
        else:
            # 다른 패턴 시도
            for pattern in [pattern1, pattern2, pattern3, pattern4, pattern5, pattern6, pattern7, pattern8, pattern9, pattern11]:
                match = re.search(pattern, line)
                if match:
                    current_pattern = pattern
                    break
                
        if match and current_pattern:
            if current_pattern in [pattern1, pattern2, pattern9]:
                start_year, start_month, end_year, end_month = match.groups()
                start_date = f"{start_year}-{start_month.zfill(2)}-01"
                end_date = f"{end_year}-{end_month.zfill(2)}-01"
                start = datetime.strptime(start_date, "%Y-%m-%d")
                end = datetime.strptime(end_date, "%Y-%m-%d")
            elif current_pattern == pattern10:
                start_year, start_month, start_day, end_year, end_month, end_day = match.groups()
                start_date = f"{start_year}-{start_month.zfill(2)}-{start_day.zfill(2)}"
                end_date = f"{end_year}-{end_month.zfill(2)}-{end_day.zfill(2)}"
                start = datetime.strptime(start_date, "%Y-%m-%d")
                end = datetime.strptime(end_date, "%Y-%m-%d")
            elif current_pattern in [pattern11, pattern12]:
                start_year, start_month, end_year, end_month = match.groups()
                start_date = f"{start_year}-{start_month.zfill(2)}-01"
                end_date = f"{end_year}-{end_month.zfill(2)}-01"
                start = datetime.strptime(start_date, "%Y-%m-%d")
                end = datetime.strptime(end_date, "%Y-%m-%d")
            else:
                start_year, start_month = match.groups()
                start_date = f"{start_year}-{start_month.zfill(2)}-01"
                start = datetime.strptime(start_date, "%Y-%m-%d")
                
                # 종료일 처리
                if '현재' in line or '재직중' in line or '재직 중' in line:
                    end = datetime.now()
                else:
                    # 종료일 패턴 처리 (일 부분 무시)
                    end_pattern = r'[~-–]\s*(\d{4})[\.-/](\d{1,2})(?:[\.-/]\d{1,2})?'
                    end_match = re.search(end_pattern, line)
                    if end_match:
                        end_year, end_month = end_match.groups()
                        end_date = f"{end_year}-{end_month.zfill(2)}-01"
                        end = datetime.strptime(end_date, "%Y-%m-%d")
                    else:
                        # 종료일이 없는 경우
                        period_str = f"{start_year}-{start_month.zfill(2)}~종료일 입력 필요"
                        if current_company:
                            period_str = f"{current_company}: {period_str}"
                        experience_periods.append(period_str)
                        continue
            
            # 경력기간 계산
            if current_pattern in [pattern10, pattern11, pattern12]:
                # 패턴 10, 11, 12의 경우 정확한 일자 계산
                months = (end.year - start.year) * 12 + (end.month - start.month)
                if end.day < start.day:
                    months -= 1
                if months < 0:
                    months = 0
            else:
                # 다른 패턴의 경우 기존 로직 유지
                months = (end.year - start.year) * 12 + (end.month - start.month) + 1
            
            total_months += months
            
            years = months // 12
            remaining_months = months % 12
            decimal_years = round(months / 12, 1)
            
            # 결과 문자열 생성
            if current_pattern == pattern10:
                period_str = f"{start_year}-{start_month.zfill(2)}~{end_year}-{end_month.zfill(2)} ({years}년 {remaining_months}개월, {decimal_years}년)"
            elif current_pattern in [pattern11, pattern12]:
                period_str = f"{start_year}-{start_month.zfill(2)}~{end_year}-{end_month.zfill(2)} ({years}년 {remaining_months}개월, {decimal_years}년)"
            else:
                period_str = f"{start_year}-{start_month.zfill(2)}~{end.year}-{str(end.month).zfill(2)} ({years}년 {remaining_months}개월, {decimal_years}년)"
            
            if current_company:
                period_str = f"{current_company}: {period_str}"
            experience_periods.append(period_str)
    
    # 총 경력기간 계산
    total_years = total_months // 12
    total_remaining_months = total_months % 12
    total_decimal_years = round(total_months / 12, 1)
    
    # 결과 문자열 생성
    result = ""
    if experience_periods:
        result = f"총 경력기간: {total_years}년 {total_remaining_months}개월 ({total_decimal_years}년)\n"
        result += "\n".join(experience_periods)
    
    return result, total_years, total_remaining_months, total_decimal_years

# 페이지 설정 (반드시 첫 번째 명령어여야 함)
st.set_page_config(
    page_title="HR Resume Analyzer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
if 'current_page' not in st.session_state:
    st.session_state['current_page'] = 'resume'
if 'analysis_result' not in st.session_state:
    st.session_state['analysis_result'] = None
if 'interview_questions' not in st.session_state:
    st.session_state['interview_questions'] = None
if 'job_description' not in st.session_state:
    st.session_state['job_description'] = None

# URL 파라미터 처리
page_param = st.query_params.get("page", "resume")
valid_pages = ['resume', 'interview1', 'interview2']

# URL 파라미터가 유효한 경우에만 페이지 상태 업데이트
if isinstance(page_param, str) and page_param in valid_pages:
    st.session_state['current_page'] = page_param

# OpenAI API 키 설정
openai.api_key = st.secrets["OPENAI_API_KEY"]

# 사이드바 스타일 수정
st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            min-width: 400px !important;
            max-width: 400px !important;
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
        /* 사이드바 버튼 스타일 */
        [data-testid="stSidebar"] .stButton button {
            width: 200px !important;
            padding: 5px 6px !important;
            margin: 2px 2px !important;
            border: 1px solid #ddd;
            border-radius: 5px;
            background-color: white;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 0.9em !important;
            color: rgb(49, 51, 63) !important;
        }
        [data-testid="stSidebar"] .stButton button:hover {
            background-color: #f0f0f0;
        }
        [data-testid="stSidebar"] .stButton button[data-baseweb="button"][kind="primary"] {
            background-color: #e6e6e6;
            border-color: #999;
            color: rgb(49, 51, 63) !important;
        }
        /* 사이드바 버튼 컨테이너 스타일 */
        [data-testid="stSidebar"] .button-container {
            display: flex;
            justify-content: flex-start;
            gap: 5px;
            margin-bottom: 20px;
        }
    </style>
""", unsafe_allow_html=True)

# 사이드바 내용
with st.sidebar:
    st.image("https://neurophethr.notion.site/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2Fe3948c44-a232-43dd-9c54-c4142a1b670b%2Fneruophet_logo.png?table=block&id=893029a6-2091-4dd3-872b-4b7cd8f94384&spaceId=9453ab34-9a3e-45a8-a6b2-ec7f1cefbd7f&width=410&userId=&cache=v2", 
             width=120)
    
    st.markdown("<div class='sidebar-title'>HR-채용</div>", unsafe_allow_html=True)

    # 버튼 컨테이너 추가
    st.markdown('<div class="button-container">', unsafe_allow_html=True)
    
    # 페이지 전환 함수들
    def switch_to_resume():
        st.query_params["page"] = "resume"
        st.session_state['current_page'] = 'resume'

    def switch_to_interview1():
        st.query_params["page"] = "interview1"
        st.session_state['current_page'] = 'interview1'

    def switch_to_interview2():
        st.query_params["page"] = "interview2"
        st.session_state['current_page'] = 'interview2'

    # 페이지 전환 버튼 추가
    st.button("🤖 이력서분석", 
            key="btn_resume", 
            on_click=switch_to_resume,
            type="primary" if st.session_state['current_page'] == "resume" else "secondary")

    st.button("☝️ 1차 면접 질문", 
            key="btn_interview1", 
            on_click=switch_to_interview1,
            type="primary" if st.session_state['current_page'] == "interview1" else "secondary")

    st.button("✌️ 2차 면접 질문", 
            key="btn_interview2", 
            on_click=switch_to_interview2,
            type="primary" if st.session_state['current_page'] == "interview2" else "secondary")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    
    # 파일 업로더 스타일 수정
    st.markdown("""
        <style>
            [data-testid="stFileUploader"] {
                width: 100%;
            }
            [data-testid="stFileUploader"] section {
                border: 2px dashed #ccc;
                border-radius: 4px;
                padding: 20px;
                background: #f8f9fa;
            }
            .upload-text {
                color: #666;
                font-size: 14px;
            }
            /* 파일명 숨기기 */
            .st-emotion-cache-1v0mbdj > span {
                display: none;
            }
        </style>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "이력서를 선택해주세요.",
        type=['pdf'],
        help="200MB 이하의 PDF 파일만 가능합니다"
    )
    
    if uploaded_file:
        # PDF 내용 추출 및 표시
        pdf_data = uploaded_file.read()
        pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_data))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        
        # 이력서 내용을 세션 상태에 저장
        if 'resume_text' not in st.session_state:
            st.session_state.resume_text = ""
        st.session_state.resume_text = text
        
        # 이력서 내용 표시 스타일
        st.markdown("""
            <style>
                .resume-text {
                    background-color: white;
                    padding: 20px;
                    border-radius: 5px;
                    border: 1px solid #ddd;
                    max-height: 500px;
                    overflow-y: auto;
                    font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
                    font-size: 0.9em;
                    line-height: 1.3;
                    white-space: pre-wrap;
                    margin: 10px 0;
                }
                @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500&display=swap');
            </style>
        """, unsafe_allow_html=True)

    else:
        st.markdown("<div class='upload-text'> 이력서 분석 및 면접 질문생성 기초 데이터 입니다. </div>", unsafe_allow_html=True)

    # 맨 마지막에 도움말 추가
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("도움말"):
        st.write("""
        🤖 이력서분석 : PDF 형식의 이력서 파일을 업로드 > 채용요건 확인 > 경력기간 체크(필요 시) > '분석 시작하기' \n
        ☝️ 1차 면접 질문 : 직무기반의 경험, 프로젝트, 문제해결, 자격요건 관련 사례 질문\n
        ✌️ 2차 면접 질문 : 핵심가치 기반의 [도전]두려워 말고 시도합니다, [책임감]대충은 없습니다, [협력]동료와 협업합니다, [전문성]능동적으로 일합니다
        """)
    st.markdown('<div class="label-text"><a href="https://neurophet.sharepoint.com/sites/HR2/Shared%20Documents/Forms/AllItems.aspx?as=json&id=%2Fsites%2FHR2%2FShared%20Documents%2F%EC%B1%84%EC%9A%A9&viewid=f1a0986e%2Dd990%2D4f37%2Db273%2Dd8a6df2f4c40" target="_blank" class="web-link">🔗이력서 링크 ></a></div>', unsafe_allow_html=True)

# 채용공고 데이터
job_descriptions = {
    "ra_manager": """[의료기기 인허가(RA) 팀장]

담당업무
- 국내외 의료기기 인허가 (MFDS, FDA, CE, MHLW 등) 및 사후관리
- 국가별 기술문서 작성 및 최신화
- 국가별 의료기기 규제 요구사항 분석
- 의료기기법/규격/가이던스 변경사항 모니터링
- 품질시스템 심사 대응 (ISO 13485, KGMP, MDSAP 등)

필수자격
- 제품 인허가 업무경력 7년이상
- 의료기기 인증팀 관리 경험
- SaMD, SiMD, 전기전자 의료기기 인허가 경험
- 영어 중급 이상 (Reading & Writing 필수)

우대사항
- 3등급 SW 의료기기 허가 경험
- 의료기기 개발 프로세스에 대한 이해
- 의료기기 RA(의료기기 규제과학 전문가) 자격증 소지자""",
    
    "marketing": """[의료 AI 솔루션 마케팅(3~6년)]

담당업무
- 의료 AI 솔루션 마케팅 전략 수립 및 실행
- 제품 포지셔닝 및 가치 제안
- 디지털 마케팅 캠페인 기획 및 실행
- 마케팅 성과 분석 및 보고

필수자격
- 의료기기/헬스케어 마케팅 경력 3년 이상
- 디지털 마케팅 전략 수립 및 실행 경험
- 데이터 기반 마케팅 성과 분석 능력

우대사항
- AI/의료 분야 이해도 보유
- 글로벌 마케팅 경험
- 의료진 대상 마케팅 경험""",
    
    "japan_head": """[일본 법인장]

담당업무
- 일본 법인 총괄 및 운영 관리
- 일본 시장 사업 전략 수립 및 실행
- 현지 영업/마케팅 조직 구축 및 관리
- 일본 시장 매출 및 수익성 관리

필수자격
- 일본 의료기기 시장 경력 10년 이상
- 의료기기 기업 임원급 경험 보유
- 일본어 비즈니스 레벨 이상

우대사항
- AI 의료기기 관련 경험
- 일본 의료기기 인허가 경험
- 글로벌 기업 경영 경험"""
}

# 현재 페이지에 따른 내용 표시
if st.session_state['current_page'] == "resume":
    st.markdown("""
        <h5 style='color: #333333; margin-bottom: 20px;'>
            🤖 이력서분석
        </h5>
    """, unsafe_allow_html=True)
    
    # 화면을 두 개의 컬럼으로 분할
    left_col, right_col = st.columns(2)

    # 왼쪽 컬럼: 채용공고 선택 및 내용, 경력기간 산정
    with left_col:
        job_option = st.selectbox(
            "채용공고 선택",  # 레이블을 위에서 직접 표시했으므로 여기서는 빈 문자열로 설정
            ["선택해주세요", "의료기기 인허가(RA) 팀장", "의료 AI 솔루션 마케팅", "일본 법인장", "직접 입력"]
        )

        if job_option == "직접 입력":
            job_description = st.text_area("채용공고 내용을 입력해주세요", height=300)
        else:
            job_map = {
                "의료기기 인허가(RA) 팀장": "ra_manager",
                "의료 AI 솔루션 마케팅": "marketing",
                "일본 법인장": "japan_head"
            }
            if job_option in job_map:
                default_description = job_descriptions[job_map[job_option]]
                job_description = st.text_area(
                    "- 채용공고 내용 (필요시 수정 가능합니다)",
                    value=default_description,
                    height=220
                )
            else:
                job_description = ""
        experience_text = st.text_area(
            "- 경력기간 입력",  
            height=120
        )

        if experience_text:
            try:
                result, total_years, total_remaining_months, total_decimal_years = calculate_experience(experience_text)
                st.markdown(f'<div class="resume-text">{result}</div>', unsafe_allow_html=True)
                
                # 경력기간 정보를 세션 상태에 저장
                st.session_state.experience_years = total_years
                st.session_state.experience_months = total_remaining_months
                st.session_state.experience_decimal_years = total_decimal_years
            except Exception as e:
                st.error(f"경력기간 계산 중 오류가 발생했습니다: {str(e)}")

    # 오른쪽 컬럼: 이력서 내용
    with right_col:
        if uploaded_file:
            st.markdown('<div class="label-text">📄 이력서 내용 </div>', unsafe_allow_html=True)
            st.markdown(f'<div class="resume-text">{text}</div>', unsafe_allow_html=True)

    st.markdown("---")

    # 버튼을 왼쪽에 배치하고 스타일 적용
    col1, col2 = st.columns([1, 4])
    with col1:
        analyze_button = st.button(
            "분석 시작하기",
            key="analyze_button",
            help="이력서와 채용공고를 분석합니다"
        )

    # 분석 로직
    if analyze_button:
        if uploaded_file is not None and job_description:
            with st.spinner("이력서를 분석중입니다..."):
                try:
                    # 이미 추출된 텍스트 사용
                    text = st.session_state.resume_text
                    
                    # 기존 분석 로직
                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": """당신은 전문 채용 담당자입니다. 
다음 형식에 맞춰 이력서를 분석해주세요:

📝경력 요약
    ㆍ총 경력 기간: 총 X년 Y개월
    ㆍ주요 경력:
        [최근 회사명]: [직위/직책]
        [이전 회사명]: [직위/직책]
        [이전 회사명]: [직위/직책]
    ㆍ주요 업무 : [핵심 업무 내용 요약]

🧠 추측되는 성격
    ㆍ[성격 특성] (예: [이력서에서 발견된 근거 문장])
    ㆍ[성격 특성] (예: [이력서에서 발견된 근거 문장])
    ㆍ[성격 특성] (예: [이력서에서 발견된 근거 문장])
    ㆍ[성격 특성] (예: [이력서에서 발견된 근거 문장])

⚠️ 미확인/부족한 요건:
    ㆍ[공고에서 요구하는 항목이 이력서에 없거나 불충분한 경우 요약]
    ㆍ...
    ㆍ...

조건:
- "없다"고 단정하지 말고, '명확히 나타나지 않음' / '구체적인 내용 부족' / '경험이 불분명함' 등 완곡하고 객관적인 표현을 사용해 주세요.
- 경력 연수나 특정 인증, 시스템 경험 등이 불충분하거나 확인 어려운 경우 구체적으로 짚어주세요.
- 최대 5개 이내의 항목으로 간결하게 정리해주세요."""},
                            {"role": "user", "content": f"다음은 이력서 내용입니다:\n\n{text}\n\n다음은 채용공고입니다:\n\n{job_description}\n\n위 형식에 맞춰 이력서를 분석해주세요."}
                        ]
                    )
                    analysis_result = response.choices[0].message.content
                    
                    # 경력기간 산정 결과가 있는 경우 분석 결과에 반영
                    if 'experience_years' in st.session_state and 'experience_months' in st.session_state:                    
                        # 채용공고에서 필수 경력 연차 추출
                        required_years = 0
                        required_years_min = 0
                        required_years_max = 0
                        experience_type = None
                        
                        if "경력" in job_description:
                            # 1. x년 이상 패턴
                            pattern_over = r'경력\s*(\d+)년\s*이상'
                            # 2. x~y년 패턴
                            pattern_range = r'경력\s*(\d+)~(\d+)년'
                            # 3. x년 미만/이하 패턴
                            pattern_under = r'경력\s*(\d+)년\s*(미만|이하|이내)'
                            
                            if match := re.search(pattern_over, job_description):
                                required_years = int(match.group(1))
                                experience_type = "over"
                            elif match := re.search(pattern_range, job_description):
                                required_years_min = int(match.group(1))
                                required_years_max = int(match.group(2))
                                experience_type = "range"
                            elif match := re.search(pattern_under, job_description):
                                required_years = int(match.group(1))
                                experience_type = "under"
                        
                        # 경력 부합도 계산
                        experience_years = st.session_state.experience_years + (st.session_state.experience_months / 12)
                        fit_status = ""
                        
                        if experience_type == "over":
                            if experience_years >= required_years:
                                fit_status = "부합"
                            else:
                                # 정수 부분과 소수 부분을 분리하여 계산
                                exp_years = int(experience_years)
                                exp_months = int((experience_years % 1) * 12)
                                
                                # 부족한 년수 계산
                                remaining_years = required_years - exp_years
                                
                                # 부족한 개월수 계산
                                if exp_months > 0:
                                    remaining_months = 12 - exp_months
                                    remaining_years -= 1  # 개월이 있으면 년수를 1 빼고 개월을 더함
                                else:
                                    remaining_months = 0
                                
                                fit_status = f"{remaining_years}년{f' {remaining_months}개월' if remaining_months > 0 else ''} 부족"
                        elif experience_type == "range":
                            if required_years_min <= experience_years <= required_years_max:
                                fit_status = "부합"
                            else:
                                if experience_years < required_years_min:
                                    # 정수 부분과 소수 부분을 분리하여 계산
                                    exp_years = int(experience_years)
                                    exp_months = int((experience_years % 1) * 12)
                                    
                                    # 부족한 년수 계산
                                    remaining_years = required_years_min - exp_years
                                    
                                    # 부족한 개월수 계산
                                    if exp_months > 0:
                                        remaining_months = 12 - exp_months
                                        remaining_years -= 1  # 개월이 있으면 년수를 1 빼고 개월을 더함
                                    else:
                                        remaining_months = 0
                                    
                                    fit_status = f"{remaining_years}년{f' {remaining_months}개월' if remaining_months > 0 else ''} 부족"
                                else:
                                    over_years = int(experience_years - required_years_max)
                                    over_months = int((experience_years % 1) * 12)
                                    fit_status = f"{over_years}년{f' {over_months}개월' if over_months > 0 else ''} 초과"
                        elif experience_type == "under":
                            if experience_years <= required_years:
                                fit_status = "부합"
                            else:
                                over_years = int(experience_years - required_years)
                                over_months = int((experience_years % 1) * 12)
                                fit_status = f"{over_years}년{f' {over_months}개월' if over_months > 0 else ''} 초과"
                        
                        # 분석 결과에서 경력기간 부분을 찾아서 교체
                        experience_patterns = [
                            r"ㆍ총 경력 기간:.*",
                            r"ㆍ총 경력기간:.*"
                        ]
                        
                        # 경력 요건이 없는 경우와 있는 경우 분리
                        if not experience_type:
                            replacement = f"ㆍ총 경력 기간: {st.session_state.experience_years}년 {st.session_state.experience_months}개월"
                        else:
                            replacement = f"ㆍ총 경력 기간: {st.session_state.experience_years}년 {st.session_state.experience_months}개월 ({fit_status})"
                        
                        for pattern in experience_patterns:
                            analysis_result = re.sub(pattern, replacement, analysis_result)
                    
                    st.session_state.analysis_result = analysis_result
                except Exception as e:
                    st.error(f"분석 중 오류가 발생했습니다: {str(e)}")
        else:
            st.warning("이력서 파일과 채용공고를 모두 입력해주세요.")

    # 분석 결과를 구분선으로 분리하여 표시
    if st.session_state.analysis_result:
        st.markdown("<div style='margin-top: 10px;'>", unsafe_allow_html=True)
        st.text_area("분석 결과", st.session_state.analysis_result, height=400)
        st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state['current_page'] == "interview1":
    st.markdown("""
        <h5 style='color: #333333; margin-bottom: 20px;'>
            ☝️ 1차 면접 질문
        </h5>
    """, unsafe_allow_html=True)
    st.markdown("""
        <small style='color: #666666;'>
            1~6번은 직무기반의 경험, 프로젝트, 문제해결, 자격요건 관련 사례 질문<br>
            7~10번은 핵심가치 기반의 '[도전]두려워 말고 시도합니다, [책임감]대충은 없습니다, [협력]동료와 협업합니다, [전문성]능동적으로 일합니다'와 관련된 사례 질문
        </small>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    # 질문 추출 버튼을 왼쪽에 배치
    col1, col2 = st.columns([1, 4])
    with col1:
        question_button = st.button(
            "질문 추출하기",
            key="question_button",
            help="분석 결과를 바탕으로 면접 질문을 생성합니다"
        )

    # 질문 생성 로직
    if question_button:
        if st.session_state.analysis_result and st.session_state.analysis_result != "":
            with st.spinner("면접 질문을 생성중입니다..."):
                try:
                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": """당신은 경험 많은 면접관입니다. 
다음 형식에 맞춰 10개의 면접 질문을 생성해주세요:

[직무 관련 질문 1-6번]
- 경력과 프로젝트 경험
- 문제 해결 사례
- 자격요건 충족 여부
- 전문성 검증
각 질문은 구체적인 경험과 상황, 역할, 결과를 물어보는 방식으로 작성

[핵심가치 관련 질문 7-10번]
7번: [도전] 새로운 시도나 혁신 경험
8번: [책임감] 책임감 있는 업무 수행 사례
9번: [협력] 팀워크와 협업 경험
10번: [전문성] 전문성 발휘 사례

각 질문은 다음 형식으로 작성:
1. [구체적인 상황/경험에 대한 질문] + [역할과 결과에 대한 추가 질문]"""},
                            {"role": "user", "content": f"이력서 분석 결과:\n{st.session_state.analysis_result}\n\n채용공고:\n{job_description}\n\n위 내용을 바탕으로 상세한 면접 질문 10개를 생성해주세요."}
                        ]
                    )
                    st.session_state.interview_questions = response.choices[0].message.content
                except Exception as e:
                    st.error(f"질문 생성 중 오류가 발생했습니다: {str(e)}")
        else:
            st.warning("먼저 이력서 분석을 진행해주세요.")

    # 면접 질문 결과 표시
    if st.session_state.interview_questions:
        st.markdown("<div style='margin-top: 10px;'>", unsafe_allow_html=True)
        st.text_area("면접 질문", st.session_state.interview_questions, height=450)
        st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state['current_page'] == "interview2":
    st.markdown("""
        <h5 style='color: #333333; margin-bottom: 20px;'>
            ✌️ 2차 면접 질문
        </h5>
    """, unsafe_allow_html=True)
    st.info("2차 면접 질문 기능은 준비 중입니다.")

