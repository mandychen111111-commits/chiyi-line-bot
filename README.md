# 奇異生技 LINE Bot

## 部署步驟

### 第一步：申請帳號（三個都要）
1. **LINE Developers**：https://developers.line.biz/
   - 建立 Messaging API Channel
   - 記下 Channel Secret 和 Channel Access Token

2. **Anthropic API**：https://console.anthropic.com/
   - 記下 API Key

3. **GitHub**：https://github.com/
   - 建立新 repository，上傳這個資料夾所有檔案

4. **Render**：https://render.com/
   - 用 GitHub 帳號登入

### 第二步：部署到 Render
1. 登入 Render → New → Web Service
2. 連接你的 GitHub repository
3. 設定：
   - Name：chiyi-line-bot
   - Runtime：Python 3
   - Build Command：pip install -r requirements.txt
   - Start Command：gunicorn main:app
4. 新增環境變數（Environment Variables）：
   - LINE_CHANNEL_ACCESS_TOKEN = （你的Token）
   - LINE_CHANNEL_SECRET = （你的Secret）
   - ANTHROPIC_API_KEY = （你的Key）
5. 點 Deploy

### 第三步：設定 LINE Webhook
1. 部署完成後，Render 會給你一個網址，例如：
   https://chiyi-line-bot.onrender.com
2. 回到 LINE Developers → Messaging API
3. Webhook URL 填入：https://chiyi-line-bot.onrender.com/callback
4. 開啟 Use webhook
5. 按 Verify 測試

### 完成！
加入你的 LINE@ 帳號，傳訊息測試看看。
