# 뉴로핏 채용 - 이력서 분석 시스템

이 프로젝트는 이력서를 분석하고 면접 질문을 생성하는 Streamlit 기반 웹 애플리케이션입니다.

## 기능

- 이력서 PDF 파일 업로드 및 분석
- 채용공고 기반 이력서 분석
- 맞춤형 면접 질문 생성
- 연봉 협상 가이드 제공

## 설치 방법

1. 저장소 클론
```bash
git clone https://github.com/jiyounglee-hr/hr-resume.git
cd hr-resume
```

2. 필요한 패키지 설치
```bash
pip install -r requirements.txt
```

3. 환경 변수 설정
`.env` 파일을 생성하고 다음 내용을 추가합니다:
```
OPENAI_API_KEY=your_api_key_here
```

## 실행 방법

```bash
streamlit run app.py
```

## 기술 스택

- Python 3.8+
- Streamlit
- OpenAI API
- PyPDF2

## 주의사항

- OpenAI API 키가 필요합니다.
- PDF 형식의 이력서 파일만 지원합니다.
- 채용공고 내용을 입력해야 분석이 가능합니다. 