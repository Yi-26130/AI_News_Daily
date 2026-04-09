# 路径：AI_News_Agency/main.py
from langgraph.graph import StateGraph, START, END
from state import AgencyState
from agents.nodes import (
    researcher_node, filter_node,  # 记得导入新名字
    geek_node, vc_node, public_node, chief_editor_node,  # 导入辩论天团
    writer_node, checker_node, route_checker,
    archive_node
)
import datetime

def build_agency():
    workflow = StateGraph(AgencyState)

    # 1. 安排部门入驻大楼
    workflow.add_node("researcher_node", researcher_node)
    workflow.add_node("filter_node", filter_node)

    # 🔥 专家天团入驻
    workflow.add_node("geek_node", geek_node)
    workflow.add_node("vc_node", vc_node)
    workflow.add_node("public_node", public_node)
    workflow.add_node("chief_editor_node", chief_editor_node)

    workflow.add_node("writer_node", writer_node)
    workflow.add_node("checker_node", checker_node)
    workflow.add_node("archive_node",archive_node)

    # 2. 规划工作流 (见证魔法的时刻)
    workflow.add_edge(START, "researcher_node")
    workflow.add_edge("researcher_node", "filter_node")

    # 🔥 并行发车 (Fan-out)：初筛完后，同时发给三个专家
    workflow.add_edge("filter_node", "geek_node")
    workflow.add_edge("filter_node", "vc_node")
    workflow.add_edge("filter_node", "public_node")

    # 🔥 汇聚结果 (Fan-in)：三个专家全吵完，统一交给总编
    workflow.add_edge("geek_node", "chief_editor_node")
    workflow.add_edge("vc_node", "chief_editor_node")
    workflow.add_edge("public_node", "chief_editor_node")

    # 总编定调后，交给撰稿人和质检部
    workflow.add_edge("chief_editor_node", "writer_node")
    workflow.add_edge("writer_node", "checker_node")

    # 条件循环（打回重写）
    workflow.add_conditional_edges(
        "checker_node",
        route_checker,
        {
            "writer_node": "writer_node",
            "archive_node": "archive_node"  # ✨ 新增映射：如果交警指路档案局，就走向档案局
        }
    )

    workflow.add_edge("archive_node", END)

    return workflow.compile()


# 路径：AI_News_Agency/main.py (只需修改文件最底部)
# 在文件最开头或 import 区域加上：
from tools.notifier import push_to_wechat

if __name__ == "__main__":
    print("🏢 【全自动 AI 科技通讯社】 CEO 按下启动按钮！\n" + "=" * 50)
    app = build_agency()
    today = datetime.datetime.now().strftime("%Y年%m月%d日")
    final_state = app.invoke({"date": today, "loop_count": 0})

    final_report = final_state.get("final_publish", "未生成终稿（触发最大重试次数）")
    print("\n" + "=" * 50)
    print(f"📰 【{today} 科技与AI速递 终稿】发布成功！")
    print("=" * 50 + "\n")
    print(final_report)

    # ✨ 新增：下班前，把终稿发给主理人微信
    # 只有在成功生成终稿时才推送，避免收到一堆“未生成终稿”的垃圾消息
    if final_state.get("review_feedback") == "PASS":
        push_to_wechat(
            title=f"📰 {today} AI科技通讯社简报",
            content=final_report
        )