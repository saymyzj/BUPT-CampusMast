# -----------------------------------------------------------------------------
# 文件说明：
# 这是前端服务的生产镜像构建文件。
# 它采用多阶段构建：先用 Node 生成静态资源，再用 Nginx 托管构建结果，供反向代理
# 或直接静态访问使用。
# -----------------------------------------------------------------------------

FROM node:20-alpine AS build

WORKDIR /app

COPY frontend/package*.json /app/
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

COPY frontend /app

RUN npm run build

FROM nginx:1.27-alpine

COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
