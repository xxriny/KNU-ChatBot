from flask import Flask, request, jsonify, send_from_directory
import pandas as pd
import os
from datetime import datetime
import logging
from difflib import get_close_matches

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

@app.route('/')
def hello():
    return '안녕'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, 'data/llm_classified_results.csv')
IMAGE_FOLDER = os.path.join(BASE_DIR, 'data/images')
AZURE_BASE_URL = 'https://kchatbot.azurewebsites.net'

df = pd.read_csv(CSV_PATH)


def parse_deadline(deadline_str):
    try:
        if '~' in deadline_str:
            start = deadline_str.split('~')[0].strip()
            start = start.replace('.', '-').replace(' ', '')
            return pd.to_datetime(start, errors='coerce')
        elif '해당 없음' in deadline_str or '한 달' in deadline_str:
            return pd.NaT
        else:
            return pd.to_datetime(deadline_str, errors='coerce')
    except:
        return pd.NaT

df['deadline'] = df['deadline'].fillna('').apply(parse_deadline)
df['정규과'] = df['department'].fillna('').str.replace(' ', '').str.lower()
df['정규토픽'] = df['topic'].fillna('').str.replace(' ', '').str.lower()

def normalize_to_closest(value, choices):
    value = value.replace(' ', '').lower()
    matches = get_close_matches(value, choices, n=1, cutoff=0.6)
    return matches[0] if matches else value

@app.route('/images/<path:filename>')
def serve_image(filename):
    return send_from_directory(IMAGE_FOLDER, filename)

@app.route('/message', methods=['POST'])
def message():
    data = request.get_json()
    utterance = data.get('action', {}).get('params', {}).get('utterance', '').strip()

    try:
        parts = [s.strip() for s in utterance.split(',')]
        if len(parts) < 2:
            raise ValueError
        topic_input = parts[0]
        department_input = parts[1]
        sort_option = parts[2] if len(parts) >= 3 else '마감순'
    except ValueError:
        return jsonify({
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": "입력 형식은 '주제, 학과[, 정렬옵션]'처럼 콤마로 구분해주세요.\n예: 공모전, 컴퓨터공학과, 마감순"
                        }
                    }
                ]
            }
        })

    today = pd.to_datetime(datetime.today().date())

    topic_norm = normalize_to_closest(topic_input, df['정규토픽'].unique())
    department_norm = normalize_to_closest(department_input, df['정규과'].unique())

    matches = df[
        df['정규토픽'].str.contains(topic_norm, na=False) &
        df['정규과'].apply(lambda x: department_norm in x) &
        df['deadline'].notna() & (df['deadline'] >= today)
    ]

    if sort_option == '마감순':
        matches = matches.sort_values(by='deadline', ascending=True)
    elif sort_option == '최신순':
        matches = matches.sort_values(by='deadline', ascending=False)
    elif sort_option == '오래된순':
        matches = matches.sort_values(by='deadline', ascending=True)

    if matches.empty:
        return jsonify({
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": f"'{topic_input}, {department_input}' 관련 마감 기한이 지난 정보이거나 검색 결과가 없습니다."
                        }
                    }
                ]
            }
        })

    cards = []
    for _, row in matches.head(3).iterrows():
        title = row['title']
        one_line = row['one_line'] if pd.notna(row['one_line']) else '요약 없음'
        deadline = row['deadline'].strftime('%Y-%m-%d') if pd.notna(row['deadline']) else '정보 없음'
        description = f"마감일: {deadline}\n요약: {one_line}"

        link = row['detail_link']
        raw_path = row.get('image', '')
        image_url = f"{AZURE_BASE_URL}/images/{os.path.basename(raw_path)}" if pd.notna(raw_path) and raw_path else None

        card = {
            "title": title,
            "description": description,
            "thumbnail": {"imageUrl": image_url} if image_url else {},
            "buttons": [
                {
                    "action": "webLink",
                    "label": "자세히 보기",
                    "webLinkUrl": link
                }
            ]
        }
        cards.append(card)

    return jsonify({
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "carousel": {
                        "type": "basicCard",
                        "items": cards
                    }
                }
            ]
        }
    })
