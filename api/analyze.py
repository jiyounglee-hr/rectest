from http.server import BaseHTTPRequestHandler
import json
import os
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
root_dir = str(Path(__file__).resolve().parent.parent)
sys.path.append(root_dir)

from resume_summarizer import ResumeSummarizer
import tempfile

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        try:
            # CORS 헤더 설정
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()

            # 요청 본문 읽기
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            # multipart/form-data 파싱
            boundary = self.headers.get('Content-Type', '').split('boundary=')[1].encode()
            form = self.parse_multipart(post_data, boundary)
            
            # 파일과 JD 텍스트 추출
            resume_file = form.get('resume', [None])[0]
            jd_text = form.get('jd_text', [b''])[0].decode('utf-8')

            if not resume_file or not jd_text:
                raise ValueError('이력서 파일과 JD 텍스트가 필요합니다.')

            # 임시 파일로 저장
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                temp_file.write(resume_file)
                temp_path = temp_file.name

            try:
                # 이력서 분석기 초기화
                summarizer = ResumeSummarizer()
                
                # 이력서 텍스트 추출
                resume_text = summarizer.read_resume(temp_path)
                if not resume_text:
                    raise ValueError('이력서 파일을 읽을 수 없습니다.')

                # 분석 수행
                if self.path == '/api/analyze':
                    result = summarizer.generate_summary(resume_text, jd_text)
                elif self.path == '/api/generate_questions':
                    result = summarizer.generate_interview_questions(resume_text, jd_text)
                else:
                    raise ValueError('잘못된 API 경로입니다.')

                # 응답 데이터 생성
                response_data = {
                    'status': 'success',
                    'html': result
                }

            finally:
                # 임시 파일 삭제
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

            # JSON 응답 전송
            self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
            error_response = {
                'status': 'error',
                'error': str(e)
            }
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode('utf-8'))

    def parse_multipart(self, data, boundary):
        form = {}
        parts = data.split(boundary)
        
        for part in parts[1:-1]:
            if b'\r\n\r\n' in part:
                header, content = part.split(b'\r\n\r\n', 1)
                header = header.decode('utf-8')
                
                if 'Content-Disposition' in header:
                    field_name = header.split('name="')[1].split('"')[0]
                    content = content.strip(b'\r\n')
                    if 'filename=' in header:
                        form[field_name] = [content]
                    else:
                        form[field_name] = [content]
        
        return form

def handle_request(request):
    try:
        # CORS 헤더 설정
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Content-Type': 'application/json'
        }

        # OPTIONS 요청 처리
        if request.method == 'OPTIONS':
            return ('', 204, headers)

        if request.method != 'POST':
            return (json.dumps({'error': 'Method not allowed'}), 405, headers)

        # 파일 처리 및 분석
        if 'file' not in request.files:
            return (json.dumps({'error': '파일이 없습니다'}), 400, headers)

        file = request.files['file']
        
        # 디버깅을 위한 로그
        print("Received file:", file.filename)
        
        try:
            # 파일 처리 로직
            analyzed_text = process_pdf(file)  # 이 함수가 실제 분석을 수행
            
            result = {
                'result': analyzed_text
            }
            
            print("Analysis result:", result)  # 디버깅 로그
            return (json.dumps(result), 200, headers)
            
        except Exception as e:
            print(f"Processing error: {str(e)}")  # 상세 에러 로그
            return (json.dumps({'error': f'파일 처리 중 오류: {str(e)}'}), 500, headers)

    except Exception as e:
        print(f"Server error: {str(e)}")  # 서버 에러 로그
        return (json.dumps({'error': str(e)}), 500, headers) 