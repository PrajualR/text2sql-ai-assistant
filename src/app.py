import logging
import queue
import threading
import time
import textwrap

import streamlit as st

from database.execute_query import QueryExecutionError
from llm.intent_classifier import IntentClassificationError
from llm.sql_generator import SQLGenerationError
from services.conversation import ConversationContext
from services.sql_service import SQLService, SQLServiceError
from services.validation_service import SQLValidationError
from exceptions import UnsupportedQuestionError


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# Page config + styling
# ----------------------------------------------------------------------

st.set_page_config(
    page_title="ESG Intelligence",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="collapsed",
)


st.html(textwrap.dedent("""
        <style>

        /* ==============================================================
           OCEAN BLUE + CYAN DESIGN SYSTEM
           ============================================================== */

        :root {
            --navy-950: #061827;
            --navy-900: #082238;
            --navy-850: #0A2942;
            --navy-800: #0D3452;
            --navy-700: #124363;

            --cyan: #22D3EE;
            --cyan-bright: #06B6D4;
            --cyan-dark: #0891B2;
            --cyan-soft: #CFFAFE;

            --page-bg: #071A2B;
            --panel-bg: #0A243A;
            --panel-bg-2: #0D2D47;

            --border: #1D4B68;
            --border-soft: #245673;

            --text: #E7F7FC;
            --text-soft: #B8D2DF;
            --muted: #7895A7;
            --muted-dark: #5F7C8E;

            --white: #FFFFFF;

            --success: #34D399;
            --warning: #FBBF24;
            --danger: #FB7185;
        }


        /* ==============================================================
           GLOBAL
           ============================================================== */

        .stApp {
            background: var(--page-bg);
            color: var(--text);
        }

        html,
        body,
        [class*="css"] {
            font-family:
                Inter,
                ui-sans-serif,
                system-ui,
                -apple-system,
                BlinkMacSystemFont,
                "Segoe UI",
                sans-serif;
        }

        #MainMenu,
        footer {
            visibility: hidden;
        }

        [data-testid="stHeader"] {
            background: transparent;
        }

        .block-container {
            max-width: 1450px;
            padding-top: 1.15rem;
            padding-bottom: 5.5rem;
            padding-left: 2rem;
            padding-right: 2rem;
        }


        /* ==============================================================
           NATIVE STREAMLIT SIDEBAR
           Collapsed by default; hamburger opens it.
           ============================================================== */

        section[data-testid="stSidebar"] {
            background: var(--navy-950);
            border-right: 1px solid var(--border);
        }

        section[data-testid="stSidebar"] > div {
            background: var(--navy-950);
        }

        section[data-testid="stSidebar"] .block-container {
            padding: 1.25rem 1rem;
        }

        section[data-testid="stSidebar"] .stButton > button {
            width: 100%;
            min-height: 2.35rem;
            border-radius: 9px;
            border: 1px solid var(--border);
            background: var(--navy-900);
            color: var(--text-soft);
            font-size: .78rem;
            transition:
                background .18s ease,
                border-color .18s ease,
                color .18s ease;
        }

        section[data-testid="stSidebar"] .stButton > button:hover {
            background: var(--navy-800);
            border-color: var(--cyan-dark);
            color: var(--cyan-soft);
        }

        section[data-testid="stSidebar"] [data-testid="stExpander"] {
            border: 1px solid var(--border) !important;
            background: var(--navy-900) !important;
            border-radius: 9px !important;
        }

        section[data-testid="stSidebar"] [data-testid="stExpander"] summary {
            color: var(--text-soft) !important;
        }


        /* ==============================================================
           SIDEBAR BRAND
           ============================================================== */

        .sidebar-brand {
            display: flex;
            align-items: center;
            gap: .7rem;
            margin-bottom: .75rem;
        }

        .brand-mark {
            width: 38px;
            height: 38px;
            border-radius: 11px;
            background: linear-gradient(
                135deg,
                var(--cyan-dark),
                var(--cyan)
            );
            color: var(--navy-950);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            font-weight: 800;
            box-shadow: 0 7px 22px rgba(6, 182, 212, .20);
        }

        .brand-title {
            font-size: .95rem;
            font-weight: 750;
            color: var(--text);
        }

        .brand-subtitle {
            font-size: .66rem;
            color: var(--muted);
            margin-top: 1px;
        }

        .sidebar-description {
            color: var(--text-soft);
            font-size: .72rem;
            line-height: 1.55;
            margin: .9rem 0 1rem;
        }

        .section-label {
            color: var(--cyan);
            font-size: .61rem;
            font-weight: 800;
            letter-spacing: .14em;
            text-transform: uppercase;
            margin: 1.25rem 0 .55rem;
        }


        /* ==============================================================
           TOP HEADER
           ============================================================== */

        .top-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            margin-bottom: 1rem;
        }

        .header-eyebrow {
            color: var(--cyan);
            font-size: .61rem;
            font-weight: 800;
            letter-spacing: .15em;
            text-transform: uppercase;
            margin-bottom: .25rem;
        }

        .header-title {
            color: var(--text);
            font-size: 1.65rem;
            line-height: 1.1;
            font-weight: 760;
            letter-spacing: -.035em;
            margin: 0;
        }

        .header-subtitle {
            color: var(--muted);
            font-size: .72rem;
            margin-top: .32rem;
        }

        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: .4rem;
            padding: .42rem .68rem;
            border: 1px solid var(--border-soft);
            border-radius: 999px;
            background: var(--navy-900);
            color: var(--text-soft);
            font-size: .63rem;
            font-weight: 650;
            white-space: nowrap;
        }

        .status-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: var(--success);
            box-shadow: 0 0 0 4px rgba(52, 211, 153, .09);
        }


        /* ==============================================================
           MAIN TWO-PANE WORKSPACE
           ============================================================== */

        .workspace-shell {
            border: 1px solid var(--border);
            border-radius: 14px;
            background: var(--panel-bg);
            overflow: hidden;
            min-height: 620px;
        }

        .workspace-label {
            color: var(--cyan);
            font-size: .59rem;
            font-weight: 800;
            letter-spacing: .13em;
            text-transform: uppercase;
        }

        .workspace-meta {
            color: var(--muted);
            font-size: .59rem;
        }


        /* ==============================================================
           CONVERSATION PANE
           ============================================================== */

        .conversation-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: .72rem .85rem;
            border-bottom: 1px solid var(--border);
            background: var(--navy-900);
        }

        .conversation-body {
            padding: .65rem;
        }

        .conversation-empty {
            min-height: 500px;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            color: var(--muted);
        }

        .conversation-empty-inner {
            max-width: 250px;
        }

        .conversation-empty-icon {
            width: 38px;
            height: 38px;
            margin: 0 auto .65rem;
            border-radius: 10px;
            border: 1px solid var(--border);
            background: var(--navy-850);
            color: var(--cyan);
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .conversation-empty-title {
            color: var(--text);
            font-size: .78rem;
            font-weight: 700;
            margin-bottom: .25rem;
        }

        .conversation-empty-copy {
            color: var(--muted);
            font-size: .62rem;
            line-height: 1.55;
        }

        .user-log {
            display: flex;
            justify-content: flex-end;
            margin: .5rem 0;
        }

        .user-log-bubble {
            max-width: 88%;
            padding: .48rem .65rem;
            border-radius: 10px 10px 3px 10px;
            background: var(--navy-700);
            border: 1px solid var(--border-soft);
            color: var(--text);
            font-size: .68rem;
            line-height: 1.4;
        }

        .assistant-log {
            display: flex;
            align-items: center;
            gap: .5rem;
            padding: .52rem .58rem;
            margin: .28rem 0 .6rem;
            border: 1px solid var(--border);
            border-radius: 9px;
            background: var(--navy-900);
        }

        .assistant-log-icon {
            width: 23px;
            height: 23px;
            flex-shrink: 0;
            border-radius: 7px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: .68rem;
        }

        .assistant-log-icon.success {
            background: rgba(52, 211, 153, .12);
            color: var(--success);
        }

        .assistant-log-icon.unsupported {
            background: rgba(34, 211, 238, .10);
            color: var(--cyan);
        }

        .assistant-log-icon.error {
            background: rgba(251, 113, 133, .10);
            color: var(--danger);
        }

        .assistant-log-copy {
            min-width: 0;
            flex: 1;
        }

        .assistant-log-title {
            color: var(--text-soft);
            font-size: .65rem;
            font-weight: 700;
        }

        .assistant-log-preview {
            color: var(--muted);
            font-size: .59rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            margin-top: 1px;
        }


        /* ==============================================================
           WORKBENCH PANE
           ============================================================== */

        .workbench-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: .72rem .85rem;
            border-bottom: 1px solid var(--border);
            background: var(--navy-900);
        }

        .workbench-title {
            color: var(--text);
            font-size: .75rem;
            font-weight: 750;
        }

        .workbench-subtitle {
            color: var(--muted);
            font-size: .59rem;
            margin-top: .1rem;
        }

        .workbench-body {
            padding: .85rem;
        }

        .workbench-empty {
            min-height: 500px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .workbench-empty-card {
            max-width: 360px;
            text-align: center;
            border: 1px solid var(--border);
            background: var(--navy-850);
            border-radius: 12px;
            padding: 1.25rem;
        }

        .workbench-empty-icon {
            width: 38px;
            height: 38px;
            border-radius: 10px;
            border: 1px solid var(--border-soft);
            background: rgba(34, 211, 238, .07);
            color: var(--cyan);
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto .65rem;
        }

        .workbench-empty-title {
            color: var(--text);
            font-size: .8rem;
            font-weight: 750;
        }

        .workbench-empty-copy {
            color: var(--muted);
            font-size: .62rem;
            line-height: 1.55;
            margin-top: .3rem;
        }


        /* ==============================================================
           QUESTION INSIDE WORKBENCH
           ============================================================== */

        .question-card {
            border: 1px solid var(--border);
            border-radius: 10px;
            background: var(--navy-900);
            padding: .65rem .75rem;
            margin-bottom: .75rem;
        }

        .question-label {
            color: var(--cyan);
            font-size: .58rem;
            font-weight: 800;
            letter-spacing: .11em;
            text-transform: uppercase;
            margin-bottom: .25rem;
        }

        .question-text {
            color: var(--text);
            font-size: .74rem;
            line-height: 1.45;
        }


        /* ==============================================================
           PROCESSING STATE
           ============================================================== */

        .processing-card {
            border: 1px solid var(--border-soft);
            border-radius: 10px;
            background: var(--navy-850);
            padding: .72rem .8rem;
            margin-bottom: .75rem;
        }

        .thinking-wrap {
            display: flex;
            align-items: center;
            gap: .55rem;
        }

        .thinking-orb {
            width: 8px;
            height: 8px;
            flex-shrink: 0;
            border-radius: 50%;
            background: var(--cyan);
            box-shadow: 0 0 0 5px rgba(34, 211, 238, .08);
            animation: pulseOrb 1.35s ease-in-out infinite;
        }

        .shimmer-text {
            font-size: .72rem;
            font-weight: 550;
            background: linear-gradient(
                90deg,
                var(--muted) 10%,
                var(--cyan) 45%,
                var(--muted) 80%
            );
            background-size: 220% 100%;
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            animation: shimmer 1.5s linear infinite;
        }

        @keyframes shimmer {
            0% {
                background-position: 220% 0;
            }
            100% {
                background-position: -220% 0;
            }
        }

        @keyframes pulseOrb {
            0%,
            100% {
                transform: scale(.8);
                opacity: .5;
            }
            50% {
                transform: scale(1.15);
                opacity: 1;
            }
        }


        /* ==============================================================
           RESULT
           ============================================================== */

        .assistant-result {
            border: 1px solid var(--border);
            border-radius: 11px;
            background: var(--navy-900);
            padding: .78rem .85rem;
            margin-bottom: .7rem;
        }

        .result-label {
            color: var(--cyan);
            font-size: .58rem;
            font-weight: 800;
            letter-spacing: .11em;
            text-transform: uppercase;
            margin-bottom: .35rem;
        }

        .insight-text {
            color: var(--text);
            font-size: .75rem;
            line-height: 1.6;
        }


        /* ==============================================================
           RESPONSE NOTE
           ============================================================== */

        .response-note {
            display: flex;
            align-items: flex-start;
            gap: .65rem;
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: .75rem .8rem;
            background: var(--navy-900);
        }

        .response-note.unsupported {
            border-left: 3px solid var(--cyan);
        }

        .response-note.error {
            border-left: 3px solid var(--danger);
        }

        .response-note-icon {
            font-size: .85rem;
            line-height: 1.4;
            flex-shrink: 0;
        }

        .response-note-title {
            color: var(--text);
            font-size: .73rem;
            font-weight: 700;
            margin-bottom: .2rem;
        }

        .response-note-text {
            color: var(--text-soft);
            font-size: .68rem;
            line-height: 1.5;
        }


        /* ==============================================================
           STREAMLIT WIDGETS
           ============================================================== */

        [data-testid="stExpander"] {
            border: 1px solid var(--border) !important;
            border-radius: 9px !important;
            background: var(--navy-900) !important;
        }

        [data-testid="stExpander"] summary {
            color: var(--text-soft) !important;
            font-size: .68rem !important;
            font-weight: 650 !important;
        }

        [data-testid="stDataFrame"] {
            border: 1px solid var(--border);
            border-radius: 9px;
            overflow: hidden;
        }

        [data-testid="stRadio"] label {
            color: var(--text-soft) !important;
            font-size: .68rem !important;
        }

        [data-testid="stChatInput"] {
            border-radius: 13px !important;
            border: 1px solid var(--border-soft) !important;
            background: var(--navy-900) !important;
        }

        [data-testid="stChatInput"] textarea {
            color: var(--text) !important;
            font-size: .75rem !important;
        }

        [data-testid="stChatInput"] textarea::placeholder {
            color: var(--muted) !important;
        }

        .stButton > button {
            border-radius: 8px;
        }

        .feedback-title {
            color: var(--muted);
            font-size: .62rem;
            font-weight: 650;
            margin-top: .45rem;
            margin-bottom: .15rem;
        }

        .followup-label {
            color: var(--cyan);
            font-size: .59rem;
            font-weight: 800;
            letter-spacing: .1em;
            text-transform: uppercase;
            margin: .85rem 0 .45rem;
        }


        /* ==============================================================
           MOBILE
           ============================================================== */

        @media (max-width: 900px) {
            .block-container {
                padding-left: .75rem;
                padding-right: .75rem;
            }

            .header-title {
                font-size: 1.35rem;
            }

            .status-badge {
                display: none;
            }
        }

        </style>
        """))


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

