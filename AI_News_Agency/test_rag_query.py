# 路径：AI_News_Agency/test_rag_query.py
import chromadb
import logging
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
import dashscope

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger("RAG_Test")


# ================= 同步引入阿里云 Embedding 适配器 =================
class DashScopeEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        resp = dashscope.TextEmbedding.call(
            model=dashscope.TextEmbedding.Models.text_embedding_v4,
            input=input
        )
        if resp.status_code == 200:
            return [item['embedding'] for item in resp.output['embeddings']]
        else:
            raise Exception("DashScope API 报错，请检查 API KEY 或网络。")


def test_terminology_retrieval():
    logger.info("🔍 正在连接 V4 版高级本地知识库...")

    # 注意路径变了，连到我们新炼制的 v4 数据库
    client = chromadb.PersistentClient(path="./agency_db_v4")
    aliyun_ef = DashScopeEmbeddingFunction()

    try:
        # 获取集合时，必须带上翻译官
        collection = client.get_collection(
            name="ai_terminology",
            embedding_function=aliyun_ef
        )
        logger.info(f"✅ 成功连接集合！当前知识库中共包含 {collection.count()} 条专业术语。")
    except Exception as e:
        logger.error("❌ 找不到集合，请确认是否已运行新版的 init_knowledge_base.py！")
        return

    test_queries = [
        "这条新闻提到了模型采用了 MoE 架构，这是什么意思？",
        "什么是 RAG 技术？",
        "新闻里说这家公司的模型上下文窗口很大，有何优势？",
        "和算力无关的测试：什么是草莓？"
    ]

    logger.info("\n" + "=" * 50)
    logger.info("🚀 启动语义检索测试 (引擎: text-embedding-v4, Top-K = 1)")
    logger.info("=" * 50)

    for query in test_queries:
        logger.info(f"❓ 【模拟查询】: {query}")

        results = collection.query(
            query_texts=[query],
            n_results=1
        )

        documents = results['documents'][0]
        distances = results['distances'][0]

        if documents:
            distance = distances[0]
            # ✨ 核心魔法：设置严格的阈值卡点！
            # 只有当距离小于 0.88 时，我们才认为它是真正的“命中”
            if distance < 0.88:
                logger.info(f"💡 【精准命中】: {documents[0]}")
                logger.info(f"📏 【向量距离】: {distance:.4f} (小于阈值 0.88，通过！)")
            else:
                logger.warning(f"⚠️ 找到一条数据，但距离为 {distance:.4f} (大于阈值 0.88)。判定为不相关，已抛弃！")
        else:
            logger.warning("⚠️ 数据库为空。")

        logger.info("-" * 50)


if __name__ == "__main__":
    test_terminology_retrieval()