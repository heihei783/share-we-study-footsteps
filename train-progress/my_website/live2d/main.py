from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from openai import OpenAI
from dotenv import load_dotenv
from typing import Optional
import os
import sqlite3
import uvicorn
import requests
import base64
import urllib3


# --- 配置与初始化 ---

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()
app = FastAPI(title="Live2D AI Backend")

# 增加请求体大小限制 (20MB)
app.state.max_request_size = 50 * 1024 * 1024


@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    if request.headers.get("content-length"):
        content_length = int(request.headers["content-length"])
        if content_length > app.state.max_request_size:
            return JSONResponse(
                status_code=413, content={"reply": "图片太大，请上传小于 10MB 的图片"}
            )
    response = await call_next(request)
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 密钥配置
MY_API2D_KEY = os.getenv("Api_key")
MY_FISH_AUDIO_KEY = os.getenv("Fish_audio_api_key")
MINIMAX_API_KEY = os.getenv("Minimax_api_key")
# 注意：MiniMax 通常需要 Group ID，请在 .env 中设置，或直接填写
MINIMAX_GROUP_ID = os.getenv("Minimax_group_id")

# 初始化 OpenAI 客户端 (API2D 作为备用)
client = OpenAI(api_key=MY_API2D_KEY, base_url="https://oa.api2d.net/v1")

VOICE_MODEL_MAP = {
    "爱丽丝": "e488ebeadd83496b97a3cd472dcd04ab",
    "塔菲": "55b28b196e1c4fff9a55cd32a46eff25",
    "小孩姐": "4ca68a299cb24ae599dbb828dc31a73c",
    "才羽桃": "05c25a82cfe0426ab63d3d71ba8656cf",
    "可莉": "0b8449eb752c4f888f463fc5d2c0db65",
    "丁真": "54a5170264694bfc8e9ad98df7bd89c3",
    "小团团": "0da1e00b71164d8cb3761c714b11da64",
    "曼波": "0f08cacd3e354471a4b94dd00b4cc4a3",
    "东雪莲": "94abfed6539d48d281fdb06dc0e09664",
}

DB_FILE = "chat_history.db"


