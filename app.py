import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import google.generativeai as genai
import datetime

# ==========================================
# 1. APIキーの設定 (Secretsから読み込む)
# ==========================================
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=GOOGLE_API_KEY)

# ==========================================
# 2. スプレッドシートの設定 (Secretsから読み込む)
# ==========================================
SPREADSHEET_NAME = 'マイコーチングデータ'

scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def add_data_and_get_advice(time_str, weight, content):
    try:
        # 金庫からJSONの中身を取り出す
        key_dict = dict(st.secrets["gcp_service_account"])
        
        # 認証
        creds = Credentials.from_service_account_info(key_dict, scopes=scopes)
        gc = gspread.authorize(creds)
        sh = gc.open(SPREADSHEET_NAME)
        
        # 1. データを書き込む
        worksheet_log = sh.worksheet("ログ")
        today = datetime.date.today().strftime("%Y/%m/%d")
        worksheet_log.append_row([today, time_str, weight, content])
        
        # 2. コーチング設定を読む
        worksheet_settings = sh.worksheet("設定")
        prompt_cell = worksheet_settings.acell('B1').value
        if not prompt_cell:
            prompt_cell = "あなたは厳しいけど優しいコーチです。"

        # 直近データの取得
        logs = worksheet_log.get_all_values()
        recent_logs = logs[-6:]
        
        # 3. Geminiに相談
        # ★ここを 'gemini-1.5-pro' に変更しました！（深く思考するモデル）
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        full_prompt = f"""
        【役割】{prompt_cell}
        【履歴】{recent_logs}
        【今回】日付:{today}, 時間:{time_str}, 体重:{weight}, 内容:{content}
        上記を踏まえて、深く洞察し、具体的かつ論理的なフィードバックとアクションプランを提示してください。
        """
        
        response = model.generate_content(full_prompt)
        return response.text

    except Exception as e:
        return f"エラー: {e}"

# ==========================================
# 3. アプリ画面
# ==========================================
st.title("🧠 My AI Coach (Pro Mode)")
st.write("Proモデルが深く思考中...")

col1, col2 = st.columns(2)
with col1:
    input_time = st.text_input("帰宅時間")
with col2:
    input_weight = st.text_input("体重")

input_content = st.text_area("インプット内容")

if st.button("送信 🚀"):
    if input_time and input_weight and input_content:
        # スピナーのメッセージも変更
        with st.spinner('Gemini Proが深く思考しています...（少々お待ちください）'):
            advice = add_data_and_get_advice(input_time, input_weight, input_content)
            st.success("完了！")

            st.info(advice)
