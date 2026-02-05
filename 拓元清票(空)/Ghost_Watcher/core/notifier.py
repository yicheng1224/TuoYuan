import requests
import json

class Notifier:
    def __init__(self, discord_url=None, line_token=None, line_user_id=None):
        self.discord_url = discord_url
        self.line_token = line_token
        self.line_user_id = line_user_id

    def _send_discord(self, message, level):
        """ 發送 Discord 通知 (支援所有等級) """
        if not self.discord_url: return

        data = {
            "username": "拓元監控官",
            "content": message
        }
        
        # P0 等級加入 @everyone
        if level == "P0":
            data["content"] = f"@everyone 🚨 **緊急票況！**\n{message}"
            data["tts"] = True
        
        try:
            requests.post(self.discord_url, json=data)
        except Exception as e:
            print(f"❌ Discord 發送失敗: {e}")

    def _send_line(self, message):
        """ 發送 LINE 通知 (僅限 P0 等級，使用 Messaging API) """
        if not self.line_token or not self.line_user_id: return

        url = "https://api.line.me/v2/bot/message/push"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.line_token}"
        }
        payload = {
            "to": self.line_user_id,
            "messages": [
                {
                    "type": "text",
                    "text": message
                }
            ]
        }

        try:
            r = requests.post(url, headers=headers, json=payload)
            if r.status_code != 200:
                print(f"❌ LINE 發送失敗 ({r.status_code}): {r.text}")
            else:
                print("✅ LINE 通知已發送")
        except Exception as e:
            print(f"❌ LINE 連線錯誤: {e}")

    def send(self, message, level="P1"):
        """
        統一發送入口
        - Discord: 接收所有訊息 (P0, P1)
        - LINE: 僅接收緊急訊息 (P0) 以節省額度
        """
        # 1. 總是發送 Discord
        self._send_discord(message, level)

        # 2. 只有在緊急 (P0) 時才發送 LINE
        if level == "P0":
            self._send_line(message)