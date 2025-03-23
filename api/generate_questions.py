from http.server import BaseHTTPRequestHandler
import json
from openai import OpenAI
import os

def generate_questions(resume_text, job_description):
    try:
        # 입력 텍스트 길이 제한
        resume_text = resume_text[:2000]  # 이력서 텍스트 제한
        job_description = job_description[:1000]  # 채용공고 텍스트 제한
        
        client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        
        prompt = f"""다음 내용을 바탕으로 10개의 구체적인 면접 질문을 생성해주세요:

[직무 기반 질문]
1-6: 직무 경험, 프로젝트, 문제해결, 자격요건 관련 질문

[조직 적합성 질문]
7-10: 뉴로핏 핵심가치(도전,책임감,협력,전문성) 관련 질문

이력서: {resume_text}
채용요건: {job_description}

각 질문은 구체적이고 상황 중심적으로 작성해주세요."""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # 더 빠른 처리를 위해 GPT-3.5 사용
            messages=[
                {"role": "system", "content": "간단명료하게 질문을 생성해주세요."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000  # 토큰 수 제한
        )
        
        # 응답 받은 후 포맷팅
        result = response.choices[0].message.content
        
        # 기본 카테고리 구조 추가
        if "[직무 기반 질문]" not in result:
            formatted_result = "[직무 기반 질문]\n" + result
        
        return formatted_result
        
        # 기본 카테고리 구조 추가
        if "[조직 적합성 질문]" not in result:
            formatted_result = "[조직 적합성 질문]\n" + result
        
        return formatted_result
    
    except Exception as e:
        print(f"에러: {str(e)}")
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