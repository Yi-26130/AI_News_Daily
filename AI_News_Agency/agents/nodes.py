# 路径：AI_News_Agency/agents/nodes.py (部分代码更新)
# 路径：AI_News_Agency/agents/nodes.py (加在文件开头)
import hashlib
import chromadb
import dashscope
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings

# 实例化阿里云翻译官
class DashScopeEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        resp = dashscope.TextEmbedding.call(
            model=dashscope.TextEmbedding.Models.text_embedding_v4,
            input=input
        )
        if resp.status_code == 200:
            return [item['embedding'] for item in resp.output['embeddings']]
        else:
            raise Exception("DashScope API 报错")
import os
import logging
import concurrent.futures
from typing import List
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

from prompts import CHECKER_PROMPT, WRITER_PROMPT
from state import AgencyState, NewsItem  # ✨ 记得导入 NewsItem
from tools.rss_scraper import fetch_tech_news

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AI_Agency")

llm = ChatOpenAI(model="qwen3-max", base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")


class NewsEvaluation(BaseModel):
    score: int = Field(description="新闻的AI相关度与重要性综合得分 (0-10分)")
    reasoning: str = Field(description="打分理由，限50字")


# ================= 部门 A：采编部 (核心重构：边界防御) =================
def researcher_node(state: AgencyState):
    logger.info("👨‍🔬 [采编部] 收到 CEO 指令！正在启动定向雷达获取海量原始数据...")

    # 1. 获取野生字典列表
    raw_news_dicts = fetch_tech_news.invoke({"max_news_per_source": 15})

    # 2. ✨ 核心排雷：在此处将野生字典全部实例化为正规的 NewsItem 对象
    news_pool = []
    for item in raw_news_dicts:
        try:
            # 使用解包语法 **item 将字典转化为 Pydantic 对象
            news_obj = NewsItem(**item)
            news_pool.append(news_obj)
        except Exception as e:
            # 容错：如果某个新闻缺胳膊少腿，直接丢弃，不影响全局
            logger.warning(f"⚠️ [采编部] 抛弃一条格式损坏的脏数据: {e}")

    logger.info(f"👨‍🔬[采编部] 格式化完毕，共 {len(news_pool)} 条标准新闻存入新闻池。")
    return {"news_pool": news_pool}


# 路径：AI_News_Agency/agents/nodes.py

# ================= 部门 B：初筛部 (修复版：恢复多线程打分) =================
def filter_node(state: AgencyState):
    logger.info("🪲 [初筛部] 正在用多线程过滤垃圾新闻，提取 Top 10...")
    news_pool = state.get("news_pool", [])

    if not news_pool:
        logger.warning("⚠️ [初筛部] 新闻池为空，无需打分！")
        return {"top_news": []}

    # 声明结构化输出
    evaluator_llm = llm.with_structured_output(NewsEvaluation)

    def evaluate_single_news(news: NewsItem) -> NewsItem:
        prompt = f"""
        你现在是一个初级新闻筛选员。
        请评估以下新闻与AI科技的相关度与重要性。
        新闻标题：{news.title}
        新闻摘要：{news.summary}
        """
        try:
            result = evaluator_llm.invoke(prompt)
            news.score = result.score
            news.reasoning = result.reasoning
            return news
        except Exception as e:
            logger.error(f"❌ [初筛部] 评估 {news.title[:10]} 时出错: {e}")
            news.score = 0
            return news

    # 启动并发打分
    scored_news_list = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(evaluate_single_news, news_pool)
        for evaluated_news in results:
            scored_news_list.append(evaluated_news)

    # 排序并提取 Top 10
    scored_news_list.sort(key=lambda x: x.score, reverse=True)
    top_news = scored_news_list[:10]

    logger.info(f"🪲 [初筛部] 筛选完毕！成功提取 {len(top_news)} 条 Top 10 情报移交专家团。")
    return {"top_news": top_news}


# ================= 🔥 部门 C1：专家圆桌 - 极客特工 =================
def geek_node(state: AgencyState):
    logger.info("🤓 [极客特工] 正在从技术原教旨主义角度审视新闻...")
    top_news = state.get("top_news", [])
    news_str = "\n".join([f"标题: {n.title}\n摘要: {n.summary}" for n in top_news])

    prompt = f"你是冷酷的AI极客特工。请从技术突破、架构创新、算力需求等硬核角度，点评以下今天的新闻。语言要极客、犀利，不超过300字：\n{news_str}"

    try:
        response = llm.invoke(prompt)
        return {"geek_opinion": response.content}
    except Exception as e:
        logger.error(f"极客特工宕机: {e}")
        return {"geek_opinion": "技术评估失败。"}


# ================= 🔥 部门 C2：专家圆桌 - 风投巨鳄 =================
def vc_node(state: AgencyState):
    logger.info("💰 [风投巨鳄] 正在评估这些技术的商业变现与资本价值...")
    top_news = state.get("top_news", [])
    news_str = "\n".join([f"标题: {n.title}\n摘要: {n.summary}" for n in top_news])

    prompt = f"你是华尔街顶级AI风投。请从商业化落地、公司估值、行业洗牌的角度，点评以下今天的新闻。满眼都是钱，语言要充满资本气息，不超过300字：\n{news_str}"

    try:
        response = llm.invoke(prompt)
        return {"vc_opinion": response.content}
    except Exception as e:
        logger.error(f"风投巨鳄宕机: {e}")
        return {"vc_opinion": "商业评估失败。"}


# ================= 🔥 部门 C3：专家圆桌 - 伦理反思者 =================
def public_node(state: AgencyState):
    logger.info("🛡️ [伦理反思者] 正在凝视深渊，分析技术对社会造成的冲击...")
    top_news = state.get("top_news", [])
    news_str = "\n".join([f"标题: {n.title}\n摘要: {n.summary}" for n in top_news])

    prompt = f"你是人文主义者兼伦理学家。请从隐私泄露、AI失控、普通人失业等角度，对以下新闻提出尖锐的质疑或警告。不要被技术的狂热冲昏头脑，不超过300字：\n{news_str}"

    try:
        response = llm.invoke(prompt)
        return {"public_opinion": response.content}
    except Exception as e:
        logger.error(f"伦理反思者宕机: {e}")
        return {"public_opinion": "伦理评估失败。"}


# ================= 🔥 部门 D：总编室 =================
def chief_editor_node(state: AgencyState):
    logger.info("⚖️ [总编室] 正在汇总三方激烈辩论，敲定今日通讯社最终调性...")

    prompt = f"""
    你是《AI科技通讯社》的总编。请阅读今天三位专家的激烈辩论报告：
    【极客意见】：{state.get('geek_opinion')}
    【风投意见】：{state.get('vc_opinion')}
    【伦理意见】：{state.get('public_opinion')}

    请你融合这三方的观点，写一段 400 字左右的《今日通讯社定调指南》。
    这份指南将直接发给撰稿部，指导他们写出具有极高深度、多维视角的终稿文章。
    """
    try:
        response = llm.invoke(prompt)
        logger.info("⚖️ [总编室] 定调指南生成完毕！")
        return {"expert_debate_summary": response.content}
    except Exception as e:
        logger.error(f"总编室宕机: {e}")
        return {"expert_debate_summary": "请自由发挥。"}


# ⚠️ [撰稿部 writer_node 更新说明]：
# 请在 writer_node 的 prompt 组装时，把总编的定调加进去：
# prompt = WRITER_PROMPT.format(..., expert_debate_summary=state.get("expert_debate_summary"))
# （撰稿部 writer_node 和质检部 checker_node 暂时不需要大动，因为我们已经保证了 top_news 里装的全是精美的 NewsItem 对象了）

# 路径：AI_News_Agency/agents/nodes.py (替换原有的 writer_node)

# ================= 部门 E：撰稿部 (RAG 升级版 & 修复状态流转与计数) =================
def writer_node(state: AgencyState):
    logger.info("✍️ [撰稿部] 正在根据专家定调撰写深度初稿...")
    top_news_list = state.get("top_news", [])

    # ✨ 核心修复 1：读取当前系统里的循环次数，拿个计步器
    current_loop = state.get("loop_count", 0)

    if not top_news_list:
        logger.warning("⚠️ [撰稿部] 没有收到任何精选新闻，将输出空报告。")
        # ⚠️ 务必使用 draft_report
        return {"draft_report": "今日无值得关注的高价值 AI 新闻。", "loop_count": current_loop + 1}

    formatted_news = "\n".join([
        f"【标题】{news.title}\n【链接】{news.link}\n【摘要】{news.summary}\n【核心价值】{news.reasoning}"
        for news in top_news_list
    ])

    # --- RAG 检索启动 ---
    logger.info("📚 [撰稿部] 正在向 ChromaDB 向量库请教专业术语...")
    glossary_text = "今日新闻未触发专业术语注释。"
    try:
        client = chromadb.PersistentClient(path="./agency_db_v4")
        aliyun_ef = DashScopeEmbeddingFunction()
        collection = client.get_collection(name="ai_terminology", embedding_function=aliyun_ef)

        search_query = "\n".join([f"{n.title} {n.summary}" for n in top_news_list])
        results = collection.query(query_texts=[search_query[:1000]], n_results=3)

        hit_terms = []
        for doc, dist in zip(results['documents'][0], results['distances'][0]):
            if dist < 0.88:  # 严格防盗门过滤幻觉
                hit_terms.append(f"- {doc}")

        if hit_terms:
            glossary_text = "\n".join(hit_terms)
            logger.info(f"💡 [撰稿部] RAG 命中！成功提取到 {len(hit_terms)} 条术语解释，准备注入稿件！")
        else:
            logger.info("🤖 [撰稿部] 新闻中未检测到资料库中存在的术语。")
    except Exception as e:
        logger.warning(f"⚠️ [撰稿部] 术语库检索失败，将跳过注释环节。原因: {e}")
    # --- RAG 检索结束 ---

    prompt = WRITER_PROMPT.format(
        current_date=state.get("date", "未知日期"),
        raw_news=formatted_news,
        feedback=state.get("review_feedback", "无"),
        expert_debate_summary=state.get("expert_debate_summary", "今日无特定调性。"),
        terminology_glossary=glossary_text
    )

    try:
        response = llm.invoke(prompt)
        final_draft = response.content
        logger.info(f"✍️ [撰稿部] 初稿撰写完毕，字数：{len(final_draft)} 字，已移交质检部！")

        # ✨ 核心修复 2：将写好的文章放入 draft_report，同时将工作次数 + 1 汇报上去！
        return {
            "draft_report": final_draft,
            "loop_count": current_loop + 1
        }
    except Exception as e:
        logger.error(f"❌ [撰稿部] 撰稿失败: {e}")
        return {
            "draft_report": "撰稿过程中发生错误。",
            "loop_count": current_loop + 1
        }


# ================= 部门 F：质检部 (对象化与健壮性重构版) =================
def checker_node(state: AgencyState):
    logger.info("🔎 [质检部] 正在进行严苛的事实核查（Fact-Checking）...")

    top_news_list = state.get("top_news", [])

    # ✨ 扫雷重点：同理，改为面向对象属性访问
    formatted_news = "\n".join([f"标题: {n.title} \n摘要: {n.summary}" for n in top_news_list])

    prompt = CHECKER_PROMPT.format(
        raw_news=formatted_news,
        draft_report=state.get("draft_report", "")
    )

    try:
        response = llm.invoke(prompt)
        feedback = response.content
    except Exception as e:
        logger.error(f"❌ [质检部] 呼叫事实核查模型失败: {e}")
        # 如果质检员断联，为了安全起见，强制打回
        return {"review_feedback": f"质检系统异常，强制打回重写。报错: {str(e)}"}

    if "通过" in feedback:
        logger.info("✅ [质检部] 审核通过！没有任何幻觉与捏造，准许发布！")
        return {"review_feedback": "PASS", "final_publish": state["draft_report"]}
    else:
        logger.warning(f"❌ [质检部] 警报！发现违规或幻觉！打回意见：{feedback}")
        return {"review_feedback": feedback}



# ================= 部门 G：档案局 (自动归档与去重) =================
def archive_node(state: AgencyState):
    logger.info("🗄️ [档案局] 正在将今日情报刻入永久历史记忆库...")
    top_news_list = state.get("top_news", [])

    if not top_news_list:
        logger.info("🤖 [档案局] 今日无新闻可归档。")
        return {}  # 不改变任何状态，直接放行

    try:
        # 1. 连接我们的 v4 数据库
        client = chromadb.PersistentClient(path="./agency_db_v4")
        aliyun_ef = DashScopeEmbeddingFunction()

        # 2. 注意！这里我们新建一个集合叫 historical_news（历史新闻库）
        # 千万别和术语库(ai_terminology)混在一起！
        collection = client.get_or_create_collection(
            name="historical_news",
            embedding_function=aliyun_ef,
            metadata={"description": "AI科技通讯社的历史新闻档案库"}
        )

        documents = []
        metadatas = []
        ids = []

        # 3. 遍历今天的 Top 10 新闻，准备入库
        for news in top_news_list:
            # ✨ 核心去重魔法：将 URL 转化为全球唯一的 MD5 身份证号！
            url_hash = hashlib.md5(news.link.encode('utf-8')).hexdigest()

            # 组装我们要让 RAG 记住的文本（包含标题、摘要和专家视角的深刻洞察）
            doc_text = f"【新闻标题】{news.title}\n【深度摘要】{news.summary}\n【专家洞察】{news.reasoning}"

            documents.append(doc_text)

            # 打上元数据标签，方便未来按日期过滤
            metadatas.append({
                "title": news.title,
                "url": news.link,
                "date": state.get("date", "未知日期"),
                "type": "news_archive"
            })

            # 绑定 ID
            ids.append(f"news_{url_hash}")

        # 4. 执行 Upsert（有则更新，无则插入，完美防重！）
        if ids:
            collection.upsert(documents=documents, metadatas=metadatas, ids=ids)
            logger.info(f"✅ [档案局] 成功将 {len(ids)} 条新闻并入历史档案库！(已自动过滤重复项)")

    except Exception as e:
        logger.error(f"❌ [档案局] 归档过程发生致命错误: {e}")

    # 档案局是一个“旁路节点”，只干活不改变工作流状态，原样返回 state
    return {}

# ================= 交警（路由） =================
def route_checker(state: AgencyState):
    # 通过了，或者重写了超过3次（防破产），不要直接下班，去档案局归档！
    if state["review_feedback"] == "PASS" or state["loop_count"] >= 3:
        return "archive_node"  # ✨ 核心修改：将 END 改为 archive_node
    return "writer_node"