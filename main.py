import os
import google.generativeai as genai
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi,
    ReplyMessageRequest, TextMessage
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

app = Flask(__name__)

# === 設定區（從環境變數讀取）===
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

print(f"[啟動] LINE Token: {LINE_CHANNEL_ACCESS_TOKEN[:20]}..." if LINE_CHANNEL_ACCESS_TOKEN else "[啟動] LINE Token: 未設定")
print(f"[啟動] Gemini API Key: {GEMINI_API_KEY[:20]}..." if GEMINI_API_KEY else "[啟動] Gemini API Key: 未設定")

configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 設定 Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# === 讀取知識庫 ===
def load_knowledge_base():
    kb_path = os.path.join(os.path.dirname(__file__), "knowledge_base.txt")
    try:
        with open(kb_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print("[警告] 找不到 knowledge_base.txt")
        return "（知識庫無法載入）"

KNOWLEDGE_BASE = load_knowledge_base()
print(f"[啟動] 知識庫已載入，共 {len(KNOWLEDGE_BASE)} 字")

# === System Prompt：定義 Bot 身份與行為 ===
SYSTEM_PROMPT = f"""你是「奇異生技小幫手」，一個專業、親切的 LINE 客服助理。

你的工作是根據以下知識庫，回覆用戶關於奇異生技產品、頭皮養護知識、購買與服務的問題。

【回覆原則】
1. 回答要簡潔明瞭，不要太長（最多 200 字）
2. 如果知識庫有相關影片連結，務必附上
3. 如果問題是關於購買，引導到客服 LINE 或官網
4. 如果問題超出知識庫範圍，請說「這個問題需要更專業的說明，建議加入我們的客服 LINE：https://lin.ee/OFTbf29 讓專人為您服務 😊」
5. 語氣要親切、帶一點溫度，可以適當使用 emoji
6. 不要捏造任何資訊

【知識庫內容】
{KNOWLEDGE_BASE}
"""

# 創建 Gemini 模型（使用最新的 gemini-1.5-flash），設定 system instruction
gemini_model = genai.GenerativeModel(
    'gemini-1.5-flash',
    system_instruction=SYSTEM_PROMPT
)

# === 處理 LINE Webhook ===
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("[錯誤] LINE 簽名驗證失敗")
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_message = event.message.text
    user_id = event.source.user_id
    print(f"[收到訊息] 使用者: {user_id}, 內容: {user_message}")

    # 呼叫 Gemini API
    reply_text = None
    try:
        print(f"[Gemini] 開始呼叫...")
        response = gemini_model.generate_content(
            user_message,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=500,
                temperature=0.7,
            )
        )
        reply_text = response.text
        print(f"[Gemini] 成功回應: {reply_text[:100]}...")
    except Exception as e:
        print(f"[Gemini 錯誤] {type(e).__name__}: {str(e)}")
        reply_text = "抱歉，系統暫時忙碌中，請稍後再試，或直接加入客服 LINE：https://lin.ee/OFTbf29 😊"

    # 回覆給用戶
    if reply_text:
        try:
            print(f"[LINE 回覆] 開始回覆使用者...")
            with ApiClient(configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=reply_text)]
                    )
                )
            print(f"[LINE 回覆] 成功")
        except Exception as e:
            print(f"[LINE 回覆錯誤] {type(e).__name__}: {str(e)}")

@app.route("/", methods=["GET"])
def health_check():
    return "奇異生技 LINE Bot 運作中 ✅"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"[啟動] Flask 啟動在 port {port}")
    app.run(host="0.0.0.0", port=port)
