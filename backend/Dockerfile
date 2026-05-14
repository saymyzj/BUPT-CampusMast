# -----------------------------------------------------------------------------
# 文件说明：
# 这是后端服务的生产镜像构建文件。
# 它用于把 FastAPI 应用打包成可直接在单台 Linux 云服务器或容器环境中运行的镜像，
# 与 `docker-compose.prod.yml` 配合后即可完成后端部署。
# -----------------------------------------------------------------------------

FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY backend /app

EXPOSE 9000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9000"]

