from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # CORS 헤더 설정
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()

            # 테스트용 응답 데이터
            response_data = {
                'status': 'success',
                'html': """
                <div class="interview-guide">
                    <h2>💡 직무 적합성 검증 질문</h2>
                    <div class="question-section">
                        <h3>1. 전문성 검증</h3>
                        <ul>
                            <li>이전 업무에서 가장 큰 성과는 무엇이었나요?</li>
                            <li>현재 지원하신 직무와 관련된 전문 지식을 어떻게 쌓아오셨나요?</li>
                            <li>업무 수행 시 가장 중요하게 생각하는 부분은 무엇인가요?</li>
                        </ul>
                    </div>
                    <h2>🚀 핵심가치 검증 질문</h2>
                    <div class="question-section">
                        <h3>1. 도전정신</h3>
                        <ul>
                            <li>새로운 도전을 했던 경험에 대해 이야기해주세요.</li>
                            <li>실패를 극복했던 경험이 있다면 말씀해주세요.</li>
                        </ul>
                    </div>
                </div>
                """
            }

            # JSON 응답 전송
            self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
            error_response = {
                'status': 'error',
                'error': str(e)
            }
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers() 