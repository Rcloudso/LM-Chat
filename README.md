# LM Studio 本地大模型对话应用

这是一个使用FastAPI构建的Web应用，用于与本地运行的LM Studio API进行交互，实现本地大模型的对话功能。

## 功能特点

- 简洁美观的用户界面
- 支持调整模型参数（温度、最大生成长度）
- 支持流式输出（需LM Studio API支持）
- 保存对话历史

## 安装要求

- Python 3.8+
- LM Studio 应用（需要在本地运行并启用API服务）

## 安装步骤

1. 克隆或下载本仓库
2. 安装依赖包：

```bash
pip install -r requirements.txt
```

## 使用方法

1. 确保LM Studio已在本地运行，并已启用API服务（默认端口为1234）
2. 启动Web应用：

```bash
python main.py
```

3. 在浏览器中访问：`http://localhost:8000`

## 自定义配置