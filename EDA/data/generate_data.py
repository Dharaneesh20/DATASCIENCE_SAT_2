"""
AquaTrack Utilities - Synthetic Water Usage Dataset Generator
Challenge ID: Use Case 19 | Water Usage Insight | DS Sprint SAT-2
Reproducible generation with fixed random seed (42).
"""

import os
import shutil
import zipfile
import numpy as np
import pandas as pd


def set_seed(seed=42):
    np.random.seed(seed)


def create_connections():
    """
    Generate connections.csv (120 unique connections)
    Columns: connection, type, locality, household_size_band
    """
    conn_ids = [f"CON-{i:03d}" for i in range(1, 121)]
    
    localities = [
        "Green Valley",   # Suburban residential, garden watering
        "Riverside",      # Mixed residential & light commercial
        "Highland Park",  # Affluent residential, pools, large lots
        "Central Ward",   # Dense urban apartments
        "Metro Square",   # Commercial retail & corporate offices
        "Industrial Zone" # Commercial & light manufacturing
    ]
    
    records = []
    
    for i, cid in enumerate(conn_ids):
        # 96 residential (80%), 24 commercial (20%)
        if i < 96:
            ctype = "Residential"
            # Localities for residential
            loc_probs = [0.30, 0.22, 0.20, 0.28, 0.0, 0.0]
            loc = np.random.choice(localities, p=loc_probs)
            # Household size band: Small (30%), Medium (50%), Large (20%)
            h_size = np.random.choice(["Small", "Medium", "Large"], p=[0.30, 0.50, 0.20])
        else:
            ctype = "Commercial"
            # Localities for commercial
            loc_probs = [0.0, 0.15, 0.0, 0.05, 0.45, 0.35]
            loc = np.random.choice(localities, p=loc_probs)
            h_size = "Not Applicable"
            
        records.append({
            "connection": cid,
            "type": ctype,
            "locality": loc,
            "household_size_band": h_size
        })
        
    df_conn = pd.DataFrame(records)
    
    # Introduce intentional inconsistent capitalization and whitespace into 'type' (8 cases)
    dirty_type_indices = [4, 18, 35, 62, 79, 98, 107, 115]
    dirty_variations = [
        " residential",
        "Residential ",
        "RESIDENTIAL",
        " residential ",
        "Commercial ",
        "COMMERCIAL",
        " commercial",
        " commercial "
    ]
    
    for idx, var in zip(dirty_type_indices, dirty_variations):
        df_conn.at[idx, "type"] = var
        
    return df_conn


def create_weather(start_date="2024-01-01", end_date="2024-07-31"):
    """
    Generate weather.csv (Daily observations across 213 days)
    Columns: date, temperature, rain
    """
    dates = pd.date_range(start=start_date, end=end_date, freq="D")
    n_days = len(dates)
    
    # Seasonal temperature curve: Jan (~20°C) -> May (~40°C) -> Jul (~31°C)
    t = np.linspace(0, np.pi, n_days)
    base_temp = 20.0 + 20.0 * np.sin(t * 0.9)
    daily_noise = np.random.normal(0, 1.8, n_days)
    temp = np.round(base_temp + daily_noise, 1)
    
    # Rainfall pattern:
    # Jan-Apr (days 0-120): Mostly dry, prob 0.06
    # May (days 121-151): Pre-monsoon showers, prob 0.20
    # Jun-Jul (days 152-212): Monsoon rains, prob 0.50
    rain = np.zeros(n_days)
    for day in range(n_days):
        if day < 121:
            if np.random.rand() < 0.06:
                rain[day] = np.round(np.random.exponential(4.0) + 1.0, 1)
        elif day < 152:
            if np.random.rand() < 0.20:
                rain[day] = np.round(np.random.gamma(2.5, 4.0) + 3.0, 1)
        else:
            if np.random.rand() < 0.50:
                rain[day] = np.round(np.random.gamma(3.5, 6.0) + 5.0, 1)
                
    df_weather = pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "temperature": temp,
        "rain": rain
    })
    
    # Injected data quality: missing weather values (6 temp, 6 rain)
    missing_temp_idx = [12, 45, 89, 134, 178, 202]
    missing_rain_idx = [25, 63, 101, 142, 185, 209]
    
    for idx in missing_temp_idx:
        df_weather.at[idx, "temperature"] = np.nan
    for idx in missing_rain_idx:
        df_weather.at[idx, "rain"] = np.nan
        
    return df_weather


