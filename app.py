# app.py -- Project Aegis (Redesigned UI -- BFSI Professional Theme)
# Uses st.columns([1, 3]) instead of st.sidebar — panel always visible.

import streamlit as st
import requests
from datetime import datetime

API_URL = "https://project-aegis-api.onrender.com"

st.set_page_config(
    page_title="Aegis Policy Intelligence",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
}

/* Hide native sidebar */
[data-testid="stSidebar"],
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapseButton"],
button[aria-label="Open sidebar"],
button[aria-label="Close sidebar"] {
    display: none !important;
    width: 0 !important;
    min-width: 0 !important;
}

.block-container {
    background-color: #F7F6F2 !important;
    padding-top: 1rem !important;
    padding-bottom: 2rem !important;
    max-width: 100% !important;
    padding-left: 1.5rem !important;
    padding-right: 1.5rem !important;
}

/* ── Header ── */
.aegis-header {
    background: linear-gradient(135deg, #0F2044 0%, #1A3A6B 100%);
    border-left: 5px solid #C9A84C;
    border-radius: 4px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1.25rem;
    overflow: visible !important;
    width: 100% !important;
}
.aegis-header h1 {
    font-family: 'DM Serif Display', serif !important;
    color: #FFFFFF !important;
    font-size: 1.8rem !important;
    margin: 0 0 0.3rem 0 !important;
}
.aegis-header p {
    color: #A8B8C8 !important;
    font-size: 0.82rem !important;
    margin: 0 !important;
    font-family: 'DM Mono', monospace !important;
    letter-spacing: 0.04em;
    white-space: nowrap !important;
    overflow: visible !important;
    display: flex;
    align-items: center;
    flex-wrap: nowrap;
    gap: 0;
}
.aegis-header .gold-tag {
    display: inline-block;
    background: #C9A84C;
    color: #0F2044 !important;
    font-size: 0.7rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 2px;
    margin-right: 8px;
    font-family: 'DM Mono', monospace !important;
    letter-spacing: 0.08em;
}

/* ── Query input ── */
div[data-testid="stTextInput"] input {
    background: #FFFFFF !important;
    border: 1.5px solid #CBD5E0 !important;
    border-radius: 4px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 1rem !important;
    color: #1A1A2E !important;
    padding: 0.75rem 1rem !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
    caret-color: #0F2044 !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color: #0F2044 !important;
    box-shadow: 0 0 0 3px rgba(15,32,68,0.08) !important;
}

/* ── Run button (primary) ── */
button[kind="primary"],
[data-testid="baseButton-primary"] {
    background-color: #0F2044 !important;
    color: #C9A84C !important;
    border: 1.5px solid #C9A84C !important;
    border-radius: 4px !important;
    font-family: 'DM Mono', monospace !important;
    font-weight: 500 !important;
    letter-spacing: 0.06em !important;
    font-size: 0.85rem !important;
}
button[kind="primary"]:hover,
[data-testid="baseButton-primary"]:hover {
    background-color: #1A3A6B !important;
    color: #C9A84C !important;
}

/* ── Clear conversation button (secondary) ── */
button[kind="secondary"],
[data-testid="baseButton-secondary"] {
    background-color: transparent !important;
    color: #C9A84C !important;
    border: 1.5px solid #C9A84C !important;
    border-radius: 4px !important;
    font-family: 'DM Mono', monospace !important;
    font-weight: 500 !important;
    letter-spacing: 0.06em !important;
    font-size: 0.82rem !important;
}
button[kind="secondary"]:hover,
[data-testid="baseButton-secondary"]:hover {
    background-color: #C9A84C !important;
    color: #0F2044 !important;
    border-color: #C9A84C !important;
}

/* ── Category badges ── */
.category-badge {
    display: inline-block;
    background: #EBF4FF;
    border: 1px solid #BEE3F8;
    color: #2B6CB0 !important;
    font-family: 'DM Mono', monospace;
    font-size: 0.75rem;
    padding: 3px 10px;
    border-radius: 2px;
    font-weight: 500;
    letter-spacing: 0.06em;
    margin-bottom: 8px;
}
.category-badge.travel  { background:#FFFBEB; border-color:#F6E05E; color:#744210 !important; }
.category-badge.hr      { background:#F0FFF4; border-color:#9AE6B4; color:#22543D !important; }
.category-badge.it      { background:#EBF8FF; border-color:#90CDF4; color:#2C5282 !important; }
.category-badge.finance { background:#FAF5FF; border-color:#D6BCFA; color:#44337A !important; }
.category-badge.legal   { background:#FFF5F5; border-color:#FEB2B2; color:#742A2A !important; }

/* ── Chat messages ── */
div[data-testid="stChatMessage"] {
    border: 1px solid rgba(128,128,128,0.2) !important;
    border-radius: 4px !important;
    padding: 1rem 1.25rem !important;
    margin-bottom: 0.75rem !important;
    max-width: 100% !important;
}
/* Target only paragraph text inside chat — NOT wrapper divs */
div[data-testid="stChatMessage"] p {
    font-size: 1.1rem !important;
    line-height: 1.85 !important;
    color: #1A1A2E !important;
    word-break: break-word !important;
    overflow-wrap: break-word !important;
    white-space: normal !important;
}
/* Markdown content wrapper */
div[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p {
    font-size: 1.1rem !important;
    line-height: 1.85 !important;
    color: #1A1A2E !important;
}

/* ── Source cards ── */
.source-card {
    border: 1px solid rgba(128,128,128,0.2);
    border-left: 3px solid #C9A84C;
    border-radius: 4px;
    padding: 1rem 1.1rem;
    margin-bottom: 0.6rem;
    font-size: 0.95rem;
}
.source-card .doc-id {
    font-family: 'DM Mono', monospace;
    font-size: 0.85rem;
    color: #0F2044;
    font-weight: 600;
}
.source-card .section-name {
    color: #4A5568;
    font-size: 0.92rem;
    margin-top: 2px;
}
.source-card .score-bar-wrap {
    margin-top: 8px; background: #EDF2F7;
    border-radius: 2px; height: 4px; overflow: hidden;
}
.source-card .score-bar-fill {
    height: 4px;
    background: linear-gradient(90deg, #C9A84C, #E6B94D);
    border-radius: 2px;
}
.source-card .preview {
    color: #2D3748;
    font-size: 0.92rem;
    margin-top: 10px;
    line-height: 1.75;
    border-top: 1px solid #EDF2F7;
    padding-top: 10px;
}

.section-label {
    font-size: 0.7rem; font-weight: 600; letter-spacing: 0.1em;
    text-transform: uppercase; color: #718096;
    margin-bottom: 0.5rem; margin-top: 1.25rem;
}

#MainMenu, footer, header { visibility: hidden; }
div[data-testid="stDecoration"] { display: none; }
</style>
""", unsafe_allow_html=True)

# ── Session state ────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "session_id" not in st.session_state:
    st.session_state.session_id = f"session_{datetime.now().strftime('%H%M%S')}"
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "query_count" not in st.session_state:
    st.session_state.query_count = 0


# ══════════════════════════════════════════════════════════════
# HELPER: render a styled box in the left panel
# ══════════════════════════════════════════════════════════════
LP_CSS = (
    "background:#0F2044; color:#E8E4D9; padding:10px 12px;"
    "font-family:'DM Sans',sans-serif; font-size:0.88rem; line-height:1.5;"
    "border-right:3px solid #C9A84C;"
)

def lp_block(html: str):
    """Render a small HTML chunk inside the left-panel styling."""
    st.markdown(
        f'<div style="{LP_CSS}">{html}</div>',
        unsafe_allow_html=True,
    )

def lp_divider():
    st.markdown(
        f'<div style="{LP_CSS} padding:0 12px;">'
        '<hr style="border:none;border-top:1px solid rgba(201,168,76,0.3);margin:4px 0;">'
        '</div>',
        unsafe_allow_html=True,
    )

def lp_section(title: str):
    st.markdown(
        f'<div style="{LP_CSS} padding:6px 12px 2px 12px;">'
        f'<div style="font-size:0.66rem;font-weight:600;letter-spacing:0.1em;'
        f'text-transform:uppercase;color:#C9A84C;font-family:\'DM Mono\',monospace;">'
        f'{title}</div></div>',
        unsafe_allow_html=True,
    )

def lp_stat(label: str, value: str, small: bool = False):
    vs = "font-size:0.7rem;margin-top:1px;" if small else "font-size:1rem;margin-top:1px;"
    st.markdown(
        f'<div style="{LP_CSS} padding:4px 12px;">'
        '<div style="background:rgba(201,168,76,0.08);border:1px solid rgba(201,168,76,0.25);'
        'border-radius:3px;padding:7px 10px;">'
        f'<div style="font-size:0.64rem;color:#A8B8C8;letter-spacing:0.08em;'
        f'text-transform:uppercase;font-family:\'DM Mono\',monospace;">{label}</div>'
        f'<div style="{vs}color:#C9A84C;font-weight:600;'
        f'font-family:\'DM Mono\',monospace;">{value}</div>'
        '</div></div>',
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════
# TWO-COLUMN LAYOUT
# ══════════════════════════════════════════════════════════════
left_col, main_col = st.columns([1, 3], gap="medium")

# ── LEFT PANEL ───────────────────────────────────────────────
with left_col:

    # Brand header
    lp_block(
        '<div style="font-family:\'DM Mono\',monospace;font-size:0.62rem;'
        'color:#C9A84C;letter-spacing:0.15em;">IITM PRAVARTAK · AGENTIC AI</div>'
        '<div style="font-family:\'DM Serif Display\',serif;font-size:1.35rem;'
        'color:#FFFFFF;line-height:1.2;">Project Aegis</div>'
        '<div style="font-size:0.76rem;color:#A8B8C8;">Enterprise Policy Intelligence</div>'
        '<div style="margin-top:8px;padding-top:8px;border-top:1px solid rgba(201,168,76,0.2);'
        'display:flex;align-items:center;gap:6px;">'
        '<div style="width:22px;height:22px;border-radius:50%;background:#C9A84C;'
        'display:flex;align-items:center;justify-content:center;'
        'font-size:0.6rem;font-weight:700;color:#0F2044;font-family:\'DM Mono\',monospace;">RA</div>'
        '<div style="font-size:0.75rem;color:#E8E4D9;font-family:\'DM Sans\',sans-serif;">Ramya A</div>'
        '</div>'
    )

    lp_divider()

    # Corpus stats
    lp_section("Corpus")
    lp_stat("Policy documents", "8")
    lp_stat("Indexed chunks", "284")
    lp_stat("Embedding model", "text-embedding-3-large", small=True)

    lp_divider()

    # Policy domains
    lp_section("Policy Domains")
    domains = [
        ("✈", "Travel", "3 docs"),
        ("👤", "HR &amp; Leave", "2 docs"),
        ("🔒", "IT Security", "1 doc"),
        ("🎓", "Learning &amp; Dev", "1 doc"),
        ("📋", "Code of Conduct", "1 doc"),
    ]
    rows = ""
    for icon, name, count in domains:
        rows += (
            f'<div style="display:flex;justify-content:space-between;align-items:center;'
            f'padding:4px 0;border-bottom:1px solid rgba(201,168,76,0.1);font-size:0.84rem;">'
            f'<span>{icon}&nbsp;&nbsp;{name}</span>'
            f'<span style="font-family:\'DM Mono\',monospace;font-size:0.7rem;color:#C9A84C;">'
            f'{count}</span></div>'
        )
    lp_block(rows)

    lp_divider()

    # Pipeline
    lp_section("Retrieval Pipeline")
    active = st.session_state.last_result is not None
    for step in [
        "Multi-Query Expansion", "HyDE Search", "Metadata Pre-Filter",
        "RRF Fusion (k=60)", "Post-Filter by Date", "CrossEncoder Reranking",
        "Token Budget Check", "LLM Answer Generation",
    ]:
        bg = "#68D391" if active else "rgba(201,168,76,0.3)"
        shadow = "box-shadow:0 0 5px #68D391;" if active else ""
        st.markdown(
            f'<div style="{LP_CSS} padding:2px 12px;">'
            f'<div style="display:flex;align-items:center;gap:7px;">'
            f'<div style="width:7px;height:7px;border-radius:50%;background:{bg};{shadow}'
            f'flex-shrink:0;"></div>'
            f'<span style="font-size:0.78rem;">{step}</span>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

    lp_divider()

    # Token budget (conditional)
    if st.session_state.last_result and st.session_state.last_result.get("token_info"):
        ti = st.session_state.last_result["token_info"]
        used   = ti.get("total_tokens_after", 0)
        budget = ti.get("budget", 3000)
        pct    = min(int((used / budget) * 100), 100)
        bar_c  = "#EF4444" if ti.get("truncated") else "#68D391"

        lp_section("Context Window")
        st.markdown(
            f'<div style="{LP_CSS} padding:4px 12px;">'
            '<div style="background:rgba(201,168,76,0.08);border:1px solid rgba(201,168,76,0.25);'
            'border-radius:3px;padding:7px 10px;">'
            '<div style="font-size:0.64rem;color:#A8B8C8;letter-spacing:0.08em;'
            'text-transform:uppercase;font-family:\'DM Mono\',monospace;">Tokens used / budget</div>'
            f'<div style="font-size:1rem;color:#C9A84C;font-weight:600;'
            f'font-family:\'DM Mono\',monospace;margin-top:1px;">{used:,} / {budget:,}</div>'
            f'<div style="background:rgba(255,255,255,0.06);border-radius:3px;height:5px;'
            f'margin-top:5px;overflow:hidden;">'
            f'<div style="height:5px;border-radius:3px;width:{pct}%;background:{bar_c};"></div>'
            '</div></div></div>',
            unsafe_allow_html=True,
        )
        if ti.get("truncated"):
            lp_block(
                f'<div style="font-size:0.72rem;color:#FCA5A5;">'
                f'{ti["dropped_chunks"]} chunk(s) trimmed</div>'
            )
        lp_divider()

    # Session query count
    remaining = 10 - st.session_state.query_count
    lp_stat("Queries this session", f"{st.session_state.query_count} / 10")
    lp_block(
        f'<div style="font-size:0.7rem;color:{"#FCA5A5" if remaining == 0 else "#68D391" if remaining > 3 else "#F6AD55"};'
        f'font-family:\'DM Mono\',monospace;margin-top:2px;">'
        f'{"⚠ Limit reached" if remaining == 0 else f"{remaining} remaining"}</div>'
    )

    # Clear button
    if st.button("Clear conversation", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.last_result  = None
        st.session_state.query_count  = 0
        st.rerun()


# ── MAIN CONTENT ─────────────────────────────────────────────
with main_col:

    st.markdown("""
    <div class="aegis-header">
        <h1>Policy Intelligence System</h1>
        <p>
            <span class="gold-tag">AEGIS</span>
            Context-aware retrieval &nbsp;·&nbsp;
            Cross-encoder reranking &nbsp;·&nbsp;
            Grounded answers
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-label">Policy Question</div>', unsafe_allow_html=True)

    q_col, b_col = st.columns([5, 1])
    with q_col:
        query = st.text_input(
            label="query",
            placeholder="e.g.  What is the maternity leave entitlement for a primary caregiver?",
            label_visibility="collapsed"
        )
    with b_col:
        ask_btn = st.button("Run →", type="primary", use_container_width=True)

    st.markdown("""
    <div style="font-size:0.75rem; color:#A0AEC0; margin-top:6px;
                font-family:'DM Mono',monospace; letter-spacing:0.02em;">
        Try: &nbsp;"What is the daily meal per diem?" &nbsp;·&nbsp;
        "Mileage rate for personal car?" &nbsp;·&nbsp;
        "Phishing incident reporting SLA?"
    </div>
    """, unsafe_allow_html=True)

    # ── Execute query ────────────────────────────────────────
    QUERY_LIMIT = 10
    if st.session_state.query_count >= QUERY_LIMIT:
        st.markdown(
            f'''<div style="background:#FFF5F5;border:1px solid #FEB2B2;border-left:4px solid #E53E3E;
            border-radius:4px;padding:0.9rem 1.25rem;margin-top:0.75rem;font-family:'DM Sans',sans-serif;">
            <div style="color:#742A2A;font-weight:600;font-size:0.95rem;">Session limit reached</div>
            <div style="color:#9B2C2C;font-size:0.85rem;margin-top:3px;">
            You have used all {QUERY_LIMIT} queries for this session.
            Click <strong>Clear conversation</strong> in the left panel to start a new session.
            </div></div>''',
            unsafe_allow_html=True
        )
    elif ask_btn and query.strip():
        loading_placeholder = st.empty()
        loading_placeholder.markdown("""
        <div style="background:#0F2044; border-left:4px solid #C9A84C; border-radius:4px;
                    padding:1rem 1.25rem; margin-top:0.75rem; display:flex;
                    align-items:center; gap:12px;">
            <div style="width:14px; height:14px; border-radius:50%;
                        border:2px solid #C9A84C; border-top-color:transparent;
                        animation:spin 0.8s linear infinite; flex-shrink:0;"></div>
            <div>
                <div style="color:#FFFFFF; font-family:'DM Sans',sans-serif;
                            font-size:0.9rem; font-weight:500;">
                    Retrieving and reasoning...
                </div>
                <div style="color:#A8B8C8; font-family:'DM Mono',monospace;
                            font-size:0.72rem; margin-top:2px; letter-spacing:0.04em;">
                    Multi-query expansion → RRF fusion → CrossEncoder reranking → LLM
                </div>
            </div>
        </div>
        <style>
        @keyframes spin { to { transform: rotate(360deg); } }
        </style>
        """, unsafe_allow_html=True)

        try:
            resp = requests.post(
                f"{API_URL}/ask",
                json={"query": query, "session_id": st.session_state.session_id},
                timeout=60
            )
            resp.raise_for_status()
            data = resp.json()

            loading_placeholder.empty()
            st.session_state.last_result  = data
            st.session_state.query_count += 1
            st.session_state.chat_history.append({
                "query":    query,
                "answer":   data.get("answer", ""),
                "category": data.get("category_detected", ""),
                "sources":  data.get("sources", []),
            })
            st.rerun()

        except Exception as e:
            loading_placeholder.empty()
            st.error(f"Pipeline error: {str(e)}")

    # ── Conversation output ──────────────────────────────────
    if st.session_state.chat_history:
        st.markdown(
            '<div class="section-label" style="margin-top:1.5rem;">Results</div>',
            unsafe_allow_html=True
        )

        for turn in reversed(st.session_state.chat_history):

            with st.chat_message("user"):
                st.write(turn["query"])

            if turn.get("category"):
                cat = turn["category"].lower()
                st.markdown(
                    f'<span class="category-badge {cat}">📂 {turn["category"].upper()}</span>',
                    unsafe_allow_html=True
                )

            with st.chat_message("assistant"):
                st.write(turn["answer"])

            if turn.get("sources"):
                st.markdown(
                    '<div class="section-label" style="margin-top:0.75rem;">Sources</div>',
                    unsafe_allow_html=True
                )
                for i, src in enumerate(turn["sources"], 1):
                    doc_id  = src.get("document_id", "Unknown")
                    section = src.get("section", "")
                    score   = float(src.get("score", 0))
                    preview = src.get("text_preview", "")[:250]
                    bar_pct = int(score * 100)

                    st.markdown(f"""
                    <div class="source-card">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span class="doc-id">{i}. {doc_id}</span>
                            <span style="font-family:'DM Mono',monospace; font-size:0.72rem;
                                         color:#C9A84C;">{score:.3f}</span>
                        </div>
                        <div class="section-name">{section}</div>
                        <div class="score-bar-wrap">
                            <div class="score-bar-fill" style="width:{bar_pct}%;"></div>
                        </div>
                        <div class="preview">{preview}...</div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown(
                "<hr style='border-color:#E2E8F0; margin:1.25rem 0;'>",
                unsafe_allow_html=True
            )
