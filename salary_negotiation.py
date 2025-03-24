import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv
import pandas as pd
import math

# 환경 변수 로드
load_dotenv()

# OpenAI API 키 확인
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    st.error("OpenAI API 키가 설정되지 않았습니다. Streamlit Cloud의 Secrets에서 OPENAI_API_KEY를 설정해주세요.")
    st.stop()

# OpenAI 클라이언트 초기화
try:
    client = OpenAI(api_key=api_key)
    # API 키 유효성 검사
    client.models.list()
except Exception as e:
    st.error(f"OpenAI API 키가 유효하지 않습니다. 오류: {str(e)}")
    st.stop()

def show_salary_negotiation():
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
        
        # 1. 처우협상 섹션
        st.markdown("""
            <h4 style='color: #333333; margin-bottom: 20px;'>
               💰 처우협상 분석 및 제안
            </h4>
        """, unsafe_allow_html=True)

        # 이력서 분석으로 돌아가는 버튼
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("📄 이력서 분석 및 면접질문 TIP", key="resume_button"):
            st.session_state['current_page'] = 'resume'
            st.rerun()

    st.markdown("##### 🔎 처우 기본정보")
    
    try:
        # 엑셀 파일 업로드
        uploaded_file = st.file_uploader("임금 테이블 엑셀 파일을 업로드하세요", type=['xlsx'])
        
        if uploaded_file:
            # 엑셀 파일 읽기
            df = pd.read_excel(uploaded_file)
            
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
                    other_salary = st.number_input("기타 보상상 (만원)", min_value=0, step=100)
                with col5:
                    desired_salary = st.number_input("희망연봉 (만원)", min_value=0, step=100)
                
                # 4줄: 인정경력 연차, 학력특이사항
                col6, col7 = st.columns(2)
                with col6:
                    years = st.number_input("인정경력 (년)", min_value=0.0, step=0.1, format="%.1f")  # 소수점 한자리까지 입력 가능
                with col7:
                    education_notes = st.text_input("학력특이사항", "")
                
                # 전체 경력을 년 단위로 변환 (분석용) - 반올림 적용
                years_exp = round(years)  # 반올림 적용
                
                # 5줄: 특이사항
                special_notes = st.text_area("특이사항 (성과, 스킬, 기타)", height=100)
                
                # 분석하기 버튼
                submitted = st.form_submit_button("분석하기")

                if submitted:
                    # 선택된 직군상세에 해당하는 직군 가져오기
                    selected_job_category = job_mapping[job_role]
                    
                    # 해당 직군과 연차에 맞는 데이터 필터링 (반올림된 연차 사용)
                    filtered_df = df[
                        (df['직군'] == selected_job_category) & 
                        (df['연차'] == years_exp)  # 반올림된 연차로 필터링
                    ]
                    
                    if filtered_df.empty:
                        st.warning(f"선택하신 직군 '{job_role}' ({selected_job_category})과 연차 {years_exp}년에 해당하는 데이터가 없습니다.")
                        return
                    
                    # 첫 번째 행 선택
                    filtered_data = filtered_df.iloc[0]
                    
                    # 분석 결과 표시
                    st.markdown("<br><br>", unsafe_allow_html=True)
                    st.markdown("#### 📊 연봉 분석 결과")
                    
                    # 직군 정보 표시
                    st.markdown(f"**선택된 직군 정보:** {selected_job_category} - {job_role}")
                    
                    # 연봉 정보 표시
                    min_salary = filtered_data['최소연봉']
                    max_salary = filtered_data['최대연봉']
                    avg_salary = (min_salary + max_salary) / 2
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("현재 연봉", f"{current_salary:,.0f}만원")
                    with col2:
                        st.metric("최소 연봉", f"{min_salary:,.0f}만원")
                    with col3:
                        st.metric("평균 연봉", f"{avg_salary:,.0f}만원")
                    with col4:
                        st.metric("최대 연봉", f"{max_salary:,.0f}만원")
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    # 2. 상세 분석 결과
                    st.markdown("##### 💡 연봉 책정 가이드")
                    
                    analysis_text = ""
                    
                    # 임금 테이블 기준 분석
                    if current_salary < min_salary:
                        analysis_text += f"⚠️ 현재 연봉(기본연봉)이 시장 최소값보다 {min_salary - current_salary:,.0f}만원 낮습니다.\n"
                        recommended_salary = min_salary
                    elif current_salary > max_salary:
                        analysis_text += f"⚠️ 현재 연봉(기본연봉)이 시장 최대값보다 {current_salary - max_salary:,.0f}만원 높습니다.\n"
                        recommended_salary = max_salary
                    else:
                        analysis_text += "✅ 현재 연봉(기본연봉)이 시장 범위 내에 있습니다.\n"
                        recommended_salary = current_salary
                    
                    # 연봉 보존율 계산
                    preservation_rate = (recommended_salary / current_salary) * 100
                    
                    # 중간 금액 계산 (기준연봉과 희망연봉의 중간값)
                    middle_salary = (avg_salary + desired_salary) / 2

                    # 총보상 계산
                    total_compensation = current_salary + other_salary
                    
                    # 제시금액 계산 로직
                    def calculate_suggested_salary(total_comp, min_salary, avg_salary, max_salary):
                        increase_10 = total_comp * 1.1
                        increase_5 = total_comp * 1.05
                        increase_2 = total_comp * 1.02
                        
                        # 1. 최종보상 * 1.1이 최소연봉보다 낮은 경우
                        if increase_10 <= avg_salary:  # 조건 수정: 최소연봉 대신 평균연봉과 비교
                            return int(increase_10)
                        # 2. 최종보상 * 1.05가 평균연봉보다 낮은 경우
                        elif increase_5 < avg_salary:
                            return int(avg_salary)
                        # 3. 최종보상 * 1.05가 평균연봉보다 높은 경우
                        elif increase_5 >= avg_salary and total_comp <= avg_salary:
                            return int(increase_5)
                        # 4. 최종보상이 평균연봉보다 높고 최대연봉보다 낮은 경우
                        elif total_comp > avg_salary and total_comp <= max_salary:
                            return int(increase_2)
                        # 5. 최종보상이 최대연봉보다 높은 경우
                        else:
                            return "[별도 계산 필요]"
                        
                    # 제시금액 계산
                    suggested_salary = calculate_suggested_salary(
                        total_compensation, 
                        min_salary, 
                        avg_salary, 
                        max_salary
                    )

                    # 기존 분석 결과 표시 후...
                    
                    st.markdown("### 협상(안)")
                    
                    # 협상(안) 보고서
                    st.info(f"""
                    {position} 합격자 {candidate_name}님 처우 협상(안) 보고 드립니다.

                    {candidate_name}님의 경력은 {years:.1f}년으로 {selected_job_category} 임금테이블 기준으로는 
                    기준연봉 {avg_salary:,.0f}만원 ~ 상위10% {max_salary:,.0f}만원까지 고려할 수 있습니다.
                    
                    최종보상 {total_compensation:,.0f}만원, 기준(평균)연봉 {avg_salary:,.0f}만원을 고려했을 때 
                    제시금액은 {suggested_salary if isinstance(suggested_salary, str) else f'{suggested_salary:,.0f}만원'}이 어떨지 의견 드립니다.

                    [연봉산정]
                    - 인정경력: {years:.1f}년 (인정경력 기준: {years_exp}년)
                    - 최종연봉: 기본연봉 {current_salary:,.0f}만원 + 기타 {other_salary:,.0f}만원
                    - 희망연봉: {desired_salary:,.0f}만원
                    - 기준(임금테이블) 연봉: {avg_salary:,.0f}만원 (최소 연봉: {min_salary:,.0f}만원, 최대 연봉: {max_salary:,.0f}만원)
                    """)
                    
                    # 상세 분석 결과 expander 부분
                    with st.expander("상세 분석 결과 보기"):
                        st.info(f"""
                        💰 추천 연봉 범위: {recommended_salary:,.0f}만원 
                        (현재 연봉 대비 {preservation_rate:.1f}% 수준)
                        
                        📌 판단 근거:
                        {analysis_text}
                        
                        🔍 고려사항:
                        1. 임금 테이블 기준: {min_salary:,.0f}만원 ~ {max_salary:,.0f}만원
                        2. 연봉 보존율: {preservation_rate:.1f}%
                        3. 특이사항: {special_notes if special_notes else "없음"}
                        4. 제시금액 계산 순서                 
                            - 최종보상 * 1.1 < 평균연봉이면 최종보상 * 1.1 정도 제안 (10% 증액) 
                            - 최종보상 * 1.05 < 평균연봉이면 평균연봉 정도 제안 (5% 증액) 
                            - 최종보상 * 1.05 >= 평균연봉이면 최종보상 * 1.05까지 제안 (5% 증액) 
                            - 최종보상 > 평균연봉 (단, 최종보상 <= 최대연봉)이면 최종보상 * 1.02까지 제안 (2% 증액) 
                            - 최종보상 > 최대연봉이면 별도 계산 필요  
                        """)
                    
    except Exception as e:
        st.error("엑셀 파일을 불러오는 중 오류가 발생했습니다.")
        st.exception(e)

    st.markdown("<hr>", unsafe_allow_html=True)
