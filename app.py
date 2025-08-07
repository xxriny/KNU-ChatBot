# from flask import Flask, request, jsonify
# import pyodbc
# import os
# from datetime import datetime
# import logging
# from urllib.parse import quote
# from dotenv import load_dotenv

# load_dotenv() 
# logging.basicConfig(level=logging.INFO)

# app = Flask(__name__)

# AZURE_BASE_URL = 'https://kchatbot.azurewebsites.net'
# DEFAULT_IMAGE = f"{AZURE_BASE_URL}/images/default.png"
# DB_SERVER=os.getenv("DB_SERVER")

# def get_db_connection():
#     return pyodbc.connect(
#         f"DRIVER={{ODBC Driver 18 for SQL Server}};"
#         f"SERVER={os.getenv('DB_SERVER')};"
#         f"DATABASE={os.getenv('DB_NAME')};"
#         f"UID={os.getenv('DB_USER')};"
#         f"PWD={os.getenv('DB_PASSWORD')};"
#         f"Encrypt=no;"  # 인증서 없는 경우
#     )

# @app.route('/')
# def hello():
#     return '안녕'
# @app.route('/message', methods=['POST'])
# def message():
#     try:
#         data = request.get_json(force=True)
#         print("DEBUG - JSON data:", data)
#     except Exception as e:
#         print("ERROR - JSON 파싱 실패:", str(e))
#         return 'Invalid JSON', 400

#     skill_data = data.get('skillData', {})
#     topic = skill_data.get('topic')
#     department = skill_data.get('department')
#     sort_option = skill_data.get('sort')

#     if not topic or not department:
#         utterance = (
#             data.get('userRequest', {}).get('utterance')
#             or data.get('action', {}).get('params', {}).get('utterance', '')
#         ).strip()

#         parts = [s.strip() for s in utterance.split(',')]
#         if len(parts) < 2:
#             return make_text_response("방금 하신 말씀을 잘 이해하지 못했어요.\n'주제, 학과' 형식으로 알려주셔야 가장 정확하게 찾아드릴 수 있어요!")

#         topic = parts[0]
#         department = parts[1]
#         sort_option = parts[2] if len(parts) >= 3 else '마감순'

#     topic = topic.replace(' ', '').lower()
#     department = department.replace(' ', '').lower()
#     today = datetime.today().date()

#     query = """
#         SELECT DISTINCT n.id, n.title, n.deadline, n.oneline, n.topic, n.created_at, n.url
#         FROM dbo.notice n
#         JOIN dbo.notice_department d ON n.id = d.notice_id
#         WHERE REPLACE(LOWER(d.department), ' ', '') LIKE ?
#         AND REPLACE(LOWER(n.topic), ' ', '') LIKE ?
#         AND (n.deadline IS NULL OR n.deadline >= ?)
#     """

#     if sort_option == '마감순':
#         query += " ORDER BY n.deadline ASC"
#     elif sort_option == '최신순':
#         query += " ORDER BY n.created_at DESC"
#     elif sort_option == '오래된순':
#         query += " ORDER BY n.created_at ASC"

#     conn = get_db_connection()
#     cursor = conn.cursor()
#     try:
#         cursor.execute(query, f"%{department[:2]}%", f"%{topic}%", today)
#         rows = cursor.fetchall()

#         if not rows:
#             return make_text_response(f"'{topic}, {department}' 관련 마감 기한이 지난 정보이거나 공지사항이 존재하지 않아요.")

#         cards = []
#         for row in rows[:3]:
#             notice_id, title, deadline, one_line, topic, created_at, link_url = row

#             cursor.execute("""
#                 SELECT TOP 1 file_url
#                 FROM dbo.notice_attachment
#                 WHERE notice_id = ?
#                 ORDER BY file_order ASC
#             """, notice_id)
#             img_row = cursor.fetchone()

#             if img_row and img_row[0]:
#                 encoded_path = quote(img_row[0])
#                 image_url = encoded_path if encoded_path.startswith('http') else DEFAULT_IMAGE
#             else:
#                 image_url = DEFAULT_IMAGE

#             description = f"마감일: {deadline.strftime('%Y-%m-%d') if deadline else '정보 없음'}\n요약: {one_line or '요약 없음'}"

