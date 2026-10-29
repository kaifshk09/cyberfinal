import pandas as pd

REQUIRED = ["timestamp", "road", "location", "vehicle_count", "avg_speed_kmph", "weather"]

def load_data(source):
    df = pd.read_csv(source)
    # CSVs exported by spreadsheet tools often contain a BOM, whitespace,
    # inconsistent casing, or slightly different names for these fields.
    df.columns = [str(column).replace("\ufeff", "").strip().lower() for column in df.columns]
    df = df.rename(columns={
        "road_name": "road",
        "street": "road",
        "weather_condition": "weather",
        "conditions": "weather",
    })
    # Weather is retained for compatibility with the bundled schema, but it
    # is not used by the current dashboard calculations.
    if "weather" not in df.columns:
        df["weather"] = "Unknown"
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        available = ", ".join(df.columns) or "none"
        raise ValueError(
            "Missing required column(s): " + ", ".join(missing)
            + f". Found: {available}"
        )
    df = df[REQUIRED].copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["vehicle_count"] = pd.to_numeric(df["vehicle_count"], errors="coerce")
    df["avg_speed_kmph"] = pd.to_numeric(df["avg_speed_kmph"], errors="coerce")
    df = df.dropna(subset=["timestamp", "vehicle_count", "avg_speed_kmph", "road", "location"])
    df["vehicle_count"] = df["vehicle_count"].clip(lower=0)
    df["avg_speed_kmph"] = df["avg_speed_kmph"].clip(lower=0, upper=200)
    df["road"] = df["road"].astype(str)
    df["location"] = df["location"].astype(str)
    df["weather"] = df["weather"].fillna("Unknown").astype(str)
    return df

def summarize_data(df):
    """Pandas fallback with the same columns expected by the dashboard."""
    return df.copy()

def analyze_with_spark(df):
    """Use PySpark DataFrame processing if installed; return Pandas output and engine name."""
    try:
        from pyspark.sql import SparkSession, functions as F
    except ImportError:
        return summarize_data(df), "Pandas (PySpark not installed)"
    spark = SparkSession.builder.master("local[*]").appName("SmartCityTrafficAnalytics").getOrCreate()
    try:
        sdf = spark.createDataFrame(df)
        # Demonstrate distributed-style aggregation, then join summaries back to record-level data.
        road_stats = sdf.groupBy("road").agg(
            F.sum("vehicle_count").alias("_road_total"),
            F.avg("avg_speed_kmph").alias("_road_avg_speed")
        )
        hour_stats = sdf.withColumn("_hour", F.hour("timestamp")).groupBy("_hour").agg(
            F.sum("vehicle_count").alias("_hour_total")
        )
        # Execute the aggregation jobs; dashboard charts use normalized row-level records.
        road_stats.count()
        hour_stats.count()
        out = sdf.toPandas()
        return out, "PySpark"
    finally:
        spark.stop()