if "active_message_idx" not in st.session_state:
    st.session_state.active_message_idx = None


# ----------------------------------------------------------------------
# Pipeline stages
# ----------------------------------------------------------------------

PIPELINE_STAGES = [
    "Understanding the question...",
    "Finding the relevant data...",
    "Generating and validating the query...",
    "Running the query...",
    "Preparing the result...",
]

STAGE_SECONDS = 0.9


# ----------------------------------------------------------------------
# Error handling
# ----------------------------------------------------------------------

def user_message_for_error(exc: Exception) -> str:

    if isinstance(exc, IntentClassificationError):
        return (
            "I couldn't determine how to handle that question. "
            "Try rephrasing it as a direct question about the ESG data."
        )

    if isinstance(exc, SQLGenerationError):
        return (
            "I couldn't translate that into a query. "
            "Try naming a specific metric, facility, country, or year."
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
            "Something went wrong running that query against the database. "
            "Please try again."
        )

    if isinstance(exc, SQLServiceError):
        return "I couldn't complete that request. Please try again."

    return "Something unexpected went wrong. Please try again."


# ----------------------------------------------------------------------
# Background pipeline runner
# ----------------------------------------------------------------------

def _run_pipeline(
    question: str,
    history: ConversationContext,
    result_queue: queue.Queue,
):
    """
    Runs entirely off the Streamlit main thread.

    Classification and logging happen here, inside the live except block,
    so the actual exception traceback is still available to the logger.
    """

    try:
        result = SQLService.process_question(question, history)
        result_queue.put(("success", result))

    except UnsupportedQuestionError as exc:
        logger.info("Unsupported request: %s", exc)
        result_queue.put(("unsupported", exc))

    except Exception as exc:
        logger.exception("Pipeline failed while processing question.")
        result_queue.put(("error", exc))


