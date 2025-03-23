from http.server import BaseHTTPRequestHandler
import json
from openai import OpenAI
import os
import PyPDF2
import io

def analyze_pdf(pdf_content):
    try:
        # PDF 파일 읽기
        pdf_file = io.BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        # PDF 텍스트 추출 및 길이 제한
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        
        # 텍스트 길이 제한 (처음 3000자만 사용)
        text = text[:5000]

        # 더 간단한 프롬프트 사용
        prompt = f"""다음 이력서를 간단히 분석해주세요:

1. 핵심 경력 요약 
   - 총 경력 기간
   - 주요 직무 경험:
      1) [회사명]: [직위]
      2) [회사명]: [직위]
      3) [회사명]: [직위]
   - 주요 업무 내용

2. 채용요건 연관성 분석
   - 부합되는 요건
   - 미확인/부족 요건

- 분석 결과에서 ** 기호를 사용하지 말 것

이력서 내용: {text}"""

        # OpenAI API 호출 - GPT-3.5-turbo 사용 (더 빠름)
        client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # 더 빠른 처리를 위해 GPT-3.5 사용
            messages=[
                {"role": "system", "content": "간단하고 핵심적인 내용만 분석해주세요."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000  # 토큰 수 제한
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"에러 발생: {str(e)}")
        raise Exception(str(e))

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            result = analyze_pdf(post_data)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response_data = {"result": result}
            self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
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