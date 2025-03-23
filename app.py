import streamlit as st
import PyPDF2
import io
from openai import OpenAI
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 페이지 설정
st.set_page_config(
    page_title="뉴로핏 이력서 분석기",
    page_icon="📄",
    layout="wide"
)

# 로고 추가
st.image("https://neurophethr.notion.site/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2Fe3948c44-a232-43dd-9c54-c4142a1b670b%2Fneruophet_logo.png?table=block&id=893029a6-2091-4dd3-872b-4b7cd8f94384&spaceId=9453ab34-9a3e-45a8-a6b2-ec7f1cefbd7f&width=410&userId=&cache=v2", 
         width=150)

st.title("이력서 분석 & 면접 질문 생성")

def analyze_pdf(pdf_content):
    try:
        # PDF 파일 읽기
        pdf_file = io.BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        # PDF 텍스트 추출
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()

        # OpenAI API 호출
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        prompt = f"""다음 이력서를 분석하여 아래 항목별로 평가해주세요:

1. 핵심 경력 요약 
   - 총 경력 기간
   - 주요 직무 경험:
      1) [회사명]: [직위] (기간)
      2) [회사명]: [직위] (기간)
      3) [회사명]: [직위] (기간)
   - 주요 업무 내용

2. 채용요건 연관성 분석
   - 부합되는 요건
   - 미확인/부족 요건

분석 요약: 전반적인 평가를 간단히 작성

이력서 내용: {text}"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "당신은 전문 채용 담당자입니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"에러 발생: {str(e)}"

def generate_questions(resume_text, job_description):
    try:
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        prompt = f"""다음 내용을 바탕으로 면접 질문을 생성해주세요:

이력서: {resume_text}

채용요건: {job_description}

[직무 기반 질문]
1. 가장 중요한 프로젝트 경험 질문
2. 어려운 문제를 해결한 구체적 사례 질문
3. 채용공고의 필수 자격요건 관련 질문
4. 채용공고의 우대사항 관련 질문
5. 직무 관련 전문 지식을 검증하는 질문
6. 실제 업무 상황에서의 대처 방안을 묻는 질문

[조직 적합성 질문 - 뉴로핏 핵심가치 기반]
7. [도전] "두려워 말고 시도합니다"와 관련된 경험 질문
8. [책임감] "대충은 없습니다"와 관련된 사례 질문
9. [협력] "동료와 협업합니다"와 관련된 경험 질문
10. [전문성] "능동적으로 일합니다"와 관련된 사례 질문"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "면접 질문을 생성하는 면접관입니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"에러 발생: {str(e)}"

# 파일 업로더
uploaded_file = st.file_uploader("이력서 PDF 파일을 업로드해주세요", type="pdf")

# 채용공고 입력
job_description = st.text_area("채용공고 내용을 입력해주세요")

if uploaded_file is not None:
    # 분석 시작 버튼
    if st.button("분석 시작"):
        with st.spinner("이력서를 분석하고 있습니다..."):
            # PDF 파일 읽기
            pdf_content = uploaded_file.read()
            
            # 이력서 분석
            analysis_result = analyze_pdf(pdf_content)
            
            # 결과 표시
            st.subheader("이력서 분석 결과")
            st.write(analysis_result)
            
            # 면접 질문 생성
            if job_description:
                st.subheader("면접 질문 TIP")
                with st.spinner("면접 질문을 생성하고 있습니다..."):
                    questions = generate_questions(analysis_result, job_description)
                    st.write(questions)

# 설명 추가
with st.expander("도움말"):
    st.write("""
    1. PDF 형식의 이력서 파일을 업로드해주세요.
    2. 채용공고 내용을 입력해주세요.
    3. '분석 시작' 버튼을 클릭하면 이력서 분석과 면접 질문이 생성됩니다.
    """) 