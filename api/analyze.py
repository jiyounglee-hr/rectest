from http.server import BaseHTTPRequestHandler
import json
from openai import OpenAI
import os
import PyPDF2
import io
import traceback

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
        client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        
        prompt = """다음 이력서를 분석하여 아래 항목별로 평가해주세요:

분석 항목:
1. 핵심 경력 요약 
   - 총 경력 기간
   - 주요 직무 경험

2. 채용요건 연관성 분석 (채용요건별로 이력서의 내용을 확인) 
   - 부합되는 요건 (필수사항, 우대사항 중 보유한 역량 리스트)
   - 미확인/부족 요건: (확인이 필요한 역량 리스트) 

참고사항:
- 객관적 사실 중심으로 분석할 것
- 확인된 내용만 기술할 것
- 추측성 내용은 제외할 것
- 분석 결과에서 ** 기호를 사용하지 말 것
- 각 섹션의 제목은 볼드 처리 없이 일반 텍스트로 표시할 것
- 주요 직무 경험은 들여쓰기 후 1), 2), 3) 형식으로 표시할 것

이력서 내용:
{text}
"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "당신은 전문 채용 담당자입니다. 이력서를 객관적으로 분석하고, 주요 직무 경험은 들여쓰기와 번호를 사용하여 구조화된 형식으로 작성해주세요."},
                {"role": "user", "content": prompt.format(text=text)}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        result = response.choices[0].message.content.replace('**', '')
        return result
    except Exception as e:
        print(f"상세 에러 정보: {traceback.format_exc()}")
        raise Exception(f"PDF 분석 중 오류 발생: {str(e)}")

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            print("요청 시작")  # 디버깅용
            content_length = int(self.headers['Content-Length'])
            print(f"Content-Length: {content_length}")  # 디버깅용
            
            # 요청 본문 읽기
            post_data = self.rfile.read(content_length)
            print(f"데이터 읽기 완료: {len(post_data)} bytes")  # 디버깅용
            
            # PDF 파일 분석
            result = analyze_pdf(post_data)
            print("분석 완료")  # 디버깅용
            
            # 응답 헤더 설정
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            # 응답 데이터 전송
            response_data = {"result": result}
            response_json = json.dumps(response_data, ensure_ascii=False)
            self.wfile.write(response_json.encode('utf-8'))
            print("응답 전송 완료")  # 디버깅용
            
        except Exception as e:
            print(f"핸들러 에러: {traceback.format_exc()}")  # 디버깅용
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            error_response = {"error": str(e)}
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers() 