def create_maintenance(df_conn):
    """
    Generate maintenance.csv (75 maintenance records)
    Columns: connection, leak_report, repair_date
    """
    all_conns = df_conn["connection"].tolist()
    np.random.shuffle(all_conns)
    selected_conns = all_conns[:70]
    
    records = []
    
    # Category 1: Repaired leaks (26 connections)
    repaired_conns = selected_conns[:26]
    repair_dates = pd.date_range("2024-02-15", "2024-06-25", periods=26).strftime("%Y-%m-%d")
    for cid, rdate in zip(repaired_conns, repair_dates):
        records.append({
            "connection": cid,
            "leak_report": "Yes",
            "repair_date": rdate
        })
        
    # Category 2: Unresolved leaks (12 connections)
    unresolved_conns = selected_conns[26:38]
    for cid in unresolved_conns:
        records.append({
            "connection": cid,
            "leak_report": "Yes",
            "repair_date": ""
        })
        
    # Category 3: Inspected, No leak reported (29 connections)
    no_leak_conns = selected_conns[38:67]
    for cid in no_leak_conns:
        records.append({
            "connection": cid,
            "leak_report": "No",
            "repair_date": ""
        })
        
    # Category 4: Ambiguous / Missing leak_report (3 connections)
    missing_report_conns = selected_conns[67:70]
    for cid in missing_report_conns:
        records.append({
            "connection": cid,
            "leak_report": np.nan,
            "repair_date": ""
        })
        
    # Category 5: Unmatched connection records (5 connections not in connections.csv)
    unmatched_conns = ["CON-981", "CON-982", "CON-983", "CON-984", "CON-985"]
    for i, cid in enumerate(unmatched_conns):
        records.append({
            "connection": cid,
            "leak_report": "Yes" if i % 2 == 0 else "No",
            "repair_date": "2024-04-10" if i % 2 == 0 else ""
        })
        
    df_maint = pd.DataFrame(records)
    repaired_map = dict(zip(repaired_conns, repair_dates))
    unresolved_set = set(unresolved_conns)
    
    return df_maint, repaired_map, unresolved_set


