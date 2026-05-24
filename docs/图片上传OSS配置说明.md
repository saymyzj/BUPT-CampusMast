# 图片上传 OSS 配置说明

## 当前上传链路

发布任务页的图片上传采用“前端直传 OSS”的设计：

1. 用户在前端选择 JPG / PNG 图片。
2. 前端请求后端 `POST /api/upload/sign`。
3. 后端根据 OSS 配置生成预签名上传地址 `uploadUrl`，同时返回最终访问地址 `fileUrl`。
4. 前端使用 `PUT` 将图片直接上传到 `uploadUrl`。
5. 上传成功后，发布任务时把 `fileUrl` 数组作为 `imageUrls` 提交。
6. 数据库只保存图片 URL 列表，不保存图片二进制内容。

对应存储结构：

- 图片文件：阿里云 OSS Bucket。
- 任务表：`tasks.image_urls`，以 JSON 字符串形式保存 URL 数组。
- 前端字段：`CreateTaskRequest.imageUrls?: string[]`。

## 当前报错原因

浏览器报错示例：

```text
Access to fetch at 'https://campusmast-dev.oss-cn-hangzhou.aliyuncs.com/...' from origin 'http://localhost:5173' has been blocked by CORS policy
OSSAccessKeyId=replace-me
```

这里有两个关键信息：

- `OSSAccessKeyId=replace-me` 表示后端使用的 OSS AccessKey 仍是占位值，不是真实密钥。
- CORS 报错表示浏览器从 `http://localhost:5173` 向 OSS 发起 `PUT` 直传时，OSS Bucket 没有允许该来源跨域上传。

因此，图片上传失败不是发布任务接口的问题，而是 OSS 签名配置和 Bucket 跨域配置尚未完成。

## 需要配置的后端环境变量

后端需要配置真实 OSS 参数：

```env
OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
OSS_BUCKET_NAME=campusmast-dev
OSS_ACCESS_KEY_ID=真实 AccessKey ID
OSS_ACCESS_KEY_SECRET=真实 AccessKey Secret
OSS_BASE_URL=https://campusmast-dev.oss-cn-hangzhou.aliyuncs.com
```

注意：

- `replace-me` 只能作为本地占位，不能用于真实上传。
- 修改配置后需要重启后端服务。
- 当前代码已把 `replace-me` 识别为未配置，避免生成看似真实但必然失败的 OSS 签名。

## 需要配置的 OSS CORS

在阿里云 OSS Bucket 的跨域设置中增加规则。

本地开发至少需要：

```text
AllowedOrigin: http://localhost:5173
AllowedMethod: PUT, GET, OPTIONS
AllowedHeader: *
ExposeHeader: ETag
```

上线后还需要把生产前端域名加入 `AllowedOrigin`，例如：

```text
AllowedOrigin: https://你的生产前端域名
```

## 判断是否配置成功

配置完成并重启后端后，重新上传图片：

- 签名 URL 中不应再出现 `OSSAccessKeyId=replace-me`。
- 浏览器控制台不应再出现 OSS CORS preflight 报错。
- 图片上传成功后，发布任务请求体中应包含 `imageUrls`。
- 任务详情或列表读取任务数据时，应能拿到对应 `imageUrls`。

## 本地开发行为

如果 OSS 未配置，后端会返回 mock 上传地址，前端不会真正上传文件到阿里云，但会保留页面预览和流程联调能力。

这只适合本地开发，不代表图片文件已经真实持久化。
