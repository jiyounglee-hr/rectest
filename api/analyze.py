from http.server import BaseHTTPRequestHandler
import json
import os
import openai
from PyPDF2 import PdfReader
from io import BytesIO

def process_pdf(file_data):
    try:
        # PDF 파일 읽기
        pdf = PdfReader(BytesIO(file_data))
        text = ""
        for page in pdf.pages:
            text += page.extract_text()
        
        # OpenAI API 설정
        openai.api_key = os.getenv('OPENAI_API_KEY')
        
        # GPT 분석 요청
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "이력서를 분석하여 주요 경력과 기술을 요약해주세요."},
                {"role": "user", "content": text}
            ]
        )
        
        return response.choices[0].message['content']
    except Exception as e:
        print(f"PDF 처리 중 에러: {str(e)}")
        raise e

def handle_request(event):
    try:
        # CORS 헤더
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Content-Type': 'application/json'
        }
        
        # OPTIONS 요청 처리
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 204,
                'headers': headers,
                'body': ''
            }
            
        if event.get('httpMethod') != 'POST':
            return {
                'statusCode': 405,
                'headers': headers,
                'body': json.dumps({'error': 'Method not allowed'})
            }
            
        # multipart/form-data 처리
        body = event.get('body', '')
        if not body:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': '요청 본문이 비어있습니다.'})
            }
            
        try:
            # PDF 처리 및 분석
            analyzed_text = process_pdf(body)
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'result': analyzed_text})
            }
            
        except Exception as e:
            print(f"처리 중 에러: {str(e)}")
            return {
                'statusCode': 500,
                'headers': headers,
                'body': json.dumps({'error': f'처리 중 에러: {str(e)}'})
            }
            
    except Exception as e:
        print(f"서버 에러: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': f'서버 에러: {str(e)}'})
        }

def main(req):
    return handle_request(req) 