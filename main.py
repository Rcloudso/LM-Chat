from main_business.app import app
from main_business.models import init_db
import uvicorn


# 初始化应用程序
def init_application():
    init_db()
    return app


app = init_application()

# 启动服务器
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
