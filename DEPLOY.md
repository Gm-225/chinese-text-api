# Chinese Text Intelligence API - 部署与上架指南

## 产品概述

中文文本智能分析 API：一次调用，返回情感分析、关键词提取、文本摘要、自动分类、文本统计。

## API 端点

| 端点 | 方法 | 功能 | 免费额度 | 付费额度 |
|---|---|---|---|---|
| /analyze | POST | 全量分析 | 100次/月 | 1000-10000次/月 |
| /sentiment | POST | 情感分析 | 100次/月 | 同上 |
| /keywords | POST | 关键词提取 | 100次/月 | 同上 |
| /summarize | POST | 文本摘要 | 100次/月 | 同上 |
| /batch-sentiment | POST | 批量情感 | 50次/月 | 500-5000次/月 |
| /health | GET | 健康检查 | 无限 | 无限 |

## RapidAPI 定价方案

- **Free**: $0/月 → 100 requests/month
- **Basic**: $9.99/月 → 1,000 requests/month
- **Pro**: $29.99/月 → 10,000 requests/month
- **Enterprise**: $99.99/月 → 100,000 requests/month

## 部署步骤（Railway.app 免费方案）

1. 注册 railway.app（GitHub 登录）
2. New Project → Deploy from GitHub repo
3. 上传代码到 GitHub 仓库
4. Railway 自动检测 FastAPI 并部署
5. 获取公网 URL → 填入 RapidAPI

## RapidAPI 上架步骤

1. 注册 rapidapi.com
2. Add New API → 填入基本信息
3. Base URL 填 Railway 部署地址
4. 添加 Endpoints（用 /analyze 等）
5. 设置定价方案
6. 提交审核（1-3 天）
7. 上线开始赚钱

## 技术栈

- FastAPI (Python 3.11+)
- jieba（分词）
- SnowNLP（情感分析）
- uvicorn（服务器）
- 零外部 API 依赖 = 零运行成本
