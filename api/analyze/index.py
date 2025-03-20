from http.server import BaseHTTPRequestHandler
import json
import os
from openai import OpenAI
from PyPDF2 import PdfReader
from io import BytesIO

def analyze_pdf(pdf_data):
    try:
        # PDF 읽기
        pdf = PdfReader(BytesIO(pdf_data))
        text = ""
        for page in pdf.pages:
            text += page.extract_text()

        # OpenAI 클라이언트 초기화
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        prompt = f"""
        다음 이력서를 분석하여 구조화된 형식으로 결과를 제공해주세요.

        이력서 내용: {text}

        다음 형식으로 분석해주세요:

        [핵심 경력 요약]
        ▶ 총 경력 기간: 
        
        ▶ 주요 직무 경험 (최대 5가지):
        1. 
        2. 
        3. 
        4. 
        5. 

        [채용요건 연관성 분석]
        ▶ 부합되는 요건 (필수사항, 우대사항 중 보유한 역량 리스트):
        - 
        - 
        -
        -
        -
        - 

        ▶ 미확인/부족 요건 (확인이 필요한 역량 리스트):
        - 
        - 
        -
        -
        - 

        참고사항:
        - 객관적 사실에 기반하여 분석할 것
        - 경력은 구체적인 기간으로 표시
        - 주요 직무 경험은 가장 연관성 높은 순서로 나열
        - 채용요건 분석은 이력서 내용을 근거로 제시
        """

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "당신은 전문 채용 담당자입니다. 이력서를 분석하여 채용요건과의 적합성을 판단합니다."},
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content

    except Exception as e:
        print(f"PDF 분석 중 에러: {str(e)}")
        raise e

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        try:
            # CORS 헤더
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            # 요청 본문 읽기
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            # PDF 분석
            result = analyze_pdf(post_data)
            
            # JSON 응답 전송
            response = json.dumps({'result': result})
            self.wfile.write(response.encode('utf-8'))

        except Exception as e:
            print(f"서버 에러: {str(e)}")
            error_response = json.dumps({'error': str(e)})
            self.wfile.write(error_response.encode('utf-8')) 