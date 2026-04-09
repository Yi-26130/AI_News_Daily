# 路径：AI_News_Agency/tools/notifier.py
import requests
import json
import logging
import os

logger = logging.getLogger("AI_Agency.Notifier")


def push_to_wechat(title: str, content: str):
    """
    通过 企业微信群机器人 直接推送 Markdown 简报
    """
    # ⚠️ 安全守则：从环境变量读取 Webhook 地址
    webhook_url = os.getenv("WECOM_WEBHOOK")

    if not webhook_url:
        logger.warning("⚠️ [推送部] 未找到 WECOM_WEBHOOK 环境变量，已跳过企业微信推送。")
        return False

    # 组装超级漂亮的 Markdown 格式
    # 企业微信机器人的 Markdown 支持给文字上色，这里我们把标题标为绿色（info）
    markdown_text = f"### <font color='info'>{title}</font>\n\n{content}"

    # 按照企业微信官方 API 要求的 JSON 格式打包
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "content": markdown_text
        }
    }

    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(webhook_url, headers=headers, data=json.dumps(payload))

        # 企微 API 会返回 JSON，里面有 errcode。0 代表成功。
        result = response.json()
        if result.get("errcode") == 0:
            logger.info("✅ [推送部] 简报已通过企业微信机器人成功投递！")
            return True
        else:
            logger.error(f"❌ [推送部] 投递失败，官方报错: {result.get('errmsg')}")
            return False
    except Exception as e:
        logger.error(f"❌ [推送部] 投递时发生网络错误: {e}")
        return False