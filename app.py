from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px
from src.traffic_pipeline import load_data, analyze_with_spark, summarize_data

st.set_page_config(page_title="Smart City Traffic Analytics", page_icon="🚦", layout="wide")
st.markdown("""
<style>
.stApp {background: #0b1220;}
[data-testid="stMetric"] {background: #121d30; border: 1px solid #26364f; padding: 16px; border-radius: 14px;}
div[data-testid="stMetricValue"] {color: #75e6d0;}
.block-container {padding-top: 1.8rem;}
</style>
""", unsafe_allow_html=True)

st.title("🚦 Smart City Traffic Analytics")
st.caption("Big Data mini project · PySpark processing · Interactive traffic insights")
st.info("Educational analytics demo using a bundled sample dataset. It is not a live traffic feed and does not predict real-time road conditions.")

DEFAULT_DATA = Path(__file__).resolve().parent / "data" / "traffic_data.csv"
with st.sidebar:
    st.header("⚙️ Data settings")
    uploaded = st.file_uploader("Upload a traffic CSV (optional)", type=["csv"])
    use_spark = st.checkbox("Use PySpark processing when available", value=True)
    st.markdown("---")
    st.markdown("**Expected columns**")
    st.code("timestamp, road, location, vehicle_count, avg_speed_kmph, weather")
    st.caption("If PySpark is not installed, the app automatically uses Pandas.")

try:
    if uploaded is not None:
        df = load_data(uploaded)
        data_label = "Uploaded dataset"
    else:
        df = load_data(DEFAULT_DATA)
        data_label = "Bundled sample dataset"
except Exception as exc:
    st.error(f"Could not load dataset: {exc}")
    st.stop()

if df.empty:
    st.warning("The selected dataset is empty.")
    st.stop()

if use_spark:
    try:
        processed, engine = analyze_with_spark(df)
    except Exception as exc:
        processed, engine = summarize_data(df), "Pandas fallback"
        st.warning(f"PySpark processing could not start; using Pandas fallback. Details: {exc}")
else:
    processed, engine = summarize_data(df), "Pandas"

df = processed.copy()
df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
df = df.dropna(subset=["timestamp"])
if df.empty:
    st.error("No valid timestamps found. Check the timestamp column format.")
    st.stop()
df["hour"] = df["timestamp"].dt.hour
df["date"] = df["timestamp"].dt.date
df["congestion"] = df.apply(
    lambda r: "High" if r["avg_speed_kmph"] < 20 else ("Moderate" if r["avg_speed_kmph"] < 35 else "Low"), axis=1
)

st.caption(f"Data source: **{data_label}** · Processing engine: **{engine}** · Records: **{len(df):,}**")

roads = sorted(df["road"].dropna().astype(str).unique().tolist())
locations = sorted(df["location"].dropna().astype(str).unique().tolist())
with st.sidebar:
    chosen_roads = st.multiselect("Filter roads", roads, default=roads)
    chosen_locations = st.multiselect("Filter locations", locations, default=locations)
    min_date, max_date = df["timestamp"].min().date(), df["timestamp"].max().date()
    date_range = st.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)

filtered = df[df["road"].astype(str).isin(chosen_roads) & df["location"].astype(str).isin(chosen_locations)].copy()
if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    filtered = filtered[(filtered["timestamp"].dt.date >= date_range[0]) & (filtered["timestamp"].dt.date <= date_range[1])]

if filtered.empty:
    st.warning("No records match the current filters. Select a different road, location or date range.")
    st.stop()

vehicles = int(filtered["vehicle_count"].sum())
avg_speed = float(filtered["avg_speed_kmph"].mean())
busy_road = filtered.groupby("road")["vehicle_count"].sum().idxmax()
peak_hour = int(filtered.groupby("hour")["vehicle_count"].sum().idxmax())
high_congestion_pct = float((filtered["avg_speed_kmph"] < 20).mean() * 100)

