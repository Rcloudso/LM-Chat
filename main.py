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

# 聊天API端点
@app.post("/api/chat")
async def chat(chat_request: ChatRequest):
    try:
        async with httpx.AsyncClient() as client:
            if chat_request.stream:
                # 流式响应处理
                async with client.stream(
                    'POST',
                    f"{api_base}/chat/completions",
                    json=chat_request.dict(),
                    timeout=None
                ) as response:
                    if response.status_code != 200:
                        raise HTTPException(status_code=response.status_code, detail=f"LM Studio API error: {response.text}")
                    # async for chunk in response.aiter_lines():
                    # 有值，可以正常输出
                    #     print(chunk)
                    # str类型
                    #     print(type(chunk))
                    from fastapi.responses import StreamingResponse
                    async def generate():
                        try:
                            async for chunk in response.aiter_lines():
                                chunk = chunk.replace("data: ", "")
                                try:
                                    data = json.loads(chunk)
                                    if not isinstance(data, dict):
                                        print(f"Invalid data format: expected dict, got {type(data)}")
                                        continue
                                    if 'choices' not in data:
                                        print(f"Missing 'choices' in response data")
                                        continue
                                    yield f"data: {chunk}\n\n"
                                except json.JSONDecodeError as e:
                                    print(f"JSON parsing error: {str(e)} in chunk: {chunk}")
                                except httpx.StreamClosed:
                                    print("Stream connection closed during data processing")
                                    break
                        except httpx.StreamClosed as e:
                            error_msg = f"Stream connection closed: {str(e)}"
                            yield f'data: {{"error": "{error_msg}"}}\n\n'
                        except Exception as e:
                            error_msg = f"Unexpected streaming error: {str(e)}"
                            yield f'data: {{"error": "{error_msg}"}}\n\n'
                        finally:
                            if not response.is_closed:
                                yield 'data: [DONE]\n\n'
                    
                    return StreamingResponse(
                        generate(),
                        media_type="text/event-stream"
                    )
            else:
                # 非流式响应处理
                response = await client.post(
                    f"{api_base}/chat/completions",
                    json=chat_request.dict(),
                    timeout=None
                )
                if response.status_code != 200:
                    raise HTTPException(status_code=response.status_code, detail=f"LM Studio API error: {response.text}")
                
                response_data = response.json()
                if not isinstance(response_data, dict) or 'choices' not in response_data:
                    raise HTTPException(status_code=500, detail="Invalid response format from LM Studio API")
                
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
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Error communicating with LM Studio API: {str(e)}")

# 启动服务器
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)