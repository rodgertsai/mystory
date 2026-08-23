import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import ollama

# 預設的分鏡導演 System Prompt
SYSTEM_PROMPT = (
    "你是一位專業短動畫導演。請將使用者的主題拆解為精確 45 秒、"
    "5 個關鍵鏡頭的短片分鏡腳本，包含時間軸、鏡頭語言、動態描述與英文繪圖提示詞。"
)

class OllamaChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Qwen3 故事與分鏡對話助手 (100% 離線)")
        self.root.geometry("800x650")
        
        # 本地 Ollama Client (連接斷網 Docker 容器)
        self.client = ollama.Client(host='http://127.0.0.1:11434')
        self.model_name = "qwen3:14b"
        self.chat_history = [{"role": "system", "content": SYSTEM_PROMPT}]

        self._build_ui()

    def _build_ui(self):
        # 1. 對話紀錄顯示區
        self.chat_area = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, font=("Segoe UI", 10), state=tk.DISABLED
        )
        self.chat_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # 2. 底部輸入與按鈕區
        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(padx=10, pady=(0, 10), fill=tk.X)

        self.input_box = tk.Text(bottom_frame, height=3, font=("Segoe UI", 10))
        self.input_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        self.input_box.bind("<Return>", self._on_enter_pressed)

        btn_frame = tk.Frame(bottom_frame)
        btn_frame.pack(side=tk.RIGHT, fill=tk.Y)

        self.send_btn = ttk.Button(btn_frame, text="發送 (Enter)", command=self.send_message)
        self.send_btn.pack(fill=tk.BOTH, expand=True)

        self.clear_btn = ttk.Button(btn_frame, text="清空對話", command=self.clear_chat)
        self.clear_btn.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

    def _append_text(self, text, prefix=""):
        self.chat_area.config(state=tk.NORMAL)
        if prefix:
            self.chat_area.insert(tk.END, prefix)
        self.chat_area.insert(tk.END, text)
        self.chat_area.see(tk.END)
        self.chat_area.config(state=tk.DISABLED)

    def _on_enter_pressed(self, event):
        # Shift+Enter 換行，單獨 Enter 發送
        if not event.state & 0x1:
            self.send_message()
            return "break"

    def send_message(self):
        user_text = self.input_box.get("1.0", tk.END).strip()
        if not user_text:
            return

        self.input_box.delete("1.0", tk.END)
        self._append_text(f"👤 你:\n{user_text}\n\n")
        self.chat_history.append({"role": "user", "content": user_text})

        # 鎖定發送按鈕
        self.send_btn.config(state=tk.DISABLED)
        self._append_text("🤖 Qwen:\n")

        # 啟動背景執行緒處理 Ollama 推論串流
        threading.Thread(target=self._stream_ollama_response, daemon=True).start()

    def _stream_ollama_response(self):
        full_reply = ""
        try:
            stream = self.client.chat(
                model=self.model_name,
                messages=self.chat_history,
                stream=True
            )
            for chunk in stream:
                content = chunk.get('message', {}).get('content', '')
                full_reply += content
                self.root.after(0, self._append_text, content)

            self.chat_history.append({"role": "assistant", "content": full_reply})
            self.root.after(0, self._append_text, "\n\n" + "-"*40 + "\n\n")
        except Exception as e:
            self.root.after(0, self._append_text, f"\n[連線錯誤: {str(e)}]\n\n")
        finally:
            self.root.after(0, lambda: self.send_btn.config(state=tk.NORMAL))

    def clear_chat(self):
        self.chat_history = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.delete("1.0", tk.END)
        self.chat_area.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = OllamaChatApp(root)
    root.mainloop()