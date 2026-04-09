# 路径：AI_News_Agency/app.py
import streamlit as st
import datetime
import time

# 导入我们的流水线
from main import build_agency

# ================= 1. 网页全局配置 (苹果风的大白底与宽屏) =================
st.set_page_config(
    page_title="AI News Daily | Apple Style",
    page_icon="",  # 嘿嘿，用个苹果图标
    layout="wide",
    initial_sidebar_state="collapsed"  # 默认关闭侧边栏，因为我们不用它了
)

# ================= 2. 核心 CSS 注入：像素级复刻 Apple 审美 =================
apple_css = """
<style>
    /* 1. 强制全局使用苹果无衬线字体库 */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Helvetica Neue", Helvetica, Arial, sans-serif !important;
        color: #1d1d1f; /* 苹果深空灰字体色 */
    }

    /* 2. 隐藏丑陋的 Streamlit 默认菜单和顶栏 */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* 3. 苹果风胶囊按钮设计 */
    .stButton>button {
        background-color: #000000 !important; /* 纯黑底色 */
        color: #ffffff !important;
        border-radius: 980px !important; /* 极致圆角 */
        padding: 12px 30px !important;
        font-size: 17px !important;
        font-weight: 500 !important;
        border: none !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 14px 0 rgba(0,0,0,0.1) !important;
    }

    .stButton>button:hover {
        background-color: #333333 !important; /* 悬停深灰 */
        transform: scale(1.02) !important;
    }

    /* 4. 数据卡片（Metric）的优雅排版 */
    [data-testid="stMetricValue"] {
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
    }

    /* 5. 标题居中与间距微调 */
    .hero-title {
        text-align: center;
        font-size: 3.5rem;
        font-weight: 700;
        letter-spacing: -0.03em;
        margin-bottom: 0.2em;
    }
    .hero-subtitle {
        text-align: center;
        font-size: 1.5rem;
        font-weight: 400;
        color: #86868b;
        margin-bottom: 3em;
    }
    /* 6. 隐藏 Streamlit 原生的 Markdown 标题锚点（那个烦人的小胶囊图标） */
    .stMarkdown a.anchor-link {
        display: none !important;
    }
    
    /* 让标题超链接变成果粉最爱的深邃蓝，且去掉下划线 */
    .stMarkdown h3 a {
        color: #1d1d1f !important;  /* ✨ 这里改回了和正文一致的颜色 */
        text-decoration: none !important;
    }
    .stMarkdown h3 a:hover {
        text-decoration: underline !important;
    }
    /* 7. 让 Markdown 分割线优雅且可见（Apple 标准浅灰） */
    .stMarkdown hr {
        margin: 3em 0 !important; /* 上下留白加大，呼吸感拉满 */
        border: none !important;
        /* ✨ 换成 Apple 原生系统分割线的色号 #d2d2d7，绝对能看清且不刺眼 */
        border-top: 1px solid #d2d2d7 !important; 
    }
</style>
"""
st.markdown(apple_css, unsafe_allow_html=True)

# ================= 3. 页面主视图 (Hero Section) =================
# 预留顶部大留白
st.write("<br><br>", unsafe_allow_html=True)

st.markdown('<div class="hero-title">AI News Daily</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-subtitle">洞察未来，从这里开始。</div>', unsafe_allow_html=True)

# 使用三列布局，把按钮极其优雅地放在正中间
col_spacer1, col_center, col_spacer2 = st.columns([3, 2, 3])

with col_center:
    # 居中的启动按钮
    run_button = st.button("生成今日行业简报", use_container_width=True)

st.write("<br><br>", unsafe_allow_html=True)

# ================= 4. 核心逻辑与渲染区 =================
if "final_state" not in st.session_state:
    st.session_state.final_state = None

if run_button:
    with st.spinner("🧠 智能引擎正在深度采编中，请稍候..."):
        today_str = datetime.datetime.now().strftime("%Y年%m月%d日")
        app = build_agency()

        start_time = time.time()
        final_state = app.invoke({"date": today_str, "loop_count": 0})
        st.session_state.final_state = final_state

        cost_time = round(time.time() - start_time, 1)
        st.toast(f"生成完毕，耗时 {cost_time} 秒", icon="✨")

# ================= 5. 精美的数据展示 =================
if st.session_state.final_state:
    state = st.session_state.final_state

    st.divider()  # 一条极简的分割线

    # 顶部数据看板
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric(label="全网扫描 (篇)", value=len(state.get('news_pool', [])))
    with m2:
        st.metric(label="精选收录 (篇)", value=len(state.get('top_news', [])))
    with m3:
        st.metric(label="AI 质检拦截 (次)", value=max(0, state.get('loop_count', 1) - 1))

    st.write("<br>", unsafe_allow_html=True)

    # 两栏布局：左边是最终报告，右边是折叠的专家意见
    left_col, right_col = st.columns([6, 4])

    with left_col:
        st.subheader(" 今日定稿")
        st.markdown(state.get("final_publish", "暂无内容生成。"))

    with right_col:
        st.subheader("专家圆桌记录")
        st.caption("以下内容由多智能体辩论动态生成")

        with st.expander("极客特工 (技术视角)"):
            st.write(state.get("geek_opinion", "无数据"))

        with st.expander("风投巨鳄 (商业视角)"):
            st.write(state.get("vc_opinion", "无数据"))

        with st.expander("伦理学家 (社会视角)"):
            st.write(state.get("public_opinion", "无数据"))

        with st.expander("总编室定调指南"):
            st.info(state.get("expert_debate_summary", "无数据"))