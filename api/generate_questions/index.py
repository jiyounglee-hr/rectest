from http.server import BaseHTTPRequestHandler
import json
import openai
import os

def generate_questions(resume_text, job_description):
    try:
        openai.api_key = os.environ.get('OPENAI_API_KEY')
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "당신은 경험 많은 면접관입니다."},
                {"role": "user", "content": f"다음 이력서와 채용요건을 바탕으로 면접 질문을 생성해주세요:\n\n이력서: {resume_text}\n\n채용요건: {job_description}"}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        return response.choices[0].message.content.replace('**', '')
    except Exception as e:
        print(f"OpenAI API 에러: {str(e)}")
        raise Exception(str(e))

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        response_data = {}
        
        try:
            # 요청 데이터 읽기
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))

            # 질문 생성
            result = generate_questions(
                request_data.get('resume_text', ''),
                request_data.get('job_description', '')
            )
            
            response_data = {"result": result}
            
        except Exception as e:
            print(f"서버 에러: {str(e)}")
            response_data = {"error": str(e)}
        
        finally:
            # 응답 헤더 설정
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            
            # 응답 데이터 전송
            try:
                response_json = json.dumps(response_data, ensure_ascii=False)
                self.wfile.write(response_json.encode('utf-8'))
            except Exception as e:
                print(f"응답 전송 에러: {str(e)}")
                error_response = json.dumps({"error": "응답 전송 중 오류가 발생했습니다"})
                self.wfile.write(error_response.encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers() 