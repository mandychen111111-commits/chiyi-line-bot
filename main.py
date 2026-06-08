import os
import anthropic
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
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# === 讀取知識庫 ===
def load_knowledge_base():
    kb_path = os.path.join(os.path.dirname(__file__), "knowledge_base.txt")
    with open(kb_path, "r", encoding="utf-8") as f:
        return f.read()

KNOWLEDGE_BASE = load_knowledge_base()

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

# === 處理 LINE Webhook ===
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_message = event.message.text

    # 呼叫 Claude API
    try:
        response = claude_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}]
        )
        reply_text = response.content[0].text
    except Exception as e:
        reply_text = "抱歉，系統暫時忙碌中，請稍後再試，或直接加入客服 LINE：https://lin.ee/OFTbf29 😊"

    # 回覆給用戶
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )

@app.route("/", methods=["GET"])
def health_check():
    return "奇異生技 LINE Bot 運作中 ✅"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
