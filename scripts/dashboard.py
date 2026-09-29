from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st
import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "dashboard.yaml"
LOG_PATH = ROOT / "data" / "logs.jsonl"
COLORS = ["#087f73", "#d35f45", "#416b9a", "#bf8428"]

st.set_page_config(
    page_title="LLMOps Monitor",
    page_icon="M",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');
    :root {
      --paper: #f4f7f5;
      --ink: #1d2925;
      --muted: #61706a;
      --rule: #d6e0db;
      --teal: #087f73;
      --coral: #d35f45;
      --gold: #bf8428;
    }
    html, body, [class*="css"] { font-family: "IBM Plex Sans", sans-serif; }
    html, body, .stApp { max-width: 100vw; overflow-x: clip; }
    .stApp { background: var(--paper); color: var(--ink); }
    .block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 1500px; }
    h1, h2, h3 { color: var(--ink); letter-spacing: 0; }
    h1 { font-size: 2rem; font-weight: 600; margin-bottom: .2rem; }
    h2 { font-size: 1.12rem; font-weight: 600; margin-bottom: 0; }
    [data-testid="stMetricValue"] { font-family: "IBM Plex Mono", monospace; font-size: 1.45rem; }
    [data-testid="stMetricLabel"] { color: var(--muted); }
    [data-testid="stMetric"] { padding: .5rem 0; border-top: 1px solid var(--rule); }
    .eyebrow { color: var(--teal); text-transform: uppercase; font: 500 .72rem "IBM Plex Mono", monospace; letter-spacing: 0; }
    .subtle { color: var(--muted); font-size: .82rem; }
    hr { border-color: var(--rule); }
        @media (max-width: 700px) {
            .block-container { padding-left: 12px !important; padding-right: 12px !important; }
            [data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stMainBlockContainer"] {
                width: 100vw !important; min-width: 0 !important; max-width: 100vw !important;
            }
            [data-testid="stHorizontalBlock"] {
                flex-direction: column !important; gap: 1rem !important; width: 100% !important; min-width: 0 !important;
            }
            [data-testid="column"] {
                flex: 1 1 100% !important; width: 100% !important; min-width: 0 !important; max-width: 100% !important;
            }
            [data-testid="stVegaLiteChart"] { width: 100% !important; min-width: 0 !important; max-width: 100% !important; }
        }
    </style>
    """,
    unsafe_allow_html=True,
)

dashboard = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))["dashboard"]
slo = yaml.safe_load((ROOT / "config" / "slo.yaml").read_text(encoding="utf-8"))
time_range = int(dashboard["time_range_minutes"])
refresh_seconds = int(dashboard["refresh_seconds"])
retrieval_success_min = float(slo["guardrails"]["retrieval_success_rate_pct_min"])


@st.cache_data(ttl=refresh_seconds)
def read_records(path: str, modified_ns: int) -> list[dict]:
    del modified_ns
    records = []
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return records
    for line in lines:
        try:
            record = json.loads(line)
            timestamp = record.get("ts")
            if timestamp:
                record["timestamp"] = datetime.fromisoformat(
                    timestamp.replace("Z", "+00:00")
                ).astimezone(timezone.utc)
                records.append(record)
        except (json.JSONDecodeError, TypeError, ValueError):
            continue
    return records


def time_index(now: datetime) -> pd.DatetimeIndex:
    end = pd.Timestamp(now).floor("min")
    return pd.date_range(end=end, periods=time_range, freq="1min", tz="UTC")


def minute_sum(frame: pd.DataFrame, field: str, index: pd.DatetimeIndex) -> pd.Series:
    if frame.empty or field not in frame:
        return pd.Series(0.0, index=index)
    values = pd.to_numeric(frame[field], errors="coerce")
    series = values.groupby(frame["timestamp"].dt.floor("min")).sum()
    return series.reindex(index, fill_value=0).astype(float)


def minute_count(frame: pd.DataFrame, index: pd.DatetimeIndex) -> pd.Series:
    if frame.empty:
        return pd.Series(0.0, index=index)
    series = frame.groupby(frame["timestamp"].dt.floor("min")).size()
    return series.reindex(index, fill_value=0).astype(float)


def chart_frame(index: pd.DatetimeIndex, series: dict[str, pd.Series]) -> pd.DataFrame:
    rows = []
    for name, values in series.items():
        rows.extend(
            {"minute": minute.to_pydatetime(), "series": name, "value": float(value)}
            for minute, value in values.items()
        )
    return pd.DataFrame(rows)


def line_chart(
    frame: pd.DataFrame,
    *,
    unit: str,
    thresholds: list[tuple[str, float]],
    zero: bool = False,
) -> alt.Chart:
    base = alt.Chart(frame).encode(
        x=alt.X("minute:T", scale=alt.Scale(type="utc"), title=None, axis=alt.Axis(format="%H:%M", labelColor="#61706a", grid=False)),
        y=alt.Y(
            "value:Q",
            title=unit,
            scale=alt.Scale(zero=zero),
            axis=alt.Axis(labelColor="#61706a", titleColor="#61706a", gridColor="#dce4e0"),
        ),
        color=alt.Color("series:N", scale=alt.Scale(range=COLORS), legend=alt.Legend(title=None, orient="top")),
        tooltip=[alt.Tooltip("minute:T", title="Minute"), "series:N", alt.Tooltip("value:Q", format=".2f")],
    )
    lines = base.mark_line(strokeWidth=2, point=alt.OverlayMarkDef(size=20))
    if not thresholds:
        return lines.properties(height=210).configure_view(strokeOpacity=0)
    rule_data = pd.DataFrame(
        [{"value": value, "series": name} for name, value in thresholds]
    )
    rules = (
        alt.Chart(rule_data)
        .mark_rule(strokeDash=[5, 4], strokeWidth=1.5)
        .encode(
            y=alt.Y("value:Q"),
            color=alt.Color("series:N", scale=alt.Scale(range=["#d35f45", "#bf8428"]), legend=alt.Legend(title=None, orient="top")),
            tooltip=["series:N", alt.Tooltip("value:Q", format=".2f")],
        )
    )
    return (
        (lines + rules)
        .resolve_scale(color="independent")
        .properties(height=210)
        .configure_view(strokeOpacity=0)
    )


def panel_header(panel: dict, *, unit: str, threshold: str) -> None:
    st.subheader(panel["title"])
    st.caption(f"Last {panel.get('time_range_minutes', time_range)} min  ·  {unit}  ·  Threshold {threshold}")


def render_dashboard() -> None:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=time_range)
    source_mtime = LOG_PATH.stat().st_mtime_ns if LOG_PATH.exists() else 0
    records = read_records(str(LOG_PATH), source_mtime)
    frame = pd.DataFrame(
        [record for record in records if cutoff <= record["timestamp"] <= now]
    )
    if not frame.empty:
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)

    panels = {panel["id"]: panel for panel in dashboard["panels"]}
    st.markdown('<div class="eyebrow">Operations / language systems</div>', unsafe_allow_html=True)
    st.title(dashboard["title"])
    st.caption(
        f"Local telemetry  ·  Rolling {time_range} minutes  ·  Updated {now.strftime('%H:%M:%S UTC')}  ·  Refresh {refresh_seconds}s"
    )
    st.divider()

    response = frame[frame["event"] == "response_sent"] if not frame.empty else frame
    requests = frame[frame["event"] == "request_received"] if not frame.empty else frame
    latency = pd.to_numeric(response.get("latency_ms", pd.Series(dtype=float)), errors="coerce").dropna()
    ttft = pd.to_numeric(response.get("ttft_ms", pd.Series(dtype=float)), errors="coerce").dropna()
    cost = pd.to_numeric(response.get("cost_usd", pd.Series(dtype=float)), errors="coerce").fillna(0)
    st.metric("Requests in window", f"{len(requests):,}")
    summary_columns = st.columns(3)
    summary_columns[0].metric("Latency P95", f"{latency.quantile(.95):.0f} ms" if not latency.empty else "--")
    summary_columns[1].metric("TTFT P95", f"{ttft.quantile(.95):.0f} ms" if not ttft.empty else "--")
    summary_columns[2].metric("Total cost", f"${cost.sum():.4f}")
    st.divider()

    left, right = st.columns(2, gap="large")
    index = time_index(now)

    with left:
        panel = panels["latency"]
        panel_header(panel, unit=panel["unit"], threshold="P95 <= 3000 ms")
        if response.empty:
            st.info("No response records in this window.")
        else:
            latency_series = {
                name.upper(): pd.to_numeric(response.set_index("timestamp")[field], errors="coerce")
                .groupby(lambda stamp: stamp.floor("min"))
                .quantile(q)
                .reindex(index)
                for name, field, q in (("p50", "latency_ms", .50), ("p95", "latency_ms", .95), ("p99", "latency_ms", .99), ("ttft_p95", "ttft_ms", .95))
            }
            st.altair_chart(
                line_chart(chart_frame(index, latency_series), unit="ms", thresholds=[("P95 limit", panel["threshold"]["value"])]),
                use_container_width=True,
            )

        panel = panels["traffic"]
        panel_header(panel, unit="requests / minute", threshold=">= 1 req/min")
        traffic = minute_count(requests, index)
        st.altair_chart(
            line_chart(chart_frame(index, {"Requests/min": traffic}), unit="requests / min", thresholds=[("Minimum traffic", panel["threshold"]["value"])]),
            use_container_width=True,
        )

        panel = panels["cost"]
        panel_header(panel, unit="USD", threshold="total <= $2.50")
        cumulative_cost = minute_sum(response, "cost_usd", index).cumsum()
        st.altair_chart(
            line_chart(chart_frame(index, {"Cumulative cost": cumulative_cost}), unit="USD", thresholds=[("60-minute limit", panel["threshold"]["value"])]),
            use_container_width=True,
        )

    with right:
        panel = panels["errors"]
        panel_header(panel, unit="percent", threshold="errors <= 2%; retrieval >= 90%")
        failures = frame[frame["event"] == "request_failed"] if not frame.empty else frame
        failure_count = minute_count(failures, index)
        request_count = minute_count(requests, index)
        error_rate = failure_count.div(request_count.where(request_count > 0)) * 100
        tool_records = response[response.get("tool_success", pd.Series(index=response.index, dtype=object)).notna()] if not response.empty else response
        retrieval_success = minute_sum(tool_records.assign(_success=tool_records["tool_success"].astype(float)), "_success", index).div(
            minute_count(tool_records, index).where(minute_count(tool_records, index) > 0)
        ) * 100
        st.altair_chart(
            line_chart(
                chart_frame(index, {"Error rate": error_rate, "Retrieval success": retrieval_success}),
                unit="percent",
                thresholds=[("Error limit", panel["threshold"]["value"]), ("Retrieval minimum", retrieval_success_min)],
            ),
            use_container_width=True,
        )
        if not failures.empty and "error_type" in failures:
            st.caption("Failure breakdown")
            st.dataframe(failures["error_type"].fillna("unknown").value_counts().rename_axis("error_type").reset_index(name="count"), hide_index=True, use_container_width=True)

        panel = panels["tokens"]
        panel_header(panel, unit="tokens", threshold="total <= 50,000")
        input_tokens = minute_sum(response, "tokens_in", index).cumsum()
        output_tokens = minute_sum(response, "tokens_out", index).cumsum()
        st.altair_chart(
            line_chart(chart_frame(index, {"Input tokens": input_tokens, "Output tokens": output_tokens}), unit="tokens", thresholds=[("60-minute limit", panel["threshold"]["value"])]),
            use_container_width=True,
        )

        panel = panels["quality"]
        panel_header(panel, unit="score (0-1)", threshold=">= 0.75")
        if response.empty:
            st.info("No quality records in this window.")
        else:
            quality = pd.to_numeric(response.set_index("timestamp")["quality_score"], errors="coerce")
            quality = quality.groupby(lambda stamp: stamp.floor("min")).mean().reindex(index)
            st.altair_chart(
                line_chart(chart_frame(index, {"Mean quality": quality}), unit="score", thresholds=[("Quality minimum", panel["threshold"]["value"])]),
                use_container_width=True,
            )

    if frame.empty:
        st.warning(f"No valid JSONL records found in the last {time_range} minutes at {LOG_PATH.relative_to(ROOT)}.")


@st.fragment(run_every=f"{refresh_seconds}s")
def dashboard_fragment() -> None:
    render_dashboard()


dashboard_fragment()