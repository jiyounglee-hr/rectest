from http.server import BaseHTTPRequestHandler
import json
import os
from openai import OpenAI

def generate_questions(resume_text, job_description):
    try:
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        prompt = f"""
        다음 이력서와 채용공고를 바탕으로 면접 질문을 생성해주세요.
        
        이력서 내용: {resume_text}
        
        채용공고: {job_description}
        
        다음 카테고리별로 구체적인 면접 질문을 생성해주세요:

        [경력 기반 질문] (2개)
        1. 가장 중요한 프로젝트 경험 질문
        2. 어려운 문제를 해결한 구체적 사례 질문

        [직무 적합성 질문] (2개)
        3. 채용공고의 필수 자격요건 관련 질문
        4. 채용공고의 우대사항 관련 질문

        [기술/전문성 질문] (2개)
        5. 직무 관련 전문 지식을 검증하는 질문
        6. 실제 업무 상황에서의 대처 방안을 묻는 질문

        [조직 적합성 질문] (4개 - 뉴로핏 핵심가치 기반)
        7. [도전] "두려워 말고 시도합니다"와 관련된 경험 질문
        8. [책임감] "대충은 없습니다"와 관련된 사례 질문
        9. [협력] "동료와 협업합니다"와 관련된 경험 질문
        10. [전문성] "능동적으로 일합니다"와 관련된 사례 질문

        [성장 가능성 질문] (1개)
        11. 자기 개발 계획과 비전 질문

        각 질문은:
        - 이력서의 구체적인 내용을 참조할 것
        - 채용공고의 요구사항과 연계할 것
        - 구체적이고 상황 중심적일 것
        - 단순 예/아니오로 답할 수 없는 형태로 작성할 것
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "당신은 경험 많은 면접관입니다. 지원자의 이력서와 채용공고를 분석하여 구체적이고 효과적인 면접 질문을 생성합니다."},
                {"role": "user", "content": prompt}
            ]
        )
        
        # 응답에서 ** 제거
        result = response.choices[0].message.content.replace('**', '')
        return result

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