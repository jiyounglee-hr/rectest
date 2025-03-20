from http.server import BaseHTTPRequestHandler
import json
from openai import OpenAI
import os

def generate_questions(resume_text, job_description):
    try:
        client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        
        # 프롬프트 최적화 및 토큰 수 제한
        resume_summary = resume_text[:1000]  # 이력서 내용 제한
        job_summary = job_description[:500]  # 채용요건 내용 제한
        
        prompt = f"""다음 내용을 바탕으로 간단한 면접 질문을 생성해주세요:

이력서: {resume_summary}

채용요건: {job_summary}

다음 형식으로 11개의 질문을 생성해주세요:

[경력 기반 질문]
1. 
2. 

[직무 적합성 질문]
3. 
4. 

[기술/전문성 질문]
5. 
6. 

[조직 적합성 질문]
7. 
8. 
9. 
10. 

[성장 가능성 질문]
11. 
"""
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "면접관으로서 간단하고 명확한 질문을 생성하세요."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000,  # 토큰 수 제한
            timeout=15  # 타임아웃 설정
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI API 에러: {str(e)}")
        raise Exception(str(e))

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))

            result = generate_questions(
                request_data.get('resume_text', ''),
                request_data.get('job_description', '')
            )
            
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