def create_meter_readings(df_conn, df_weather, repaired_map, unresolved_set):
    """
    Generate meter.csv (20,000–30,000 rows before cleaning)
    Columns: date, connection, usage
    """
    dates = df_weather["date"].tolist()
    temps = df_weather["temperature"].fillna(28.0).tolist()
    rains = df_weather["rain"].fillna(0.0).tolist()
    dt_objects = pd.to_datetime(dates)
    day_of_week = dt_objects.dayofweek
    
    conn_meta = {}
    for _, row in df_conn.iterrows():
        cid = row["connection"]
        ctype = str(row["type"]).strip().capitalize()
        loc = row["locality"]
        hband = row["household_size_band"]
        
        # Base consumption (kL/day)
        if ctype == "Residential":
            if hband == "Small":
                base = 0.42
            elif hband == "Medium":
                base = 0.88
            else:
                base = 1.55
        else: # Commercial
            if loc == "Central Ward":
                base = 4.2
            elif loc == "Riverside":
                base = 6.5
            elif loc == "Metro Square":
                base = 9.8
            else:
                base = 14.5
                
        # Locality multiplier
        loc_mults = {
            "Highland Park": 1.25,
            "Green Valley": 1.10,
            "Riverside": 1.00,
            "Central Ward": 0.92,
            "Metro Square": 1.00,
            "Industrial Zone": 1.12
        }
        loc_mult = loc_mults.get(loc, 1.0)
        
        conn_factor = np.random.normal(1.0, 0.08)
        conn_factor = max(0.7, min(1.3, conn_factor))
        
        conn_meta[cid] = {
            "type": ctype,
            "base": base * loc_mult * conn_factor,
            "locality": loc,
            "hband": hband
        }
        
    records = []
    
    unresolved_start_days = {
        cid: np.random.randint(45, 105) for cid in unresolved_set
    }
    
    for day_idx, d_str in enumerate(dates):
        cur_dt = dt_objects[day_idx]
        dow = day_of_week[day_idx]
        temp = temps[day_idx]
        rain = rains[day_idx]
        
        # Weather adjustments
        temp_adj = 1.0 + (temp - 27.0) * 0.012
        rain_adj = 0.88 if rain > 8.0 else (0.94 if rain > 1.0 else 1.0)
        
        for cid, meta in conn_meta.items():
            ctype = meta["type"]
            base = meta["base"]
            
            # Day of week adjustments
            if ctype == "Residential":
                dow_adj = 1.18 if dow in [5, 6] else (0.95 if dow == 0 else 0.98)
            else:
                dow_adj = 1.12 if dow in [0, 1, 2, 3, 4] else (0.45 if dow == 6 else 0.75)
                
            noise = np.random.lognormal(mean=0.0, sigma=0.15)
            usage = base * dow_adj * temp_adj * rain_adj * noise
            
            # Maintenance Leak Simulation
            # 1. Repaired leak: elevated before repair_date, normal after repair_date
            if cid in repaired_map:
                r_date_str = repaired_map[cid]
                r_dt = pd.to_datetime(r_date_str)
                leak_start_dt = r_dt - pd.Timedelta(days=np.random.randint(30, 50))
                if leak_start_dt <= cur_dt < r_dt:
                    leak_amount = 2.5 + np.random.uniform(0.5, 2.0)
                    usage += leak_amount
                    
            # 2. Unresolved leak: elevated after start date till end of simulation
            if cid in unresolved_set:
                start_day = unresolved_start_days[cid]
                if day_idx >= start_day:
                    leak_amount = 3.0 + np.random.uniform(0.8, 2.5)
                    usage += leak_amount
                    
            records.append({
                "date": d_str,
                "connection": cid,
                "usage": round(usage, 3)
            })
            
    df_meter = pd.DataFrame(records)
    
    # ---------------- INTENTIONAL DATA QUALITY INJECTIONS ----------------
    
    # 1. Spontaneous High-Usage Spikes (90 occurrences)
    spike_indices = np.random.choice(df_meter.index, size=90, replace=False)
    for idx in spike_indices:
        curr_val = df_meter.at[idx, "usage"]
        df_meter.at[idx, "usage"] = round(curr_val + np.random.uniform(9.0, 24.0), 3)
        
    # 2. Missing Meter Days (420 dropped readings)
    drop_indices = np.random.choice(df_meter.index, size=420, replace=False)
    df_meter = df_meter.drop(index=drop_indices).reset_index(drop=True)
    
    # 3. Missing Usage Values (150 readings)
    missing_usage_indices = np.random.choice(df_meter.index, size=150, replace=False)
    for idx in missing_usage_indices:
        df_meter.at[idx, "usage"] = np.nan
        
    # 4. Negative Usage Values (45 readings)
    negative_indices = np.random.choice(
        [i for i in df_meter.index if i not in missing_usage_indices], 
        size=45, 
        replace=False
    )
    for idx in negative_indices:
        df_meter.at[idx, "usage"] = round(-abs(np.random.uniform(0.15, 4.50)), 3)
        
    # 5. Duplicate Meter Records (210 duplicated records)
    dup_candidates = np.random.choice(df_meter.index, size=210, replace=False)
    duplicates = df_meter.loc[dup_candidates].copy()
    df_meter = pd.concat([df_meter, duplicates], ignore_index=True)
    
    # Shuffle and sort
    df_meter = df_meter.sample(frac=1.0, random_state=42).reset_index(drop=True)
    df_meter = df_meter.sort_values(by=["date", "connection"]).reset_index(drop=True)
    
    return df_meter, conn_meta