def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                user_id TEXT, 
                role_name TEXT, 
                role_type TEXT, 
                content TEXT
            )
        """)


init_db()


class ChatRequest(BaseModel):
    message: str = ""
    image: Optional[str] = None
    roleName: str
    userId: str
    voice: Optional[str] = None


# --- 工具函数 ---


def get_minimax_response(messages: list) -> Optional[str]:
    """
    调用 MiniMax V2 接口，支持图文混合输入
    """
    print(f"[MiniMax] 正在尝试调用 MiniMax (支持识图)...")
    url = (
        f"https://api.minimax.chat/v1/text/chatcompletion_v2?GroupId={MINIMAX_GROUP_ID}"
    )
    headers = {
        "Authorization": f"Bearer {MINIMAX_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "abab6.5s-chat",
        "messages": messages,
        "tools": [],
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        res_json = response.json()

        # 检查 MiniMax 业务错误码 (1030: 余额不足, 2013: 账号欠费)
        base_status = res_json.get("base_resp", {}).get("status_code")
        if base_status in [1030, 2013]:
            print(f"[MiniMax] 提示：额度不足或欠费 ({base_status})")
            return None

        if response.status_code == 200:
            return res_json["choices"][0]["message"]["content"]
        else:
            print(f"[MiniMax Error] HTTP {response.status_code}: {res_json}")
            return None
    except Exception as e:
        print(f"[MiniMax Exception] {e}")
        return None


def get_tts_audio(text: str, voice_name: str) -> Optional[str]:
    model_id = VOICE_MODEL_MAP.get(voice_name)
    if not model_id:
        return None
    url = "https://api.rubia.top/v1/tts"
    headers = {
        "Authorization": f"Bearer {MY_FISH_AUDIO_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "reference_id": model_id,
        "format": "mp3",
        "latency": "normal",
    }

    try:
        response = requests.post(
            url, json=payload, headers=headers, timeout=25, verify=False
        )
        if response.status_code == 200:
            return base64.b64encode(response.content).decode("utf-8")
    except Exception as e:
        print(f"[TTS Exception] {e}")
    return None


# --- 路由接口 ---


@app.post("/get_history")
async def get_history(request: ChatRequest):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT role_type, content FROM history WHERE role_name = ? AND user_id = ? ORDER BY id ASC",
                (request.roleName, request.userId),
            )
            rows = cursor.fetchall()
            return {"history": [{"role": r[0], "content": r[1]} for r in rows]}
    except Exception as e:
        return {"history": []}


@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()

            # 1. 获取历史记录
            cursor.execute(
                "SELECT role_type, content FROM history WHERE role_name = ? AND user_id = ? ORDER BY id DESC LIMIT 10",
                (request.roleName, request.userId),
            )
            history_rows = cursor.fetchall()[::-1]

            # 2. 构建基础 Messages (System Prompt)
            system_prompt = f"你现在是{request.roleName}，请用二次元少女语气简短回复。你能看见图片内容并给出回应，多用可爱语言。不要使用颜文字。"
            messages = [{"role": "system", "content": system_prompt}]

            for r in history_rows:
                # 历史记录保持纯文本
                messages.append(
                    {"role": r[0], "content": r[1].replace(" [图片消息]", "")}
                )

            # 3. 处理当前输入 (构造多模态内容)
            # 原始 Base64 图片
            raw_image = request.image or ""

            # GPT-4o 需要带 data:image/jpeg;base64, 前缀
            img_data_with_prefix = raw_image
            if img_data_with_prefix and not img_data_with_prefix.startswith("data:"):
                img_data_with_prefix = f"data:image/jpeg;base64,{img_data_with_prefix}"

            # MiniMax 需要纯 Base64，不要 Data URI 前缀
            img_data_pure_base64 = raw_image
            if img_data_pure_base64 and "base64," in img_data_pure_base64:
                img_data_pure_base64 = img_data_pure_base64.split("base64,")[1]

            # 构建用户消息内容（用于 MiniMax）
            if request.image:
                user_content = [
                    {"type": "text", "text": request.message or "看看这张图"},
                    {"type": "image_url", "image_url": {"url": img_data_pure_base64}},
                ]
            else:
                user_content = request.message

            # 将当前用户输入加入消息队列（用于 MiniMax）
            current_user_msg = {"role": "user", "content": user_content}
            messages.append(current_user_msg)

            # 4. 尝试第一路线：MiniMax (支持识图)
            ai_reply = get_minimax_response(messages)

            # 5. 如果 MiniMax 失败，切换到第二路线：GPT-4o (支持识图)
            if ai_reply is None:
                print("[Chat] MiniMax 无法处理，正在切换至 GPT-4o...")
                try:
                    # GPT-4o 需要带前缀的图片格式，构造新消息
                    if request.image:
                        gpt4o_user_content = [
                            {"type": "text", "text": request.message or "看看这张图"},
                            {
                                "type": "image_url",
                                "image_url": {"url": img_data_with_prefix},
                            },
                        ]
                    else:
                        gpt4o_user_content = request.message

                    gpt4o_messages = [
                        {
                            "role": "system",
                            "content": f"你现在是{request.roleName}，请用二次元少女语气简短回复。你能看见图片内容并给出回应，多用可爱语言。不要使用颜文字。",
                        }
                    ]
                    for r in history_rows:
                        gpt4o_messages.append(
                            {"role": r[0], "content": r[1].replace(" [图片消息]", "")}
                        )
                    gpt4o_messages.append(
                        {"role": "user", "content": gpt4o_user_content}
                    )

                    response = client.chat.completions.create(
                        model="gpt-4o", messages=gpt4o_messages, max_tokens=300
                    )
                    ai_reply = response.choices[0].message.content
                except Exception as e:
                    print(f"[GPT-4o Exception] {e}")
                    ai_reply = "呜呜，我的网络好像坏掉了，晚点再试试吧~"

            # 6. 生成语音与保存记录 (保持原样)
            audio_base64 = (
                get_tts_audio(ai_reply, request.voice) if request.voice else None
            )

            log_text = (request.message or "发送了图片") + (
                " [图片消息]" if request.image else ""
            )
            cursor.execute(
                "INSERT INTO history (user_id, role_name, role_type, content) VALUES (?, ?, 'user', ?)",
                (request.userId, request.roleName, log_text),
            )
            cursor.execute(
                "INSERT INTO history (user_id, role_name, role_type, content) VALUES (?, ?, 'assistant', ?)",
                (request.userId, request.roleName, ai_reply),
            )
            conn.commit()

            return {"reply": ai_reply, "audio": audio_base64}

    except Exception as e:
        import traceback

        traceback.print_exc()
        return {"reply": "服务器酱开小差了...", "audio": None}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
