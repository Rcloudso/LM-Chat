import json
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import httpx
import uvicorn
from pydantic import BaseModel
from typing import List, Optional
import os

app = FastAPI(title="LM Studio Chat Interface")

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="static"), name="static")

# 设置模板目录
templates = Jinja2Templates(directory="templates")

# 默认LM Studio API地址
DEFAULT_API_BASE = "http://127.0.0.1:1234/v1"

# 配置LM Studio API地址
api_base = os.environ.get("LM_STUDIO_API_BASE", DEFAULT_API_BASE)


# 定义消息模型
class Message(BaseModel):
    role: str
    content: str


# 构建聊天请求
class ChatRequest(BaseModel):
    messages: List[Message]
    model: str = "QwQ"
    temperature: float = 0.7
    max_tokens: int = 4096
    stream: bool = False


# 构建聊天响应
class ChatResponse(BaseModel):
    choices: List[dict]


# 首页路由
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


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
                    # error_detail = await response.aread()
                    # error_detail = error_detail.decode() if isinstance(error_detail, bytes) else error_detail
                    # yield f'data: {{"error": "API返回错误: {response.status_code} - {error_detail}"}}\n\n'
                    # yield 'data: [DONE]\n\n'
                    # return

                    # 处理流式数据
                    async for chunk in response.aiter_lines():
                        chunk = chunk.strip()
                        if chunk.startswith('data: '):
                            chunk = chunk[len('data: '):]
                        if chunk == "[DONE]":
                            break  # 结束流
                        try:
                            data = json.loads(chunk)
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
                resp.raise_for_status()  # 自动处理非200状态码
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
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive"
            }
        )
    else:
        result = await get_no_stream()
        return result


# 启动服务器
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
