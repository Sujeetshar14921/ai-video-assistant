import streamlit as st
import time
from dotenv import load_dotenv
from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarizer import summarize, generate_title
from core.extractor import extract_action_items, extract_key_decisions, extract_questions
from core.rag_engine import build_rag_chain, ask_question

load_dotenv()

# ─── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Video Assistant",
    page_icon="⏺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS — "Tape Deck" design system ────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@600;700;800;900&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

/* ── Tokens ── */
:root {
    --ink:        #10151c;
    --ink-2:      #171d26;
    --panel:      #1c232e;
    --line:       #2b3441;
    --tape:       #e2a33d;
    --tape-soft:  rgba(226,163,61,0.14);
    --tape-dim:   #8a6a35;
    --signal:     #5fb8a8;
    --signal-soft:rgba(95,184,168,0.14);
    --rec:        #d1495b;
    --rec-soft:   rgba(209,73,91,0.16);
    --paper:      #ece7da;
    --mute:       #7c8697;
}

/* ── Global Reset ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: var(--ink) !important;
    color: var(--paper) !important;
}

.stApp { background: var(--ink) !important; }

/* Faint reel-tape texture */
.stApp::before {
    content: '';
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    background-image: repeating-linear-gradient(
        180deg,
        transparent 0px,
        transparent 27px,
        rgba(226,163,61,0.025) 27px,
        rgba(226,163,61,0.025) 28px
    );
    pointer-events: none;
    z-index: 0;
}

/* ── Sidebar — "DECK" ── */
[data-testid="stSidebar"] {
    background: var(--ink-2) !important;
    border-right: 1px solid var(--line) !important;
}
[data-testid="stSidebar"] * { color: var(--paper) !important; }

.deck-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    color: var(--tape);
    border: 1px solid var(--tape-dim);
    background: var(--tape-soft);
    padding: 0.2rem 0.55rem;
    border-radius: 3px;
    display: inline-block;
}

.brand-mark {
    font-family: 'Big Shoulders Display', sans-serif;
    font-weight: 800;
    font-size: 1.9rem;
    line-height: 0.95;
    letter-spacing: -0.01em;
    color: var(--paper);
}
.brand-mark span { color: var(--tape); }

.rec-row {
    display: flex;
    align-items: center;
    gap: 0.45rem;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    color: var(--mute);
    margin-top: 0.35rem;
}
.rec-dot {
    width: 7px; height: 7px;
    border-radius: 50%;
    background: var(--rec);
    box-shadow: 0 0 6px var(--rec);
    animation: blink 1.4s infinite;
}
@keyframes blink { 0%,100% {opacity:1;} 50% {opacity:0.25;} }

/* ── Headings ── */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Big Shoulders Display', sans-serif !important;
    color: var(--paper) !important;
    font-weight: 800 !important;
}

/* ── Hero ── */
.hero-title {
    font-family: 'Big Shoulders Display', sans-serif;
    font-size: clamp(2.2rem, 5vw, 3.8rem);
    font-weight: 900;
    line-height: 0.98;
    margin: 0;
    color: var(--paper);
    letter-spacing: -0.01em;
}
.hero-title span { color: var(--tape); }

.hero-sub {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    color: var(--mute);
    letter-spacing: 0.08em;
    margin-top: 0.5rem;
}

/* Waveform divider instead of a plain <hr> */
.wave-divider {
    width: 100%; height: 22px;
    margin: 1.4rem 0;
    background-image: repeating-linear-gradient(
        90deg,
        var(--line) 0px, var(--line) 2px,
        transparent 2px, transparent 7px
    );
    background-position: center;
    background-size: 7px 100%;
    background-repeat: repeat-x;
    opacity: 0.9;
    mask-image: linear-gradient(90deg, transparent, black 8%, black 92%, transparent);
}
hr { display: none !important; }

/* ── Clip cards (formerly generic "cards") ── */
.clip {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 6px;
    padding: 1.4rem 1.5rem;
    margin-bottom: 1rem;
    position: relative;
    transition: border-color 0.2s;
}
.clip:hover { border-color: var(--tape-dim); }

.clip-tag {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--tape);
    margin-bottom: 0.85rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.clip-tag::before {
    content: '';
    width: 3px; height: 12px;
    background: var(--tape);
    display: inline-block;
}