def create_billing(df_meter, df_conn):
    """
    Generate billing.csv (600–1,000 rows)
    Columns: connection, billing_cycle, charge
    """
    df_clean = df_meter.dropna(subset=["usage"]).copy()
    df_clean = df_clean[df_clean["usage"] >= 0].copy()
    df_clean["billing_cycle"] = pd.to_datetime(df_clean["date"]).dt.strftime("%Y-%m")
    
    monthly_usage = df_clean.groupby(["connection", "billing_cycle"])["usage"].sum().reset_index()
    
    conn_type_map = {}
    for _, row in df_conn.iterrows():
        ctype = str(row["type"]).strip().capitalize()
        conn_type_map[row["connection"]] = ctype
        
    records = []
    
    for _, row in monthly_usage.iterrows():
        cid = row["connection"]
        cycle = row["billing_cycle"]
        kL = row["usage"]
        ctype = conn_type_map.get(cid, "Residential")
        
        # Tariff structure in INR
        if ctype == "Residential":
            fixed = 160.0
            if kL <= 15:
                volumetric = kL * 24.0
            elif kL <= 30:
                volumetric = (15 * 24.0) + ((kL - 15) * 42.0)
            else:
                volumetric = (15 * 24.0) + (15 * 42.0) + ((kL - 30) * 72.0)
        else: # Commercial
            fixed = 650.0
            if kL <= 100:
                volumetric = kL * 75.0
            else:
                volumetric = (100 * 75.0) + ((kL - 100) * 105.0)
                
        surcharge = np.random.uniform(-0.015, 0.025) * (fixed + volumetric)
        charge = round(fixed + volumetric + surcharge, 2)
        
        records.append({
            "connection": cid,
            "billing_cycle": cycle,
            "charge": charge
        })
        
    df_billing = pd.DataFrame(records)
    
    # Injected data quality: missing charges (20) & unmatched connections (14)
    missing_charge_indices = np.random.choice(df_billing.index, size=20, replace=False)
    for idx in missing_charge_indices:
        df_billing.at[idx, "charge"] = np.nan
        
    unmatched_records = []
    unmatched_ids = [f"CON-{i}" for i in range(951, 958)]
    for uid in unmatched_ids:
        unmatched_records.append({
            "connection": uid,
            "billing_cycle": "2024-05",
            "charge": round(np.random.uniform(550.0, 2400.0), 2)
        })
        unmatched_records.append({
            "connection": uid,
            "billing_cycle": "2024-06",
            "charge": round(np.random.uniform(580.0, 2600.0), 2)
        })
        
    df_unmatched = pd.DataFrame(unmatched_records)
    df_billing = pd.concat([df_billing, df_unmatched], ignore_index=True)
    
    assert (df_billing["charge"].dropna() >= 0).all(), "Found negative charge!"
    return df_billing


