# app.py — Project Aegis (Updated UI)

import streamlit as st
import requests

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Project Aegis — Policy Intelligence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- GLOBAL STYLES ---
st.markdown("""
<style>

/* GLOBAL FONT */
html, body, [class*="css"] {
    font-size: 18px !important;
}

/* CHAT TEXT */
div[data-testid="stChatMessage"] p,
div[data-testid="stChatMessage"] li {
    font-size: 1.15rem !important;
    line-height: 1.8 !important;
}

/* EXPANDER */
div[data-testid="stExpander"] p,
div[data-testid="stExpander"] li {
    font-size: 1.05rem !important;
}

/* SIDEBAR */
section[data-testid="stSidebar"] * {
    font-size: 1.05rem !important;
}

/* POLICY ALIGNMENT */
.policy-item {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 6px;
}

.policy-icon {
    width: 22px;
    text-align: center;
    font-size: 1.2rem;
}

/* INPUT */
input {
    font-size: 1.05rem !important;
}

/* BUTTON */
button[kind="primary"] {
    font-size: 1.05rem !important;
}

/* HEADERS */
h1 { font-size: 2rem !important; }
h2 { font-size: 1.5rem !important; }

.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

</style>
""", unsafe_allow_html=True)

# --- Session state ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "session_id" not in st.session_state:
    st.session_state.session_id = "streamlit_session_1"
if "last_result" not in st.session_state:
    st.session_state.last_result = None

# --- Sidebar ---
with st.sidebar:
    st.title("🛡️ Project Aegis")
    st.markdown("Advanced Enterprise RAG System for corporate policy Q&A.")
    st.divider()

    st.subheader("Pipeline Concepts")
    all_concepts = [
        "Multi-Query Expansion",
        "HyDE",
        "Metadata Pre-Filter",
        "RRF Fusion",
        "Post-Filter by Date",
        "Cross-Encoder Reranking",
    ]

    active_concepts = []
    if st.session_state.last_result:
        active_concepts = st.session_state.last_result.get("concepts_used", [])

    for c in all_concepts:
        if c in active_concepts:
            st.success(f"✅ {c}")
        else:
            st.markdown(f"- {c}")

    st.divider()
    st.subheader("Policy Corpus")

    st.markdown("""
    <div class="policy-item">
        <span class="policy-icon">✈️</span>
        <span><b>Travel</b> — 3 docs</span>
    </div>
    <div class="policy-item">
        <span class="policy-icon">👥</span>
        <span><b>HR</b> — 3 docs</span>
    </div>
    <div class="policy-item">
        <span class="policy-icon">🔒</span>
        <span><b>IT Security</b> — 1 doc</span>
    </div>
    <div class="policy-item">
        <span class="policy-icon">🎓</span>
        <span><b>Learning & Training</b> — 1 doc</span>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    if st.button("🗑️ Clear chat"):
        st.session_state.chat_history = []
        st.session_state.last_result = None
        st.rerun()

# --- Main ---
st.title("🛡️ Policy Intelligence — Enterprise RAG System")
st.markdown("**IITM Pravartak — Agentic AI Assignment** | Built by Ramya")
st.divider()

# --- Input ---
col1, col2 = st.columns([5, 1])

with col1:
    query = st.text_input(
        label="Ask a policy question",
        placeholder="e.g. What is the taxi reimbursement limit?",
        label_visibility="collapsed"
    )

with col2:
    ask_btn = st.button("Ask →", type="primary", use_container_width=True)

# --- Execute ---
if ask_btn and query.strip():
    with st.spinner("Searching policies..."):
        try:
            resp = requests.post(
                f"{API_URL}/ask",
                json={"query": query, "session_id": st.session_state.session_id},
                timeout=60
            )
            resp.raise_for_status()
            data = resp.json()

            st.session_state.last_result = data
            st.session_state.chat_history.append({
                "query": query,
                "answer": data["answer"]
            })

            st.rerun()

        except Exception as e:
            st.error(f"Error: {str(e)}")

# --- Output ---
if st.session_state.last_result:
    data = st.session_state.last_result

    if st.session_state.chat_history:
        last = st.session_state.chat_history[-1]

        with st.chat_message("user"):
            st.write(last["query"])

    if data.get("category_detected"):
        st.info(f"📂 Category: {data['category_detected']}")

    with st.chat_message("assistant"):
        st.write(data["answer"])

    st.divider()

    if data.get("sources"):
        st.subheader("📄 Sources")

        for i, source in enumerate(data["sources"], start=1):
            with st.expander(f"Source {i} — {source['document_id']}"):
                st.metric("Relevance", f"{source['score']:.2f}")
                st.progress(float(source["score"]))
                st.write(source["text_preview"] + "...")
