from http.server import BaseHTTPRequestHandler
import json
from openai import OpenAI
import os
import traceback

def generate_questions(resume_text, job_description):
    try:
        if not resume_text or not job_description:
            raise ValueError("이력서 내용과 채용공고가 모두 필요합니다.")

        # 입력 텍스트 길이 제한
        resume_text = resume_text[:2000]
        job_description = job_description[:1000]
        
        client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        if not os.environ.get('OPENAI_API_KEY'):
            raise ValueError("OpenAI API 키가 설정되지 않았습니다.")
        
        prompt = f"""다음 내용을 바탕으로 10개의 구체적인 면접 질문을 생성해주세요면접 질문을 생성해주세요:

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
7. [도전] 관련된 경험 질문
8. [책임감] 관련된 사례 질문
9. [협력] 경험 질문
10. [전문성] 관련된 사례 질문"""

        print(f"OpenAI API 호출 시작") # 디버깅용

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "면접 질문을 생성하는 면접관입니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )

        print(f"OpenAI API 응답 받음") # 디버깅용
        
        result = response.choices[0].message.content
        print(f"응답 길이: {len(result)}") # 디버깅용
        
        return result
        
    except Exception as e:
        print(f"에러 발생: {str(e)}")
        print(f"상세 에러: {traceback.format_exc()}")
        raise Exception(f"질문 생성 중 오류 발생: {str(e)}")

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            print("POST 요청 시작") # 디버깅용
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))

            print("데이터 파싱 완료") # 디버깅용

            resume_text = request_data.get('resume_text', '')
            job_description = request_data.get('job_description', '')

            if not resume_text or not job_description:
                raise ValueError("이력서 내용과 채용공고가 모두 필요합니다.")

            result = generate_questions(resume_text, job_description)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response_data = {"result": result}
            response_json = json.dumps(response_data, ensure_ascii=False)
            self.wfile.write(response_json.encode('utf-8'))
            
            print("응답 전송 완료") # 디버깅용
            
        except Exception as e:
            print(f"핸들러 에러: {str(e)}")
            print(f"상세 에러: {traceback.format_exc()}")
            
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            error_response = {
                "error": str(e),
                "detail": traceback.format_exc()
            }
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers() 