def create_data_quality_report():
    """
    Generate data_quality_report.csv
    Comprehensive tracking table of all injected data flaws.
    """
    issues = [
        {
            "dataset": "meter.csv",
            "issue_type": "Missing Values",
            "column_affected": "usage",
            "count_injected": 150,
            "description": "Daily consumption readings recorded as NaN due to corrupted telemetry packet payload.",
            "suggested_treatment": "Impute using rolling median of connection baseline or exclude from rate calculations."
        },
        {
            "dataset": "meter.csv",
            "issue_type": "Invalid Negative Values",
            "column_affected": "usage",
            "count_injected": 45,
            "description": "Negative water usage values (-0.15 to -4.50 kL) caused by mechanical meter backspin or human data entry inversion.",
            "suggested_treatment": "Inspect meter reverse-flow flags; take absolute value if proven inversion, or replace with NaN and interpolate."
        },
        {
            "dataset": "meter.csv",
            "issue_type": "Duplicate Records",
            "column_affected": "date, connection",
            "count_injected": 210,
            "description": "Duplicate daily reading records caused by dual gateway telemetry retransmission.",
            "suggested_treatment": "De-duplicate by dropping duplicate (date, connection) tuples, retaining primary single instance."
        },
        {
            "dataset": "meter.csv",
            "issue_type": "Data Transmission Dropout (Missing Days)",
            "column_affected": "date, connection",
            "count_injected": 420,
            "description": "Missing calendar days for connections where the smart meter failed to connect to cell tower.",
            "suggested_treatment": "Reindex date ranges per connection to detect temporal gaps and apply forward-fill or seasonal interpolation."
        },
        {
            "dataset": "meter.csv",
            "issue_type": "Genuine High-Usage Spikes",
            "column_affected": "usage",
            "count_injected": 90,
            "description": "Sudden extreme consumption spikes (6x-12x above median) reflecting real burst pipes, pool filling, or plumbing failures.",
            "suggested_treatment": "Flag via ML anomaly detection algorithms (Isolation Forest, DBSCAN) for investigation rather than naive deletion."
        },
        {
            "dataset": "connections.csv",
            "issue_type": "Inconsistent Formatting & Whitespace",
            "column_affected": "type",
            "count_injected": 8,
            "description": "Inconsistent casing and leading/trailing whitespace (e.g. ' residential', 'RESIDENTIAL', 'Commercial ').",
            "suggested_treatment": "Apply string trimming (.strip()) and title capitalization (.capitalize())."
        },
        {
            "dataset": "billing.csv",
            "issue_type": "Missing Values",
            "column_affected": "charge",
            "count_injected": 20,
            "description": "Monthly billing charges recorded as NaN due to uncalculated billing cycles or pending adjustments.",
            "suggested_treatment": "Recalculate charge using tariff schedule based on aggregated monthly meter usage."
        },
        {
            "dataset": "billing.csv",
            "issue_type": "Referential Integrity Violation (Unmatched Keys)",
            "column_affected": "connection",
            "count_injected": 14,
            "description": "Billing records referencing connection IDs (CON-951 to CON-957) absent from master connections table.",
            "suggested_treatment": "Perform left/inner joins to isolate orphaned billing records and verify CRM master data synchronization."
        },
        {
            "dataset": "weather.csv",
            "issue_type": "Missing Values",
            "column_affected": "temperature",
            "count_injected": 6,
            "description": "Missing daily temperature readings from regional meteorological station sensor downtime.",
            "suggested_treatment": "Impute using time-series interpolation (.interpolate(method='time')) or adjacent day averages."
        },
        {
            "dataset": "weather.csv",
            "issue_type": "Missing Values",
            "column_affected": "rain",
            "count_injected": 6,
            "description": "Missing daily precipitation readings due to rain gauge sensor maintenance.",
            "suggested_treatment": "Impute with 0.0 or seasonal local rain average."
        },
        {
            "dataset": "maintenance.csv",
            "issue_type": "Referential Integrity Violation (Unmatched Keys)",
            "column_affected": "connection",
            "count_injected": 5,
            "description": "Maintenance work orders referencing connection IDs (CON-981 to CON-985) not registered in connections table.",
            "suggested_treatment": "Cross-reference with municipal field service database or filter out prior to joining with master customer registry."
        },
        {
            "dataset": "maintenance.csv",
            "issue_type": "Missing Values",
            "column_affected": "leak_report",
            "count_injected": 3,
            "description": "Work order records with unspecified/blank leak report status.",
            "suggested_treatment": "Standardize missing status to 'Unknown' or verify manual field inspection logs."
        },
        {
            "dataset": "maintenance.csv",
            "issue_type": "Domain Null Values (Unresolved Leaks & No-Leak Audits)",
            "column_affected": "repair_date",
            "count_injected": 41,
            "description": "Blank repair_date for 12 ongoing/unresolved leak reports and 29 negative leak audits.",
            "suggested_treatment": "Distinguish between true nulls (no repair needed) vs pending repairs (ongoing active leak)."
        }
    ]
    return pd.DataFrame(issues)


def package_zip(root_folder="water-usage-insight", zip_filename="water_usage_synthetic_datasets.zip"):
    """
    Package the dataset folder into a clean ZIP archive.
    """
    print(f"\n[Packaging] Compressing '{root_folder}' into '{zip_filename}'...")
    with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(root_folder):
            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, os.path.dirname(root_folder))
                zipf.write(abs_path, rel_path)
    print(f"            Successfully created archive: {os.path.abspath(zip_filename)} ({os.path.getsize(zip_filename):,} bytes)")


