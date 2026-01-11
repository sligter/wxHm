# wxHm - WeChat LiveCode Manager Dockerfile
# 基于 Python 3.11 官方镜像

FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p uploads logs

# 暴露端口
EXPOSE 8092

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8092/', timeout=5)" || exit 1

# 启动命令 - 使用 gunicorn
CMD ["gunicorn", "--workers", "1", "--bind", "0.0.0.0:8092", "--access-logfile", "logs/access.log", "--error-logfile", "logs/error.log", "app:app"]