.clip-content {
    font-size: 0.9rem;
    line-height: 1.7;
    color: var(--paper);
}

/* ── Inputs & Buttons ── */
.stTextInput > div > div > input,
.stSelectbox > div > div {
    background: var(--ink-2) !important;
    border: 1px solid var(--line) !important;
    border-radius: 5px !important;
    color: var(--paper) !important;
    font-family: 'IBM Plex Mono', monospace !important;
}
.stTextInput > div > div > input:focus {
    border-color: var(--tape) !important;
    box-shadow: 0 0 0 2px var(--tape-soft) !important;
}

.stButton > button {
    background: var(--tape) !important;
    color: #171106 !important;
    border: none !important;
    border-radius: 5px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-weight: 600 !important;
    font-size: 0.8rem !important;
    letter-spacing: 0.06em !important;
    padding: 0.6rem 1.4rem !important;
    transition: all 0.15s !important;
    text-transform: uppercase !important;
}
.stButton > button:hover {
    background: #f0b354 !important;
    transform: translateY(-1px) !important;
}
.stButton > button[kind="secondary"] {
    background: var(--ink-2) !important;
    color: var(--mute) !important;
    border: 1px solid var(--line) !important;
}

/* ── Tape counter (pipeline status) ── */
.counter-row {
    display: flex;
    align-items: center;
    gap: 0.7rem;
    padding: 0.55rem 0.7rem;
    background: var(--ink-2);
    border-radius: 5px;
    margin: 0.3rem 0;
    border: 1px solid var(--line);
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.74rem;
}
.counter-code { color: var(--mute); min-width: 2.2rem; }
.dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.dot-active  { background: var(--tape); box-shadow: 0 0 7px var(--tape); animation: blink 1.3s infinite; }
.dot-done    { background: var(--signal); }
.dot-pending { background: var(--line); }

/* ── Chat / "COMMS" panel ── */
.chat-container {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 6px;
    padding: 1.25rem;
    max-height: 420px;
    overflow-y: auto;
    margin-bottom: 1rem;
}
.chat-msg { margin-bottom: 1rem; display: flex; flex-direction: column; gap: 0.25rem; }
.chat-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.63rem;
    font-weight: 600;
    letter-spacing: 0.14em;
    text-transform: uppercase;
}
.chat-bubble {
    display: inline-block;
    padding: 0.6rem 1rem;
    border-radius: 5px;
    font-size: 0.85rem;
    line-height: 1.6;
    max-width: 90%;
}
.user-label { color: var(--tape); }
.bot-label  { color: var(--signal); }
.user-bubble { background: var(--tape-soft); border: 1px solid var(--tape-dim); align-self: flex-end; }
.bot-bubble  { background: var(--signal-soft); border: 1px solid rgba(95,184,168,0.35); align-self: flex-start; }

/* ── Transcript reel box ── */
.transcript-box {
    background: var(--ink-2);
    border: 1px solid var(--line);
    border-radius: 5px;
    padding: 1.25rem;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    line-height: 1.8;
    max-height: 300px;
    overflow-y: auto;
    color: var(--mute);
    white-space: pre-wrap;
    word-break: break-word;
}

/* ── Empty state ── */
.empty-slate {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 4.5rem 2rem;
    text-align: center;
    border: 1px dashed var(--line);
    border-radius: 8px;
}
.empty-slate .slate-icon {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.75rem;
    letter-spacing: 0.2em;
    color: var(--tape);
    border: 1px solid var(--tape-dim);
    padding: 0.3rem 0.8rem;
    border-radius: 3px;
    margin-bottom: 1.2rem;
}

/* ── Misc Streamlit overrides ── */
.stProgress > div > div > div { background: var(--tape) !important; }
.stSpinner > div { border-top-color: var(--tape) !important; }
[data-testid="stMarkdownContainer"] p { color: var(--paper) !important; }
label { color: var(--mute) !important; font-size: 0.78rem !important; font-family: 'IBM Plex Mono', monospace !important; }