def generate_all(output_dir="water-usage-insight"):
    set_seed(42)
    
    data_dir = os.path.join(output_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    
    print("=" * 70)
    print("AquaTrack Utilities - Generating Synthetic Datasets (Seed=42)")
    print("=" * 70)
    
    # 1. Connections
    print("\n[1/5] Generating connections.csv...")
    df_conn = create_connections()
    conn_path = os.path.join(data_dir, "connections.csv")
    df_conn.to_csv(conn_path, index=False)
    print(f"      Saved: {conn_path} | Shape: {df_conn.shape}")
    
    # 2. Weather
    print("\n[2/5] Generating weather.csv...")
    df_weather = create_weather()
    weather_path = os.path.join(data_dir, "weather.csv")
    df_weather.to_csv(weather_path, index=False)
    print(f"      Saved: {weather_path} | Shape: {df_weather.shape}")
    
    # 3. Maintenance
    print("\n[3/5] Generating maintenance.csv...")
    df_maint, repaired_map, unresolved_set = create_maintenance(df_conn)
    maint_path = os.path.join(data_dir, "maintenance.csv")
    df_maint.to_csv(maint_path, index=False)
    print(f"      Saved: {maint_path} | Shape: {df_maint.shape}")
    
    # 4. Meter readings
    print("\n[4/5] Generating meter.csv...")
    df_meter, conn_meta = create_meter_readings(df_conn, df_weather, repaired_map, unresolved_set)
    meter_path = os.path.join(data_dir, "meter.csv")
    df_meter.to_csv(meter_path, index=False)
    print(f"      Saved: {meter_path} | Shape: {df_meter.shape}")
    
    # 5. Billing
    print("\n[5/5] Generating billing.csv...")
    df_billing = create_billing(df_meter, df_conn)
    billing_path = os.path.join(data_dir, "billing.csv")
    df_billing.to_csv(billing_path, index=False)
    print(f"      Saved: {billing_path} | Shape: {df_billing.shape}")
    
    # 6. Data Quality Report
    print("\n[6/6] Generating data_quality_report.csv...")
    df_report = create_data_quality_report()
    report_path = os.path.join(data_dir, "data_quality_report.csv")
    df_report.to_csv(report_path, index=False)
    print(f"      Saved: {report_path} | Shape: {df_report.shape}")
    
    # Validation & Diagnostics
    print("\n" + "=" * 70)
    print("DATASET VALIDATION & DIAGNOSTICS REPORT")
    print("=" * 70)
    
    datasets = {
        "connections.csv": df_conn,
        "weather.csv": df_weather,
        "maintenance.csv": df_maint,
        "meter.csv": df_meter,
        "billing.csv": df_billing,
        "data_quality_report.csv": df_report
    }
    
    for name, df in datasets.items():
        print(f"\n--- {name} ---")
        print(f"Shape: {df.shape[0]:,} rows x {df.shape[1]} columns")
        print(f"Columns: {list(df.columns)}")
        print("Missing values per column:")
        null_counts = df.isnull().sum()
        for col, count in null_counts.items():
            print(f"  - {col}: {count} ({count/len(df)*100:.2f}%)")
            
    # Specific Checks
    print("\n>>> Specific Data Quality Validations <<<")
    meter_dups = df_meter.duplicated(subset=["date", "connection"]).sum()
    meter_neg = (df_meter["usage"] < 0).sum()
    print(f"[meter.csv] Duplicate (date, connection) pairs: {meter_dups}")
    print(f"[meter.csv] Negative usage count: {meter_neg}")
    print(f"[meter.csv] Extreme spikes (>20 kL): {(df_meter['usage'] > 20.0).sum()}")
    
    raw_types = df_conn["type"].tolist()
    non_standard_types = [t for t in raw_types if t not in ["Residential", "Commercial"]]
    print(f"[connections.csv] Non-standard type labels: {len(non_standard_types)} ({set(non_standard_types)})")
    
    valid_conn_set = set(df_conn["connection"])
    billing_conn_set = set(df_billing["connection"])
    billing_unmatched = billing_conn_set - valid_conn_set
    print(f"[billing.csv] Unmatched connection IDs: {len(billing_unmatched)} ({billing_unmatched})")
    billing_neg = (df_billing["charge"] < 0).sum()
    print(f"[billing.csv] Negative charges count: {billing_neg}")
    
    maint_conn_set = set(df_maint["connection"])
    maint_unmatched = maint_conn_set - valid_conn_set
    print(f"[maintenance.csv] Unmatched connection IDs: {len(maint_unmatched)} ({maint_unmatched})")
    
    # Package into ZIP archive
    package_zip(root_folder=output_dir, zip_filename="water_usage_synthetic_datasets.zip")
    
    print("\n" + "=" * 70)
    print("All datasets successfully generated, validated, and compressed.")
    print("=" * 70)
    
    return datasets


if __name__ == "__main__":
    generate_all()