def render_status_line(placeholder, stage_index: int):

    label = PIPELINE_STAGES[stage_index]

    placeholder.markdown(
        textwrap.dedent(
            f"""
            <div class="thinking-wrap">
                <span class="thinking-orb"></span>
                <span class="shimmer-text">{label}</span>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )


def run_with_progress(
    question: str,
    history: ConversationContext,
):
    """
    Runs SQLService.process_question on a background thread while the main
    thread animates one shimmering status line.

    The timer only controls the visual stage pacing.
    Completion itself is controlled by the actual background thread.
    """

    result_queue: queue.Queue = queue.Queue()

    thread = threading.Thread(
        target=_run_pipeline,
        args=(question, history, result_queue),
        daemon=True,
    )

    thread.start()

    status_placeholder = st.empty()

    start = time.time()
    outcome = None

    while outcome is None:

        elapsed = time.time() - start

        stage_index = min(
            int(elapsed / STAGE_SECONDS),
            len(PIPELINE_STAGES) - 1,
        )

        render_status_line(
            status_placeholder,
            stage_index,
        )

        try:
            outcome = result_queue.get(timeout=0.15)

        except queue.Empty:
            continue

    status_placeholder.empty()

    return outcome


# ----------------------------------------------------------------------
# Result rendering
# ----------------------------------------------------------------------

def stream_text(
    container,
    text: str,
    speed: float = 0.02,
    max_chars: int = 450,
):
    """
    Lightweight word-by-word reveal.

    Long responses skip the animation so the UI never feels artificially slow.
    """

    if len(text) > max_chars:
        container.markdown(text)
        return

    words = text.split(" ")

    display = ""

    for word in words:

        display += word + " "

        container.markdown(
            display + "▌"
        )

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

    st.html('<div class="feedback-title">Was this answer helpful?</div>')

    c1, c2, _ = st.columns([0.55, 0.55, 10])

    with c1:

        if st.button(
            "👍",
            key=f"up_{idx}",
        ):
            st.session_state[fb_key] = "up"

    with c2:

        if st.button(
            "👎",
            key=f"down_{idx}",
        ):
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

        if st.button(
            "Submit feedback",
            key=f"submit_{idx}",
        ):

            logger.info(
                "Feedback for message %s: %s | note=%s",
                idx,
                st.session_state.get(f"reason_{idx}"),
                note,
            )

            st.caption("Thanks — noted.")


def render_result(
    idx: int,
    result,
    animate_insight: bool = False,
):
    """
    Render a completed successful answer.

    Unsupported questions and failures never enter this function.
    """

    has_chart = result.chart is not None

    has_data = (
        result.dataframe is not None
        and not result.dataframe.empty
    )

    if (
        animate_insight
        and st.session_state.settings["typing_effect"]
    ):

        insight_container = st.empty()

        stream_text(
            insight_container,
            result.insight,
        )

    else:

        st.html(textwrap.dedent(f"""
                <div class="assistant-result">
                    <div class="result-label">ESG Insight</div>
                    <div class="insight-text">
                        {result.insight}
                    </div>
                </div>
                """))

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
                    config={
                        "displaylogo": False,
                    },
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
                config={
                    "displaylogo": False,
                },
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

            csv = result.dataframe.to_csv(
                index=False
            ).encode("utf-8")

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

        st.code(
            result.sql,
            language="sql",
        )

    with st.expander("Query details"):

        st.html(f"- **Rows returned:** {len(result.dataframe)}\n"
            f"- **Columns:** "
            f"{', '.join(result.dataframe.columns) if not result.dataframe.empty else '—'}\n"
            f"- **Validation:** Passed — read-only query, schema checked, row limit enforced"
        )

    render_feedback(idx)

    if idx == len(st.session_state.messages) - 1 and has_data:

        st.html(
            '<div class="followup-label">Continue exploring</div>')

        followups = get_suggested_followups(
            result.dataframe
        )

        cols = st.columns(
            len(followups)
        )

        for c, suggestion in zip(
            cols,
            followups,
        ):

            with c:

                if st.button(
                    suggestion,
                    key=f"sugg_{idx}_{suggestion}",
                    width="stretch",
                ):

                    st.session_state.pending_question = suggestion

                    st.rerun()


def render_response_note(
    kind: str,
    message: str,
):
    """
    Clean user-facing response for unsupported questions and failures.

    No SQL, chart, table, feedback, query details, or technical
    exception information is shown here.
    """

    if kind == "unsupported":

        icon = "?"
        title = "I can't help with that"
        css_class = "unsupported"

    else:

        icon = "!"
        title = "Unable to complete the request"
        css_class = "error"

    st.html(textwrap.dedent(f"""
            <div class="response-note {css_class}">
                <div class="response-note-icon">{icon}</div>

                <div>
                    <div class="response-note-title">
                        {title}
                    </div>

                    <div class="response-note-text">
                        {message}
                    </div>
                </div>
            </div>
            """))


# ----------------------------------------------------------------------
# Sidebar
# ----------------------------------------------------------------------

with st.sidebar:

    st.html(textwrap.dedent("""
            <div class="sidebar-brand">

                <div class="brand-mark">
                    ◈
                </div>

                <div>
                    <div class="brand-title">
                        ESG Intelligence
                    </div>

                    <div class="brand-subtitle">
                        Natural Language Assistant
                    </div>
                </div>

            </div>
            """))

    st.html(textwrap.dedent("""
            <div class="sidebar-description">
                Analytics over ESG manufacturing data — emissions,
                energy, water, waste, workforce, and compliance
                metrics across facilities.
            </div>
            """))

    if st.button(
        "＋  New conversation",
        width="stretch",
    ):

        st.session_state.messages = []

        st.session_state.history.clear()

        st.session_state.active_message_idx = None

        for key in list(st.session_state.keys()):

            if key.startswith(
                (
                    "feedback_",
                    "reason_",
                    "note_",
                    "view_",
                )
            ):
                del st.session_state[key]

        st.rerun()

    st.html('<div class="section-label">Try asking</div>')

    examples = [
        "Compare Scope 1 emissions by country",
        "Top 5 facilities by water withdrawal",
        "Trend of waste recycling over the last 3 years",
        "Show women representation by country",
    ]

    for ex in examples:

        if st.button(
            ex,
            width="stretch",
            key=f"ex_{ex}",
        ):

            st.session_state.pending_question = ex


    st.html('<div class="section-label">Configuration</div>')

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

        st.html("1. Question is classified\n"
            "2. Relevant ESG context is retrieved\n"
            "3. SQL is generated from the database schema\n"
            "4. SQL is validated for safety and schema correctness\n"
            "5. Query runs against the database\n"
            "6. Insight and visualization are prepared"
        )


# ----------------------------------------------------------------------
# Input resolution
# ----------------------------------------------------------------------

question = st.chat_input(
    "Ask a question about your ESG data..."
)

if "pending_question" in st.session_state:

    question = st.session_state.pop(
        "pending_question"
    )


# ----------------------------------------------------------------------
# Add new user message BEFORE layout
# ----------------------------------------------------------------------

just_asked = False

if question:

    question = question.strip()

    if question:

        st.session_state.messages.append(
            {
                "role": "user",
                "content": question,
                "kind": "user",
            }
        )

        just_asked = True


# ----------------------------------------------------------------------
# Resolve active workbench item
# ----------------------------------------------------------------------

def resolve_active_idx():

    active = st.session_state.get(
        "active_message_idx"
    )

    if (
        active is not None
        and 0 <= active < len(st.session_state.messages)
        and st.session_state.messages[active].get("kind")
        in (
            "success",
            "unsupported",
            "error",
        )
    ):
        return active

    for idx in range(
        len(st.session_state.messages) - 1,
        -1,
        -1,
    ):

        msg = st.session_state.messages[idx]

        if msg.get("kind") in (
            "success",
            "unsupported",
            "error",
        ):
            return idx

    return None


# ----------------------------------------------------------------------
# Header
# ----------------------------------------------------------------------

st.html(textwrap.dedent("""
        <div class="top-header">

            <div>

                <div class="header-eyebrow">
                    ESG Intelligence
                </div>

                <div class="header-title">
                    Analytics Workbench
                </div>

                <div class="header-subtitle">
                    Ask questions in natural language and inspect
                    grounded insights, visualizations, and validated SQL.
                </div>

            </div>

            <div class="status-badge">
                <span class="status-dot"></span>
                Ready
            </div>

        </div>
        """))


# ----------------------------------------------------------------------
# Two-pane workspace
# ----------------------------------------------------------------------

left_col, right_col = st.columns(
    [0.40, 0.60],
    gap="small",
)


# ----------------------------------------------------------------------
# LEFT — Conversation
# ----------------------------------------------------------------------

with left_col:

    st.html(textwrap.dedent("""
            <div class="workspace-shell">

                <div class="conversation-header">
                    <span class="workspace-label">
                        Conversation
                    </span>

                    <span class="workspace-meta">
                        Recent questions
                    </span>
                </div>

            </div>
            """))

    # The actual conversation widgets are rendered immediately below
    # the header. Keeping them outside the HTML shell prevents Streamlit
    # widgets from being swallowed by custom HTML.

    if not st.session_state.messages:

        st.html(textwrap.dedent("""
                <div class="conversation-empty">
                    <div class="conversation-empty-inner">

                        <div class="conversation-empty-icon">
                            ✦
                        </div>

                        <div class="conversation-empty-title">
                            No questions yet
                        </div>

                        <div class="conversation-empty-copy">
                            Ask an ESG analytics question to start
                            the conversation.
                        </div>

                    </div>
                </div>
                """))

    else:

        for idx, msg in enumerate(
            st.session_state.messages
        ):

            if msg.get("role") == "user":

                st.html(textwrap.dedent(f"""
                        <div class="user-log">
                            <div class="user-log-bubble">
                                {msg["content"]}
                            </div>
                        </div>
                        """))

                continue

            kind = msg.get(
                "kind",
                "error",
            )

            if kind == "success":

                icon = "✓"
                title = "Analysis ready"

            elif kind == "unsupported":

                icon = "?"
                title = "Unsupported question"

            else:

                icon = "!"
                title = "Request failed"

            preview = (
                msg.get("content", "")
                .replace("\n", " ")
                .strip()
            )

            if len(preview) > 70:
                preview = preview[:70] + "..."

            icon_class = kind

            row_col, view_col = st.columns(
                [8, 2],
                gap="small",
            )

            with row_col:

                st.html(textwrap.dedent(f"""
                        <div class="assistant-log">

                            <div class="assistant-log-icon {icon_class}">
                                {icon}
                            </div>

                            <div class="assistant-log-copy">

                                <div class="assistant-log-title">
                                    {title}
                                </div>

                                <div class="assistant-log-preview">
                                    {preview}
                                </div>

                            </div>

                        </div>
                        """))

            with view_col:

                if st.button(
                    "View →",
                    key=f"view_message_{idx}",
                    width="stretch",
                ):

                    st.session_state.active_message_idx = idx

                    st.rerun()


# ----------------------------------------------------------------------
# RIGHT — Analytical Workbench
# ----------------------------------------------------------------------

with right_col:

    st.html(textwrap.dedent("""
            <div class="workspace-shell">

                <div class="workbench-header">

                    <div>

                        <div class="workbench-title">
                            Analytical Workbench
                        </div>

                        <div class="workbench-subtitle">
                            Inspect the selected response
                        </div>

                    </div>

                </div>

            </div>
            """))

    # --------------------------------------------------------------
    # Fresh question: execute pipeline here
    # --------------------------------------------------------------

    if just_asked:

        current_user_idx = (
            len(st.session_state.messages) - 1
        )

        current_question = (
            st.session_state.messages[
                current_user_idx
            ]["content"]
        )

        st.html(textwrap.dedent(f"""
                <div class="question-card">

                    <div class="question-label">
                        Your question
                    </div>

                    <div class="question-text">
                        {current_question}
                    </div>

                </div>
                """))

        st.html(
            '<div class="processing-card">')

        status, payload = run_with_progress(
            current_question,
            st.session_state.history,
        )

        st.html('</div>')

        if status == "success":

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": payload.insight,
                    "kind": "success",
                    "result": payload,
                }
            )

            assistant_idx = (
                len(st.session_state.messages) - 1
            )

            st.session_state.active_message_idx = (
                assistant_idx
            )

            render_result(
                assistant_idx,
                payload,
                animate_insight=True,
            )

        elif status == "unsupported":

            message = str(payload)

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": message,
                    "kind": "unsupported",
                    "result": None,
                }
            )

            assistant_idx = (
                len(st.session_state.messages) - 1
            )

            st.session_state.active_message_idx = (
                assistant_idx
            )

            render_response_note(
                "unsupported",
                message,
            )

        else:

            message = user_message_for_error(
                payload
            )

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": message,
                    "kind": "error",
                    "result": None,
                }
            )

            assistant_idx = (
                len(st.session_state.messages) - 1
            )

            st.session_state.active_message_idx = (
                assistant_idx
            )

            render_response_note(
                "error",
                message,
            )


    # --------------------------------------------------------------
    # Existing conversation: inspect selected result
    # --------------------------------------------------------------

    else:

        active_idx = resolve_active_idx()

        if active_idx is None:

            st.html(textwrap.dedent("""
                    <div class="workbench-empty">

                        <div class="workbench-empty-card">

                            <div class="workbench-empty-icon">
                                ✦
                            </div>

                            <div class="workbench-empty-title">
                                Your analytical workspace
                            </div>

                            <div class="workbench-empty-copy">
                                Select a completed answer from the
                                conversation, or ask a new question below.
                                Results, visualizations, SQL, validation
                                details, and feedback appear here.
                            </div>

                        </div>

                    </div>
                    """))

        else:

            msg = st.session_state.messages[
                active_idx
            ]

            if msg.get("role") == "assistant":

                user_question = ""

                if active_idx > 0:

                    previous = (
                        st.session_state.messages[
                            active_idx - 1
                        ]
                    )

                    if previous.get("role") == "user":
                        user_question = previous.get(
                            "content",
                            "",
                        )

                if user_question:

                    st.html(textwrap.dedent(f"""
                            <div class="question-card">

                                <div class="question-label">
                                    Question
                                </div>

                                <div class="question-text">
                                    {user_question}
                                </div>

                            </div>
                            """))

                if msg.get("kind") == "success":

                    render_result(
                        active_idx,
                        msg["result"],
                        animate_insight=False,
                    )

                else:

                    render_response_note(
                        msg.get("kind", "error"),
                        msg.get(
                            "content",
                            "",
                        ),
                    )


# ----------------------------------------------------------------------
# Small bottom hint
# ----------------------------------------------------------------------

if not st.session_state.messages:

    st.html(textwrap.dedent("""
            <div style="
                text-align:center;
                color:#5F7C8E;
                font-size:.61rem;
                margin-top:.7rem;
            ">
                Ask about emissions, energy, water, waste,
                workforce, facilities, countries, or years.
            </div>
            """))