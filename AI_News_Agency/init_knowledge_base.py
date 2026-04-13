# 路径：AI_News_Agency/init_knowledge_base.py
import os
import json
import logging
import hashlib
import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
import dashscope

# 配置企业级日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Init_RAG_DB")

# ✨✨✨ 终极修复：强行塞入通行证 ✨✨✨
# 请把下面这行里的 sk-... 替换成你真实的阿里云 API_KEY！
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY", "")


# ================= 1. 阿里云 Embedding 适配器 (防弹升级版) =================
class DashScopeEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        if not dashscope.api_key or dashscope.api_key == "sk-请在这里填入你的真实密钥":
            raise Exception("🛑 停！你还没填入真实的 API Key，阿里云拒绝服务！")

        resp = dashscope.TextEmbedding.call(
            model=dashscope.TextEmbedding.Models.text_embedding_v4,
            input=input
        )
        if resp.status_code == 200:
            return [item['embedding'] for item in resp.output['embeddings']]
        else:
            # 这一步极其关键，它会把阿里云报错的真实原因打印出来
            error_msg = f"状态码: {resp.status_code}, 详细原因: {resp.message}"
            logger.error(f"❌ 阿里云接口拒绝访问: {error_msg}")
            raise Exception(f"DashScope API 报错: {error_msg}")


# ...后面的 init_terminology_db_from_json() 代码保持原样不用动...


def init_terminology_db_from_json():
    logger.info("🚀 启动 ChromaDB 知识库海量灌入程序 (引擎: text-embedding-v4)...")

    # ================= 2. 读取本地 JSON 字典 =================
    json_file_path = "ai_terms_batch.json"
    if not os.path.exists(json_file_path):
        logger.error(f"❌ 找不到文件 {json_file_path}！请先创建该文件并填入大模型生成的 JSON 数据！")
        return

    with open(json_file_path, "r", encoding="utf-8") as f:
        try:
            seed_data = json.load(f)
        except json.JSONDecodeError:
            logger.error("❌ JSON 文件格式有误，请确保里面是纯粹的 JSON 数组，没有其他废话。")
            return

    logger.info(f"📂 成功读取到 {len(seed_data)} 条术语数据！准备入库...")

    # ================= 3. 连接向量数据库 =================
    client = chromadb.PersistentClient(path="./agency_db_v4")
    aliyun_ef = DashScopeEmbeddingFunction()
    collection = client.get_or_create_collection(
        name="ai_terminology",
        embedding_function=aliyun_ef,
        metadata={"description": "AI 科技通讯社的专业术语解释库 (V4版本)"}
    )

    # ================= 4. 工业级切片：分批入库防限流 =================
    batch_size = 10  # 每次只发 20 条给阿里云，极其安全且稳定

    for i in range(0, len(seed_data), batch_size):
        batch_data = seed_data[i:i + batch_size]

        documents = []
        metadatas = []
        ids = []

        for idx, item in enumerate(batch_data):
            term = item["term"]
            explanation = item["explanation"]
            documents.append(f"专业术语【{term}】的解释是：{explanation}")
            metadatas.append({"term": term, "type": "terminology"})

            # ✨✨✨ 终极修复：使用术语本身生成绝对唯一的 MD5 身份证号
            term_hash = hashlib.md5(term.encode('utf-8')).hexdigest()
            ids.append(f"term_{term_hash}")

        try:
            logger.info(f"🧠 正在调用阿里云向量化并刻入硬盘: 第 {i + 1} 到 {i + len(batch_data)} 条...")
            collection.upsert(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
        except Exception as e:
            logger.error(f"❌ 写入第 {i + 1} 批数据时发生致命错误: {e}")

    logger.info("✅ 知识库海量数据初始化大功告成！你的智能体现在满腹经纶了！")


if __name__ == "__main__":
    init_terminology_db_from_json()
