from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


st.set_page_config(
    page_title="Breast Cancer | Patient Insights",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded",
)

INK = "#172238"
MUTED = "#738096"
TEAL = "#167d83"
CORAL = "#e8796c"
PALETTE = ["#167d83", "#e8796c", "#6e7fbb", "#d5a742", "#7eaa87", "#a276a8"]

st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
      html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
      .stApp { background: #f5f7fa; color: #172238; }
      [data-testid="stHeader"] { background: rgba(245,247,250,.94); }
      [data-testid="stSidebar"] { background: #fff; border-right: 1px solid #e6ebf1; }
      .block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1500px; }
      h1, h2, h3 { font-family: 'Manrope', sans-serif; color: #172238; letter-spacing: -.035em; }
      h1 { font-size: 2.25rem !important; font-weight: 800 !important; margin-bottom: .15rem !important; }
      h2 { font-size: 1.25rem !important; font-weight: 700 !important; }
      .eyebrow { color: #167d83; text-transform: uppercase; letter-spacing: .15em; font-size: .7rem; font-weight: 700; }
      .subtitle { color: #738096; font-size: 1rem; margin: 0 0 1.2rem; }
      .metric-card { background: white; border: 1px solid #e6ebf1; border-radius: 15px; padding: 17px 19px 15px; min-height: 112px; box-shadow: 0 4px 16px rgba(23,34,56,.035); }
      .metric-label { color: #738096; font-size: .78rem; font-weight: 600; margin-bottom: 8px; }
      .metric-value { color: #172238; font: 800 1.65rem 'Manrope', sans-serif; letter-spacing: -.04em; }
      .metric-note { color: #8792a3; font-size: .72rem; margin-top: 3px; }
      .section-note { color:#738096; font-size:.82rem; margin-top:-.45rem; margin-bottom:.9rem; }
      .insight { background:#fff; border:1px solid #e6ebf1; border-left:4px solid #167d83; border-radius:12px; padding:14px 16px; color:#334159; line-height:1.5; font-size:.9rem; min-height:84px; }
      .insight b { color:#172238; }
      .notice { background:#fff8ea; border:1px solid #f1dfb8; border-radius:12px; padding:13px 16px; color:#6d5731; font-size:.88rem; }
      div[data-testid="stPlotlyChart"] { background:white; border:1px solid #e6ebf1; border-radius:15px; padding:7px; box-shadow:0 4px 16px rgba(23,34,56,.025); }
      div[data-testid="stTabs"] button { font-weight:600; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def read_csv(file_bytes: bytes) -> pd.DataFrame:
    return pd.read_csv(BytesIO(file_bytes))


def find_default_file() -> Path | None:
    for name in ("Breast_Cancer.csv", "breast_cancer.csv", "Breast_Cancer_Data.csv"):
        candidate = Path(__file__).parent / name
        if candidate.exists():
            return candidate
    return None


def tidy_data(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()
    df.columns = [str(c).strip() for c in df.columns]
    # Match common spelling/case variants without changing the source file.
    lookup = {c.casefold().replace("_", " ").strip(): c for c in df.columns}
    aliases = {
        "differentiate": "Differentiation",
        "differentiation": "Differentiation",
        "reginol node positive": "Positive Nodes",
        "regional node positive": "Positive Nodes",
        "regional nodes positive": "Positive Nodes",
        "regional node examined": "Nodes Examined",
        "regional nodes examined": "Nodes Examined",
        "6th stage": "Stage",
        "stage": "Stage",
        "a stage": "A Stage",
        "t stage": "T Stage",
        "n stage": "N Stage",
        "estrogen status": "Estrogen Status",
        "progesterone status": "Progesterone Status",
        "survival months": "Survival Months",
        "tumor size": "Tumor Size",
        "marital status": "Marital Status",
        "status": "Status",
        "age": "Age",
        "race": "Race",
        "grade": "Grade",
    }
    rename = {lookup[src]: dest for src, dest in aliases.items() if src in lookup and lookup[src] != dest}
    df = df.rename(columns=rename)
    for col in ("Age", "Tumor Size", "Survival Months", "Positive Nodes", "Nodes Examined", "Grade"):
        if col in df:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "Status" in df:
        df["Status"] = df["Status"].astype("string").str.strip().str.title()
    if "Age" in df:
        df["Age Band"] = pd.cut(
            df["Age"], bins=[0, 39, 49, 59, 69, 79, 120],
            labels=["<40", "40–49", "50–59", "60–69", "70–79", "80+"],
        )
    return df


def metric(label: str, value: str, note: str) -> None:
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div><div class="metric-note">{note}</div></div>',
        unsafe_allow_html=True,
    )


def chart_layout(fig: go.Figure, height: int = 340) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=18, r=18, t=40, b=18),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans, sans-serif", color=INK, size=12),
        title=dict(font=dict(family="Manrope, sans-serif", size=15, color=INK), x=0.03, xanchor="left"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title_text=""),
        xaxis=dict(showgrid=False, linecolor="#e8edf2", title_font_color=MUTED),
        yaxis=dict(showgrid=True, gridcolor="#eef1f5", zeroline=False, title_font_color=MUTED),
    )
    return fig


st.sidebar.markdown('<div class="eyebrow">Patient cohort</div>', unsafe_allow_html=True)
st.sidebar.markdown("### Data & filters")
uploaded = st.sidebar.file_uploader("Upload the notebook CSV", type=["csv"], help="Expected file: Breast_Cancer.csv")

if uploaded is not None:
    raw_df = read_csv(uploaded.getvalue())
    source_label = uploaded.name
else:
    default_path = find_default_file()
    if default_path:
        raw_df = read_csv(default_path.read_bytes())
        source_label = default_path.name
    else:
        st.markdown('<div class="eyebrow">Notebook insights · dataset review</div>', unsafe_allow_html=True)
        st.title("Patient outcomes, at a glance")
        st.markdown('<p class="subtitle">An interactive dashboard built from the analysis fields in the notebook.</p>', unsafe_allow_html=True)
        st.markdown(
            '<div class="notice"><b>Dataset needed to populate charts.</b> The notebook reads '
            '<code>/content/Breast_Cancer.csv</code>, but that CSV is not included in this project folder. '
            'Upload it in the sidebar, or place <code>Breast_Cancer.csv</code> beside <code>app.py</code>. '
            'The notebook currently analyzes breast cancer patient data, not e-commerce transactions.</div>',
            unsafe_allow_html=True,
        )
        st.markdown("\n")
        st.markdown("#### What this dashboard explores")
        st.write("Age profile · stage mix · patient status · tumor size · survival duration · estrogen and progesterone status · regional lymph nodes")
        st.stop()

df = tidy_data(raw_df)
if df.empty:
    st.error("The uploaded CSV has no rows.")
    st.stop()

st.sidebar.caption(f"Source: {source_label} · {len(df):,} rows")
st.sidebar.markdown("---")
filter_fields = [c for c in ["Status", "Stage", "Race", "Marital Status", "Estrogen Status", "Progesterone Status"] if c in df.columns]
filtered = df.copy()
for col in filter_fields:
    vals = sorted(df[col].dropna().astype(str).unique().tolist())
    if vals:
        selected = st.sidebar.multiselect(col, vals, default=vals, key=f"filter_{col}")
        filtered = filtered[filtered[col].astype(str).isin(selected)]

if "Age" in df and df["Age"].notna().any():
    lo, hi = int(df["Age"].min()), int(df["Age"].max())
    age_range = st.sidebar.slider("Age range", min_value=lo, max_value=hi, value=(lo, hi))
    filtered = filtered[filtered["Age"].between(*age_range)]
if "Tumor Size" in df and df["Tumor Size"].notna().any():
    lo, hi = int(df["Tumor Size"].min()), int(df["Tumor Size"].max())
    tumor_range = st.sidebar.slider("Tumor size", min_value=lo, max_value=hi, value=(lo, hi), help="Range in the dataset's recorded units")
    filtered = filtered[filtered["Tumor Size"].between(*tumor_range)]

st.markdown('<div class="eyebrow">Cohort overview</div>', unsafe_allow_html=True)
st.title("Patient outcomes, at a glance")
st.markdown('<p class="subtitle">Explore how patient characteristics, stage and recorded outcomes vary across the selected cohort.</p>', unsafe_allow_html=True)
if filtered.empty:
    st.warning("These filters return no records. Broaden one or more selections to continue.")
    st.stop()

status_counts = filtered["Status"].value_counts() if "Status" in filtered else pd.Series(dtype="int64")
dead_key = next((k for k in status_counts.index if str(k).casefold() in ("dead", "deceased")), None)
death_pct = status_counts[dead_key] / len(filtered) * 100 if dead_key is not None else None
avg_age = filtered["Age"].mean() if "Age" in filtered else None
median_tumor = filtered["Tumor Size"].median() if "Tumor Size" in filtered else None
median_survival = filtered["Survival Months"].median() if "Survival Months" in filtered else None

kpis = st.columns(5)
with kpis[0]: metric("PATIENT RECORDS", f"{len(filtered):,}", f"of {len(df):,} total records")
with kpis[1]: metric("RECORDED DEATHS", f"{death_pct:.1f}%" if death_pct is not None else "—", "share labeled dead in this cohort" if death_pct is not None else "Status field not available")
with kpis[2]: metric("AVERAGE AGE", f"{avg_age:.1f}" if pd.notna(avg_age) else "—", "years at recorded diagnosis" if avg_age is not None else "Age field not available")
with kpis[3]: metric("MEDIAN TUMOR SIZE", f"{median_tumor:.0f}" if pd.notna(median_tumor) else "—", "dataset units" if median_tumor is not None else "Tumor Size field not available")
with kpis[4]: metric("MEDIAN OBSERVED MONTHS", f"{median_survival:.0f}" if pd.notna(median_survival) else "—", "recorded follow-up duration" if median_survival is not None else "Survival Months field not available")

st.markdown("\n")
insights = []
if "Age Band" in filtered and filtered["Age Band"].notna().any():
    peak = filtered["Age Band"].value_counts().idxmax()
    insights.append(f"The largest age band is <b>{peak}</b> ({(filtered['Age Band'] == peak).sum():,} records).")
if "Stage" in filtered and filtered["Stage"].notna().any():
    stage = filtered["Stage"].astype(str).value_counts().idxmax()
    insights.append(f"The most common stage is <b>{stage}</b> ({(filtered['Stage'].astype(str) == stage).sum():,} records).")
if "Status" in filtered and "Survival Months" in filtered:
    sm = filtered.groupby("Status", observed=True)["Survival Months"].median().dropna()
    if len(sm) >= 2:
        max_group, min_group = sm.idxmax(), sm.idxmin()
        insights.append(f"Median recorded months range from <b>{sm[min_group]:.0f}</b> ({min_group}) to <b>{sm[max_group]:.0f}</b> ({max_group}).")
if insights:
    cols = st.columns(len(insights))
    for col, insight in zip(cols, insights):
        with col: st.markdown(f'<div class="insight">{insight}</div>', unsafe_allow_html=True)

st.markdown("\n")
tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Survival & tumor", "Receptors & nodes", "Explore data"])

with tab1:
    left, right = st.columns([1.05, 1])
    with left:
        if "Status" in filtered:
            counts = filtered["Status"].value_counts().rename_axis("Status").reset_index(name="Patients")
            fig = px.pie(counts, names="Status", values="Patients", hole=.66, color_discrete_sequence=[TEAL, CORAL, *PALETTE])
            fig.update_traces(textposition="outside", textinfo="label+percent", hole=.66)
            fig.update_layout(title="Patient status", showlegend=False, annotations=[dict(text=f"{len(filtered):,}<br><span style='font-size:11px'>patients</span>", x=.5, y=.5, showarrow=False, font=dict(size=20, color=INK))])
            st.plotly_chart(chart_layout(fig), use_container_width=True)
        if "Age Band" in filtered:
            counts = filtered.groupby("Age Band", observed=False).size().rename("Patients").reset_index()
            fig = px.bar(counts, x="Age Band", y="Patients", color="Patients", color_continuous_scale=["#d9eeeb", TEAL], title="Age profile")
            fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(chart_layout(fig, 320), use_container_width=True)
        else:
            st.info("Age field not found in this file.")
    with right:
        if "Stage" in filtered:
            stage = filtered["Stage"].astype(str).value_counts().rename_axis("Stage").reset_index(name="Patients")
            fig = px.bar(stage.sort_values("Patients"), x="Patients", y="Stage", orientation="h", color="Patients", color_continuous_scale=["#d9eeeb", TEAL], title="Cases by stage")
            fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(chart_layout(fig), use_container_width=True)
        if "Status" in filtered and "Stage" in filtered:
            cross = pd.crosstab(filtered["Stage"], filtered["Status"], normalize="index").mul(100).reset_index().melt(id_vars="Stage", var_name="Status", value_name="Share")
            fig = px.bar(cross, x="Stage", y="Share", color="Status", barmode="stack", color_discrete_sequence=[TEAL, CORAL, *PALETTE], title="Status mix within each stage", labels={"Share": "Share of stage (%)"})
            fig.update_layout(yaxis_range=[0, 100])
            st.plotly_chart(chart_layout(fig, 320), use_container_width=True)

with tab2:
    st.markdown('<div class="section-note">Recorded follow-up months describe the dataset field; they are not an estimate of individual prognosis.</div>', unsafe_allow_html=True)
    left, right = st.columns(2)
    with left:
        if "Survival Months" in filtered and "Status" in filtered:
            fig = px.box(filtered, x="Status", y="Survival Months", color="Status", points="outliers", color_discrete_sequence=[TEAL, CORAL, *PALETTE], title="Recorded months by status")
            st.plotly_chart(chart_layout(fig), use_container_width=True)
        elif "Survival Months" in filtered:
            fig = px.histogram(filtered, x="Survival Months", nbins=30, title="Recorded months distribution", color_discrete_sequence=[TEAL])
            st.plotly_chart(chart_layout(fig), use_container_width=True)
    with right:
        if "Tumor Size" in filtered and "Status" in filtered:
            fig = px.violin(filtered, x="Status", y="Tumor Size", color="Status", box=True, points=False, color_discrete_sequence=[TEAL, CORAL, *PALETTE], title="Tumor size by status")
            st.plotly_chart(chart_layout(fig), use_container_width=True)
        elif "Tumor Size" in filtered:
            fig = px.histogram(filtered, x="Tumor Size", nbins=30, title="Tumor size distribution", color_discrete_sequence=[TEAL])
            st.plotly_chart(chart_layout(fig), use_container_width=True)
    if "Tumor Size" in filtered and "Survival Months" in filtered:
        color = "Status" if "Status" in filtered else None
        hover = [x for x in ["Age", "Stage", "Positive Nodes"] if x in filtered]
        fig = px.scatter(filtered, x="Tumor Size", y="Survival Months", color=color, hover_data=hover, opacity=.65, color_discrete_sequence=[TEAL, CORAL, *PALETTE], title="Tumor size and recorded months")
        st.plotly_chart(chart_layout(fig, 390), use_container_width=True)

with tab3:
    left, right = st.columns(2)
    receptor_cols = [c for c in ["Estrogen Status", "Progesterone Status"] if c in filtered]
    with left:
        if receptor_cols:
            rcol = st.selectbox("Receptor marker", receptor_cols, key="receptor_select")
            if "Status" in filtered:
                cross = pd.crosstab(filtered[rcol], filtered["Status"], normalize="index").mul(100).reset_index().melt(id_vars=rcol, var_name="Status", value_name="Share")
                fig = px.bar(cross, x=rcol, y="Share", color="Status", barmode="group", color_discrete_sequence=[TEAL, CORAL, *PALETTE], title=f"Status mix by {rcol.lower()}", labels={"Share": "Share within marker (%)"}, text_auto=".1f")
                st.plotly_chart(chart_layout(fig), use_container_width=True)
            else:
                counts = filtered[rcol].value_counts().rename_axis(rcol).reset_index(name="Patients")
                fig = px.bar(counts, x=rcol, y="Patients", title=f"Patients by {rcol.lower()}", color_discrete_sequence=[TEAL])
                st.plotly_chart(chart_layout(fig), use_container_width=True)
        else:
            st.info("Estrogen Status and Progesterone Status columns were not found.")
    with right:
        if "Positive Nodes" in filtered:
            if "Stage" in filtered:
                fig = px.box(filtered, x="Stage", y="Positive Nodes", color="Stage", points=False, color_discrete_sequence=PALETTE, title="Positive nodes by stage")
            else:
                fig = px.histogram(filtered, x="Positive Nodes", nbins=25, title="Positive regional nodes", color_discrete_sequence=[TEAL])
            st.plotly_chart(chart_layout(fig), use_container_width=True)
        elif "Nodes Examined" in filtered:
            fig = px.histogram(filtered, x="Nodes Examined", nbins=25, title="Regional nodes examined", color_discrete_sequence=[TEAL])
            st.plotly_chart(chart_layout(fig), use_container_width=True)
        else:
            st.info("No regional lymph node fields were found.")
    numeric = filtered.select_dtypes(include="number")
    if len(numeric.columns) >= 2:
        corr = numeric.corr(numeric_only=True)
        fig = px.imshow(corr, text_auto=".2f", zmin=-1, zmax=1, color_continuous_scale="RdBu_r", aspect="auto", title="Numeric feature correlations")
        fig.update_layout(height=430)
        st.plotly_chart(chart_layout(fig, 450), use_container_width=True)

with tab4:
    st.markdown("#### Filtered records")
    st.caption(f"Showing {len(filtered):,} of {len(df):,} records. Download the filtered cohort as CSV.")
    st.download_button("Download filtered CSV", filtered.to_csv(index=False).encode("utf-8"), "filtered_patient_cohort.csv", "text/csv", type="primary")
    st.dataframe(filtered, use_container_width=True, hide_index=True, height=440)
    missing = (
        filtered.isna()
        .mean()
        .mul(100)
        .rename_axis("Field")
        .reset_index(name="Missing (%)")
        .sort_values("Missing (%)", ascending=False)
    )
    missing = missing[missing["Missing (%)"] > 0]
    if not missing.empty:
        st.markdown("#### Missing values in selected cohort")
        fig = px.bar(missing, x="Missing (%)", y="Field", orientation="h", color="Missing (%)", color_continuous_scale=["#f5d9d4", CORAL], title="Share of missing values")
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(chart_layout(fig, max(250, len(missing) * 35)), use_container_width=True)

st.markdown("\n")
st.caption("Exploratory view of the uploaded dataset. Group comparisons are descriptive and do not establish causation.")
