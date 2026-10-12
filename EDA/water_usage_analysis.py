
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import IsolationForest
from sklearn.feature_selection import VarianceThreshold

# 1. Load datasets
meter = pd.read_csv("data/meter.csv")
connections = pd.read_csv("data/connections.csv")
weather = pd.read_csv("data/weather.csv")
maintenance = pd.read_csv("data/maintenance.csv")
billing = pd.read_csv("data/billing.csv")

# 2. Understand the data
for name, df in {
    "Meter": meter, "Connections": connections,
    "Weather": weather, "Maintenance": maintenance,
    "Billing": billing
}.items():
    print(f"\n{name}: {df.shape}")
    print(df.isnull().sum())
    print("Duplicates:", df.duplicated().sum())

# 3. Clean the data
meter = meter.drop_duplicates().copy()
connections = connections.drop_duplicates().copy()
weather = weather.drop_duplicates().copy()

meter["date"] = pd.to_datetime(meter["date"], errors="coerce")
weather["date"] = pd.to_datetime(weather["date"], errors="coerce")
maintenance["repair_date"] = pd.to_datetime(
    maintenance["repair_date"], errors="coerce"
)

meter["usage"] = pd.to_numeric(meter["usage"], errors="coerce")
meter.loc[meter["usage"] < 0, "usage"] = float("nan")

connections["type"] = (
    connections["type"].astype("string").str.strip().str.lower()
)

# Keep one connection record per ID
connections = connections.drop_duplicates("connection")

# 4. Combine data at connection-date level
daily = meter.dropna(subset=["date", "connection", "usage"])
daily = daily.groupby(
    ["date", "connection"], as_index=False
)["usage"].sum()

data = daily.merge(connections, on="connection", how="left")
data = data.merge(weather, on="date", how="left")

# 5. EDA: usage by locality
print("\nUsage by locality:")
print(data.groupby("locality")["usage"].mean().sort_values(ascending=False))

data.groupby("locality")["usage"].mean().plot(kind="bar")
plt.title("Average Water Usage by Locality")
plt.ylabel("Average Usage")
plt.tight_layout()
plt.show()

# 6. Residential vs commercial
print("\nUsage by connection type:")
print(data.groupby("type")["usage"].mean())

data.boxplot(column="usage", by="type")
plt.title("Residential vs Commercial Usage")
plt.suptitle("")
plt.show()

# 7. Weather relationship
print("\nWeather correlation:")
print(data[["usage", "temperature", "rain"]].corr(numeric_only=True))

data.plot.scatter(x="temperature", y="usage")
plt.title("Temperature vs Water Usage")
plt.show()

# 8. Feature engineering
data = data.sort_values(["connection", "date"])
data["previous_usage"] = data.groupby("connection")["usage"].shift(1)
data["usage_change"] = data["usage"] - data["previous_usage"]
data["month"] = data["date"].dt.month

# 9. Detect unusual readings
features = ["usage", "previous_usage", "usage_change"]
model_data = data[features].dropna().copy()

model = IsolationForest(random_state=42, contamination="auto")
model_data["anomaly"] = model.fit_predict(model_data[features])
model_data["anomaly"] = model_data["anomaly"].map(
    {1: "Normal", -1: "Anomaly"}
)

print("\nAnomaly counts:")
print(model_data["anomaly"].value_counts())

# 10. Feature selection
numeric_features = data[["usage", "previous_usage",
                         "usage_change", "temperature", "rain"]]
numeric_features = numeric_features.dropna()

selector = VarianceThreshold(threshold=0)
selector.fit(numeric_features)

print("Selected features:",
      numeric_features.columns[selector.get_support()].tolist())

# 11. Save outputs
data.to_csv("cleaned_water_usage.csv", index=False)
model_data.to_csv("water_usage_anomalies.csv", index=False)

print("\nAnalysis completed successfully!")
