import streamlit as st
import pandas as pd
import numpy as np
from oauth2client.service_account import ServiceAccountCredentials
import gspread
from gspread.client import Client
import json
import time
from datetime import datetime
import base64
from io import BytesIO
import PyPDF2
from xhtml2pdf import pisa

# Google Sheets 클라이언트 초기화 함수
def init_google_sheets():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["google_credentials"], scope)
    client = Client(auth=creds)
    return client

# PDF 생성 함수
def create_pdf(html_content):
    # PDF 생성을 위한 메모리 버퍼
    result = BytesIO()
    
    # HTML을 PDF로 변환
    pdf = pisa.pisaDocument(
        BytesIO(html_content.encode("UTF-8")),
        result,
        encoding='UTF-8'
    )
    
    # 변환 실패 시 에러 반환
    if pdf.err:
        st.error("PDF 생성 중 오류가 발생했습니다.")
        return None
    
    # PDF 바이트 데이터 반환
    return result.getvalue()

# 페이지 설정 (반드시 첫 번째 명령어여야 함)
st.set_page_config(
    page_title="HR Resume Analyzer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

import PyPDF2
from io import BytesIO
import os
import openai
from dotenv import load_dotenv
from datetime import datetime
import pandas as pd
import re
import base64
import requests
from bs4 import BeautifulSoup
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import time
from xhtml2pdf import pisa
from pathlib import Path

# OpenAI API 키 설정
openai.api_key = st.secrets["OPENAI_API_KEY"]

def get_eval_template_from_sheet(selected_dept, selected_job):
    try:
        # 선택된 본부에 해당하는 템플릿이 있는 경우 해당 템플릿 반환
        if selected_dept in eval_template:
            return eval_template[selected_dept]
            
        # 선택된 본부에 해당하는 템플릿이 없는 경우 구글 시트에서 조회
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        credentials_dict = {
            "type": st.secrets["google_credentials"]["type"],
            "project_id": st.secrets["google_credentials"]["project_id"],
            "private_key_id": st.secrets["google_credentials"]["private_key_id"],
            "private_key": st.secrets["google_credentials"]["private_key"],
            "client_email": st.secrets["google_credentials"]["client_email"],
            "client_id": st.secrets["google_credentials"]["client_id"],
            "auth_uri": st.secrets["google_credentials"]["auth_uri"],
            "token_uri": st.secrets["google_credentials"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["google_credentials"]["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["google_credentials"]["client_x509_cert_url"]
        }
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
        gc = gspread.authorize(credentials)
        sheet_id = st.secrets["google_sheets"]["department_job_sheet_id"]
        worksheet = gc.open_by_key(sheet_id).sheet1
        
        try:
            data = worksheet.get_all_records()
        except gspread.exceptions.APIError as e:
            st.warning("평가 템플릿을 불러오는 중 일시적인 오류가 발생했습니다. 기본 템플릿을 사용합니다.")
            return default_template
        
        for row in data:
            if row['본부'] == selected_dept and row['직무'] == selected_job:
                def format_items(val):
                    if not val:
                        return ""
                    # 먼저 모든 bullet point를 제거하고 쉼표나 줄바꿈으로 분리
                    items = []
                    text = str(val).replace('•', '').strip()
                    for item in text.replace('\n', ',').split(','):
                        if item.strip():
                            items.append(item.strip())
                    return "\n".join(f"• {item}" for item in items)
                
                st.markdown("""
                    <style>
                        .eval-content {
                            font-size: 0.9em;
                            white-space: pre-wrap;
                            margin: 0;
                            padding: 0;
                            line-height: 1.8;
                        }
                        .stMarkdown div[data-testid="stMarkdownContainer"] p {
                            white-space: pre-wrap;
                        }
                    </style>
                """, unsafe_allow_html=True)
                
                return [
                    {"구분": "업무 지식", "내용": format_items(row.get('업무지식', '')), "만점": 30, "점수": 0, "의견": ""},
                    {"구분": "직무기술", "내용": format_items(row.get('직무기술', '')), "만점": 30, "점수": 0, "의견": ""},
                    {"구분": "직무 수행 태도 및 자세", "내용": format_items(row.get('직무수행 태도 및 자세', '')), "만점": 30, "점수": 0, "의견": ""},
                    {"구분": "기본인성", "내용": "• 복장은 단정한가?\n• 태도는 어떤가?\n• 적극적으로 답변하는가?", "만점": 10, "점수": 0, "의견": ""}
                ]
        
        # 해당하는 템플릿이 없는 경우 기본 템플릿 반환
        return default_template
        
    except Exception as e:
        return default_template

# 구글 스프레드시트 인증 및 데이터 가져오기
def get_google_sheet_data():
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        credentials_dict = {
            "type": st.secrets["google_credentials"]["type"],
            "project_id": st.secrets["google_credentials"]["project_id"],
            "private_key_id": st.secrets["google_credentials"]["private_key_id"],
            "private_key": st.secrets["google_credentials"]["private_key"],
            "client_email": st.secrets["google_credentials"]["client_email"],
            "client_id": st.secrets["google_credentials"]["client_id"],
            "auth_uri": st.secrets["google_credentials"]["auth_uri"],
            "token_uri": st.secrets["google_credentials"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["google_credentials"]["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["google_credentials"]["client_x509_cert_url"]
        }
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
        gc = gspread.authorize(credentials)
        
        # 본부와 직무 데이터가 있는 시트 ID
        sheet_id = st.secrets["google_sheets"]["department_job_sheet_id"]
        worksheet = gc.open_by_key(sheet_id).sheet1
        
        # 데이터 가져오기
        data = worksheet.get_all_records()
        
        # 본부와 직무 데이터 정리
        departments = sorted(list(set(row['본부'] for row in data if row['본부'])))
        jobs = {}
        for dept in departments:
            jobs[dept] = sorted(list(set(row['직무'] for row in data if row['본부'] == dept and row['직무'])))
            
        return departments, jobs
    except Exception as e:
        # st.error(f"구글 스프레드시트 데이터를 가져오는 중 오류가 발생했습니다: {str(e)}")
        return [], {}

# 평가 항목 템플릿 가져오기
def get_evaluation_template():
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        credentials_dict = {
            "type": st.secrets["google_credentials"]["type"],
            "project_id": st.secrets["google_credentials"]["project_id"],
            "private_key_id": st.secrets["google_credentials"]["private_key_id"],
            "private_key": st.secrets["google_credentials"]["private_key"],
            "client_email": st.secrets["google_credentials"]["client_email"],
            "client_id": st.secrets["google_credentials"]["client_id"],
            "auth_uri": st.secrets["google_credentials"]["auth_uri"],
            "token_uri": st.secrets["google_credentials"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["google_credentials"]["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["google_credentials"]["client_x509_cert_url"]
        }
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
        gc = gspread.authorize(credentials)
        
        # 평가 항목 데이터가 있는 시트 ID
        sheet_id = st.secrets["google_sheets"]["evaluation_template_sheet_id"]
        worksheet = gc.open_by_key(sheet_id).sheet1
        
        # 데이터 가져오기
        data = worksheet.get_all_records()
        
        # 직무별 평가 항목 정리
        eval_templates = {}
        for row in data:
            dept = row.get('본부', '')
            job = row.get('직무', '')
            if dept and job:
                key = f"{dept}-{job}"
                if key not in eval_templates:
                    eval_templates[key] = []
                eval_templates[key].append({
                    "구분": row.get('구분', ''),
                    "내용": row.get('내용', '').split('\n'),  # 줄바꿈으로 구분된 내용을 리스트로 변환
                    "만점": int(row.get('만점', 0))
                })
        
        return eval_templates
        
    except Exception as e:
        # st.error(f"평가 항목 템플릿을 가져오는 중 오류가 발생했습니다: {str(e)}")
        return {}

# 기본 평가 템플릿
default_template = [
    {"구분": "업무 지식", "내용": "", "만점": 30, "점수": 0, "의견": ""},
    {"구분": "직무기술", "내용": "", "만점": 30, "점수": 0, "의견": ""},
    {"구분": "직무 수행 태도 및 자세", "내용": "", "만점": 30, "점수": 0, "의견": ""},
    {"구분": "기본인성", "내용": "", "만점": 10, "점수": 0, "의견": ""}
]

# 본부와 직무 데이터 가져오기
departments, jobs = get_google_sheet_data()

# 기본값 설정
selected_dept = None
selected_job = None


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

# 세션 상태 초기화
if 'current_page' not in st.session_state:
    st.session_state['current_page'] = 'resume'
if 'analysis_result' not in st.session_state:
    st.session_state['analysis_result'] = None
if 'interview_questions1' not in st.session_state:
    st.session_state['interview_questions1'] = None
if 'interview_questions2' not in st.session_state:
    st.session_state['interview_questions2'] = None
if 'job_description' not in st.session_state:
    st.session_state['job_description'] = None
if 'interview_evaluation' not in st.session_state:
    st.session_state['interview_evaluation'] = None

# URL 파라미터 처리
page_param = st.query_params.get("page", "resume")
valid_pages = ['resume', 'interview1', 'interview2', 'evaluation', 'admin']

# URL 파라미터가 유효한 경우에만 페이지 상태 업데이트
if isinstance(page_param, str) and page_param in valid_pages:
    st.session_state['current_page'] = page_param

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

    def switch_to_evaluation():
        st.query_params["page"] = "evaluation"
        st.session_state['current_page'] = 'evaluation'

        
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
        st.markdown("---")  
    def switch_to_admin():
        st.query_params["page"] = "admin"
        st.session_state['current_page'] = 'admin'
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

    st.button("📝 면접평가표", 
            key="btn_evaluation", 
            on_click=switch_to_evaluation,
            type="primary" if st.session_state['current_page'] == "evaluation" else "secondary")
    
    st.markdown('</div>', unsafe_allow_html=True)

    # 맨 마지막에 도움말 추가
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("도움말"):
        st.write("""
        🤖 이력서분석 : PDF 형식의 이력서 파일을 업로드 > 채용요건 확인 > 경력기간 체크(필요 시) > '분석 시작하기' \n
        ☝️ 1차 면접 질문 : 직무기반의 경험, 프로젝트, 문제해결, 자격요건 관련 사례 질문\n
        ✌️ 2차 면접 질문 : 핵심가치 기반의 [도전]두려워 말고 시도합니다, [책임감]대충은 없습니다, [협력]동료와 협업합니다, [전문성]능동적으로 일합니다\n
        📝 면접평가표 : 면접 평가를 위한 평가표 (개발예정)
        """)
    st.markdown('<div class="label-text"><a href="https://neurophet.sharepoint.com/sites/HR2/Shared%20Documents/Forms/AllItems.aspx?as=json&id=%2Fsites%2FHR2%2FShared%20Documents%2F%EC%B1%84%EC%9A%A9&viewid=f1a0986e%2Dd990%2D4f37%2Db273%2Dd8a6df2f4c40" target="_blank" class="web-link">🔗후보자 이력서 링크</a></div>', unsafe_allow_html=True)
    st.markdown('<div class="label-text"><a href="https://career.neurophet.com/recruit" target="_blank" class="web-link">🔗뉴로핏 커리어</a></div>', unsafe_allow_html=True)

    # CSS 스타일 추가
    st.markdown("""
        <style>
        .admin-button {
            display: block;
            margin-top: 5px;
            background: none;
            border: none;
            color: #888888;
            font-size: 0.8em;
            opacity: 0.3;
            cursor: pointer;
            padding: 0;
            text-decoration: none !important;
        }
        .admin-button:hover {
            opacity: 0.8;
            text-decoration: none !important;
            color: #888888;
        }
        </style>
    """, unsafe_allow_html=True)

    # 빈 공간 추가
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 채용관리자 버튼
    st.markdown(f"""
        <a href="?page=admin" class="admin-button">
            ⚙️
        </a>
    """, unsafe_allow_html=True)

    # 본부와 직무 데이터 가져오기
    departments, jobs = get_google_sheet_data()
    
    # 본부와 직무 선택에 따라 템플릿 자동 반영
    if selected_dept and selected_job:
        st.session_state.eval_data = get_eval_template_from_sheet(selected_dept, selected_job)
    else:
        st.session_state.eval_data = default_template

# 채용공고 데이터
job_descriptions = {}

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
            "채용공고 타입 선택",
            ["링크 입력", "직접 입력"]
        )

        job_description = ""  # 여기로 이동
        if job_option == "직접 입력":
            job_description = st.text_area("채용공고 내용을 입력해주세요", height=300)
        else:
            # 채용공고 링크 입력
            job_link = st.text_input("채용공고 링크를 입력해주세요", placeholder="https://career.neurophet.com/...")

            if job_link:
                try:
                    # 웹 브라우저처럼 보이기 위한 헤더 설정
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                        'Sec-Fetch-Dest': 'document',
                        'Sec-Fetch-Mode': 'navigate',
                        'Sec-Fetch-Site': 'none',
                        'Sec-Fetch-User': '?1'
                    }
                    
                    # 웹 페이지 가져오기
                    response = requests.get(job_link, headers=headers, timeout=10)
                    response.raise_for_status()
                    
                    # 인코딩 설정
                    response.encoding = 'utf-8'
                    
                    # HTML 파싱
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 채용공고 내용 추출
                    job_title = soup.find(['h1', 'h2', 'h3'], string=lambda x: x and any(keyword in x.lower() for keyword in ['채용', '모집', '공고', 'job']))
                    if not job_title:
                        job_title = soup.find(['h1', 'h2', 'h3'])
                    
                    if not job_title:
                        job_title = "채용공고"
                    else:
                        job_title = job_title.get_text(strip=True)
                    
                    # 담당업무, 필수자격, 우대사항 추출
                    job_description = f"[{job_title}]\n"
                    
                    # 불필요한 내용 필터링을 위한 패턴
                    skip_patterns = [
                        "About us", "Recruit", "Culture", "Benefit", "FAQ",
                        "개인정보처리방침", "이용약관", "뉴로핏 주식회사", "Copyright",
                        "All Rights Reserved", "테헤란로", "삼원타워", "+82"
                    ]
                    
                    # 섹션별 내용 저장을 위한 딕셔너리
                    sections = {
                        "담당업무": [],
                        "필수자격": [],
                        "우대사항": [],
                        "기타정보": []
                    }
                    
                    # 모든 텍스트 블록 찾기
                    content_blocks = soup.find_all(['div', 'p', 'ul', 'li', 'section', 'article'])
                    
                    current_section = None
                    for block in content_blocks:
                        text = block.get_text(strip=True)
                        
                        # 빈 텍스트나 불필요한 내용 건너뛰기
                        if not text or any(pattern in text for pattern in skip_patterns):
                            continue
                        
                        # 섹션 제목 확인
                        if any(keyword in text for keyword in ['담당 업무', '주요 업무', '업무 내용', '수행 업무', '함께 할 업무']):
                            current_section = "담당업무"
                            continue
                        elif any(keyword in text for keyword in ['자격 요건', '필수 요건', '지원 자격', '자격사항', '이런 역량을 가진 분']):
                            current_section = "필수자격"
                            continue
                        elif any(keyword in text for keyword in ['우대사항', '우대 사항', '우대 조건', '이런 경험이 있다면']):
                            current_section = "우대사항"
                            continue
                        elif any(keyword in text for keyword in ['기타', '복리후생', '근무조건', '근무 환경', '합류 여정', '꼭 확인해주세요']):
                            current_section = "기타정보"
                            continue
                        
                        # 현재 섹션에 내용 추가
                        if current_section:
                            # 불필요한 문자 제거
                            text = text.replace("•", "").replace("·", "").replace("-", "").strip()
                            if text and len(text) > 1:  # 빈 항목이나 단일 문자 제외
                                # 중복 체크 후 추가
                                if text not in sections[current_section]:
                                    sections[current_section].append(text)
                    
                    # 섹션이 비어있는 경우 대체 방법으로 내용 추출
                    if all(len(section) == 0 for section in sections.values()):
                        # 모든 텍스트 내용을 추출
                        all_text = soup.get_text(separator='\n', strip=True)
                        job_description = f"[{job_title}]\n\n{all_text}"
                    else:
                        # 정리된 내용을 job_description에 추가
                        if sections["담당업무"]:
                            job_description += "\n담당업무\n"
                            for item in sections["담당업무"]:
                                job_description += f"- {item}\n"
                        
                        if sections["필수자격"]:
                            job_description += "\n필수자격\n"
                            for item in sections["필수자격"]:
                                job_description += f"- {item}\n"
                        
                        if sections["우대사항"]:
                            job_description += "\n우대사항\n"
                            for item in sections["우대사항"]:
                                job_description += f"- {item}\n"
                        
                        if sections["기타정보"]:
                            job_description += "\n기타 정보\n"
                            for item in sections["기타정보"]:
                                job_description += f"- {item}\n"
                    
                    # 채용공고 내용이 비어있는 경우 처리
                    if not job_description.strip():
                        raise ValueError("채용공고 내용을 찾을 수 없습니다. 링크를 확인해주세요.")
                    
                    # 채용공고 내용 표시
                    st.text_area("채용공고 내용", job_description, height=300)
                    
                except ValueError as ve:
                    st.error(str(ve))
                    job_description = ""
                except requests.exceptions.RequestException as e:
                    st.error(f"채용공고를 가져오는 중 네트워크 오류가 발생했습니다: {str(e)}")
                    job_description = ""
                except Exception as e:
                    st.error(f"채용공고를 가져오는 중 오류가 발생했습니다: {str(e)}")
                    job_description = ""
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
        if 'resume_text' in st.session_state and st.session_state.resume_text:
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
                        line-height: 1.5;
                        white-space: pre-wrap;
                        margin: 10px 0;
                    }
                </style>
            """, unsafe_allow_html=True)
            st.markdown('<div class="label-text">📄 이력서 내용 </div>', unsafe_allow_html=True)
            st.markdown(f'<div class="resume-text">{st.session_state.resume_text}</div>', unsafe_allow_html=True)

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
    ㆍ학력 : [전문대, 대학교, 대학원 / 학과]
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
    
    # 채용공고 링크 입력
    job_link = st.text_input("채용공고 링크를 입력해주세요", placeholder="https://career.neurophet.com/...")
    
    if job_link:
        try:
            # 웹 브라우저처럼 보이기 위한 헤더 설정
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1'
            }
            
            # 웹 페이지 가져오기
            response = requests.get(job_link, headers=headers, timeout=10)
            response.raise_for_status()
            
            # 인코딩 설정
            response.encoding = 'utf-8'
            
            # HTML 파싱
            soup = BeautifulSoup(response.text, 'lxml')
            
            # 채용공고 내용 추출
            job_title = soup.find('h1')
            if not job_title:
                raise ValueError("채용공고 제목을 찾을 수 없습니다.")
            job_title = job_title.get_text(strip=True)
            
            # 담당업무, 필수자격, 우대사항 추출
            job_description = f"[{job_title}]\n"
            
            # 불필요한 내용 필터링을 위한 패턴
            skip_patterns = [
                "About us", "Recruit", "Culture", "Benefit", "FAQ",
                "개인정보처리방침", "이용약관", "뉴로핏 주식회사", "Copyright",
                "All Rights Reserved", "테헤란로", "삼원타워", "+82"
            ]
            
            # 섹션별 내용 저장을 위한 딕셔너리
            sections = {
                "담당업무": [],
                "필수자격": [],
                "우대사항": [],
                "기타정보": []
            }
            
            # 모든 텍스트 블록 찾기
            content_blocks = soup.find_all(['h2', 'h3', 'h4', 'div', 'p', 'ul', 'li'])
            
            current_section = None
            for block in content_blocks:
                text = block.get_text(strip=True)
                
                # 빈 텍스트나 불필요한 내용 건너뛰기
                if not text or any(pattern in text for pattern in skip_patterns):
                    continue
                
                # 섹션 제목 확인
                if "함께 할 업무" in text:
                    current_section = "담당업무"
                    continue
                elif "역량을 가진 분" in text or "이런 분을 찾" in text:
                    current_section = "필수자격"
                    continue
                elif "경험이 있다면 더 좋" in text or "우대" in text:
                    current_section = "우대사항"
                    continue
                elif "합류 여정" in text or "꼭 확인해주세요" in text:
                    current_section = "기타정보"
                    continue
                
                # 현재 섹션에 내용 추가
                if current_section:
                    # 불필요한 문자 제거
                    text = text.replace("•", "").strip()
                    if text and len(text) > 1:  # 빈 항목이나 단일 문자 제외
                        # 중복 체크 후 추가
                        if text not in sections[current_section]:
                            sections[current_section].append(text)
            
            # 정리된 내용을 job_description에 추가
            if sections["담당업무"]:
                job_description += "\n담당업무\n"
                for item in sections["담당업무"]:
                    job_description += f"- {item}\n"
            
            if sections["필수자격"]:
                job_description += "\n필수자격\n"
                for item in sections["필수자격"]:
                    job_description += f"- {item}\n"
            
            if sections["우대사항"]:
                job_description += "\n우대사항\n"
                for item in sections["우대사항"]:
                    job_description += f"- {item}\n"
            
            if sections["기타정보"]:
                job_description += "\n기타 정보\n"
                for item in sections["기타정보"]:
                    if "근무" in item or "급여" in item or "제출" in item:
                        job_description += f"- {item}\n"
            
            # 채용공고 내용이 비어있는 경우 처리
            if not job_description.strip():
                raise ValueError("채용공고 내용을 찾을 수 없습니다. 링크를 확인해주세요.")
            
            # 채용공고 내용 표시
            st.text_area("채용공고 내용", job_description, height=300)
            
        except ValueError as ve:
            st.error(str(ve))
            job_description = ""
        except requests.exceptions.RequestException as e:
            st.error(f"채용공고를 가져오는 중 네트워크 오류가 발생했습니다: {str(e)}")
            job_description = ""
        except Exception as e:
            st.error(f"채용공고를 가져오는 중 오류가 발생했습니다: {str(e)}")
            job_description = ""
    else:
        job_description = ""
 
    # 질문 추출 버튼을 왼쪽에 배치
    col1, col2 = st.columns([1, 4])
    with col1:
        question_button = st.button(
            "질문 추출하기",
            key="question_button1",
            help="분석 결과를 바탕으로 면접 질문을 생성합니다"
        )
    st.markdown("""
        <small style='color: #666666;'>
            업무 지식 및 직무기술 직무 수행 태도 및 자세 관련 질문입니다. <br>
            인상, 태도, 복장 등 전반적인 기본자세는 잘 관찰해주시고, 경력자의 경우 이직사유에 대해서도 체크부탁드립니다. 
        </small>
    """, unsafe_allow_html=True)  
    # 질문 생성 로직
    if question_button:
        if uploaded_file and job_description:
            with st.spinner("면접 질문을 생성중입니다..."):
                try:
                    # 이력서 내용 가져오기
                    text = st.session_state.resume_text
                    
                    # 1차 면접 질문 생성
                    response1 = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": """[당신의 역할]  
당신은 지원자의 이력서와 채용공고 내용을 바탕으로 면접 질문을 준비하는 면접관입니다.  
지원자의 과거 경험을 구체적으로 확인하고, 실제 업무 수행 역량을 검증하기 위해 STAR 기법에 기반한 질문을 작성해야 합니다.

[목적]  
다음 정보를 바탕으로, 지원자의 경험과 역량을 효과적으로 검증할 수 있는 면접 질문을 STAR 구조로 생성하세요.  
각 질문은 다음 4단계가 자연스럽게 드러나야 합니다:  
- Situation (상황)  
- Task (과제)  
- Action (행동)  
- Result (결과)  

[입력 데이터]  
① 이력서: 지원자의 경력, 프로젝트 경험, 사용 기술, 직무 배경, 업무 이력  
② 채용공고: 담당업무, 필수 자격요건, 우대사항

[질문 생성 요구사항]  
1. 업무 지식 및 직무기술은 반드시 10개를 생성해야 합니다.  
2. 직무 수행 태도 및 자세는 5개를 생성해야 합니다.  
3. 모든 질문은 STAR 구조를 따릅니다.  
4. 질문은 구체적이고 실제적인 경험을 이끌어내는 형식으로 구성해야 합니다.  
5. 질문은 이력서의 내용과 채용공고 요구사항의 연관성을 고려해 작성해야 합니다.  
6. 기본인성 항목 중 관찰 항목은 질문하지 마십시오.

[질문 카테고리 및 예시]

1. 업무 지식 및 직무기술 (반드시 10개 질문)  
지원자의 전문성과 실무 기술을 확인할 수 있는 질문을 STAR 형식으로 구성하세요.  
예시:  
- 의료기기 인허가 프로젝트 중 예상치 못한 문제가 발생했던 경험이 있다면, 그 당시 상황과 해결 과제, 본인의 대응 방식과 결과를 구체적으로 말씀해 주세요.

2. 직무 수행 태도 및 자세 (5개 질문)  
지원자의 책임감, 도전정신, 팀워크 등을 확인할 수 있는 질문을 STAR 형식으로 구성하세요.  
예시:  
- 의견 충돌이 있었던 팀 프로젝트 상황에서 본인의 입장과 대응 방식, 그리고 그 결과에 대해 설명해 주세요.

[출력 형식 예시]  
<업무 지식 및 직무기술>  
1. 질문 1 (STAR 구조)  
2. 질문 2 (STAR 구조)  
...  
10. 질문 10 (STAR 구조)

<직무 수행 태도 및 자세>  
1. 질문 1 (STAR 구조)  
...  
5. 질문 5 (STAR 구조)

[주의사항]  
- 업무 지식 및 직무기술 질문은 반드시 10개를 생성해야 합니다.  
- 모든 질문은 STAR 구조를 따릅니다.  
- 질문은 단순 사실 확인이 아닌, 지원자의 행동과 결과를 이끌어낼 수 있도록 구성하세요.  
- 이력서와 채용공고의 연결고리를 고려해 질문을 구성하세요."""},
                            {"role": "user", "content": f"이력서 내용:\n{text}\n\n채용공고:\n{job_description}\n\n위 내용을 바탕으로 STAR 기법에 기반한 면접 질문을 생성해주세요. 각 카테고리별로 최소 요구사항 이상의 질문을 생성해주세요."}
                        ]
                    )
                    st.session_state.interview_questions1 = response1.choices[0].message.content
                except Exception as e:
                    st.error(f"질문 생성 중 오류가 발생했습니다: {str(e)}")
        else:
            st.warning("이력서와 채용공고를 모두 입력해주세요.")

    # 면접 질문 결과 표시
    if st.session_state.interview_questions1:
        st.markdown("<div style='margin-top: 10px;'>", unsafe_allow_html=True)
        st.text_area("1차 면접 질문", st.session_state.interview_questions1, height=450)
        st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state['current_page'] == "interview2":
    st.markdown("""
        <h5 style='color: #333333; margin-bottom: 20px;'>
            ✌️ 2차 면접 질문
        </h5>
    """, unsafe_allow_html=True)
    
    # 채용공고 링크 입력
    job_link = st.text_input("채용공고 링크를 입력해주세요", placeholder="https://career.neurophet.com/...")
    
    if job_link:
        try:
            # 웹 브라우저처럼 보이기 위한 헤더 설정
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1'
            }
            
            # 웹 페이지 가져오기
            response = requests.get(job_link, headers=headers, timeout=10)
            response.raise_for_status()
            
            # 인코딩 설정
            response.encoding = 'utf-8'
            
            # HTML 파싱
            soup = BeautifulSoup(response.text, 'lxml')
            
            # 채용공고 내용 추출
            job_title = soup.find('h1')
            if not job_title:
                raise ValueError("채용공고 제목을 찾을 수 없습니다.")
            job_title = job_title.get_text(strip=True)
            
            # 담당업무, 필수자격, 우대사항 추출
            job_description = f"[{job_title}]\n"
            
            # 불필요한 내용 필터링을 위한 패턴
            skip_patterns = [
                "About us", "Recruit", "Culture", "Benefit", "FAQ",
                "개인정보처리방침", "이용약관", "뉴로핏 주식회사", "Copyright",
                "All Rights Reserved", "테헤란로", "삼원타워", "+82"
            ]
            
            # 섹션별 내용 저장을 위한 딕셔너리
            sections = {
                "담당업무": [],
                "필수자격": [],
                "우대사항": [],
                "기타정보": []
            }
            
            # 모든 텍스트 블록 찾기
            content_blocks = soup.find_all(['h2', 'h3', 'h4', 'div', 'p', 'ul', 'li'])
            
            current_section = None
            for block in content_blocks:
                text = block.get_text(strip=True)
                
                # 빈 텍스트나 불필요한 내용 건너뛰기
                if not text or any(pattern in text for pattern in skip_patterns):
                    continue
                
                # 섹션 제목 확인
                if "함께 할 업무" in text:
                    current_section = "담당업무"
                    continue
                elif "역량을 가진 분" in text or "이런 분을 찾" in text:
                    current_section = "필수자격"
                    continue
                elif "경험이 있다면 더 좋" in text or "우대" in text:
                    current_section = "우대사항"
                    continue
                elif "합류 여정" in text or "꼭 확인해주세요" in text:
                    current_section = "기타정보"
                    continue
                
                # 현재 섹션에 내용 추가
                if current_section:
                    # 불필요한 문자 제거
                    text = text.replace("•", "").strip()
                    if text and len(text) > 1:  # 빈 항목이나 단일 문자 제외
                        # 중복 체크 후 추가
                        if text not in sections[current_section]:
                            sections[current_section].append(text)
            
            # 정리된 내용을 job_description에 추가
            if sections["담당업무"]:
                job_description += "\n담당업무\n"
                for item in sections["담당업무"]:
                    job_description += f"- {item}\n"
            
            if sections["필수자격"]:
                job_description += "\n필수자격\n"
                for item in sections["필수자격"]:
                    job_description += f"- {item}\n"
            
            if sections["우대사항"]:
                job_description += "\n우대사항\n"
                for item in sections["우대사항"]:
                    job_description += f"- {item}\n"
            
            if sections["기타정보"]:
                job_description += "\n기타 정보\n"
                for item in sections["기타정보"]:
                    if "근무" in item or "급여" in item or "제출" in item:
                        job_description += f"- {item}\n"
            
            # 채용공고 내용이 비어있는 경우 처리
            if not job_description.strip():
                raise ValueError("채용공고 내용을 찾을 수 없습니다. 링크를 확인해주세요.")
            
            # 채용공고 내용 표시
            st.text_area("채용공고 내용", job_description, height=300)
            
        except ValueError as ve:
            st.error(str(ve))
            job_description = ""
        except requests.exceptions.RequestException as e:
            st.error(f"채용공고를 가져오는 중 네트워크 오류가 발생했습니다: {str(e)}")
            job_description = ""
        except Exception as e:
            st.error(f"채용공고를 가져오는 중 오류가 발생했습니다: {str(e)}")
            job_description = ""
    else:
        job_description = ""
    
    # 질문 추출 버튼을 왼쪽에 배치
    col1, col2 = st.columns([1, 4])
    with col1:
        question_button = st.button(
            "질문 추출하기",
            key="question_button2",
            help="분석 결과를 바탕으로 면접 질문을 생성합니다"
        )

    # 질문 생성 로직
    if question_button:
        if uploaded_file and job_description:
            with st.spinner("면접 질문을 생성중입니다..."):
                try:
                    # 이력서 내용 가져오기
                    text = st.session_state.resume_text
                    
                    # 2차 면접 질문 생성
                    response2 = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": """[당신의 역할]  
당신은 지원자의 이력서와 채용공고 내용을 바탕으로 면접 질문을 준비하는 본부장입니다.  
지원자의 핵심가치 부합도를 확인하기 위해 STAR 기법에 기반한 질문을 작성해야 합니다.

[목적]  
다음 정보를 바탕으로, 지원자의 핵심가치 부합도를 효과적으로 검증할 수 있는 면접 질문을 STAR 구조로 생성하세요.  
각 질문은 다음 4단계가 자연스럽게 드러나야 합니다:  
- Situation (상황)  
- Task (과제)  
- Action (행동)  
- Result (결과)  

[입력 데이터]  
① 이력서: 지원자의 경력, 프로젝트 경험, 사용 기술, 직무 배경, 업무 이력  
② 채용공고: 담당업무, 필수 자격요건, 우대사항

[질문 생성 요구사항]  
1. 각 핵심가치별로 3개씩, 총 12개의 질문을 생성해야 합니다.  
2. 모든 질문은 STAR 구조를 따릅니다.  
3. 질문은 구체적이고 실제적인 경험을 이끌어내는 형식으로 구성해야 합니다.  
4. 질문은 이력서의 내용과 채용공고 요구사항의 연관성을 고려해 작성해야 합니다.

[핵심가치별 질문 카테고리]

1. [도전]두려워 말고 시도합니다 (3개 질문)  
지원자의 도전정신과 새로운 시도에 대한 태도를 확인할 수 있는 질문을 STAR 형식으로 구성하세요.  
예시:  
- 새로운 기술이나 방법론을 도입해야 했던 상황에서, 그 당시 상황과 도입 과제, 본인의 대응 방식과 결과를 구체적으로 말씀해 주세요.

2. [책임감]대충은 없습니다 (3개 질문)  
지원자의 책임감과 완벽주의 성향을 확인할 수 있는 질문을 STAR 형식으로 구성하세요.  
예시:  
- 업무 수행 중 예상치 못한 문제가 발생했을 때, 그 당시 상황과 해결 과제, 본인의 대응 방식과 결과를 구체적으로 말씀해 주세요.

3. [협력]동료와 협업합니다 (3개 질문)  
지원자의 팀워크와 협업 능력을 확인할 수 있는 질문을 STAR 형식으로 구성하세요.  
예시:  
- 팀 프로젝트에서 의견 충돌이 있었던 상황에서, 그 당시 상황과 해결 과제, 본인의 대응 방식과 결과를 구체적으로 말씀해 주세요.

4. [전문성]능동적으로 일합니다 (3개 질문)  
지원자의 전문성과 주도적인 업무 수행 능력을 확인할 수 있는 질문을 STAR 형식으로 구성하세요.  
예시:  
- 업무 개선을 위해 스스로 주도적으로 문제를 발견하고 해결했던 경험이 있다면, 그 당시 상황과 개선 과제, 본인의 대응 방식과 결과를 구체적으로 말씀해 주세요.

[출력 형식 예시]  
[도전]두려워 말고 시도합니다
                             
1. 질문 1 (STAR 구조)  
2. 질문 2 (STAR 구조)  
3. 질문 3 (STAR 구조)

[책임감]대충은 없습니다 
                             
1. 질문 1 (STAR 구조)  
2. 질문 2 (STAR 구조)  
3. 질문 3 (STAR 구조)

[협력]동료와 협업합니다  
                             
1. 질문 1 (STAR 구조)  
2. 질문 2 (STAR 구조)  
3. 질문 3 (STAR 구조)

[전문성]능동적으로 일합니다  
                             
1. 질문 1 (STAR 구조)  
2. 질문 2 (STAR 구조)  
3. 질문 3 (STAR 구조)

[주의사항]  
- 각 핵심가치별로 반드시 3개의 질문을 생성해야 합니다.  
- 모든 질문은 STAR 구조를 따릅니다.  
- 질문은 단순 사실 확인이 아닌, 지원자의 행동과 결과를 이끌어낼 수 있도록 구성하세요.  
- 이력서와 채용공고의 연결고리를 고려해 질문을 구성하세요."""},
                            {"role": "user", "content": f"이력서 내용:\n{text}\n\n채용공고:\n{job_description}\n\n위 내용을 바탕으로 STAR 기법에 기반한 면접 질문을 생성해주세요. 각 카테고리별로 최소 요구사항 이상의 질문을 생성해주세요."}
                        ]
                    )
                    st.session_state.interview_questions2 = response2.choices[0].message.content
                except Exception as e:
                    st.error(f"질문 생성 중 오류가 발생했습니다: {str(e)}")
        else:
            st.warning("이력서와 채용공고를 모두 입력해주세요.")

    # 면접 질문 결과 표시
    if st.session_state.interview_questions2:
        st.markdown("<div style='margin-top: 10px;'>", unsafe_allow_html=True)
        st.text_area("2차 면접 질문", st.session_state.interview_questions2, height=450)
        st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state['current_page'] == "evaluation":
    st.markdown("""
        <h5 style='color: #333333; margin-bottom: 20px;'>
            📝 면접평가표
        </h5>
    """, unsafe_allow_html=True)
    
    # 본부와 직무 데이터 가져오기
    departments, jobs = get_google_sheet_data()
    

    # 평가 템플릿 가져오기
    eval_templates = get_evaluation_template()
    
    # 선택된 본부와 직무에 해당하는 템플릿 가져오기
    selected_template_key = f"{selected_dept}-{selected_job}" if selected_dept and selected_job else None
    eval_template = eval_templates.get(selected_template_key, default_template)
    
    # 본부와 직무 선택을 위한 세 개의 컬럼 생성
    col1, col2, col3 = st.columns([0.2, 0.2, 0.6])
    
    # 세션 상태에 본부/직무 정보 초기화
    if 'dept_job_info' not in st.session_state:
        st.session_state.dept_job_info = {
            'selected_dept': None,
            'selected_job': None
        }

    def update_selected_dept():
        st.session_state.dept_job_info['selected_dept'] = st.session_state.eval_dept
        if st.session_state.eval_dept == "선택해주세요":
            st.session_state.dept_job_info['selected_dept'] = None
        # 본부가 변경되면 직무 초기화
        st.session_state.dept_job_info['selected_job'] = None
    
    def update_selected_job():
        st.session_state.dept_job_info['selected_job'] = st.session_state.eval_job
        if st.session_state.eval_job == "선택해주세요":
            st.session_state.dept_job_info['selected_job'] = None
    
    # 왼쪽 컬럼: 본부 선택
    with col1:
        selected_dept = st.selectbox(
            "본부를 선택하세요",
            ["선택해주세요"] + departments,
            key="eval_dept",
            on_change=update_selected_dept,
            index=0 if st.session_state.dept_job_info['selected_dept'] is None 
                  else departments.index(st.session_state.dept_job_info['selected_dept']) + 1 
                  if st.session_state.dept_job_info['selected_dept'] in departments else 0
        )
        if selected_dept == "선택해주세요":
            selected_dept = None
    
    # 가운데 컬럼: 직무 선택
    with col2:
        if selected_dept and jobs.get(selected_dept):
            job_list = ["선택해주세요"] + jobs[selected_dept]
            selected_job = st.selectbox(
                "직무를 선택하세요",
                job_list,
                key="eval_job",
                on_change=update_selected_job,
                index=0 if st.session_state.dept_job_info['selected_job'] is None 
                      else jobs[selected_dept].index(st.session_state.dept_job_info['selected_job']) + 1 
                      if st.session_state.dept_job_info['selected_job'] in jobs[selected_dept] else 0
            )
            if selected_job == "선택해주세요":
                selected_job = None
        else:
            selected_job = None
            st.session_state.dept_job_info['selected_job'] = None
    
    # 오른쪽 컬럼: 여백
    with col3:
        st.empty()
    
    st.markdown(f"**선택된 본부&직무 :** {selected_dept if selected_dept else '본부 미선택'} / {selected_job if selected_job else '직무 미선택'}")
    # 본부/직무 선택에 따라 템플릿 자동 반영
    if selected_dept and selected_job:
        st.session_state.eval_data = get_eval_template_from_sheet(selected_dept, selected_job)
    else:
        st.session_state.eval_data = default_template
    
    # 세션 상태 초기화
    if 'candidate_info' not in st.session_state:
        st.session_state.candidate_info = {
            'candidate_name': '',
            'interviewer_name': '',
            'interview_date': datetime.now(),
            'education': '',
            'experience': ''
        }
    
    if 'eval_opinions' not in st.session_state:
        st.session_state.eval_opinions = [''] * len(st.session_state.eval_data)
    
    # 평가표 입력 폼 시작
    with st.form("evaluation_form", clear_on_submit=False):
        # 후보자 정보 입력
        st.markdown("<br><b>후보자 정보</b>", unsafe_allow_html=True)
        candidate_info_cols = st.columns(5)
        
        with candidate_info_cols[0]: 
            candidate_name = st.text_input(
                "후보자명",
                value=st.session_state.candidate_info['candidate_name'],
                key="candidate_name",
                label_visibility="visible"
            )
        with candidate_info_cols[1]: 
            interviewer_name = st.text_input(
                "면접관성명",
                value=st.session_state.candidate_info['interviewer_name'],
                key="interviewer_name",
                label_visibility="visible"
            )
        with candidate_info_cols[2]: 
            interview_date = st.date_input(
                "면접일자",
                value=st.session_state.candidate_info['interview_date'],
                key="interview_date",
                label_visibility="visible"
            )
        with candidate_info_cols[3]: 
            education = st.text_input(
                "최종학교/전공",
                value=st.session_state.candidate_info['education'],
                key="education",
                label_visibility="visible"
            )
        with candidate_info_cols[4]: 
            experience = st.text_input(
                "경력년월",
                value=st.session_state.candidate_info['experience'],
                key="experience",
                label_visibility="visible"
            )

        # 평가표 데이터 입력
        st.markdown("<br><b>평가표 입력</b>", unsafe_allow_html=True)
        
        for i, row in enumerate(st.session_state.eval_data):
            # 컬럼 비율 조정 (1:2:1:3:0.5)으로 변경
            cols = st.columns([1, 2, 1, 3, 0.5])
            cols[0].write(row["구분"])
            
            # 내용 컬럼에 스타일 적용
            content_lines = row["내용"].replace('•', '').split('\n')
            formatted_content = '<br>'.join([f"• {line.strip()}" for line in content_lines if line.strip()])
            cols[1].markdown(
                f"""<div style='font-size: 0.9em; line-height: 1.5;'>{formatted_content}</div>""",
                unsafe_allow_html=True
            )
            
            # 점수 입력 필드와 만점 표시를 하나의 컬럼에 배치
            score = cols[2].number_input(
                f"점수 ({row['만점']}점)",
                min_value=0,
                max_value=row["만점"],
                value=row["점수"],
                key=f"score_{i}",
                help=f"0~{row['만점']}점"
            )
            st.session_state.eval_data[i]["점수"] = score
            
            # 의견 입력을 text_area로 변경
            opinion = cols[3].text_area(
                "의견",
                value=st.session_state.eval_opinions[i],
                key=f"opinion_{i}",
                label_visibility="visible",
                height=70
            )
            st.session_state.eval_opinions[i] = opinion
            st.session_state.eval_data[i]["의견"] = opinion
            
            cols[4].write("")
            
            # 구분이 끝날 때마다 한 줄 띄우기
            if i < len(st.session_state.eval_data) - 1 and row["구분"] != st.session_state.eval_data[i + 1]["구분"]:
                st.markdown("<br>", unsafe_allow_html=True)

        # 종합의견, 전형결과, 입사가능시기
        st.markdown("<br><b>종합의견 및 결과</b>", unsafe_allow_html=True)
        summary = st.text_area("종합의견", key="summary", label_visibility="visible")
        result = st.selectbox("전형결과", ["합격", "불합격", "보류"], key="result", label_visibility="visible")
        join_date = st.text_input("입사가능시기", key="join_date", label_visibility="visible")

        # 총점 계산
        total_score = sum([row["점수"] for row in st.session_state.eval_data])

        # 제출 버튼
        submitted = st.form_submit_button("면접평가표 제출")
    
    # Form 제출 처리
    if submitted:
        try:
            # 후보자 정보 세션 상태 업데이트
            st.session_state.candidate_info.update({
                'candidate_name': candidate_name,
                'interviewer_name': interviewer_name,
                'interview_date': interview_date,
                'education': education,
                'experience': experience
            })
            
            import gspread
            from oauth2client.service_account import ServiceAccountCredentials
            import json
            scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
            credentials_dict = {
                "type": st.secrets["google_credentials"]["type"],
                "project_id": st.secrets["google_credentials"]["project_id"],
                "private_key_id": st.secrets["google_credentials"]["private_key_id"],
                "private_key": st.secrets["google_credentials"]["private_key"],
                "client_email": st.secrets["google_credentials"]["client_email"],
                "client_id": st.secrets["google_credentials"]["client_id"],
                "auth_uri": st.secrets["google_credentials"]["auth_uri"],
                "token_uri": st.secrets["google_credentials"]["token_uri"],
                "auth_provider_x509_cert_url": st.secrets["google_credentials"]["auth_provider_x509_cert_url"],
                "client_x509_cert_url": st.secrets["google_credentials"]["client_x509_cert_url"]
            }
            credentials = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
            gc = gspread.authorize(credentials)
            sheet_id = st.secrets["google_sheets"]["interview_evaluation_sheet_id"]
            worksheet = gc.open_by_key(sheet_id).sheet1
            # 데이터 저장
            row_data = [selected_dept, selected_job, candidate_name, interviewer_name, interview_date.strftime("%Y-%m-%d"), education, experience]
            for row in st.session_state.eval_data:
                content = ', '.join([line.strip() for line in row['내용'].replace('•', '').split('\n') if line.strip()])
                row_data.extend([content, row["점수"], row["의견"]])
            row_data.extend([summary, result, join_date, total_score])
            worksheet.append_row(row_data)
            
            # PDF 다운로드 버튼 표시
            import base64
            from io import BytesIO
            from xhtml2pdf import pisa
            import os

            # 현재 스크립트의 디렉토리 경로
            current_dir = os.path.dirname(os.path.abspath(__file__))
            
            # PDF 생성을 위한 HTML 템플릿
            html = f"""
            <meta charset="UTF-8">
            <div style="font-family: Arial, 'Malgun Gothic', sans-serif; font-size: 12px; line-height: 1.5;">
                <div style="margin-bottom: 20px;">
                    <h2 style="font-size: 18px; margin-bottom: 10px;"> 면접평가표</h2>
                    <p><b>본부:</b> {selected_dept} / <b>직무:</b> {selected_job}</p>
                </div>
                <p><b>ㆍ후보자 정보 </b></p>
                <div style="margin-bottom: 15px;">
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 10px;">
                        <tr>
                            <th style="width: 20%; border: 1px solid #000; padding: 5px; background-color: #f0f0f0;">후보자명</th>
                            <td style="width: 15%; border: 1px solid #000; padding: 5px;">{candidate_name}</td>
                            <th style="width: 20%; border: 1px solid #000; padding: 5px; background-color: #f0f0f0;">면접관성명</th>
                            <td style="width: 30%; border: 1px solid #000; padding: 5px;">{interviewer_name}</td>
                        </tr>
                        <tr>
                            <th style="border: 1px solid #000; padding: 5px; background-color: #f0f0f0;">면접일자</th>
                            <td style="border: 1px solid #000; padding: 5px;">{interview_date.strftime("%Y-%m-%d")}</td>
                            <th style="border: 1px solid #000; padding: 5px; background-color: #f0f0f0;">최종학교/전공</th>
                            <td style="border: 1px solid #000; padding: 5px;">{education}</td>
                        </tr>
                    </table>
                </div>
                <p><br><br><b>ㆍ평가내용</b></p>      
                <div style="margin-bottom: 15px;">
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 10px;">
                        <tr>
                            <th style="width: 18%; border: 1px solid #000; padding: 5px; background-color: #f0f0f0;">평가구분</th>
                            <th style="width: 39%; border: 1px solid #000; padding: 5px; background-color: #f0f0f0;">내용</th>
                            <th style="width: 13%; border: 1px solid #000; padding: 5px; background-color: #f0f0f0;">점수</th>
                            <th style="width: 30%; border: 1px solid #000; padding: 5px; background-color: #f0f0f0;">면접관 의견</th>
                        </tr>
                        {''.join([f"""
                        <tr>
                            <td style="border: 1px solid #000; padding: 5px;">{row['구분']}</td>
                            <td style="border: 1px solid #000; padding: 5px;">{', '.join([line.strip() for line in row['내용'].replace('•', '').split('\\n') if line.strip()])}</td>
                            <td style="border: 1px solid #000; padding: 5px; text-align: center;">{row['점수']} / {row['만점']}</td>
                            <td style="border: 1px solid #000; padding: 5px;">{row['의견']}</td>
                        </tr>
                        """ for row in st.session_state.eval_data])}
                        <tr>
                            <th colspan="2" style="border: 1px solid #000; padding: 5px;">총점</th>
                            <td style="border: 1px solid #000; padding: 5px;">{total_score} / 100</td>
                            <td style="border: 1px solid #000; padding: 5px;">-</td>
                        </tr>

                    </table>
                </div>
                <p><br><br><b>ㆍ종합의견 및 결과</b></p>      
    
                <div style="margin-bottom: 15px;">
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 10px;">
                        <tr>
                            <th style="width: 15%; border: 1px solid #000; padding: 5px; background-color: #f0f0f0;">종합의견</th>
                            <td colspan="3" style="border: 1px solid #000; padding: 5px;">{summary}</td>
                        </tr>
                        <tr>
                            <th style="border: 1px solid #000; padding: 5px; background-color: #f0f0f0;">전형결과</th>
                            <td style="width: 20%; border: 1px solid #000; padding: 5px;">{result}</td>
                            <th style="width: 15%; border: 1px solid #000; padding: 5px; background-color: #f0f0f0;">입사가능시기</th>
                            <td style="width: 35%; border: 1px solid #000; padding: 5px;">{join_date}</td>
                        </tr>
                    </table>
                </div>
            </div>
            """

            def create_pdf(html_content):
                try:
                    # HTML 템플릿에 한글 웹폰트 추가
                    html_with_font = f'''
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap">
                        <style>
                            @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');
                            * {{
                                font-family: 'Noto Sans KR', sans-serif !important;
                            }}
                            body {{
                                font-family: 'Noto Sans KR', sans-serif !important;
                                font-size: 12px;
                                line-height: 1.5;
                            }}
                            table {{
                                width: 100%;
                                border-collapse: collapse;
                                margin-bottom: 10px;
                            }}
                            th, td {{
                                border: 1px solid black;
                                padding: 8px;
                                text-align: left;
                                font-family: 'Noto Sans KR', sans-serif !important;
                            }}
                            th {{
                                background-color: #f2f2f2;
                            }}
                            h1, h2, h3, h4, h5, h6, p, span, div {{
                                font-family: 'Noto Sans KR', sans-serif !important;
                            }}
                            .content-item {{
                                margin-bottom: 8px;
                            }}
                        </style>
                    </head>
                    <body>
                        {html_content}
                    </body>
                    </html>
                    '''

                    # 내용의 각 항목을 줄바꿈으로 분리
                    html_with_font = html_with_font.replace('• ', '<div class="content-item">• ').replace('<br>', '</div>')
                    
                    # PDF 옵션 설정
                    pdf_options = {
                        'encoding': 'utf-8',
                        'page-size': 'A4',
                        'margin-top': '1.0cm',
                        'margin-right': '1.0cm',
                        'margin-bottom': '1.0cm',
                        'margin-left': '1.0cm',
                        'enable-local-file-access': True,
                        'load-error-handling': 'ignore'
                    }
                    
                    # PDF 생성
                    result_file = BytesIO()
                    pdf = pisa.pisaDocument(
                        BytesIO(html_with_font.encode('utf-8')), 
                        result_file,
                        encoding='utf-8',
                        options=pdf_options
                    )
                    
                    if pdf.err:
                        st.error(f"PDF 생성 중 오류가 발생했습니다: {pdf.err}")
                        return None
                        
                    return result_file.getvalue()
                except Exception as e:
                    st.error(f"PDF 생성 중 오류가 발생했습니다: {str(e)}")
                    return None

            # PDF 생성 및 다운로드 버튼 표시
            pdf = create_pdf(html)
            if pdf:
                b64 = base64.b64encode(pdf).decode()
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.success("제출이 완료되었습니다.")
                with col2:
                    st.markdown(
                        f'<a href="data:application/pdf;base64,{b64}" download="면접평가표.pdf" '
                        f'style="display: inline-block; padding: 8px 16px; '
                        f'background-color: #f0f2f6; color: #262730; '
                        f'text-decoration: none; border-radius: 4px; '
                        f'border: 1px solid #d1d5db;">'
                        f'📥 PDF 다운로드</a>',
                        unsafe_allow_html=True
                    )
            else:
                st.error("PDF 생성 중 오류가 발생했습니다. 인사팀에 문의해주세요.")
            
        except Exception as e:
            st.error(f"저장 중 오류: 인사팀에 문의해주세요! {str(e)}")

elif st.session_state['current_page'] == "admin":
    if 'admin_authenticated' not in st.session_state:
        st.session_state.admin_authenticated = False
    
    if not st.session_state.admin_authenticated:
        password = st.text_input("비밀번호를 입력하세요", type="password")
        if st.button("확인"):
            if password == "0314!":
                st.session_state.admin_authenticated = True
                st.rerun()
            else:
                st.error("비밀번호가 올바르지 않습니다.")
    else:
        st.markdown("""
            <h5 style='color: #333333; margin-bottom: 20px;'>
                ⚙️ 채용 관리자
            </h5>
        """, unsafe_allow_html=True)
        
        try:
            # 세션 상태에 admin_data가 없거나 마지막 업데이트 시간이 5분 이상 지났을 때만 데이터를 새로 가져옴
            current_time = time.time()
            if ('admin_data' not in st.session_state or 
                'last_update_time' not in st.session_state or 
                current_time - st.session_state.last_update_time > 300):  # 5분 = 300초
                
                with st.spinner("데이터를 불러오는 중..."):
                    gc = init_google_sheets()
                    sheet = gc.open_by_key(st.secrets["google_sheets"]["interview_evaluation_sheet_id"]).sheet1
                    time.sleep(1)  # API 호출 간격 조절
                    data = sheet.get_all_records()
                    
                    # 데이터와 마지막 업데이트 시간을 세션 상태에 저장
                    st.session_state.admin_data = data
                    st.session_state.last_update_time = current_time
            
            # 캐시된 데이터 사용
            data = st.session_state.admin_data
            df = pd.DataFrame(data)


            if df is not None:
                # 검색 필터
                col1, col2, col3 = st.columns(3)
                with col1:
                    dept_filter = st.selectbox("본부", ["전체"] + sorted(df["본부"].unique().tolist()))
                
                with col2:
                    # 선택된 본부에 해당하는 직무만 표시
                    if dept_filter != "전체":
                        job_options = ["전체"] + sorted(df[df["본부"] == dept_filter]["직무"].unique().tolist())
                    else:
                        job_options = ["전체"] + sorted(df["직무"].unique().tolist())
                    job_filter = st.selectbox("직무", job_options)
                
                with col3:
                    name_filter = st.text_input("후보자명")
                st.markdown("💾 후보자 리스트")
                # 필터 적용
                filtered_df = df.copy()
                                
                # 본부 필터링
                if dept_filter != "전체":
                    filtered_df = filtered_df[filtered_df["본부"].str.strip() == dept_filter.strip()]
                
                # 직무 필터링
                if job_filter != "전체":
                    filtered_df = filtered_df[filtered_df["직무"].str.strip() == job_filter.strip()]
                
                # 후보자명 필터링
                if name_filter:
                    filtered_df = filtered_df[filtered_df["후보자명"].str.contains(name_filter, na=False)]
                    st.write(f"후보자명 필터링 후 데이터 수: {len(filtered_df)}")

                # 필요한 컬럼만 선택
                display_columns = [
                    "본부", "직무", "후보자명", "면접관성명", "면접일자", 
                    "최종학교/전공", "경력년월", "총점", "면접결과", "종합의견",
                    "업무지식", "업무지식점수", "업무지식의견",
                    "직무기술", "직무기술점수", "직무기술의견",
                    "직무수행태도 및 자세", "직무수행태도 및 자세점수", "직무수행태도 및 자세의견",
                    "기본인성", "기본인성점수", "기본인성의견"
                ]
                
                try:
                    display_df = filtered_df[display_columns]
                except KeyError:
                    st.error("필요한 평가 데이터 컬럼이 없습니다. 데이터를 확인해주세요.")
                    display_df = filtered_df[["본부", "직무", "후보자명", "면접관성명", "면접일자", 
                                    "최종학교/전공", "경력년월", "총점", "면접결과", "종합의견"]]

                # 데이터프레임 표시용 컬럼 (기본 정보만 표시)
                display_view_columns = [
                    "본부", "직무", "후보자명", "면접관성명", "면접일자", 
                    "최종학교/전공", "경력년월", "총점", "면접결과", "종합의견"
                ]
                
                # 데이터프레임 표시
                st.dataframe(
                    display_df[display_view_columns],
                    use_container_width=True,
                    hide_index=False
                )
                st.markdown("---")
                st.markdown("📝 후보자 면접평가표 다운로드")
                # 선택 박스로 후보자 선택
                selected_candidate = st.selectbox(
                    "평가표를 다운로드할 후보자를 선택하세요",
                    options=filtered_df['후보자명'].tolist(),
                    index=None
                )

                if selected_candidate:
                    selected_row = filtered_df[filtered_df['후보자명'] == selected_candidate].iloc[0]
                    
                    # 평가 데이터 가져오기
                    eval_data = [
                        {
                            '구분': '업무 지식',
                            '내용': selected_row.get('업무지식', ''),
                            '점수': selected_row.get('업무지식점수', 0),
                            '만점': 30,
                            '의견': selected_row.get('업무지식의견', '')
                        },
                        {
                            '구분': '직무기술',
                            '내용': selected_row.get('직무기술', ''),
                            '점수': selected_row.get('직무기술점수', 0),
                            '만점': 30,
                            '의견': selected_row.get('직무기술의견', '')
                        },
                        {
                            '구분': '직무 수행 태도 및 자세',
                            '내용': selected_row.get('직무수행태도 및 자세', ''),
                            '점수': selected_row.get('직무수행태도 및 자세점수', 0),
                            '만점': 30,
                            '의견': selected_row.get('직무수행태도 및 자세의견', '')
                        },
                        {
                            '구분': '기본인성',
                            '내용': selected_row.get('기본인성', ''),
                            '점수': selected_row.get('기본인성점수', 0),
                            '만점': 10,
                            '의견': selected_row.get('기본인성의견', '')
                        }
                    ]
                    
                    # PDF 생성을 위한 HTML 템플릿
                    html_content = f"""
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap">
                        <style>
                            @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');
                            * {{
                                font-family: 'Noto Sans KR', sans-serif !important;
                            }}
                            body {{
                                font-family: 'Noto Sans KR', sans-serif !important;
                                font-size: 11px;
                                line-height: 1.5;
                            }}
                            table {{
                                width: 100%;
                                border-collapse: collapse;
                                margin-bottom: 5px;
                            }}
                            th, td {{
                                border: 1px solid black;
                                padding: 5px;
                                text-align: left;
                                font-family: 'Noto Sans KR', sans-serif !important;
                            }}
                            th {{
                                background-color: #f2f2f2;
                            }}
                            h1, h2, h3, h4, h5, h6, p, span, div {{
                                font-family: 'Noto Sans KR', sans-serif !important;
                            }}
                            .content-item {{
                                margin-bottom: 5px;
                            }}
                            .section-title {{
                                margin-left: 0px;
                            }}
                        </style>
                    </head>
                    <body>
                        <div style="padding: 5px;">
                            <h2 style="font-size: 18px; margin-bottom: 5px;"> 면접평가표</h2>
                            <p><b>본부:</b> {selected_row['본부']} / <b>직무:</b> {selected_row['직무']}</p>
                            <div class="section-title"><p><br><b>ㆍ후보자 정보</b></p></div>
                            <table>
                                <tr>
                                    <th style="width: 20%;">후보자명</th>
                                    <td style="width: 30%;">{selected_row['후보자명']}</td>
                                    <th style="width: 20%;">면접관성명</th>
                                    <td style="width: 30%;">{selected_row['면접관성명']}</td>
                                </tr>
                                <tr>
                                    <th>면접일자</th>
                                    <td>{selected_row['면접일자']}</td>
                                    <th>최종학교/전공</th>
                                    <td>{selected_row['최종학교/전공']}</td>
                                </tr>
                            </table>

                            <div class="section-title"><p><br><b>ㆍ종합의견 및 결과</b></p></div>
                            <table>
                                <tr>
                                    <th style="width: 15%;">종합의견</th>
                                    <td colspan="3">{selected_row['종합의견']}</td>
                                </tr>
                                <tr>
                                    <th>면접결과</th>
                                    <td style="width: 20%;">{selected_row['면접결과']}</td>
                                    <th style="width: 15%;">총점</th>
                                    <td style="width: 35%;">{selected_row['총점']}</td>
                                </tr>
                            </table>

                            <div class="section-title"><p><br><b>ㆍ평가내용</b></p></div>
                            <table>
                                <tr>
                                    <th style="width: 18%;">평가구분</th>
                                    <th style="width: 39%;">내용</th>
                                    <th style="width: 13%;">점수</th>
                                    <th style="width: 30%;">면접관 의견</th>
                                </tr>
                                {''.join([f"""
                                <tr>
                                    <td>{row['구분']}</td>
                                    <td>{row['내용']}</td>
                                    <td style="text-align: center;">{row['점수']} / {row['만점']}</td>
                                    <td>{row['의견']}</td>
                                </tr>
                                """ for row in eval_data])}
                                <tr>
                                    <th colspan="2">총점</th>
                                    <td style="text-align: center;">{selected_row['총점']} / 100</td>
                                    <td>-</td>
                                </tr>
                            </table>
                        </div>
                    </body>
                    </html>
                    """

                    # 버튼을 3개의 컬럼으로 나누어 배치
                    col1, col2 = st.columns([30, 70])
                    
                    with col1:
                        if st.button(f"📥 {selected_candidate}님의 면접평가표 다운로드", use_container_width=True):
                            try:
                                # PDF 옵션 설정
                                pdf_options = {
                                    'encoding': 'utf-8',
                                    'page-size': 'A4',
                                    'margin-top': '1.0cm',
                                    'margin-right': '1.0cm',
                                    'margin-bottom': '1.0cm',
                                    'margin-left': '1.0cm',
                                    'enable-local-file-access': True,
                                    'load-error-handling': 'ignore'
                                }
                                
                                # PDF 생성
                                pdf_buffer = BytesIO()
                                pisa.showLogging()
                                pdf = pisa.pisaDocument(
                                    BytesIO(html_content.encode('utf-8')),
                                    pdf_buffer,
                                    encoding='utf-8',
                                    options=pdf_options
                                )
                                
                                if not pdf.err:
                                    st.download_button(
                                        label="PDF 다운로드",
                                        data=pdf_buffer.getvalue(),
                                        file_name=f"{selected_candidate}_면접평가표.pdf",
                                        mime="application/pdf"
                                    )
                                else:
                                    st.error(f"PDF 생성 중 오류가 발생했습니다: {pdf.err}")
                            except Exception as e:
                                st.error(f"PDF 생성 중 오류가 발생했습니다: {str(e)}")
                    
                    with col2:
                        st.write("")  # 여백용 빈 컬럼
            else:
                st.info("저장된 면접평가 데이터가 없습니다.")
        except Exception as e:
            st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {str(e)}")