#             card = {
#                 "title": title,
#                 "description": description,
#                 "thumbnail": {"imageUrl": image_url},
#                 "buttons": [
#                     {
#                         "action": "webLink",
#                         "label": "자세히 보기",
#                         "webLinkUrl": link_url
#                     }
#                 ]
#             }
#             cards.append(card)

#         return jsonify({
#             "version": "2.0",
#             "template": {
#                 "outputs": [
#                     {
#                         "carousel": {
#                             "type": "basicCard",
#                             "items": cards
#                         }
#                     }
#                 ]
#             }
#         })
#     finally:
#         cursor.close()
#         conn.close()

# def make_text_response(text):
#     return jsonify({
#         "version": "2.0",
#         "template": {
#             "outputs": [
#                 {
#                     "simpleText": {
#                         "text": text
#                     }
#                 }
#             ]
#         }
#     })

# # @app.route('/message', methods=['POST'])
# # def message():
# #     data = request.get_json()
# #     print("DEBUG DATA:", data)

# #     skill_data = data.get('skillData', {})
# #     topic = skill_data.get('topic')
# #     department = skill_data.get('department')
# #     sort_option = skill_data.get('sort')

# #     if not topic or not department:
# #         utterance = (
# #             data.get('userRequest', {}).get('utterance')
# #             or data.get('action', {}).get('params', {}).get('utterance', '')
# #         ).strip()

# #         parts = [s.strip() for s in utterance.split(',')]
# #         if len(parts) < 2:
# #             return make_text_response("방금 하신 말씀을  잘 이해하지 못했어요. \n저는 '주제, 학과' 형식으로 알려주셔야 가장 정확하게 찾아드릴 수 있어요!")

# #         topic = parts[0]
# #         department = parts[1]
# #         sort_option = parts[2] if len(parts) >= 3 else '마감순'

# #     today = datetime.today().date()
# #     topic = topic.replace(' ', '').lower()
# #     department = department.replace(' ', '').lower()

# #     query = """
# #         SELECT DISTINCT n.id, n.title, n.deadline, n.oneline, n.topic, n.created_at, n.url
# #         FROM dbo.notice n
# #         JOIN dbo.notice_department d ON n.id = d.notice_id
# #         WHERE REPLACE(LOWER(d.department), ' ', '') LIKE ?
# #         AND REPLACE(LOWER(n.topic), ' ', '') LIKE ?
# #         AND (n.deadline IS NULL OR n.deadline >= ?)
# #     """

# #     if sort_option == '마감순':
# #         query += " ORDER BY n.deadline ASC"
# #     elif sort_option == '최신순':
# #         query += " ORDER BY n.created_at DESC"
# #     elif sort_option == '오래된순':
# #         query += " ORDER BY n.created_at ASC"

# #     cursor.execute(query, f"%{department[:2]}%", f"%{topic}%", today)
# #     rows = cursor.fetchall()

# #     if not rows:
# #         return make_text_response(f"'{topic}, {department}' 관련 마감 기한이 지난 정보이거나 공지사항이 존재하지 않아요.")

# #     cards = []
# #     for row in rows[:3]:
# #         notice_id, title, deadline, one_line, topic, created_at, link_url = row

# #         cursor.execute("""
# #             SELECT TOP 1 file_url
# #             FROM dbo.notice_attachment
# #             WHERE notice_id = ?
# #             ORDER BY file_order ASC
# #         """, notice_id)
# #         img_row = cursor.fetchone()
# #         if img_row and img_row[0]:
# #             encoded_path = quote(img_row[0])
# #             image_url = encoded_path if encoded_path.startswith('http') else DEFAULT_IMAGE
# #         else:
# #             image_url = DEFAULT_IMAGE

# #         description = f"마감일: {deadline.strftime('%Y-%m-%d') if deadline else '정보 없음'}\n요약: {one_line or '요약 없음'}"

# #         card = {
# #             "title": title,
# #             "description": description,
# #             "thumbnail": {"imageUrl": image_url},
# #             "buttons": [
# #                 {
# #                     "action": "webLink",
# #                     "label": "자세히 보기",
# #                     "webLinkUrl": link_url
# #                 }
# #             ]
# #         }
# #         cards.append(card)

# #     return jsonify({
# #         "version": "2.0",
# #         "template": {
# #             "outputs": [
# #                 {
# #                     "carousel": {
# #                         "type": "basicCard",
# #                         "items": cards
# #                     }
# #                 }
# #             ]
# #         }
# #     })

