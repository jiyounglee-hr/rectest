import streamlit as st
import PyPDF2
from io import BytesIO
import os
import openai
from dotenv import load_dotenv
from datetime import datetime
import pandas as pd
import re

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
                if '현재' in line or '재직중' in line:
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
    result = "\n".join(experience_periods)
    if result:
        result += f"\n\n총 경력기간: {total_years}년 {total_remaining_months}개월 ({total_decimal_years}년)"
    
    return result

# 세션 상태 초기화
if 'analysis_result' not in st.session_state:
    st.session_state['analysis_result'] = None
if 'interview_questions' not in st.session_state:
    st.session_state['interview_questions'] = None
if 'job_description' not in st.session_state:
    st.session_state['job_description'] = None
if 'current_page' not in st.session_state:
    st.session_state['current_page'] = 'resume'

# 페이지 설정
st.set_page_config(page_title="뉴로핏 채용 - 이력서 분석", layout="wide")

# OpenAI API 키 설정
openai.api_key = st.secrets["OPENAI_API_KEY"]

# 사이드바 스타일 수정
st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            min-width: 420px !important;
            max-width: 420px !important;
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
        </style>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "PDF 파일을 선택해주세요",
        type=['pdf'],
        help="200MB 이하의 PDF 파일만 가능합니다"
    )
    
    if uploaded_file:
        st.markdown(f"<div style='padding: 5px 0px; color: #666666;'>{uploaded_file.name}</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='upload-text'>Drag and drop file here<br>Limit 200MB per file • PDF</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # 맨 마지막에 도움말 추가
    st.markdown("<br>", unsafe_allow_html=True)  # 약간의 여백 추가
    with st.expander("도움말"):
        st.write("""
        1. PDF 형식의 이력서 파일을 업로드해주세요.
        2. 채용공고 내용을 입력해주세요.
        3. '분석 시작' 버튼을 클릭하면 이력서 분석과 면접 질문이 생성됩니다.
        """)

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

# 1. 채용요건 섹션
st.markdown("""
    <h4 style='color: #333333; margin-bottom: 20px;'>
        1. 채용요건
    </h4>
""", unsafe_allow_html=True)
job_option = st.selectbox(
    "채용공고 선택",
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
        # 기본값으로 기존 내용을 보여주고, 수정 가능하도록 설정
        default_description = job_descriptions[job_map[job_option]]
        job_description = st.text_area(
            "채용공고 내용 (필요시 수정 가능합니다)",
            value=default_description,
            height=500
        )
    else:
        job_description = ""

# 2. 이력서 분석 섹션 수정
st.markdown("""
    <h4 style='color: #333333; margin-bottom: 20px;'>
        2. 이력서 분석
    </h4>
""", unsafe_allow_html=True)

# 경력기간 입력 섹션 추가
st.markdown("""
    <style>
        .stTextArea textarea {
            font-family: monospace;
        }
    </style>
""", unsafe_allow_html=True)

experience_text = st.text_area(
    "경력기간 입력 (이력서의 날짜 부분을 복사하여 붙여넣으세요.)",
    height=200,
    help="예시:\n2023-04-24 ~ 2024-05-10\n2019-06-03 ~ 2023-04-21\n2019-01-21 ~ 2019-05-31\n2015-07-01 ~ 2019-01-18"
)

if experience_text:
    try:
        result = calculate_experience(experience_text)
        st.markdown("### 경력기간 계산 결과")
        st.text(result)
        st.markdown("---")
    except Exception as e:
        st.error(f"경력기간 계산 중 오류가 발생했습니다: {str(e)}")

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
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()

                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": """당신은 전문 채용 담당자입니다. 
다음 형식에 맞춰 이력서를 분석해주세요:

(1) 핵심 경력 요약
- 총 경력 기간: [총 경력 연월]
- 주요 직무 경험:
1) [최근 회사명]: [직위/직책]
2) [이전 회사명]: [직위/직책]
3) [이전 회사명]: [직위/직책]
- 주요 업무 내용: [핵심 업무 내용 요약]

(2) 채용요건 연관성 분석
- 부합되는 요건: [채용공고의 요건 중 이력서에서 확인된 항목들]
- 미확인/부족 요건: [채용공고의 요건 중 이력서에서 확인되지 않거나 부족한 항목들]"""},
                        {"role": "user", "content": f"다음은 이력서 내용입니다:\n\n{text}\n\n다음은 채용공고입니다:\n\n{job_description}\n\n위 형식에 맞춰 이력서를 분석해주세요."}
                    ]
                )
                st.session_state.analysis_result = response.choices[0].message.content
            except Exception as e:
                st.error(f"분석 중 오류가 발생했습니다: {str(e)}")
    else:
        st.warning("이력서 파일과 채용공고를 모두 입력해주세요.")

# 분석 결과를 구분선으로 분리하여 표시
if st.session_state.analysis_result:
    st.markdown("<div style='margin-top: 10px;'>", unsafe_allow_html=True)
    st.text_area("분석 결과", st.session_state.analysis_result, height=350)
    st.markdown("</div>", unsafe_allow_html=True)

# 3. 면접 질문 섹션
st.markdown("""
    <h4 style='color: #333333; margin: 30px 0 20px 0;'>
        3. 면접 질문 TIP
    </h4>
""", unsafe_allow_html=True)

st.markdown("""
    <small style='color: #666666;'>
        1~6번은 직무기반의 경험, 프로젝트, 문제해결, 자격요건 관련 사례 질문<br>
        7~10번은 핵심가치 기반의 '[도전]두려워 말고 시도합니다, [책임감]대충은 없습니다, [협력]동료와 협업합니다, [전문성]능동적으로 일합니다'와 관련된 사례 질문
    </small>
""", unsafe_allow_html=True)

# 질문 추출 버튼을 왼쪽에 배치
col3, col4 = st.columns([1, 4])
with col3:
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

# 면접 질문 결과를 구분선으로 분리하여 표시
if st.session_state.interview_questions:
    st.markdown("<div style='margin-top: 10px;'>", unsafe_allow_html=True)
    st.text_area("면접 질문", st.session_state.interview_questions, height=450)
    st.markdown("</div>", unsafe_allow_html=True) 