# -*- coding: utf-8 -*-
"""
Chinese Text Intelligence API - 中文文本智能分析
Endpoints:
  POST /analyze   - 全量分析（情感+关键词+摘要+分类）
  POST /sentiment - 情感分析
  POST /keywords  - 关键词提取
  POST /summarize - 文本摘要
  GET  /health    - 健康检查
"""
import math
import re
from collections import Counter

import jieba
import jieba.analyse
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from snownlp import SnowNLP

app = FastAPI(
    title="Chinese Text Intelligence API",
    description="中文文本智能分析：情感分析、关键词提取、文本摘要、自动分类。支持简体/繁体中文。",
    version="1.0.0",
)


class TextInput(BaseModel):
    text: str = Field(..., min_length=1, max_length=50000, description="待分析的中文文本")
    top_k: int = Field(default=10, ge=1, le=50, description="关键词/摘要返回数量")


class BatchInput(BaseModel):
    texts: list = Field(..., min_length=1, max_length=100, description="批量文本列表")
    top_k: int = Field(default=10, ge=1, le=50)


def get_sentiment(text: str) -> dict:
    """情感分析：返回正负面分数"""
    s = SnowNLP(text)
    score = s.sentiments  # 0~1，越接近1越正面
    if score > 0.7:
        label = "positive"
    elif score < 0.3:
        label = "negative"
    else:
        label = "neutral"
    return {
        "label": label,
        "positive_score": round(score, 4),
        "negative_score": round(1 - score, 4),
        "confidence": round(abs(score - 0.5) * 2, 4),
    }


def get_keywords(text: str, top_k: int = 10) -> list:
    """关键词提取：TF-IDF + TextRank 双算法"""
    tfidf = jieba.analyse.extract_tags(text, topK=top_k, withWeight=True)
    textrank = jieba.analyse.textrank(text, topK=top_k, withWeight=True)
    return [
        {
            "keyword": w,
            "tfidf_score": round(w1, 4),
            "textrank_score": round(dict(textrank).get(w, 0), 4),
        }
        for w, w1 in tfidf
    ]


def get_summary(text: str, top_k: int = 3) -> str:
    """文本摘要：提取关键句（容错版）"""
    try:
        # 先分句
        sentences = re.split(r"[。！？!?；;\n]", text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
        if len(sentences) <= top_k:
            return text[:200]
        # 用 jieba 关键词匹配度选关键句
        keywords = set(jieba.analyse.extract_tags(text, topK=10))
        scored = []
        for i, sent in enumerate(sentences):
            sent_words = set(jieba.cut(sent))
            overlap = len(keywords & sent_words)
            scored.append((overlap, i, sent))
        scored.sort(key=lambda x: (-x[0], x[1]))
        top_sentences = [s for _, _, s in scored[:top_k]]
        return "。".join(top_sentences) + "。"
    except Exception:
        return text[:200]


def get_category(text: str) -> dict:
    """简单文本分类"""
    categories = {
        "ecommerce": ["购买", "价格", "优惠券", "打折", "物流", "快递", "商品", "店铺", "评价", "退货"],
        "social_media": ["转发", "点赞", "关注", "粉丝", "视频", "直播", "热门", "话题", "博主"],
        "news": ["报道", "记者", "消息", "据悉", "新闻", "发布", "声明", "宣布", "记者会"],
        "finance": ["股票", "基金", "投资", "理财", "涨跌", "股市", "债券", "汇率", "利率"],
        "tech": ["AI", "人工智能", "算法", "模型", "编程", "代码", "软件", "互联网", "大数据"],
        "education": ["学习", "考试", "课程", "培训", "教育", "学生", "老师", "成绩", "作业"],
        "travel": ["旅游", "景点", "酒店", "机票", "攻略", "行程", "出行", "打卡"],
        "food": ["美食", "餐厅", "菜", "好吃", "味道", "推荐", "菜谱", "厨师"],
        "health": ["健康", "医生", "医院", "药品", "治疗", "症状", "诊断", "保健"],
    }
    scores = {}
    for cat, keywords in categories.items():
        score = sum(1 for kw in keywords if kw in text)
        scores[cat] = score
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return {"category": "general", "confidence": 0.0}
    return {
        "category": best,
        "confidence": round(scores[best] / max(1, sum(scores.values())), 4),
        "all_scores": {k: v for k, v in sorted(scores.items(), key=lambda x: x[1], reverse=True) if v > 0}
    }


def get_stats(text: str) -> dict:
    """文本基础统计"""
    words = list(jieba.cut(text))
    words_no_punct = [w for w in words if w.strip() and w not in "，。！？、；：""''（）\n\r\t "]
    return {
        "total_chars": len(text),
        "total_words": len(words_no_punct),
        "unique_words": len(set(words_no_punct)),
        "sentences": len(re.split(r"[。！？!?]", text)) - 1,
        "reading_time_seconds": math.ceil(len(words_no_punct) / 5 * 60),  # 假设每分钟300字
    }


@app.get("/health")
async def health():
    return {"status": "ok", "service": "chinese-text-intelligence", "version": "1.0.0"}


@app.post("/analyze")
async def analyze(input_data: TextInput):
    """全量分析：情感+关键词+摘要+分类+统计"""
    text = input_data.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="文本不能为空")

    return {
        "sentiment": get_sentiment(text),
        "keywords": get_keywords(text, input_data.top_k),
        "summary": get_summary(text, min(input_data.top_k, 5)),
        "category": get_category(text),
        "stats": get_stats(text),
    }


@app.post("/sentiment")
async def sentiment(input_data: TextInput):
    """仅情感分析"""
    return get_sentiment(input_data.text)


@app.post("/keywords")
async def keywords(input_data: TextInput):
    """仅关键词提取"""
    return {"keywords": get_keywords(input_data.text, input_data.top_k)}


@app.post("/summarize")
async def summarize(input_data: TextInput):
    """仅文本摘要"""
    return {"summary": get_summary(input_data.text, min(input_data.top_k, 5))}


@app.post("/batch-sentiment")
async def batch_sentiment(input_data: BatchInput):
    """批量情感分析"""
    results = []
    for text in input_data.texts:
        results.append(get_sentiment(text))
    return {"results": results, "count": len(results)}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8899)
