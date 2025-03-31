import json
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import httpx
import uvicorn
from pydantic import BaseModel
from typing import List, Optional
import os

app = FastAPI(title="LM Studio Chat Interface")

# 添加CORS中间件，允许前端跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境中应该设置为具体的前端URL
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头部
)

# 挂载Vue前端静态文件目录
app.mount("/assets", StaticFiles(directory="vue-frontend/dist/assets"), name="assets")
app.mount("/vite.svg", StaticFiles(directory="vue-frontend/dist", html=False), name="vite_svg")

# 默认LM Studio API地址
DEFAULT_API_BASE = "http://127.0.0.1:1234/v1"

# 配置LM Studio API地址
api_base = os.environ.get("LM_STUDIO_API_BASE", DEFAULT_API_BASE)

# 模型列表, 这里根据.lmstudio_modles里的实际模型修改
models = ["QwQ", "qwen2.5", "deepseek-r1"]

# 定义消息模型
class Message(BaseModel):
    role: str
    content: str


# 构建聊天请求
class ChatRequest(BaseModel):
    messages: List[Message]
    model: str = models[1]
    temperature: float = 0.8
    max_tokens: int = 4096
    stream: bool = False


# 构建聊天响应
class ChatResponse(BaseModel):
    choices: List[dict]


@app.post("/api/chat")
async def chat(chat_request: ChatRequest):
    from starlette.responses import StreamingResponse
    async def generate_stream():
        async with httpx.AsyncClient() as client:
            try:
                async with client.stream(
                        'POST',
                        f"{api_base}/chat/completions",
                        json=chat_request.dict(),
                        timeout=None
                ) as response:
                    # 检查响应状态码
                    response.raise_for_status()

                    # 处理流式数据
                    async for chunk in response.aiter_lines():
                        chunk = chunk.strip()
                        if chunk.startswith('data: '):
                            chunk = chunk[len('data: '):]
                            try:
                                data = json.loads(chunk)
                                # 检查delta是否为空对象
                                if data.get('choices', [{}])[0].get('delta', None) == {}:
                                    break
                                yield f"data: {json.dumps(data)}\n\n"
                            except json.JSONDecodeError as e:
                                yield f'data: {{"error": "JSON解析失败: {str(e)}"}}\n\n'
            except httpx.RequestError as e:
                yield f'data: {{"error": "请求异常: {str(e)}"}}\n\n'
            except Exception as e:
                yield f'data: {{"error": "未知错误: {str(e)}"}}\n\n'
            finally:
                yield 'data: [DONE]\n\n'

    async def get_no_stream():
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    f"{api_base}/chat/completions",
                    json=chat_request.dict(),
                    timeout=120  # 非流式建议设置合理超时
                )
                resp.raise_for_status()
                response_data = resp.json()
                choices = response_data['choices']
                if not choices:
                    return {"choices": []}

                processed_choices = []
                for choice in choices:
                    if 'message' in choice and 'content' in choice['message']:
                        processed_choices.append({
                            "message": {
                                "role": choice['message'].get('role', 'assistant'),
                                "content": choice['message']['content']
                            },
                            "index": choice.get('index', 0),
                            "finish_reason": choice.get('finish_reason', None)
                        })

                return {"choices": processed_choices}

            except httpx.HTTPStatusError as e:
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"上游API错误: {e.response.text}"
                )

    if chat_request.stream:
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream"
        )
    else:
        result = await get_no_stream()
        return result


# 挂载Vue前端静态文件目录（放在API路由之后）
app.mount("/", StaticFiles(directory="vue-frontend/dist", html=True), name="vue_frontend")

# 启动服务器
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
