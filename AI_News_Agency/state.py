# 路径：AI_News_Agency/state.py
from typing import TypedDict, List
from pydantic import BaseModel, Field


# 💡 我们的标准“集装箱”：任何新闻进入公司，必须装进这个箱子里
class NewsItem(BaseModel):
    title: str = Field(description="新闻标题")
    link: str = Field(description="新闻原始链接")
    summary: str = Field(description="新闻摘要")
    source: str = Field(description="新闻来源", default="未知")

    # 评分字段（主编部填写）
    score: float = Field(description="新闻重要性得分（0-10）", default=0.0)
    reasoning: str = Field(description="打分理由或多角色评估意见", default="")


# 路径：AI_News_Agency/state.py
class AgencyState(TypedDict):
    date: str
    news_pool: List[NewsItem]
    top_news: List[NewsItem]
    historical_context: str
    terminology_glossary: str

    # 🔥 [新增] 多智能体辩论报告槽位
    geek_opinion: str  # 极客特工的报告
    vc_opinion: str  # 风投巨鳄的报告
    public_opinion: str  # 吃瓜群众/伦理专家的报告
    expert_debate_summary: str  # 总编的最终定调总结

    draft_report: str
    review_feedback: str
    loop_count: int
    final_publish: str