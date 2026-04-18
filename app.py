import streamlit as st
import time
import requests
import json
import random
import math
import threading
import os
from dotenv import load_dotenv

load_dotenv()

def get_secret(key, default=""):
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError):
        return os.getenv(key, default)

COZE_API_TOKEN = get_secret("COZE_API_TOKEN")
WORKFLOW_ID    = get_secret("WORKFLOW_ID")
API_URL        = get_secret("API_URL", "https://api.coze.cn/v1/workflow/run")

with open(os.path.join(os.path.dirname(__file__), "mock_data.json"), encoding="utf-8") as f:
    DEMO_MOCK = {item["id"]: item for item in json.load(f)}

st.set_page_config(page_title="蒲公英 AI Vibe-Match", page_icon="🌼", layout="wide")

@st.dialog("功能提示")
def show_dialog(title, msg):
    st.markdown(f"### {title}")
    st.markdown(msg)
    if st.button("知道了", key="dialog_close"):
        st.rerun()

# ── 全局样式 ──────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp {
        background: #F9F9FB;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
    }
    h1 { color: #FF2442 !important; font-weight: 800; }

    /* 主 CTA 按钮 */
    div[data-testid="stButton"] > button {
        background: #FF2442; color: white; border: none;
        border-radius: 24px; padding: 0.6rem 2rem;
        font-size: 1rem; font-weight: 600; width: 100%;
        transition: all .2s ease;
    }
    div[data-testid="stButton"] > button:hover {
        opacity: .9; color: white; transform: scale(1.02);
    }

    .subtitle { color: #888; font-size: .95rem; margin-top: -.5rem; margin-bottom: 1.5rem; }
    .divider  { border: none; border-top: 1px solid #EBEBEB; margin: 1.2rem 0; }

    /* tag 胶囊 */
    .tag {
        display: inline-block; background: #FFF0F2; color: #FF2442;
        border-radius: 20px; padding: 2px 12px; font-size: .78rem;
        margin: 2px 3px; font-weight: 500; line-height: 1.6;
    }
    .tag-cross { background: #F0F4FF; color: #4A6CF7; }

    /* 博主卡片容器 — st.container(border=True) 的样式覆盖 */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.card-header) {
        background: white !important; border-radius: 16px !important;
        box-shadow: 0 4px 24px rgba(0,0,0,0.06) !important;
        border: none !important; overflow: hidden;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.card-header) > div {
        background: white !important;
        border: none !important;
        padding: 0 !important;
    }
    .card-header {
        padding: 1.2rem 1.6rem 1rem;
        border-bottom: 1px solid #F5F5F5;
    }
    .card-info {
        padding: .4rem .6rem .6rem;
    }
    .card-score {
        padding: .4rem .6rem .6rem;
    }
    .metric { font-size: .85rem; color: #888; margin-top: .5rem; line-height: 1.6; }
    .metric b { color: #222; font-weight: 600; }
    .ai-reason {
        background: #FFFBF0; border-radius: 10px;
        padding: .8rem 1rem; margin: .6rem 0;
        font-size: .88rem; color: #555; border-left: 3px solid #FFB800;
        line-height: 1.7;
    }
    .scene {
        background: #F6FFF8; border-radius: 10px;
        padding: .8rem 1rem; margin: .6rem 0;
        font-size: .88rem; color: #555; border-left: 3px solid #2ECC71;
        line-height: 1.7;
    }
    .section-label {
        font-size: .84rem; font-weight: 600; color: #333;
        margin-bottom: .2rem;
    }

    /* 案例快捷按钮 */
    div[data-testid="stButton"] > button[kind="tertiary"] {
        font-size: .82rem !important;
        padding: .5rem 1.2rem !important;
        white-space: nowrap !important;
        border-radius: 20px !important;
        min-height: 0 !important;
        height: auto !important;
        line-height: 1.5 !important;
        width: 100% !important;
        background: #FFF0F2 !important;
        color: #FF2442 !important;
        font-weight: 600 !important;
        border: 1.5px solid #FF2442 !important;
        letter-spacing: .03em !important;
        transition: all .2s ease !important;
    }
    div[data-testid="stButton"] > button[kind="tertiary"]:hover {
        background: #FF2442 !important;
        color: white !important;
        transform: scale(1.02) !important;
    }

    /* loading 动画 */
    @keyframes blink   { 50% { opacity: 0; } }
    @keyframes loading  { 0% { transform: translateX(-100%); } 100% { transform: translateX(100%); } }
</style>
""", unsafe_allow_html=True)

# ── 页头 ──────────────────────────────────────────────────────
st.markdown("# 🌼 蒲公英AI Vibe-Match审美匹配引擎")
st.markdown('<p class="subtitle">小红书商业化选人升级 · 从标签筛选 → 多模态自然语言匹配</p>', unsafe_allow_html=True)
st.markdown(
    '<p style="margin-top:-.3rem;margin-bottom:.6rem">'
    '<a href="https://github.com/yikemeng01/AI-Vibe-Match" target="_blank" '
    'style="display:inline-block;background:#F0F4FF;color:#4A6CF7;border-radius:20px;'
    'padding:4px 14px;font-size:.8rem;font-weight:500;text-decoration:none;'
    'border:1px solid #D6E0FF;transition:all .2s ease">'
    '📄 点击阅读完整产品方案 (PRD) 与技术架构</a></p>',
    unsafe_allow_html=True,
)
st.info("💻 提示：本项目为面向 B 端买手设计的后台工作流，请使用 **电脑端全屏浏览器** 访问以获得最佳的图表与卡片视觉体验。")
st.markdown('<hr class="divider">', unsafe_allow_html=True)

left, right = st.columns([1, 2], gap="large")

# ── 案例预设 ──────────────────────────────────────────────────
DEMO_CASES = [
    ("🧴 高端护肤", "skincare"),
    ("🪑 中古家具", "furniture"),
    ("🍵 中式养生", "wellness"),
]

with left:
    st.markdown("### 🎯 提出你的种草需求")

    # 案例快捷按钮
    st.markdown(
        '<p style="font-size:.75rem;color:#BBB;margin:0 0 .4rem">点击案例可极速预览 AI 匹配效果</p>',
        unsafe_allow_html=True,
    )
    demo_cols = st.columns(len(DEMO_CASES), gap="small")
    for i, (label, mock_id) in enumerate(DEMO_CASES):
        with demo_cols[i]:
            if st.button(label, key=f"demo_{i}", type="tertiary"):
                mock = DEMO_MOCK[mock_id]
                st.session_state["demo_brief"] = mock["input"]["brief"]
                st.session_state["demo_image_url"] = mock["input"].get("image_url", "")
                st.session_state["bloggers"] = mock["bloggers"]
                st.rerun()

    uploaded = st.file_uploader("上传推广商品主图", type=["jpg", "jpeg", "png", "webp"])
    if uploaded:
        st.image(uploaded, width=160, caption="已上传商品图")
    elif st.session_state.get("demo_image_url"):
        st.image(st.session_state["demo_image_url"], width=160, caption="预设商品图")

    brief = st.text_area(
        "描述你想要的博主氛围感",
        value=st.session_state.pop("demo_brief", ""),
        placeholder="请用大白话描述你想要的博主氛围感、受众类型或种草场景\n\n例如：想推这款中古台灯，不要硬核家居博主，找点有生活情调的跨界博主",
        height=160,
    )
    run = st.button("✨ AI 跨界寻源")

# ── API 工具函数 ──────────────────────────────────────────────

def upload_image_to_coze(image_bytes, filename):
    headers = {"Authorization": f"Bearer {COZE_API_TOKEN}"}
    files = {"file": (filename, image_bytes, "image/jpeg")}
    resp = requests.post("https://api.coze.cn/v1/files/upload", headers=headers, files=files, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    return data.get("data", {}).get("url") or data.get("data", {}).get("file_url", "")


def call_coze_api(image_url, description):
    headers = {
        "Authorization": f"Bearer {COZE_API_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "workflow_id": WORKFLOW_ID,
        "parameters": {"input_description": description, "input_image": image_url},
    }
    resp = requests.post(API_URL, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    raw = data.get("data")
    if isinstance(raw, str):
        raw = json.loads(raw)
    output = raw.get("output") if isinstance(raw, dict) else raw
    if isinstance(output, str):
        output = json.loads(output)
    return output


def parse_api_result(raw):
    if not isinstance(raw, list) or not raw:
        return None
    result = []
    for b in raw:
        tags_raw = b.get("tags", "")
        tags = [t.strip() for t in tags_raw.split("/")] if isinstance(tags_raw, str) else tags_raw
        result.append({
            "name": b.get("blogger_name", ""),
            "tags": tags,
            "fans": b.get("followers", ""),
            "cpe": b.get("cpe", ""),
            "reason": b.get("match_reason", ""),
            "scene": b.get("scene_suggestion", ""),
            "match_score": b.get("match_score", 75),
        })
    return result


# ── 评分维度 ──────────────────────────────────────────────────
SCORE_DIMS = [
    ("视觉调性", "Visual Vibe",  -12),
    ("受众画像", "Audience",      -4),
    ("情绪共鸣", "Emotion",        8),
    ("场景契合", "Scene",          -8),
    ("性价比",   "ROI",             4),
]

def gen_dim_scores(match_score, seed):
    rng = random.Random(seed)
    return [min(100, max(55, match_score + d + rng.randint(-4, 4))) for _, _, d in SCORE_DIMS]

def score_color(s):
    if s >= 88: return "#FF2442"
    if s >= 75: return "#FF6B81"
    return "#FFB3BC"

def gauge_svg(score):
    pct = max(0, min(score, 100)) / 100
    cx, cy, r = 70, 68, 50
    bg = f"M {cx-r} {cy} A {r} {r} 0 0 1 {cx+r} {cy}"
    sweep_rad = math.radians(180 - pct * 180)
    ex = cx + r * math.cos(sweep_rad)
    ey = cy - r * math.sin(sweep_rad)
    large = 1 if pct > 0.5 else 0
    fg = f"M {cx-r:.2f} {cy:.2f} A {r} {r} 0 {large} 1 {ex:.2f} {ey:.2f}"
    return (
        f'<svg width="140" height="82" viewBox="0 0 140 82">'
        f'<path d="{bg}" fill="none" stroke="#F0F0F0" stroke-width="9" stroke-linecap="round"/>'
        f'<path d="{fg}" fill="none" stroke="#FF2442" stroke-width="9" stroke-linecap="round"/>'
        f'<text x="{cx}" y="{cy+4}" text-anchor="middle" font-size="24" font-weight="800" fill="#222">{score}</text>'
        f'<text x="{cx}" y="{cy+18}" text-anchor="middle" font-size="8.5" fill="#BBB" letter-spacing="1">VIBE SCORE</text>'
        f'</svg>'
    )


# ── Loading 动画 ──────────────────────────────────────────────
LOADING_FIXED = [
    "🧠 AI 审美撮合引擎启动中...",
    "🔍 正在提取商品图片多模态特征...",
]
LOADING_WAIT = [
    "🌐 正在全网检索 Vibe 契合的 KOC...",
    "✨ 正在生成原生种草策略...",
    "🌐 正在全网检索 Vibe 契合的 KOC...",
    "✨ 正在生成原生种草策略...",
]

def _typewriter(placeholder, text, duration):
    displayed = ""
    delay = duration / max(len(text), 1)
    for ch in text:
        displayed += ch
        placeholder.markdown(
            '<div style="background:white;border-radius:12px;padding:1.2rem 1.6rem;'
            'box-shadow:0 2px 12px rgba(0,0,0,.06);text-align:center;margin:2rem 0">'
            '<div style="font-size:1rem;color:#333;font-weight:500;letter-spacing:.02em">'
            + displayed +
            '<span style="animation:blink 1s step-end infinite;color:#FF2442">|</span></div>'
            '<div style="margin-top:.5rem;height:3px;background:#F5F5F5;border-radius:99px;overflow:hidden">'
            '<div style="width:100%;height:100%;background:linear-gradient(90deg,#FF2442,#FF8C69);'
            'animation:loading 1.2s ease-in-out infinite"></div>'
            '</div></div>',
            unsafe_allow_html=True,
        )
        time.sleep(delay)

def render_loading_with_api(placeholder, api_func):
    result = {"data": None, "error": None, "done": False}

    def _call():
        try:
            result["data"] = api_func()
        except Exception as e:
            result["error"] = str(e)
        result["done"] = True

    t = threading.Thread(target=_call, daemon=True)
    t.start()

    for text in LOADING_FIXED:
        _typewriter(placeholder, text, 1.6)

    for text in LOADING_WAIT:
        if result["done"]:
            break
        _typewriter(placeholder, text, 2.5)
        if not result["done"]:
            time.sleep(0.5)

    while not result["done"]:
        time.sleep(0.3)

    placeholder.markdown(
        '<div style="background:white;border-radius:12px;padding:1.2rem 1.6rem;'
        'box-shadow:0 2px 12px rgba(0,0,0,.06);text-align:center;margin:2rem 0">'
        '<div style="font-size:1rem;color:#FF2442;font-weight:600">✅ 匹配完成！</div></div>',
        unsafe_allow_html=True,
    )
    time.sleep(0.8)
    placeholder.empty()
    return result


# ── 博主卡片渲染 ─────────────────────────────────────────────
def render_cards(bloggers):
    for b in bloggers:
        tags = b.get("tags", [])
        match_score = b.get("match_score", 75)
        dim_scores = gen_dim_scores(match_score, b["name"])

        cross_tag = b.get("cross_tag") or (tags[0] if tags else "跨界")
        tags_html = ''.join(f'<span class="tag">{t}</span>' for t in tags)
        tags_html += f'<span class="tag tag-cross">⚡ 跨界: {cross_tag}</span>'

        with st.container(border=True):
            # ── 卡片头部 ──
            st.markdown(f"""
            <div class="card-header">
                <div style="display:flex;align-items:center;gap:.8rem;margin-bottom:.5rem">
                    <div style="width:44px;height:44px;border-radius:50%;
                                background:linear-gradient(135deg,#FF2442,#FF8C69);
                                display:flex;align-items:center;justify-content:center;
                                color:white;font-weight:700;font-size:1.1rem;flex-shrink:0">
                        {b['name'][0]}
                    </div>
                    <div style="flex:1;min-width:0">
                        <div style="font-weight:700;font-size:1.05rem;color:#222">{b['name']}</div>
                        <div style="margin-top:.25rem">{tags_html}</div>
                    </div>
                    <div style="display:flex;gap:.5rem;flex-shrink:0">
                        <a href="#" style="display:inline-flex;align-items:center;gap:.3rem;
                            background:#FFF0F2;color:#FF2442;border:1.5px solid #FF2442;
                            border-radius:20px;padding:.3rem .9rem;font-size:.78rem;
                            font-weight:600;text-decoration:none;white-space:nowrap">🏠 查看主页</a>
                        <a href="#" style="display:inline-flex;align-items:center;gap:.3rem;
                            background:#FF2442;color:white;border-radius:20px;
                            padding:.3rem .9rem;font-size:.78rem;font-weight:600;
                            text-decoration:none;white-space:nowrap">💰 获取报价</a>
                    </div>
                </div>
                <div class="metric">
                    粉丝量 <b>{b['fans']}</b> &nbsp;|&nbsp;
                    预估 CPE <b style="color:#FF2442">{b['cpe']}</b> &nbsp;|&nbsp;
                    性价比 <b style="color:#2ECC71">极高 ↑</b>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # ── 卡片主体：左推荐理由 + 右评分 ──
            info_col, score_col = st.columns([3, 2], gap="small")

            with info_col:
                st.markdown(f"""
                <div class="card-info">
                    <div class="section-label">💡 AI 推荐理由</div>
                    <div class="ai-reason">{b['reason']}</div>
                    <div class="section-label" style="margin-top:.8rem">🎬 种草场景建议</div>
                    <div class="scene">{b['scene']}</div>
                </div>
                """, unsafe_allow_html=True)

            with score_col:
                bars_html = ""
                for (label, en, _), s in zip(SCORE_DIMS, dim_scores):
                    c = score_color(s)
                    bars_html += (
                        f'<div style="margin-bottom:.5rem">'
                        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.15rem">'
                        f'<span style="font-size:.78rem;color:#555;font-weight:500">{label}'
                        f'<span style="color:#BBB;font-size:.68rem;margin-left:.3rem">{en}</span></span>'
                        f'<span style="font-size:.8rem;font-weight:700;color:{c}">{s}</span>'
                        f'</div>'
                        f'<div style="background:#F5F5F5;border-radius:99px;height:6px;overflow:hidden">'
                        f'<div style="width:{s}%;height:100%;border-radius:99px;background:{c}"></div>'
                        f'</div></div>'
                    )
                st.markdown(f"""
                <div class="card-score">
                    <div style="text-align:center;margin-bottom:.6rem">
                        {gauge_svg(match_score)}
                    </div>
                    <div style="border-top:1px solid #F5F5F5;padding-top:.7rem">
                        {bars_html}
                    </div>
                </div>
                """, unsafe_allow_html=True)


# ── 右侧主区域 ───────────────────────────────────────────────
with right:
    st.markdown("### 🤖 AI 推荐结果")
    if run:
        image_url = ""
        if uploaded:
            uploaded.seek(0)
            img_bytes = uploaded.read()
            try:
                image_url = upload_image_to_coze(img_bytes, uploaded.name)
            except Exception as e:
                st.warning(f"图片上传失败: {e}")

        error_msg = None
        loading_ph = st.empty()
        result = render_loading_with_api(
            loading_ph,
            lambda: call_coze_api(image_url, brief or ""),
        )
        if result["error"]:
            error_msg = result["error"]
            st.session_state.bloggers = None
        else:
            st.session_state.bloggers = parse_api_result(result["data"])

        if error_msg:
            st.warning(f"⚠️ API 异常（已降级到演示数据）：{error_msg}")

        if not st.session_state.bloggers:
            fallback = list(DEMO_MOCK.values())[0]
            st.session_state.bloggers = fallback["bloggers"]

    if st.session_state.get("bloggers"):
        bloggers = st.session_state.bloggers
        st.success("✅ 已为你匹配 2 位高 Vibe 跨界博主，CPE 远优于同类垂类博主")
        render_cards(bloggers)

        st.markdown('<div style="height:1.5rem"></div>', unsafe_allow_html=True)
        col1, col2 = st.columns([1, 1], gap="small")
        with col1:
            if st.button("📥 导出 KOC 策略简报"):
                show_dialog("📥 导出 KOC 策略简报", "演示版本暂不支持导出，正式版将生成包含博主画像、匹配理由与种草方案的完整 PDF 简报。")
        with col2:
            if st.button("📤 一键发起合作邀约"):
                show_dialog("📤 一键发起合作邀约", "演示版本暂不支持发送邀约，正式版将对接蒲公英平台 API，自动向匹配博主发起合作意向。")
    else:
        st.markdown("""
        <div style="text-align:center;padding:4rem 2rem;color:#CCC">
            <div style="font-size:3rem">🌼</div>
            <div style="margin-top:1rem;font-size:1rem;color:#AAA">在左侧输入需求后，点击「AI 跨界寻源」</div>
            <div style="font-size:.85rem;margin-top:.4rem;color:#CCC">AI 将为你匹配最具 Vibe 契合度的跨界博主</div>
        </div>
        """, unsafe_allow_html=True)

# ── 页脚 ──────────────────────────────────────────────────────
st.markdown("""
<div style="margin-top:3rem;padding:.75rem 1.5rem;background:#F7F7F7;
    border-top:1px solid #EBEBEB;text-align:center;color:#BBB;
    font-size:.75rem;letter-spacing:.01em;line-height:1.8">
    ⚠️ &nbsp;本系统为小红书 RPT 岗位面试专属 MVP Demo。当前展示的 KOC 数据基于大模型推演生成，未接入真实商业化数据库。
</div>
""", unsafe_allow_html=True)
