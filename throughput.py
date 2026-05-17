import pandas as pd
import glob
import os

# =========================================================
# SECTION 1: FILE SETUP
# =========================================================
INPUT_DIR = "results"
OUTPUT_FILE = "results/summary_throughput.csv"

results = []

files = glob.glob(os.path.join(INPUT_DIR, "output_*.csv"))

# =========================================================
# SECTION 2: PROCESS EACH FILE (EACH ALGORITHM)
# =========================================================
for file in files:
    algo = os.path.basename(file).replace("output_", "").replace(".csv", "")
    
    current_patrons = None
    current_seed = None
    current_rows = []
    
    with open(file, "r") as f:
        lines = f.readlines()
# =========================================================
# SECTION 3: READ EACH LINE IN FILE
# =========================================================    
    for line in lines:
        line = line.strip()
        
        # Skip header
        if line.startswith("RunID") or line == "":
            continue
        
        #  When we hit SEPARATOR, it means a new simulation run
        if line.startswith("SEPARATOR"):
            # Process previous run if exists
            if current_rows and current_patrons is not None:
                df = pd.DataFrame(current_rows)
                patron_count = df["PatronID"].nunique()
                start_time = df["ArrivalTime"].min()
                end_time = df["CompletionTime"].max()
                num_orders = len(df)
                runtime = end_time - start_time
                throughput = num_orders / runtime if runtime > 0 else 0
                results.append([algo, current_patrons, current_seed, patron_count, num_orders, runtime, throughput])
            
            # Start new run
            parts = line.split(",")
            current_patrons = int(parts[1])
            current_seed = int(parts[2])
            current_rows = []
        
        else:
            # Parse data row
            parts = line.split(",")
            if len(parts) >= 8:
                try:
                    current_rows.append({
                        "PatronID": int(parts[1]),
                        "ArrivalTime": int(parts[2]),
                        "CompletionTime": int(parts[4]),
                    })
                except:
                    continue
    
    # =========================================================
    # SECTION 4: PROCESS LAST RUN IN FILE
    # =========================================================
    if current_rows and current_patrons is not None:
        df = pd.DataFrame(current_rows)
        patron_count = df["PatronID"].nunique()
        start_time = df["ArrivalTime"].min()
        end_time = df["CompletionTime"].max()
        num_orders = len(df)
        runtime = end_time - start_time
        throughput = num_orders / runtime if runtime > 0 else 0
        results.append([algo, current_patrons, current_seed, patron_count, num_orders, runtime, throughput])
# =========================================================
# SECTION 5: CREATE FINAL SUMMARY TABLE
# =========================================================
summary = pd.DataFrame(results, columns=[
    "Algorithm", "PatronCount", "Seed", "UniquePatrons",
    "OrdersCompleted", "Runtime(ms)", "Throughput"
])

summary.to_csv(OUTPUT_FILE, index=False)

print("Done!")
print(summary.groupby(["Algorithm", "PatronCount"])["Throughput"].mean().to_string())