::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--ink); }
::-webkit-scrollbar-thumb { background: var(--line); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--tape); }
</style>
""", unsafe_allow_html=True)

# ─── Session State Init ──────────────────────────────────────────────────────────
for key, default in {
    "result": None,
    "chat_history": [],
    "processing": False,
    "pipeline_done": False,
    "pipeline_steps": {},
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ─── Helpers ────────────────────────────────────────────────────────────────────
def step_status(steps: dict, key: str) -> str:
    s = steps.get(key, "pending")
    if s == "active": return "dot-active"
    if s == "done":   return "dot-done"
    return "dot-pending"

def render_step_bar(code: str, label: str, key: str):
    css = step_status(st.session_state.pipeline_steps, key)
    st.markdown(f"""
    <div class="counter-row">
        <span class="counter-code">{code}</span>
        <div class="dot {css}"></div>
        <span>{label}</span>
    </div>""", unsafe_allow_html=True)

def wave_divider():
    st.markdown('<div class="wave-divider"></div>', unsafe_allow_html=True)

# ─── Sidebar — "DECK" ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<span class="deck-label">Deck</span>', unsafe_allow_html=True)
    st.markdown('<div class="brand-mark" style="margin-top:0.6rem">AI<br><span>Video</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="rec-row"><div class="rec-dot"></div>MEETING INTELLIGENCE</div>', unsafe_allow_html=True)
    wave_divider()

    source = st.text_input("Source", placeholder="YouTube URL or /path/to/file.mp4")
    language = st.selectbox("Language", ["english", "hinglish"], index=0)
    run_btn = st.button("Run analysis", use_container_width=True)

    if st.session_state.pipeline_done:
        wave_divider()
        st.markdown('<span class="deck-label" style="color:var(--signal);border-color:var(--signal);background:var(--signal-soft)">Tape Counter</span>', unsafe_allow_html=True)
        st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)
        for code, label, key in [
            ("01", "Audio processing", "audio"),
            ("02", "Transcription",    "transcript"),
            ("03", "Title generation", "title"),
            ("04", "Summarisation",    "summary"),
            ("05", "Extraction",       "extract"),
            ("06", "RAG engine",       "rag"),
        ]:
            render_step_bar(code, label, key)

# ─── Main Area ──────────────────────────────────────────────────────────────────
st.markdown('<div class="hero-title">AI Video <span>Assistant</span></div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">DROP A RECORDING · GET A TRANSCRIPT, A SUMMARY, AND A REEL YOU CAN QUESTION</div>', unsafe_allow_html=True)
wave_divider()

# ── Run Pipeline ────────────────────────────────────────────────────────────────
if run_btn:
    if not source.strip():
        st.error("Add a YouTube URL or a file path before running analysis.")
    else:
        st.session_state.pipeline_done = False
        st.session_state.result = None
        st.session_state.chat_history = []
        st.session_state.pipeline_steps = {}

        progress_placeholder = st.empty()

        def update_step(key, state):
            st.session_state.pipeline_steps[key] = state

        try:
            with progress_placeholder.container():
                st.info("⏺ Rolling — track progress on the tape counter in the sidebar.")

            update_step("audio", "active")
            chunks = process_input(source)
            update_step("audio", "done")

            update_step("transcript", "active")
            transcript = transcribe_all(chunks, language)
            update_step("transcript", "done")

            update_step("title", "active")
            title = generate_title(transcript)
            update_step("title", "done")

            update_step("summary", "active")
            summary = summarize(transcript)
            update_step("summary", "done")

            update_step("extract", "active")
            action_items  = extract_action_items(transcript)
            decisions     = extract_key_decisions(transcript)
            questions     = extract_questions(transcript)
            update_step("extract", "done")

            update_step("rag", "active")
            rag_chain = build_rag_chain(transcript)
            update_step("rag", "done")

            st.session_state.result = {
                "title": title,
                "transcript": transcript,
                "summary": summary,
                "action_items": action_items,
                "key_decisions": decisions,
                "open_questions": questions,
                "rag_chain": rag_chain,
            }
            st.session_state.pipeline_done = True
            progress_placeholder.success("Analysis complete — reel ready below.")
            time.sleep(0.5)
            progress_placeholder.empty()
            st.rerun()

        except Exception as e:
            for k in ["audio","transcript","title","summary","extract","rag"]:
                if st.session_state.pipeline_steps.get(k) == "active":
                    st.session_state.pipeline_steps[k] = "pending"
            progress_placeholder.error(f"Analysis stopped: {e}")

# ── Results ──────────────────────────────────────────────────────────────────────
if st.session_state.result:
    r = st.session_state.result

    st.markdown(f"""
    <div class="clip">
        <div class="clip-tag">Slate — Session Title</div>
        <div style="font-family:'Big Shoulders Display',sans-serif;font-size:1.6rem;font-weight:800;color:var(--paper)">
            {r['title']}
        </div>
    </div>""", unsafe_allow_html=True)

    col1, col2 = st.columns([3, 2], gap="medium")

    with col1:
        st.markdown(f"""
        <div class="clip">
            <div class="clip-tag">A01 — Summary</div>
            <div class="clip-content">{r['summary']}</div>
        </div>""", unsafe_allow_html=True)

    with col2:
        with st.expander("A02 — Full transcript", expanded=False):
            st.markdown(f'<div class="transcript-box">{r["transcript"]}</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3, gap="medium")

    with c1:
        st.markdown(f"""
        <div class="clip">
            <div class="clip-tag">A03 — Action Items</div>
            <div class="clip-content">{r['action_items']}</div>
        </div>""", unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="clip">
            <div class="clip-tag">A04 — Key Decisions</div>
            <div class="clip-content">{r['key_decisions']}</div>
        </div>""", unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="clip">
            <div class="clip-tag">A05 — Open Questions</div>
            <div class="clip-content">{r['open_questions']}</div>
        </div>""", unsafe_allow_html=True)

    wave_divider()

    # ── RAG Chat — "COMMS" ───────────────────────────────────────────────────
    st.markdown('<div style="font-family:\'Big Shoulders Display\',sans-serif;font-size:1.3rem;font-weight:800;margin-bottom:1rem">Comms — Ask The Reel</div>', unsafe_allow_html=True)

    if st.session_state.chat_history:
        chat_html = '<div class="chat-container">'
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                chat_html += f"""
                <div class="chat-msg" style="align-items:flex-end">
                    <span class="chat-label user-label">You</span>
                    <div class="chat-bubble user-bubble">{msg['content']}</div>
                </div>"""
            else:
                chat_html += f"""
                <div class="chat-msg" style="align-items:flex-start">
                    <span class="chat-label bot-label">Assistant</span>
                    <div class="chat-bubble bot-bubble">{msg['content']}</div>
                </div>"""
        chat_html += '</div>'
        st.markdown(chat_html, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="clip" style="text-align:center;padding:2rem">
            <div style="color:var(--mute);font-size:0.85rem;font-family:'IBM Plex Mono',monospace">Ask anything the recording covered — decisions, names, next steps.</div>
        </div>""", unsafe_allow_html=True)

    chat_col1, chat_col2 = st.columns([5, 1], gap="small")
    with chat_col1:
        user_input = st.text_input("Your question", placeholder="What were the main decisions made?", label_visibility="collapsed")
    with chat_col2:
        send_btn = st.button("Send →", use_container_width=True)

    if send_btn and user_input.strip():
        with st.spinner("Scanning the reel…"):
            answer = ask_question(r["rag_chain"], user_input.strip())
        st.session_state.chat_history.append({"role": "user",      "content": user_input.strip()})
        st.session_state.chat_history.append({"role": "assistant", "content": answer})
        st.rerun()

    if st.session_state.chat_history:
        if st.button("Clear comms", type="secondary"):
            st.session_state.chat_history = []
            st.rerun()

else:
    st.markdown("""
    <div class="empty-slate">
        <div class="slate-icon">● STANDBY</div>
        <div style="font-family:'Big Shoulders Display',sans-serif;font-size:1.6rem;font-weight:800;color:var(--paper);margin-bottom:0.5rem">
            Ready to roll
        </div>
        <div style="color:var(--mute);font-size:0.85rem;max-width:400px;line-height:1.7;font-family:'IBM Plex Mono',monospace">
            Drop a YouTube URL or a local file path in the deck, pick a language, and hit Run analysis.
        </div>
    </div>""", unsafe_allow_html=True)