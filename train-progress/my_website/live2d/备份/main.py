from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from dotenv import load_dotenv
from typing import Optional, List, Dict, Any
import os
import sqlite3
import uvicorn
import requests
import base64
import urllib3

# --- 配置与初始化 ---

# 禁用 SSL 警告（解决自签名或代理环境下的 SSLError）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()
app = FastAPI(title="Live2D AI Backend")

# 跨域配置 (允许前端访问)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 密钥配置
MY_API2D_KEY = os.getenv("Api_key")
MY_FISH_AUDIO_KEY = os.getenv("Fish_audio_api_key")

# 初始化 OpenAI 客户端 (使用 API2D 代理)
client = OpenAI(
    api_key=MY_API2D_KEY, 
    base_url="https://oa.api2d.net/v1"
)

# 语音角色映射 (Fish Audio Reference IDs)
VOICE_MODEL_MAP = {
    "爱丽丝": "e488ebeadd83496b97a3cd472dcd04ab",
    "塔菲": "55b28b196e1c4fff9a55cd32a46eff25",
    "小孩姐": "4ca68a299cb24ae599dbb828dc31a73c",
    "才羽桃": "05c25a82cfe0426ab63d3d71ba8656cf",
    "可莉": "0b8449eb752c4f888f463fc5d2c0db65",
    "丁真": "54a5170264694bfc8e9ad98df7bd89c3",
    "小团团": "0da1e00b71164d8cb3761c714b11da64",
    "曼波": "0f08cacd3e354471a4b94dd00b4cc4a3",
    "东雪莲": "94abfed6539d48d281fdb06dc0e09664"
}

DB_FILE = 'chat_history.db'

def init_db():
    """初始化 SQLite 数据库表结构"""
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                user_id TEXT, 
                role_name TEXT, 
                role_type TEXT, 
                content TEXT
            )
        ''')

# 应用启动时初始化数据库
init_db()

# --- 数据模型 ---

class ChatRequest(BaseModel):
    message: str = ""
    image: Optional[str] = None
    roleName: str
    userId: str
    voice: Optional[str] = None

# --- 工具函数 ---

def get_tts_audio(text: str, voice_name: str) -> Optional[str]:
    """
    调用 Fish Audio API 将文本转换为语音
    返回: Base64 编码的音频字符串 或 None
    """
    model_id = VOICE_MODEL_MAP.get(voice_name)
    if not model_id: 
        return None

    url = "https://api.rubia.top/v1/tts" 
    headers = {
        "Authorization": f"Bearer {MY_FISH_AUDIO_KEY}", 
        "Content-Type": "application/json"
    }
    
    payload = {
        "text": text,
        "reference_id": model_id,
        "format": "mp3",
        "latency": "normal"
    }

    try:
        # timeout 设置防止 API 卡死
        response = requests.post(url, json=payload, headers=headers, timeout=25, verify=False)
        if response.status_code == 200:
            return base64.b64encode(response.content).decode('utf-8')
        else:
            print(f"[TTS Error] Status: {response.status_code}")
    except Exception as e:
        print(f"[TTS Exception] {e}")
    return None

# --- 路由接口 ---

@app.post("/get_history")
async def get_history(request: ChatRequest):
    """获取指定用户和角色的历史对话记录"""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            # 按 ID 升序获取，还原对话流
            cursor.execute(
                "SELECT role_type, content FROM history WHERE role_name = ? AND user_id = ? ORDER BY id ASC", 
                (request.roleName, request.userId)
            )
            rows = cursor.fetchall()
            return {"history": [{"role": r[0], "content": r[1]} for r in rows]}
    except Exception as e:
        print(f"[History Error] {e}")
        return {"history": []}

@app.post("/chat")
async def chat(request: ChatRequest):
    """核心聊天接口：处理文本/图片输入，调用 LLM，生成 TTS，保存历史"""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            
            # 1. 获取最近上下文 (最近 6 条)
            cursor.execute(
                "SELECT role_type, content FROM history WHERE role_name = ? AND user_id = ? ORDER BY id DESC LIMIT 6",
                (request.roleName, request.userId)
            )
            history_rows = cursor.fetchall()[::-1] # 反转回时间顺序
            
            # 2. 构建 Prompt
            messages = [{
                "role": "system", 
                "content": f"你现在是{request.roleName}，请用二次元少女语气简短回复。你能看见图片内容并给出回应,不要使用颜文字，多用可爱语言回答。"
            }]
            for r in history_rows: 
                messages.append({"role": r[0], "content": r[1]})
            
            # 3. 处理当前用户输入 (文本 + 可选图片)
            if request.image:
                user_content = [
                    {"type": "text", "text": request.message or "请看看这张图"},
                    {"type": "image_url", "image_url": {"url": request.image}}
                ]
            else:
                user_content = request.message

            messages.append({"role": "user", "content": user_content})

            # 4. 调用 LLM
            response = client.chat.completions.create(
                model="gpt-4o-mini", 
                messages=messages,
                max_tokens=300
            )
            ai_reply = response.choices[0].message.content

            # 5. 生成语音 (如果选择了语音)
            audio_base64 = None
            if request.voice:
                audio_base64 = get_tts_audio(ai_reply, request.voice)

            # 6. 保存新对话记录
            # 记录用户消息 (如果是图片，标记一下)
            log_text = request.message + (" [图片消息]" if request.image else "")
            cursor.execute(
                "INSERT INTO history (user_id, role_name, role_type, content) VALUES (?, ?, 'user', ?)",
                (request.userId, request.roleName, log_text)
            )
            # 记录 AI 回复
            cursor.execute(
                "INSERT INTO history (user_id, role_name, role_type, content) VALUES (?, ?, 'assistant', ?)",
                (request.userId, request.roleName, ai_reply)
            )
            conn.commit()

            return {"reply": ai_reply, "audio": audio_base64}
            
    except Exception as e:
        print(f"[Chat Exception] {e}")
        return {"reply": "哎呀，我的大脑刚才短路了... (服务器错误)", "audio": None}

if __name__ == "__main__":
    # 启动服务器
    uvicorn.run(app, host="127.0.0.1", port=8000)