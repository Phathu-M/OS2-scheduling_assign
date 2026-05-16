import pandas as pd
import glob
import os

INPUT_DIR = "results"
OUTPUT_FILE = "results/summary_throughput.csv"

results = []

files = glob.glob(os.path.join(INPUT_DIR, "output_*.csv"))

for file in files:
    df = pd.read_csv(file)
    df = df.dropna()
    df = df.sort_values("ArrivalTime")

    algo = os.path.basename(file).replace("output_", "").replace(".csv", "")

    # Group rows into runs based on time gaps > 2000ms
    df["run_id"] = (df["ArrivalTime"].diff() > 10000).cumsum()

    for run_id, run_data in df.groupby("run_id"):
        if len(run_data) == 0:
            continue

        patron_count = run_data["PatronID"].nunique()
        start_time = run_data["ArrivalTime"].min()
        end_time = run_data["CompletionTime"].max()
        num_orders = len(run_data)
        runtime = end_time - start_time

        throughput = num_orders / runtime if runtime > 0 else 0

        results.append([
            algo,
            run_id,
            patron_count,
            num_orders,
            runtime,
            throughput
        ])

summary = pd.DataFrame(results, columns=[
    "Algorithm",
    "RunID",
    "PatronCount",
    "OrdersCompleted",
    "Runtime(ms)",
    "Throughput"
])

summary.to_csv(OUTPUT_FILE, index=False)

print("Done!")
print(summary.groupby(["Algorithm", "PatronCount"])["Throughput"].mean().to_string())