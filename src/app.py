import logging
import queue
import threading
import time

import streamlit as st

from database.execute_query import QueryExecutionError
from exceptions import UnsupportedQuestionError
from llm.intent_classifier import IntentClassificationError
from llm.sql_generator import SQLGenerationError
from services.conversation import ConversationContext
from services.sql_service import SQLService, SQLServiceError
from services.validation_service import SQLValidationError

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Page config + styling
# ----------------------------------------------------------------------

st.set_page_config(
    page_title="ESG Analytics Assistant",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        --green: #0f766e;
        --green-2: #14b8a6;
        --green-soft: #ecfdf5;
        --ink: #172033;
        --muted: #64748b;
        --border: #e2e8f0;
        --bg: #f7f9fc;
        --white: #ffffff;
    }

    .stApp { background: var(--bg); color: var(--ink); }
    #MainMenu, footer { visibility: hidden; }

    .block-container {
        max-width: 1180px;
        padding-top: 2rem;
        padding-bottom: 6rem;
    }

    [data-testid="stHeader"] { background: transparent; }

    section[data-testid="stSidebar"] {
        background: #fff;
        border-right: 1px solid var(--border);
    }

    .sidebar-brand {
        display: flex;
        align-items: center;
        gap: 11px;
        margin-bottom: .5rem;
    }

    .brand-mark {
        width: 38px;
        height: 38px;
        border-radius: 11px;
        background: linear-gradient(135deg, #0f766e, #14b8a6);
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
        box-shadow: 0 5px 15px rgba(15,118,110,.18);
    }

    .brand-title {
        font-size: 1rem;
        font-weight: 750;
        color: var(--ink);
    }

    .brand-subtitle {
        font-size: .69rem;
        color: #94a3b8;
        margin-top: 1px;
    }

    .sidebar-description {
        color: var(--muted);
        font-size: .77rem;
        line-height: 1.55;
        margin: .9rem 0 1.15rem;
    }

    .section-label {
        color: #94a3b8;
        font-size: .67rem;
        font-weight: 800;
        letter-spacing: .1em;
        text-transform: uppercase;
        margin: 1.25rem 0 .55rem;
    }

    section[data-testid="stSidebar"] .stButton > button {
        border-radius: 10px;
        border: 1px solid var(--border);
        background: #fff;
        color: #334155;
        font-size: .77rem;
        min-height: 2.35rem;
        transition: all .18s ease;
    }

    section[data-testid="stSidebar"] .stButton > button:hover {
        border-color: #99f6e4;
        background: #f0fdfa;
        color: #115e59;
    }

    .app-header {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 1rem;
        margin-bottom: 1.35rem;
    }

    .eyebrow {
        color: var(--green);
        font-size: .67rem;
        font-weight: 800;
        letter-spacing: .12em;
        text-transform: uppercase;
        margin-bottom: .4rem;
    }

    .app-title {
        font-size: 2rem;
        line-height: 1.15;
        font-weight: 750;
        letter-spacing: -.035em;
        color: var(--ink);
        margin: 0;
    }

    .app-subtitle {
        color: var(--muted);
        font-size: .87rem;
        margin-top: .42rem;
    }

    .trust-badge {
        display: inline-flex;
        align-items: center;
        gap: 7px;
        padding: 7px 11px;
        border-radius: 999px;
        background: var(--green-soft);
        border: 1px solid #bbf7d0;
        color: #166534;
        font-size: .68rem;
        font-weight: 700;
        white-space: nowrap;
        margin-top: .2rem;
    }

    .trust-dot {
        width: 7px;
        height: 7px;
        background: #22c55e;
        border-radius: 50%;
    }

    .welcome-card {
        background: #fff;
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 2.1rem 2.3rem;
        box-shadow: 0 10px 35px rgba(15,23,42,.045);
        margin: 2.8rem auto 1.5rem;
        max-width: 850px;
        text-align: center;
    }

    .welcome-icon {
        width: 54px;
        height: 54px;
        margin: 0 auto 1rem;
        border-radius: 15px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #ecfdf5, #eff6ff);
        color: var(--green);
        font-size: 25px;
        border: 1px solid #d1fae5;
    }

    .welcome-title {
        color: var(--ink);
        font-size: 1.6rem;
        font-weight: 750;
        letter-spacing: -.025em;
    }

    .welcome-copy {
        color: var(--muted);
        font-size: .87rem;
        line-height: 1.65;
        max-width: 650px;
        margin: .55rem auto 0;
    }

    .thinking-wrap {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: .55rem .1rem .7rem;
    }

    .thinking-orb {
        width: 9px;
        height: 9px;
        border-radius: 50%;
        background: var(--green-2);
        box-shadow: 0 0 0 5px rgba(20,184,166,.10);
        animation: pulseOrb 1.4s ease-in-out infinite;
        flex-shrink: 0;
    }

    .shimmer-text {
        font-size: .82rem;
        font-weight: 500;
        background: linear-gradient(
            90deg,
            #94a3b8 15%,
            #0f766e 45%,
            #94a3b8 75%
        );
        background-size: 220% 100%;
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        animation: shimmer 1.55s linear infinite;
        display: inline-block;
    }

    @keyframes shimmer {
        0% { background-position: 220% 0; }
        100% { background-position: -220% 0; }
    }

    @keyframes pulseOrb {
        0%, 100% { transform: scale(.85); opacity: .55; }
        50% { transform: scale(1.15); opacity: 1; }
    }

    /* Result hierarchy */
    .assistant-result {
        background: #fff;
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 1.1rem 1.25rem;
        box-shadow: 0 6px 24px rgba(15,23,42,.035);
        margin: .15rem 0 .8rem;
    }

    .result-label {
        color: #94a3b8;
        font-size: .64rem;
        font-weight: 800;
        letter-spacing: .1em;
        text-transform: uppercase;
        margin-bottom: .45rem;
    }

    .insight-text {
        color: #263247;
        font-size: .91rem;
        line-height: 1.68;
    }

    [data-testid="stExpander"] {
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        background: #fff !important;
    }

    [data-testid="stExpander"] summary {
        font-size: .77rem !important;
        font-weight: 650 !important;
        color: #475569 !important;
    }

    [data-testid="stDataFrame"] {
        border: 1px solid var(--border);
        border-radius: 10px;
        overflow: hidden;
    }

    .feedback-title {
        color: #64748b;
        font-size: .71rem;
        font-weight: 600;
        margin-top: .5rem;
        margin-bottom: .15rem;
    }

    .followup-label {
        color: #94a3b8;
        font-size: .66rem;
        font-weight: 800;
        letter-spacing: .08em;
        text-transform: uppercase;
        margin: .9rem 0 .45rem;
    }

    [data-testid="stChatInput"] {
        border-radius: 16px !important;
    }

    [data-testid="stChatInput"] textarea {
        font-size: .88rem !important;
    }

    /* ---------------------------------------------------------------
       Dedicated "unsupported question" / "genuine error" component.
       Deliberately quieter than st.error() — a left-accented card that
       sits inside the normal message flow instead of a full-width red
       banner, so a "Hi" typo doesn't look like a system crash.
       --------------------------------------------------------------- */
    .response-note {
        display: flex;
        gap: .7rem;
        align-items: flex-start;
        border-radius: 14px;
        padding: .85rem 1rem;
        margin: .15rem 0 .4rem;
        border: 1px solid var(--border);
        border-left: 3px solid #cbd5e1;
        background: #fff;
    }

    .response-note.unsupported {
        border-left-color: #38bdf8;
        background: #f8fbff;
    }

    .response-note.error {
        border-left-color: #f87171;
        background: #fef8f8;
    }

    .response-note-icon {
        font-size: .95rem;
        line-height: 1.4;
        flex-shrink: 0;
        margin-top: .05rem;
    }

    .response-note-body { flex: 1; min-width: 0; }

    .response-note-title {
        font-weight: 700;
        font-size: .82rem;
        margin-bottom: .2rem;
    }

    .response-note.unsupported .response-note-title { color: #0369a1; }
    .response-note.error .response-note-title { color: #b91c1c; }

    .response-note-text {
        font-size: .81rem;
        color: #475569;
        line-height: 1.55;
        overflow-wrap: break-word;
    }

    @media (max-width: 768px) {
        .block-container { padding: 1rem .8rem 6rem; }
        .app-title { font-size: 1.55rem; }
        .trust-badge { display: none; }
        .welcome-card { padding: 1.6rem 1.1rem; margin-top: 2rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------
# Session state
# ----------------------------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "history" not in st.session_state:
    st.session_state.history = ConversationContext()

if "settings" not in st.session_state:
    st.session_state.settings = {
        "typing_effect": True,
        "show_sql_default": False,
    }

PIPELINE_STAGES = [
    "Understanding the question...",
    "Finding the relevant data...",
    "Generating and validating the query...",
    "Running the query...",
    "Preparing the result...",
]

STAGE_SECONDS = 0.9

# ----------------------------------------------------------------------
# Background pipeline runner
# ----------------------------------------------------------------------


def _run_pipeline(
    question: str, history: ConversationContext, result_queue: queue.Queue
):
    """
    Runs entirely off the Streamlit main thread. Classification AND
    logging happen here, inside the live except block — this is the
    only point where a genuine exception's traceback is actually
    available; by the time the main thread drains the queue, that
    context is gone.
    """
    try:
        result = SQLService.process_question(question, history)
        result_queue.put(("success", result))
    except UnsupportedQuestionError as exc:
        logger.info("Unsupported request: %s", exc)
        result_queue.put(("unsupported", exc))
    except Exception as exc:  # noqa: BLE001
        logger.exception("Pipeline failed while processing question.")
        result_queue.put(("error", exc))


def user_message_for_error(exc: Exception) -> str:
    """
    Maps a genuine (non-UnsupportedQuestionError) exception to static,
    curated, user-safe copy. Never returns str(exc) — real detail lives
    only in application logs, already captured with a full traceback
    by _run_pipeline at the point it was caught.
    """
    if isinstance(exc, IntentClassificationError):
        return (
            "I couldn't determine how to handle that question. Try "
            "rephrasing it as a direct question about the ESG data."
        )
    if isinstance(exc, SQLGenerationError):
        # Genuine failure only now — UNSUPPORTED_QUERY is UnsupportedQuestionError.
        return (
            "I couldn't translate that into a query. Try naming a "
            "specific metric, facility, country, or year."
        )
    if isinstance(exc, SQLValidationError):
        return (
            "That query referenced data outside what's available. "
            "Try rephrasing using terms closer to the dataset "
            "(facility, country, industry, fiscal year, emissions, "
            "energy, waste, workforce)."
        )
    if isinstance(exc, QueryExecutionError):
        return (
            "Something went wrong running that query against the "
            "database. Please try again."
        )
    # SQLServiceError (reserved, currently unused) and anything unexpected.
    return "Something unexpected went wrong. Please try again."


def render_status_line(placeholder, stage_index: int):
    """
    Shows ONE shimmering line for the current stage only. Previous
    stage text is replaced, not stacked.
    """
    label = PIPELINE_STAGES[stage_index]
    placeholder.markdown(
        f"""
        <div class="thinking-wrap">
            <span class="thinking-orb"></span>
            <span class="shimmer-text">{label}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def run_with_progress(question: str, history: ConversationContext):
    """
    Runs SQLService.process_question on a background thread while the main
    thread animates a single shimmering status line. The stage label is
    advanced on a timer purely for pacing — completion itself is driven
    entirely by the queue, so the status line disappears the instant the
    real pipeline call returns, not on a fixed schedule. Returns
    ("success", result) or ("error", exc).
    """
    result_queue: queue.Queue = queue.Queue()
    thread = threading.Thread(
        target=_run_pipeline, args=(question, history, result_queue), daemon=True
    )
    thread.start()

    status_placeholder = st.empty()
    start = time.time()
    outcome = None

    while outcome is None:
        elapsed = time.time() - start
        # Never let the timer claim the pipeline is done before the thread
        # actually finishes — cap at the second-to-last stage.
        stage_index = min(int(elapsed / STAGE_SECONDS), len(PIPELINE_STAGES) - 1)
        render_status_line(status_placeholder, stage_index)

        try:
            outcome = result_queue.get(timeout=0.15)
        except queue.Empty:
            continue

    status_placeholder.empty()  # clear immediately once the real call returns
    return outcome


# ----------------------------------------------------------------------
# Result rendering (shared by live + replayed messages)
# ----------------------------------------------------------------------


def stream_text(container, text: str, speed: float = 0.02, max_chars: int = 450):
    """Lightweight word-by-word reveal. Skips itself for long text so it
    never meaningfully delays the app."""
    if len(text) > max_chars:
        container.markdown(text)
        return

    words = text.split(" ")
    display = ""
    for word in words:
        display += word + " "
        container.markdown(display + "▌")
        time.sleep(speed)
    container.markdown(display)


def get_suggested_followups(df) -> list[str]:
    cols = set(df.columns) if df is not None else set()
    suggestions = []

    if "Facility_Name" not in cols and "Facility_ID" not in cols:
        suggestions.append("Break this down by facility")
    if "Fiscal_Year" not in cols and "Year" not in cols:
        suggestions.append("Show the trend over the last 3 years")
    if "Country" not in cols:
        suggestions.append("Compare this across countries")
    suggestions.append("Show only the top 5")

    return suggestions[:3]


def render_feedback(idx: int):
    fb_key = f"feedback_{idx}"

    if fb_key not in st.session_state:
        st.session_state[fb_key] = None

    st.markdown(
        '<div class="feedback-title">Was this answer helpful?</div>',
        unsafe_allow_html=True,
    )

    c1, c2, _ = st.columns([0.55, 0.55, 10])

    with c1:
        if st.button("👍", key=f"up_{idx}"):
            st.session_state[fb_key] = "up"

    with c2:
        if st.button("👎", key=f"down_{idx}"):
            st.session_state[fb_key] = "down"

    if st.session_state[fb_key] == "up":
        st.caption("Thanks for the feedback.")
    elif st.session_state[fb_key] == "down":
        st.radio(
            "What could be improved?",
            [
                "Incorrect result",
                "Wrong visualization",
                "Didn't answer my question",
                "Other",
            ],
            key=f"reason_{idx}",
            horizontal=True,
            label_visibility="collapsed",
        )

        note = st.text_input(
            "Anything else? (optional)",
            key=f"note_{idx}",
            label_visibility="collapsed",
            placeholder="Optional feedback...",
        )

        if st.button("Submit feedback", key=f"submit_{idx}"):
            logger.info(
                "Feedback for message %s: %s | note=%s",
                idx,
                st.session_state.get(f"reason_{idx}"),
                note,
            )
            st.caption("Thanks — noted.")


def render_result(idx: int, result, animate_insight: bool = False):
    """Render a completed, successful answer only. Never called for
    unsupported questions or failures - see render_response_note for
    those."""

    has_chart = result.chart is not None
    has_data = result.dataframe is not None and not result.dataframe.empty

    if animate_insight and st.session_state.settings["typing_effect"]:
        insight_container = st.empty()
        stream_text(insight_container, result.insight)
    else:
        st.markdown(
            '<div class="assistant-result">'
            '<div class="result-label">ESG Insight</div>'
            f'<div class="insight-text">{result.insight}</div>'
            "</div>",
            unsafe_allow_html=True,
        )

    if has_chart or has_data:
        st.write("")

        if has_chart and has_data:
            view = st.radio(
                "View",
                ["Chart", "Table"],
                key=f"view_{idx}",
                horizontal=True,
                label_visibility="collapsed",
            )

            if view == "Chart":
                st.plotly_chart(
                    result.chart,
                    width="stretch",
                    config={"displaylogo": False},
                    key=f"chart_{idx}",
                )
            else:
                st.dataframe(
                    result.dataframe,
                    width="stretch",
                    hide_index=True,
                    key=f"table_{idx}",
                )

        elif has_chart:
            st.plotly_chart(
                result.chart,
                width="stretch",
                config={"displaylogo": False},
                key=f"chart_{idx}",
            )

        else:
            st.dataframe(
                result.dataframe,
                width="stretch",
                hide_index=True,
                key=f"table_{idx}",
            )

        if has_data:
            csv = result.dataframe.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download CSV",
                data=csv,
                file_name="query_results.csv",
                mime="text/csv",
                key=f"dl_{idx}",
            )

    with st.expander(
        "View SQL",
        expanded=st.session_state.settings["show_sql_default"],
    ):
        st.code(result.sql, language="sql")

    with st.expander("Query details"):
        st.markdown(
            f"- **Rows returned:** {len(result.dataframe)}\n"
            f"- **Columns:** "
            f"{', '.join(result.dataframe.columns) if not result.dataframe.empty else '—'}\n"
            f"- **Validation:** Passed - read-only query, schema checked, row limit enforced"
        )

    render_feedback(idx)

    if idx == len(st.session_state.messages) - 1 and has_data:
        st.markdown(
            '<div class="followup-label">Continue exploring</div>',
            unsafe_allow_html=True,
        )

        followups = get_suggested_followups(result.dataframe)
        cols = st.columns(len(followups))

        for c, suggestion in zip(cols, followups):
            with c:
                if st.button(
                    suggestion,
                    key=f"sugg_{idx}_{suggestion}",
                    width="stretch",
                ):
                    st.session_state.pending_question = suggestion
                    st.rerun()


def render_response_note(kind: str, message: str):
    """
    Quiet, in-flow response for anything that isn't a successful result:
    either an unsupported/off-topic question, or a genuine backend
    failure. No SQL, no query details, no feedback, no chart/table
    controls, and no technical-details expander - the real exception is already
    captured in the server logs by _run_pipeline(), not shown here.
    """
    if kind == "unsupported":
        icon, title, css_class = "💬", "I can't help with that", "unsupported"
    else:
        icon, title, css_class = "⚠️", "Unable to complete the request", "error"

    st.markdown(
        f"""
        <div class="response-note {css_class}">
            <div class="response-note-icon">{icon}</div>
            <div class="response-note-body">
                <div class="response-note-title">{title}</div>
                <div class="response-note-text">{message}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ----------------------------------------------------------------------
# Sidebar
# ----------------------------------------------------------------------

with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="brand-mark">🌿</div>
            <div>
                <div class="brand-title">ESG Intelligence</div>
                <div class="brand-subtitle">Natural Language Assistant</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="sidebar-description">'
        "Analytics over ESG manufacturing data — emissions, energy, water, "
        "waste, workforce, and compliance metrics across facilities."
        "</div>",
        unsafe_allow_html=True,
    )

    if st.button("＋  New conversation", width="stretch"):
        st.session_state.messages = []
        st.session_state.history.clear()

        for key in list(st.session_state.keys()):
            if key.startswith(("feedback_", "reason_", "note_", "view_")):
                del st.session_state[key]

        st.rerun()

    st.markdown(
        '<div class="section-label">Try asking</div>',
        unsafe_allow_html=True,
    )

    examples = [
        "Compare Scope 1 emissions by country",
        "Top 5 facilities by water withdrawal",
        "Trend of waste recycling over the last 3 years",
        "Show women representation by country",
    ]

    for ex in examples:
        if st.button(ex, width="stretch", key=f"ex_{ex}"):
            st.session_state.pending_question = ex

    st.markdown(
        '<div class="section-label">Configuration</div>',
        unsafe_allow_html=True,
    )

    with st.expander("Settings"):
        st.session_state.settings["typing_effect"] = st.toggle(
            "Typing effect for answers",
            value=st.session_state.settings["typing_effect"],
        )

        st.session_state.settings["show_sql_default"] = st.toggle(
            "Show SQL by default",
            value=st.session_state.settings["show_sql_default"],
        )

    with st.expander("How it works"):
        st.markdown(
            "1. Question is classified\n"
            "2. Relevant ESG context is retrieved\n"
            "3. SQL is generated from the database schema\n"
            "4. SQL is validated for safety and schema correctness\n"
            "5. Query runs against the database\n"
            "6. Insight and visualization are prepared"
        )

# ----------------------------------------------------------------------
# Header
# ----------------------------------------------------------------------

st.markdown(
    """
    <div class="app-header">
        <div>
            <div class="eyebrow">ESG Intelligence</div>
            <div class="app-title">Ask your AI a question</div>
            <div class="app-subtitle">
                Get grounded insights, visualizations, and transparent SQL from your enterprise data.
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if not st.session_state.messages:
    st.markdown(
        """
        <div class="welcome-card">
            <div class="welcome-icon">✦</div>
            <div class="welcome-title">ESG Natural Language Analytics</div>
            <div class="welcome-copy">
                Ask about emissions, energy, water, waste, workforce, or compliance
                in plain English. The assistant translates your question into a
                validated query and turns the result into a business-ready insight.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        if msg["role"] == "user":
            st.markdown(msg["content"])
        elif msg["kind"] == "success":
            render_result(idx, msg["result"], animate_insight=False)
        else:
            render_response_note(msg["kind"], msg["content"])

# ----------------------------------------------------------------------
# New question
# ----------------------------------------------------------------------

question = st.chat_input("Ask your question...")
if "pending_question" in st.session_state:
    question = st.session_state.pop("pending_question")

if question:
    st.session_state.messages.append(
        {"role": "user", "content": question, "kind": "user"}
    )
    with st.chat_message("user"):
        st.markdown(question)

    new_idx = len(st.session_state.messages)

    with st.chat_message("assistant"):
        status, payload = run_with_progress(question, st.session_state.history)

        if status == "success":
            render_result(new_idx, payload, animate_insight=True)
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": payload.insight,
                    "kind": "success",
                    "result": payload,
                }
            )
        elif status == "unsupported":
            message = str(
                payload
            )  # safe: UnsupportedQuestionError only ever carries curated text
            render_response_note("unsupported", message)
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": message,
                    "kind": "unsupported",
                    "result": None,
                }
            )
        else:  # "error"
            message = user_message_for_error(payload)
            render_response_note("error", message)
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": message,
                    "kind": "error",
                    "result": None,
                }
            )
