from http.server import BaseHTTPRequestHandler
import json
import os
from openai import OpenAI

def generate_questions(resume_text, job_description):
    try:
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        prompt = f"""
        이력서 내용: {resume_text}
        
        직무 설명: {job_description}
        
        위 이력서와 직무 설명을 바탕으로 면접 질문 5개를 생성해주세요.
        각 질문은 지원자의 경력과 기술이 해당 직무와 어떻게 연관되는지 파악할 수 있도록 구성해주세요.
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "당신은 전문 면접관입니다."},
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content

    except Exception as e:
        print(f"질문 생성 중 에러: {str(e)}")
        raise e

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            # CORS 헤더
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            # 면접 질문 생성
            resume_text = request_data.get('resume_text', '')
            job_description = request_data.get('job_description', '')
            
            questions = generate_questions(resume_text, job_description)
            
            # 응답 전송
            self.wfile.write(json.dumps({
                'result': questions
            }).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'error': str(e)
            }).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers() 