c1,c2,c3,c4 = st.columns(4)
c1.metric("Vehicle observations", f"{vehicles:,}")
c2.metric("Average speed", f"{avg_speed:.1f} km/h")
c3.metric("Busiest road", busy_road)
c4.metric("Peak hour", f"{peak_hour:02d}:00")
st.caption(f"{high_congestion_pct:.1f}% of records have average speed below 20 km/h (project-defined high-congestion indicator).")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🛣️ Road Analysis", "🕒 Time Patterns", "📄 Data & Export"])
with tab1:
    left, right = st.columns(2)
    daily = filtered.groupby("date", as_index=False)["vehicle_count"].sum()
    left.plotly_chart(px.line(daily, x="date", y="vehicle_count", markers=True, title="Daily vehicle counts", labels={"date":"Date","vehicle_count":"Vehicle count"}), use_container_width=True)
    congestion = filtered.groupby("congestion", as_index=False).size().rename(columns={"size":"records"})
    right.plotly_chart(px.pie(congestion, names="congestion", values="records", hole=.5, title="Record distribution by speed-based congestion"), use_container_width=True)
    st.subheader("Key findings")
    st.write(f"- **Busiest road in the selected data:** {busy_road}")
    st.write(f"- **Highest traffic-count hour:** {peak_hour:02d}:00")
    st.write(f"- **Mean observed speed:** {avg_speed:.1f} km/h")
    st.write("- These findings describe the uploaded or sample data only; they are not live city-wide conclusions.")
with tab2:
    road_stats = filtered.groupby("road", as_index=False).agg(vehicle_count=("vehicle_count","sum"), avg_speed_kmph=("avg_speed_kmph","mean"), records=("road","size"))
    road_stats = road_stats.sort_values("vehicle_count", ascending=False)
    l,r = st.columns(2)
    l.plotly_chart(px.bar(road_stats, x="road", y="vehicle_count", color="vehicle_count", title="Total vehicles by road", labels={"road":"Road","vehicle_count":"Vehicle count"}), use_container_width=True)
    r.plotly_chart(px.bar(road_stats, x="road", y="avg_speed_kmph", title="Average speed by road", labels={"road":"Road","avg_speed_kmph":"Average speed (km/h)"}), use_container_width=True)
    st.dataframe(road_stats.round(2), use_container_width=True, hide_index=True)
with tab3:
    hourly = filtered.groupby("hour", as_index=False).agg(vehicle_count=("vehicle_count","sum"), avg_speed_kmph=("avg_speed_kmph","mean"))
    l,r = st.columns(2)
    l.plotly_chart(px.bar(hourly, x="hour", y="vehicle_count", title="Traffic volume by hour", labels={"hour":"Hour of day","vehicle_count":"Vehicle count"}), use_container_width=True)
    r.plotly_chart(px.line(hourly, x="hour", y="avg_speed_kmph", markers=True, title="Average speed by hour", labels={"hour":"Hour of day","avg_speed_kmph":"Average speed (km/h)"}), use_container_width=True)
    heat = filtered.pivot_table(index="road", columns="hour", values="vehicle_count", aggfunc="sum", fill_value=0)
    st.plotly_chart(px.imshow(heat, aspect="auto", title="Traffic intensity heatmap (road × hour)", labels={"x":"Hour","y":"Road","color":"Vehicle count"}), use_container_width=True)
with tab4:
    st.subheader("Filtered records")
    st.dataframe(filtered.sort_values("timestamp", ascending=False), use_container_width=True, hide_index=True)
    csv_bytes = filtered.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download filtered data as CSV", csv_bytes, "filtered_traffic_data.csv", "text/csv")
    report = (
        "SMART CITY TRAFFIC ANALYTICS — SUMMARY\n"
        f"Data source: {data_label}\nRecords: {len(filtered)}\nTotal vehicle count: {vehicles}\n"
        f"Average speed: {avg_speed:.2f} km/h\nBusiest road: {busy_road}\nPeak hour: {peak_hour:02d}:00\n"
        f"High-congestion indicator (<20 km/h): {high_congestion_pct:.2f}%\n"
        "Note: Educational analysis; results depend on the supplied dataset and do not represent live traffic.\n"
    )
    st.download_button("⬇️ Download summary report", report, "traffic_summary.txt", "text/plain")

with st.expander("ℹ️ Methodology and limitations"):
    st.markdown("""
    - **Data processing:** PySpark DataFrame aggregation is used when available; otherwise the app uses Pandas.
    - **High congestion indicator:** average speed below 20 km/h. This threshold is illustrative, not a universal traffic standard.
    - **Peak hour:** hour with the largest sum of `vehicle_count` in the filtered records.
    - **Limitations:** sample data is synthetic, no GPS feed is connected, and no real-time prediction is performed.
    """)