# # def make_text_response(text):
# #     return jsonify({
# #         "version": "2.0",
# #         "template": {
# #             "outputs": [
# #                 {
# #                     "simpleText": {
# #                         "text": text
# #                     }
# #                 }
# #             ]
# #         }
# #     })

# # if __name__ == '__main__':
# #     app.run(port=5000)

from flask import Flask, request, jsonify, send_from_directory
import os
from datetime import datetime
import pyodbc
from dotenv import load_dotenv

app = Flask(__name__)

# 환경 변수 로드
load_dotenv()

# 이미지 기본 설정

AZURE_BASE_URL = 'https://kchatbot.azurewebsites.net'
DEFAULT_IMAGE = f"{AZURE_BASE_URL}/images/default.png"
DB_SERVER=os.getenv("DB_SERVER")


# DB 연결 함수
def get_db_connection():
    return pyodbc.connect(
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={os.getenv('DB_SERVER')};"
        f"DATABASE={os.getenv('DB_NAME')};"
        f"UID={os.getenv('DB_USER')};"
        f"PWD={os.getenv('DB_PASSWORD')};"
        f"Encrypt=no;"
    )

@app.route('/')
def hello():
    return '안녕'

@app.route('/images/<path:filename>')
def serve_image(filename):
    return send_from_directory(IMAGE_FOLDER, filename)

@app.route('/message', methods=['POST'])
def message():
    try:
        data = request.get_json(force=True)
        print("✅ JSON Parsed:", data)
    except Exception as e:
        print("❌ JSON Error:", str(e))
        return 'Invalid JSON', 400

    skill_data = data.get('skillData', {})
    topic = skill_data.get('topic')
    department = skill_data.get('department')
    sort_option = skill_data.get('sort')

    if not topic or not department:
        utterance = (
            data.get('userRequest', {}).get('utterance')
            or data.get('action', {}).get('params', {}).get('utterance', '')
        ).strip()

        parts = [s.strip() for s in utterance.split(',')]
        if len(parts) < 2:
            return make_text_response("방금 하신 말씀을 잘 이해하지 못했어요.\n'주제, 학과' 형식으로 알려주세요!")

        topic = parts[0]
        department = parts[1]
        sort_option = parts[2] if len(parts) >= 3 else '마감순'

    normalized_topic = topic.replace(' ', '').lower()
    normalized_department = department.replace(' ', '').lower()
    today = datetime.today().date()

    query = f"""
        SELECT DISTINCT
            n.id, n.title, n.deadline, n.oneline, n.topic, n.created_at, n.url,
            a.file_url
        FROM dbo.notice n
        JOIN dbo.notice_department d ON n.id = d.notice_id
        OUTER APPLY (
            SELECT TOP 1 file_url
            FROM dbo.notice_attachment
            WHERE notice_id = n.id
            ORDER BY file_order ASC
        ) a
        WHERE REPLACE(LOWER(d.department), ' ', '') LIKE ?
        AND REPLACE(LOWER(n.topic), ' ', '') LIKE ?
        AND (n.deadline IS NULL OR n.deadline >= ?)
    """

    if sort_option == '마감순':
        query += " ORDER BY n.deadline ASC"
    elif sort_option == '최신순':
        query += " ORDER BY n.created_at DESC"
    elif sort_option == '오래된순':
        query += " ORDER BY n.created_at ASC"

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(query, f"%{normalized_department}%", f"%{normalized_topic}%", today)
        rows = cursor.fetchall()

        if not rows:
            return make_text_response(f"'{topic}, {department}' 관련 공지사항이 없어요.")

        cards = []
        for row in rows[:3]:
            notice_id, title, deadline, one_line, topic, created_at, link_url, file_url = row

            if file_url and str(file_url).startswith("http"):
                image_url = file_url
            else:
                image_url = DEFAULT_IMAGE

            description = f"마감일: {deadline.strftime('%Y-%m-%d') if deadline else '정보 없음'}\n요약: {one_line or '요약 없음'}"

            card = {
                "title": title,
                "description": description,
                "thumbnail": {"imageUrl": image_url},
                "buttons": [
                    {
                        "action": "webLink",
                        "label": "자세히 보기",
                        "webLinkUrl": link_url
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
    finally:
        cursor.close()
        conn.close()

def make_text_response(text):
    return jsonify({
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": text
                    }
                }
            ]
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
