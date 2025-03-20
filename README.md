# 이력서 서머리 시스템

이 시스템은 지원자의 이력서를 분석하여 채용 공고의 JD와 회사 핵심가치에 대한 적합성을 평가하는 도구입니다.

## 주요 기능

1. 이력서 파일 읽기 (PDF, Word, 텍스트 파일 지원)
2. JD(Job Description)와의 적합성 분석
3. 회사 핵심가치와의 부합성 분석
4. 종합적인 분석 요약 생성

## 설치 방법

1. 필요한 패키지 설치:
```bash
pip install -r requirements.txt
```

2. 환경 변수 설정:
- `.env` 파일을 생성하고 OpenAI API 키를 설정합니다:
```
OPENAI_API_KEY=your_api_key_here
```

## 사용 방법

1. `resume_summarizer.py` 파일을 실행합니다:
```bash
python resume_summarizer.py
```

2. 코드에서 다음 변수들을 설정합니다:
- `resume_path`: 분석할 이력서 파일의 경로
- `jd_text`: 채용 공고의 JD 텍스트
- `core_values`: 회사의 핵심가치 텍스트

## 출력 예시

```
=== 이력서 분석 요약 ===

1. JD 적합성 분석:
[분석 결과]

2. 핵심가치 부합성 분석:
[분석 결과]
```

## 주의사항

- OpenAI API 사용에 따른 비용이 발생할 수 있습니다.
- 이력서 파일은 텍스트 형식이어야 합니다 (PDF, Word 파일 지원 예정).
- API 키는 반드시 안전하게 관리해야 합니다. # resume-analyzer
