import html
import time
from datetime import datetime

import streamlit as st

from agent.llm import AVAILABLE_MODELS
from agent.mcp_client import run_mcp_tool_sync
from agent.planner import plan_query
from agent.prompts import TOOL_NAME
from agent.reflexion import classify_execution, execute_with_reflexion, reflect_query
from agent.synthesizer import synthesize_final_answer
from ui.metrics import audit_rows, build_run_record, compute_kpis, runs_to_csv
from ui.rbac_display import ROLES, policy_for
from ui.scenarios import (
    FILTER_GROUPS,
    scenario_label_for_prompt,
    scenarios_in_group,
)

# streamlit run app3.py
st.set_page_config(
    page_title="Secure Agentic BI — Console",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;550;600;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

:root {
  --ink: #0f1c2e;
  --muted: #5b6b7c;
  --panel: #ffffff;
  --line: #d7e0ea;
  --teal: #0d9488;
  --teal-deep: #0f766e;
  --sand: #f3f7f9;
  --danger: #c23b3b;
  --ok: #1f7a4d;
}

.stApp, .stApp p, .stApp span, .stApp label, .stApp div {
  font-family: "IBM Plex Sans", sans-serif;
}

.stApp {
  background:
    radial-gradient(1200px 500px at 10% -10%, #d9f3ef 0%, transparent 55%),
    radial-gradient(900px 420px at 95% 0%, #e7eef8 0%, transparent 50%),
    linear-gradient(180deg, #f7fafc 0%, #eef3f7 100%);
  color: var(--ink);
}

footer {visibility: hidden;}

header[data-testid="stHeader"] {
  background: rgba(247, 250, 252, 0.94) !important;
  border-bottom: 1px solid var(--line);
}

.block-container {
  padding-top: 3.75rem !important;
  padding-bottom: 2.5rem;
  max-width: 1280px;
}

.sabi-top h1 {
  font-family: Sora, sans-serif;
  font-size: 1.65rem;
  font-weight: 700;
  line-height: 1.25;
  margin: 0 0 0.3rem;
  color: var(--ink);
}
.sabi-top p {
  margin: 0 0 0.9rem;
  color: var(--muted);
  font-size: 0.95rem;
}

section[data-testid="stSidebar"] {
  min-width: 22rem !important;
  width: 22rem !important;
  display: block !important;
  visibility: visible !important;
  transform: none !important;
}

.sabi-tables {
  list-style: none;
  margin: 0.15rem 0 0.75rem;
  padding: 0;
}
.sabi-tables li {
  font-size: 0.78rem;
  line-height: 1.4;
  color: #0f1c2e;
  margin: 0 0 0.28rem;
  overflow-wrap: normal;
  word-break: normal;
}
.sabi-none {
  margin: 0 0 0.75rem;
  color: #334155;
  font-size: 0.84rem;
}
.sabi-policy-meta {
  display: flex;
  flex-direction: column;
  gap: 0.22rem;
  margin-top: 0.15rem;
}
.sabi-policy-meta span {
  display: block;
  white-space: nowrap;
  font-size: 0.84rem;
  color: #334155;
}

.sabi-section {
  font-family: Sora, sans-serif;
  font-size: 1.05rem;
  font-weight: 650;
  color: var(--ink);
  margin: 1.35rem 0 0.75rem;
}

.pipeline {
  display: grid;
  grid-template-columns: repeat(8, minmax(0, 1fr));
  gap: 0.45rem;
  background: rgba(255,255,255,0.72);
  border: 1px solid var(--line);
  border-radius: 18px;
  padding: 1rem;
  backdrop-filter: blur(8px);
}
.pipe-node {
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 0.75rem 0.55rem;
  text-align: center;
  min-height: 96px;
  box-shadow: 0 6px 16px rgba(15,28,46,0.04);
}
.pipe-node .ico { font-size: 1.25rem; margin-bottom: 0.25rem; }
.pipe-node .ttl {
  font-family: Sora, sans-serif;
  font-size: 0.72rem;
  font-weight: 650;
  color: var(--ink);
  line-height: 1.25;
}
.pipe-node .sub {
  font-size: 0.65rem;
  color: var(--muted);
  margin-top: 0.2rem;
}
.pipe-node.guard {
  border-color: #f0b4b4;
  background: linear-gradient(180deg, #fff7f7, #fff);
}
.pipe-node.db {
  border-color: #9fd6cf;
  background: linear-gradient(180deg, #f2fffc, #fff);
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.75rem;
}
.sabi-card {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 16px;
  padding: 1rem 1.05rem;
  box-shadow: 0 8px 20px rgba(15,28,46,0.04);
  height: 100%;
}
.sabi-card h4 {
  font-family: Sora, sans-serif;
  font-size: 0.92rem;
  margin: 0 0 0.4rem 0;
  color: var(--ink);
}
.sabi-card p {
  margin: 0;
  font-size: 0.86rem;
  color: var(--muted);
  line-height: 1.45;
}

.step {
  background: #fff;
  border-radius: 16px;
  border: 1px solid var(--line);
  padding: 1rem 1.05rem 1.05rem;
  position: relative;
  overflow: hidden;
  height: 100%;
}
.step::before {
  content: "";
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 4px;
  background: linear-gradient(180deg, #0d9488, #16324f);
}
.step h4 {
  font-family: Sora, sans-serif;
  font-size: 0.98rem;
  margin: 0 0 0.35rem 0;
}
.step p {
  margin: 0;
  color: var(--muted);
  font-size: 0.86rem;
  line-height: 1.45;
}

.adv {
  background: #fff;
  border: 1px solid var(--line);
  border-left: 5px solid var(--teal);
  border-radius: 14px;
  padding: 0.9rem 1rem;
  margin-bottom: 0.55rem;
}
.adv strong {
  font-family: Sora, sans-serif;
  color: var(--ink);
}
.adv span {
  color: var(--muted);
  font-size: 0.9rem;
}

.answer-box {
  background: linear-gradient(180deg, #f2fffc, #ffffff);
  border: 1px solid #b7e4dc;
  border-radius: 16px;
  padding: 1rem 1.1rem;
  margin-top: 0.9rem;
}
.answer-box .label {
  font-family: Sora, sans-serif;
  font-size: 0.78rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--teal-deep);
  font-weight: 700;
  margin-bottom: 0.35rem;
}

section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #f7fbfb 0%, #eef5f8 100%) !important;
  border-right: 1px solid var(--line);
}
[data-testid="stHeading"],
[data-testid="stHeading"] *,
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3,
[data-testid="stMarkdownContainer"] h4,
[data-testid="stMarkdownContainer"] h5,
[data-testid="stMetricLabel"],
[data-testid="stMetricValue"],
[data-testid="stMetricDelta"] {
  color: #0f1c2e !important;
}

section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stMarkdown li,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stCaption,
section[data-testid="stSidebar"] [data-testid="stHeading"],
section[data-testid="stSidebar"] [data-testid="stHeading"] * {
  color: #334155 !important;
}
[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] span {
  color: #334155 !important;
}
div[data-testid="stAlert"] [data-testid="stMarkdownContainer"],
div[data-testid="stAlert"] [data-testid="stMarkdownContainer"] p,
div[data-testid="stAlert"] [data-testid="stMarkdownContainer"] span,
div[data-testid="stAlert"] [data-testid="stMarkdownContainer"] li,
div[data-testid="stAlert"] [data-testid="stMarkdownContainer"] code {
  color: #0f1c2e !important;
  -webkit-text-fill-color: #0f1c2e !important;
  background: transparent !important;
  background-color: transparent !important;
}

[data-testid="stMarkdownContainer"] p code,
[data-testid="stMarkdownContainer"] li code,
[data-testid="stMarkdownContainer"] td code {
  background: transparent !important;
  background-color: transparent !important;
  color: #0f766e !important;
  -webkit-text-fill-color: #0f766e !important;
  padding: 0;
  border-radius: 0;
  font-weight: 650;
}

div[data-testid="stTextArea"] textarea {
  color: #0f1c2e !important;
  -webkit-text-fill-color: #0f1c2e !important;
  caret-color: #0f1c2e !important;
  background-color: #ffffff !important;
  border: 1px solid #c5d0dc !important;
  border-radius: 12px !important;
}
div[data-testid="stTextArea"] textarea::placeholder {
  color: #6b7c8f !important;
  -webkit-text-fill-color: #6b7c8f !important;
  opacity: 1 !important;
}

div[data-baseweb="select"] > div {
  background-color: #ffffff !important;
  color: #0f1c2e !important;
  border-color: #c5d0dc !important;
}
div[data-baseweb="popover"] li,
ul[role="listbox"] li {
  color: #0f1c2e !important;
  background-color: #ffffff !important;
}

[data-testid="stButtonGroup"] [data-baseweb="button-group"] {
  background: transparent;
}
[data-testid="stButtonGroup"] button {
  background: #ffffff !important;
  color: #334155 !important;
  border-color: #d7e0ea !important;
  font-family: Sora, sans-serif !important;
  font-weight: 600 !important;
}
[data-testid="stButtonGroup"] button p,
[data-testid="stButtonGroup"] button span {
  color: inherit !important;
}
[data-testid="stButtonGroup"] button:hover,
[data-testid="stButtonGroup"] button:focus-visible {
  background: #f3f7f9 !important;
  color: #0f1c2e !important;
}
[data-testid="stButtonGroup"] button[kind="segmented_controlActive"] {
  background: #e6f5f2 !important;
  color: #0f766e !important;
  border-color: #8ccfc5 !important;
}

div[data-testid="stExpander"] details summary {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  line-height: 1.4;
}
div[data-testid="stExpander"] details summary > span,
div[data-testid="stExpander"] details summary svg {
  flex: 0 0 auto;
}
div[data-testid="stExpander"] details summary p {
  margin: 0;
}

.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, #0d9488, #0f766e);
  border: none;
  border-radius: 12px;
  font-family: Sora, sans-serif;
  font-weight: 650;
  padding: 0.55rem 1.2rem;
  box-shadow: 0 8px 18px rgba(13,148,136,0.28);
}
.stButton > button[kind="primary"]:hover {
  background: linear-gradient(135deg, #0f766e, #115e59);
  border: none;
}

[data-testid="stDataFrame"] {
  background: #ffffff !important;
  border: 1px solid #d7e0ea !important;
  border-radius: 12px !important;
  overflow: hidden;
}
[data-testid="stDataFrame"] [data-testid="stDataFrameResizable"] {
  background: #ffffff !important;
}

.stDownloadButton > button {
  background: #ffffff !important;
  color: #0f1c2e !important;
  border: 1px solid #c5d0dc !important;
  border-radius: 12px !important;
  font-family: Sora, sans-serif !important;
  font-weight: 650 !important;
  box-shadow: none !important;
}
.stDownloadButton > button:hover,
.stDownloadButton > button:focus-visible {
  background: #f3f7f9 !important;
  color: #0f1c2e !important;
  border-color: #8ccfc5 !important;
}
.stDownloadButton > button p,
.stDownloadButton > button span {
  color: #0f1c2e !important;
}

@media (max-width: 1100px) {
  .pipeline { grid-template-columns: repeat(2, 1fr); }
  .card-grid { grid-template-columns: 1fr; }
}
</style>
""",
    unsafe_allow_html=True,
)


def _yes_no(flag: bool) -> str:
    return "Có" if flag else "Không"


def _breakable_name(name: str) -> str:
    """Allow wrapping only after a dot or underscore, never inside a word."""
    escaped = html.escape(name)
    return escaped.replace(".", ".<wbr>").replace("_", "_<wbr>")


def _table_items(tables: list[str]) -> str:
    if not tables:
        return "<p class='sabi-none'>Không có</p>"
    rows = "".join(f"<li>{_breakable_name(name)}</li>" for name in tables)
    return f"<ul class='sabi-tables'>{rows}</ul>"


def execute_prompt(user_input: str, selected_model: str, selected_role: str) -> dict:
    """Run the existing planner → reflexion → synthesizer path and record it."""
    started = time.perf_counter()
    thought = ""
    answer = ""
    synth_model = ""
    route_model = ""
    tool_arguments = None
    attempts: list[dict] = []
    sql = ""
    result_text = ""
    planner_ok = False
    trace_outcome = None
    attempt_outcomes: list[str] = []

    agent_plan = plan_query(user_input, selected_model)
    if not agent_plan:
        result_text = "Planner không trả về kế hoạch."
    else:
        route_model = str(agent_plan.get("model_used") or "")
        thought = str(agent_plan.get("thought") or "")
        tool_call = agent_plan.get("tool_call")
        if not tool_call:
            result_text = "Planner không trả về tool call."
        else:
            planner_ok = True
            tool_arguments = dict(tool_call.get("arguments") or {})
            query = tool_arguments.get("query") or ""
            output_file = tool_arguments.get("output_file")
            sql = query
            if not query:
                result_text = "Error: Planner did not return a SQL query."
                raw_data_to_llm = (
                    "Hệ thống bảo mật đã chặn truy vấn với lý do: " + result_text
                )
            else:

                def _execute(statement: str) -> str:
                    arguments = {"query": statement, "role": selected_role}
                    if output_file:
                        arguments["output_file"] = output_file
                    return run_mcp_tool_sync(TOOL_NAME, arguments)

                def _reflect(failed_sql: str, error: str):
                    return reflect_query(
                        user_input, failed_sql, error, selected_model
                    )

                trace = execute_with_reflexion(query, _execute, _reflect)
                result_text = trace.result
                trace_outcome = trace.outcome
                sql = trace.query or query
                attempts = [
                    {
                        "query": item.query,
                        "result": item.result,
                        "outcome": item.outcome,
                    }
                    for item in trace.attempts
                ]
                attempt_outcomes = [item.outcome for item in trace.attempts]
                blocked = trace.outcome != "ok"
                security_stop = blocked and classify_execution(trace.result) == "abort"
                if blocked:
                    if security_stop:
                        raw_data_to_llm = (
                            "Hệ thống bảo mật đã chặn truy vấn với lý do: "
                            f"{result_text}"
                        )
                    else:
                        raw_data_to_llm = (
                            "Truy vấn vẫn lỗi sau khi sửa SQL: " f"{result_text}"
                        )
                elif "output_file" not in tool_call["arguments"]:
                    raw_data_to_llm = result_text
                    st.toast("Dữ liệu đọc trực tiếp từ Database!", icon="🧠")
                else:
                    export_path = tool_call["arguments"]["output_file"]
                    try:
                        with open(export_path, "r", encoding="utf-8") as handle:
                            lines = handle.readlines()
                        raw_data_to_llm = "".join(lines[:500])
                        if len(lines) > 500:
                            raw_data_to_llm += (
                                "\n... (Dữ liệu đã được cắt bớt để bảo vệ bộ nhớ)"
                            )
                        st.toast(
                            f"Đã đọc dữ liệu từ file {export_path}",
                            icon="📁",
                        )
                    except FileNotFoundError:
                        raw_data_to_llm = (
                            "Lỗi: Không tìm thấy file dữ liệu sau khi truy vấn."
                        )

            answer, synth_model = synthesize_final_answer(
                user_input, raw_data_to_llm, selected_model
            )

    return build_run_record(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        role=selected_role,
        model=route_model or selected_model,
        scenario=scenario_label_for_prompt(user_input),
        latency_ms=int((time.perf_counter() - started) * 1000),
        planner_ok=planner_ok,
        trace_outcome=trace_outcome,
        result=result_text,
        attempt_outcomes=attempt_outcomes,
        sql=sql,
        thought=thought,
        answer=answer,
        synth_model=synth_model,
        route_model=route_model,
        attempts=attempts,
        tool_arguments=tool_arguments,
    )


def render_answer(record: dict) -> None:
    if not record.get("answer"):
        return
    st.markdown(
        """
<div class="answer-box">
  <div class="label">Phản hồi từ Agent</div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.write(record["answer"])
    if record.get("synth_model"):
        st.caption(f"Tổng hợp bởi model: **{record['synth_model']}**")


def render_trace(record: dict) -> None:
    route = record.get("route_model") or record.get("model") or "—"
    st.caption(
        f"Routing: **{route}** · role: **{record.get('role')}** · "
        f"{record.get('latency_ms')} ms · {record.get('outcome')} · "
        f"guardrail: {record.get('guardrail')}"
    )
    if record.get("thought"):
        st.info(record["thought"])
    if record.get("tool_arguments") is not None:
        st.json(record["tool_arguments"])
    for attempt in record.get("attempts") or []:
        if attempt.get("outcome") != "retry":
            continue
        st.warning("Lỗi kỹ thuật, sửa SQL rồi chạy lại.")
        st.code(attempt.get("query") or "", language="sql")
        st.caption(attempt.get("result") or "")
    outcome = record.get("outcome")
    if record.get("sql_full"):
        if outcome == "retried_ok":
            st.caption("SQL sau khi sửa")
        st.code(record["sql_full"], language="sql")
    if outcome in {"ok", "retried_ok"}:
        st.success(record.get("result") or "")
    else:
        st.error(record.get("result") or "Không thực thi được.")


def filter_runs(runs: list[dict], role: str, outcome: str) -> list[dict]:
    selected = runs
    if role != "Tất cả":
        selected = [item for item in selected if item.get("role") == role]
    if outcome != "Tất cả":
        selected = [item for item in selected if item.get("outcome") == outcome]
    return selected


VIEWS = ["Console", "Kịch bản", "Audit", "Kiến trúc"]


def selected_scenario():
    group_col, scenario_col = st.columns([1, 3], gap="small")
    with group_col:
        group = st.selectbox("Nhóm", FILTER_GROUPS, key="sabi_group")
    items = scenarios_in_group(group)
    titles = [item.title for item in items]
    if st.session_state.get("sabi_scenario_pick") not in titles:
        st.session_state.sabi_scenario_pick = titles[0]
    with scenario_col:
        choice = st.selectbox("Kịch bản", titles, key="sabi_scenario_pick")
    return next(item for item in items if item.title == choice)


def apply_scenario_prompt(scenario) -> None:
    """Fill the console prompt before the text area widget is created."""
    if st.session_state.get("sabi_prompt_scenario") == scenario.title:
        return
    st.session_state.sabi_prompt = scenario.prompt
    st.session_state.sabi_prompt_scenario = scenario.title


if st.session_state.pop("sabi_open_console", False):
    st.session_state.sabi_view = "Console"

pending_prompt = st.session_state.pop("sabi_pending_prompt", None)
if pending_prompt is not None:
    st.session_state.sabi_prompt = pending_prompt
    st.session_state.sabi_prompt_scenario = st.session_state.get("sabi_scenario_pick")

if "sabi_view" not in st.session_state:
    st.session_state.sabi_view = "Console"

if "runs" not in st.session_state:
    st.session_state.runs = []

with st.sidebar:
    st.markdown("### Cấu hình")
    selected_model = st.selectbox(
        "Model ưu tiên (Primary)",
        AVAILABLE_MODELS,
        key="sabi_model",
    )
    selected_role = st.selectbox("Role", ROLES, key="sabi_role")
    # st.caption(
    #     "Nếu model chính hết Quota (429), hệ thống tự Fallback sang model kế tiếp. "
    #     "Role này được gửi tới Gateway và ghi đè role do model trả về."
    # )
    policy = policy_for(selected_role)
    with st.container(border=True):
        st.markdown(f"**Quyền · {selected_role}**")
        st.markdown("**Được phép**")
        st.markdown(_table_items(policy["allowed_tables"]), unsafe_allow_html=True)
        st.markdown("**Bị cấm**")
        st.markdown(_table_items(policy["denied_tables"]), unsafe_allow_html=True)
        st.markdown(
            f"""
<div class="sabi-policy-meta">
  <span>Export: {_yes_no(policy["can_export"])}</span>
  <span>PII: {_yes_no(policy["can_access_pii"])}</span>
  <span>Tối đa {policy["max_rows"]} dòng</span>
</div>
""",
            unsafe_allow_html=True,
        )
    if st.button("Xóa phiên", use_container_width=True, key="sabi_clear"):
        st.session_state.runs = []
        st.session_state.last_run = None
        st.rerun()

st.markdown(
    """
<div class="sabi-top">
  <h1>Secure Agentic BI</h1>
</div>
""",
    unsafe_allow_html=True,
)
kpis = compute_kpis(st.session_state.runs)
kpi_runs, kpi_blocked, kpi_fixed, kpi_latency = st.columns(4)
kpi_runs.metric("Lượt chạy", kpis["total"])
kpi_blocked.metric("Bị chặn", kpis["blocked"])
kpi_fixed.metric("Reflexion sửa được", kpis["retried_ok"])
latency_value = (
    "—" if kpis["last_latency_ms"] is None else str(kpis["last_latency_ms"])
)
kpi_latency.metric("Độ trễ gần nhất (ms)", latency_value)

view = st.segmented_control(
    "Màn hình",
    VIEWS,
    key="sabi_view",
    label_visibility="collapsed",
    required=True,
    width="stretch",
)
if view not in VIEWS:
    view = "Console"

if view == "Console":
    scenario = selected_scenario()
    apply_scenario_prompt(scenario)
    col_chat, col_log = st.columns([6, 4], gap="large")
    with col_chat:
        with st.container(border=True):
            st.markdown("##### Console")
            st.caption(scenario.title)
            user_input = st.text_area(
                "Prompt gửi tới Agent",
                height=160,
                key="sabi_prompt",
                placeholder="Nhập hoặc chỉnh prompt tấn công / truy vấn…",
            )
            send = st.button(
                "Gửi yêu cầu",
                type="primary",
                use_container_width=True,
                key="sabi_send",
            )
    if send:
        started = time.perf_counter()
        with st.spinner(f"Đang xử lý qua `{selected_model}`..."):
            try:
                record = execute_prompt(user_input, selected_model, selected_role)
            except Exception as exc:
                record = build_run_record(
                    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    role=selected_role,
                    model=selected_model,
                    scenario=scenario_label_for_prompt(user_input),
                    latency_ms=int((time.perf_counter() - started) * 1000),
                    planner_ok=False,
                    trace_outcome=None,
                    result=f"Lỗi pipeline: {exc}",
                    attempt_outcomes=[],
                    sql="",
                )
        st.session_state.runs.append(record)
        st.session_state.last_run = record
        st.rerun()

    last_run = st.session_state.get("last_run")
    with col_chat:
        if last_run:
            render_answer(last_run)
    with col_log:
        if last_run:
            with st.container(border=True):
                st.markdown("##### Trace lần chạy gần nhất")
                render_trace(last_run)

if view == "Kịch bản":
    selected = selected_scenario()
    if st.session_state.get("sabi_preview_for") != selected.title:
        st.session_state.sabi_scenario_preview = selected.prompt
        st.session_state.sabi_preview_for = selected.title
    with st.container(border=True):
        st.markdown(f"**{selected.attack_group}**")
        st.markdown(selected.summary)
        st.markdown(f"**Mục tiêu:** {selected.targets}")
        st.markdown(f"**Guardrail kỳ vọng:** {selected.expected_guardrail}")
        st.markdown(f"**Cơ sở khoa học:** {selected.science}")
        st.text_area(
            "Prompt của kịch bản",
            height=140,
            key="sabi_scenario_preview",
            disabled=True,
        )
        if st.button("Mở trên Console", type="primary", key="sabi_use_prompt"):
            st.session_state.sabi_pending_prompt = selected.prompt
            st.session_state.sabi_open_console = True
            st.rerun()

if view == "Audit":
    runs = st.session_state.runs
    if not runs:
        st.info("Chưa có lần chạy trong phiên này.")
    else:
        filter_role, filter_outcome = st.columns(2)
        with filter_role:
            role_choice = st.selectbox(
                "Role",
                ["Tất cả", *ROLES],
                key="sabi_audit_role",
            )
        with filter_outcome:
            outcome_choice = st.selectbox(
                "Outcome",
                ["Tất cả", "ok", "blocked", "retried_ok", "failed"],
                key="sabi_audit_outcome",
            )
        visible = filter_runs(runs, role_choice, outcome_choice)
        st.dataframe(audit_rows(visible), use_container_width=True, hide_index=True)
        st.download_button(
            "Xuất CSV",
            runs_to_csv(visible),
            file_name="security_audit.csv",
            mime="text/csv",
            key="sabi_audit_csv",
        )

if view == "Kiến trúc":
    st.markdown(
        '<div class="sabi-section">Sơ đồ luồng hệ thống</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
<div class="pipeline">
  <div class="pipe-node"><div class="ico">👤</div><div class="ttl">User / Hacker</div><div class="sub">NL prompt</div></div>
  <div class="pipe-node"><div class="ico">🖥️</div><div class="ttl">Streamlit UI</div><div class="sub">Defense console</div></div>
  <div class="pipe-node"><div class="ico">🧠</div><div class="ttl">Gemini Routing</div><div class="sub">NL → JSON plan</div></div>
  <div class="pipe-node"><div class="ico">🔌</div><div class="ttl">JSON-RPC Stdio</div><div class="sub">MCP transport</div></div>
  <div class="pipe-node"><div class="ico">⚙️</div><div class="ttl">Trino MCP</div><div class="sub">Tool gateway</div></div>
  <div class="pipe-node guard"><div class="ico">🛡️</div><div class="ttl">Guardrails</div><div class="sub">AST + Taint</div></div>
  <div class="pipe-node db"><div class="ico">🐘</div><div class="ttl">PostgreSQL</div><div class="sub">pg · 13 tables</div></div>
  <div class="pipe-node db"><div class="ico">🐬</div><div class="ttl">MySQL</div><div class="sub">mysql · 8 tables</div></div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.caption("Mọi SQL phải qua Guardrails trước khi chạm database.")

    st.markdown(
        '<div class="sabi-section">Vai trò từng thành phần</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
<div class="card-grid">
  <div class="sabi-card"><h4>User / Hacker</h4><p>Gửi yêu cầu ngôn ngữ tự nhiên — phân tích hợp lệ hoặc payload red-team.</p></div>
  <div class="sabi-card"><h4>Streamlit UI</h4><p>Chọn model, role, kịch bản, rồi xem trace và câu trả lời.</p></div>
  <div class="sabi-card"><h4>Gemini LLM</h4><p>Đổi ý định thành JSON tool call. Fallback khi hết Quota 429.</p></div>
  <div class="sabi-card"><h4>JSON-RPC (Stdio)</h4><p>Kênh MCP: Agent không giữ credential DB, chỉ gọi tool đã đăng ký.</p></div>
  <div class="sabi-card"><h4>Guardrails</h4><p>AST Parser đọc cú pháp SQL; policy role chặn object ngoài allow-list.</p></div>
  <div class="sabi-card"><h4>PostgreSQL</h4><p>Core ERP: Orders, HR/Payroll, API Keys, Finance.</p></div>
  <div class="sabi-card"><h4>MySQL</h4><p>Portal: Tickets, Reviews, Logs, bộ nhớ Agent.</p></div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="sabi-section">Ba bước thực thi</div>',
        unsafe_allow_html=True,
    )
    step_plan, step_guard, step_answer = st.columns(3)
    with step_plan:
        st.markdown(
            """
<div class="step">
  <h4>LLM lập kế hoạch</h4>
  <p>Gemini sinh JSON tool call (SQL và output_file nếu có). Fallback model khi gặp 429.</p>
</div>
""",
            unsafe_allow_html=True,
        )
    with step_guard:
        st.markdown(
            """
<div class="step">
  <h4>Đánh chặn Guardrails</h4>
  <p>Read-only, RBAC và giới hạn tài nguyên chặn truy vấn trước khi Trino chạy. Lỗi kỹ thuật được Reflexion sửa.</p>
</div>
""",
            unsafe_allow_html=True,
        )
    with step_answer:
        st.markdown(
            """
<div class="step">
  <h4>Tổng hợp kết quả</h4>
  <p>Kết quả hoặc lý do chặn được diễn giải tiếng Việt trên Console.</p>
</div>
""",
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div class="sabi-section">Điểm bảo mật</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
<div class="adv"><strong>Least Privilege</strong> — <span>MCP buộc Agent chỉ gọi tool được phép; LLM không nhận credential DB.</span></div>
<div class="adv"><strong>Fault Tolerance</strong> — <span>Fallback LLM chuyển model dự phòng khi hết Quota.</span></div>
<div class="adv"><strong>Proactive Defense</strong> — <span>Gateway từ chối SQL không read-only và bảng ngoài policy của role.</span></div>
<div class="adv"><strong>Federated Security</strong> — <span>Trino là lối vào duy nhất cho PostgreSQL và MySQL.</span></div>
<div class="adv"><strong>Adversarial Testing</strong> — <span>26 kịch bản phủ baseline, sáu nhóm tấn công, và export trong sandbox.</span></div>
""",
        unsafe_allow_html=True,
    )
