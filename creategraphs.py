import csv
import glob
from collections import defaultdict
from turtle import pd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# =========================================================
# SECTION 1: LOAD RAW SIMULATION DATA
# =========================================================
def load_data():
    """
    Loads ONLY raw scheduling simulation outputs.
    Excludes summary and throughput files.
    """

    data = []

    # Only read simulation outputs (NOT summary files)
    files = glob.glob("results/output_*.csv")

    for file in files:
        with open(file, "r") as f:
            reader = csv.DictReader(f)

            for row in reader:
                data.append({
                "file": file,
                "arrival": int(row["ArrivalTime"]),   
                "patron": int(row["PatronID"]),
                "waiting": int(row["WaitingTime"]),
                "turnaround": int(row["TurnaroundTime"]),
                "response": int(row["ResponseTime"]),
            })

    return data

def assign_run_ids(data):
    """
    Groups rows into runs based on gaps in ArrivalTime.
    A new run starts when there's a gap of more than 2 seconds (2000ms)
    between consecutive arrival times.
    """
    if not data:
        return data
    
    data.sort(key=lambda x: (x["file"], x["arrival"]))
    
    run_id = 0
    prev_arrival = None
    prev_file = None
    
    for row in data:
        if prev_file != row["file"] or (row["arrival"] - prev_arrival) > 2000:
            run_id += 1
        row["run_id"] = run_id
        prev_arrival = row["arrival"]
        prev_file = row["file"]
    
    return data

# =========================================================
# SECTION 2: IDENTIFY SCHEDULING ALGORITHM
# =========================================================
def get_algorithm(filename):
    filename = filename.upper()

    if "FCFS" in filename:
        return "FCFS"
    elif "SJF" in filename:
        return "SJF"
    elif "PRIORITY" in filename:
        return "Priority"
    elif "MLFQ" in filename:
        return "MLFQ"
    else:
        return "UNKNOWN"


# =========================================================
# SECTION 3: AGGREGATE METRICS (AVERAGE OVER RUNS/SEEDS)
# =========================================================
def aggregate(data):
    """
    Groups data by (algorithm, run_id) and computes:
    - number of unique patrons in that run (used as x-axis)
    - average metrics across all orders in that run
    """
    # First assign run IDs
    data = assign_run_ids(data)

    # Group by (algorithm, run_id)
    grouped = defaultdict(lambda: {
        "waiting": [],
        "turnaround": [],
        "response": [],
        "patrons": set()
    })

    for row in data:
        alg = get_algorithm(row["file"])
        key = (alg, row["run_id"])
        grouped[key]["waiting"].append(row["waiting"])
        grouped[key]["turnaround"].append(row["turnaround"])
        grouped[key]["response"].append(row["response"])
        grouped[key]["patrons"].add(row["patron"])

    # Now average per (algorithm, patron_count)
    averages = defaultdict(lambda: defaultdict(lambda: {
        "waiting": [], "turnaround": [], "response": []
    }))

    for (alg, run_id), values in grouped.items():
        patron_count = len(values["patrons"])
        averages[alg][patron_count]["waiting"].append(
            sum(values["waiting"]) / len(values["waiting"]))
        averages[alg][patron_count]["turnaround"].append(
            sum(values["turnaround"]) / len(values["turnaround"]))
        averages[alg][patron_count]["response"].append(
            sum(values["response"]) / len(values["response"]))

    # Final average across seeds
    final = defaultdict(dict)
    for alg in averages:
        for patron_count in averages[alg]:
            vals = averages[alg][patron_count]
            final[alg][patron_count] = {
                "waiting": sum(vals["waiting"]) / len(vals["waiting"]),
                "turnaround": sum(vals["turnaround"]) / len(vals["turnaround"]),
                "response": sum(vals["response"]) / len(vals["response"]),
            }

    return final


# =========================================================
# SECTION 4: PLOTTING FUNCTION (LINE GRAPHS)
# =========================================================
def plot_metric(averages, metric, title):
    plt.figure(figsize=(12, 6))

    colors = {
        "FCFS": "#378ADD",
        "SJF": "#639922",
        "Priority": "#EF9F27",
        "MLFQ": "#7F77DD"
    }

    for alg in averages:
        x = sorted(averages[alg].keys())
        y = [averages[alg][p][metric] for p in x]
        plt.plot(x, y, marker="o", linewidth=2, label=alg, color=colors.get(alg, "gray"))

    plt.xlabel("Number of Patrons")
    plt.ylabel(f"{metric.capitalize()} Time (ms)")
    plt.title(title)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.yscale("linear")   # fixed — no more log scale conflict
    plt.tight_layout()
    plt.savefig(f"results/{metric}_vs_patrons.png", dpi=300)
    plt.close()
    
def plot_boxplots(data, metric, title):
    data = assign_run_ids(data)
    
    from collections import defaultdict
    grouped = defaultdict(list)
    
    for row in data:
        alg = get_algorithm(row["file"])
        grouped[alg].append(row[metric])
    
    alg_order = ["FCFS", "SJF", "Priority", "MLFQ"]
    colors = ["#378ADD", "#639922", "#EF9F27", "#7F77DD"]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    bp = ax.boxplot(
    [grouped[a] for a in alg_order],
    tick_labels=alg_order,
    patch_artist=True,
    medianprops=dict(color="black", linewidth=2)
)
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    ax.set_ylabel(f"{metric.capitalize()} Time (ms)")
    ax.set_title(title)
    ax.grid(True, alpha=0.3, axis="y")
    plt.tight_layout()
    plt.savefig(f"results/{metric}_boxplot.png", dpi=300)
    plt.close()
    
# =========================================================
# SECTION 5: LOAD PRECOMPUTED THROUGHPUT
# =========================================================
def load_throughput():
    return pd.read_csv("results/summary_throughput.csv")


# =========================================================
# SECTION 6: PLOT THROUGHPUT
# =========================================================
def plot_throughput(throughput_df):
    plt.figure(figsize=(12, 6))
    
    colors = {
        "FCFS": "#378ADD",
        "SJF": "#639922",
        "PRIORITY": "#EF9F27",
        "MLFQ": "#7F77DD"
    }
    
    for alg in throughput_df["Algorithm"].unique():
        subset = throughput_df[throughput_df["Algorithm"] == alg]
        grouped = subset.groupby("PatronCount")["Throughput"].mean()
        plt.plot(grouped.index, grouped.values, marker="o", linewidth=2, 
                 label=alg, color=colors.get(alg, "gray"))
    
    plt.xlabel("Number of Patrons")
    plt.ylabel("Throughput (orders/ms)")
    plt.title("Throughput vs Number of Patrons")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("results/throughput.png", dpi=300)
    plt.close()

# =========================================================
# SECTION 7: MAIN EXECUTION PIPELINE
# =========================================================
def main():
    data = load_data()
    averages = aggregate(data)

    # Line graphs (avg per patron count)
    plot_metric(averages, "waiting", "Waiting Time vs Number of Patrons")
    plot_metric(averages, "turnaround", "Turnaround Time vs Number of Patrons")
    plot_metric(averages, "response", "Response Time vs Number of Patrons")

    # Boxplots (distribution per algorithm)
    plot_boxplots(data, "waiting", "Distribution of Waiting Time by Algorithm")
    plot_boxplots(data, "turnaround", "Distribution of Turnaround Time by Algorithm")
    plot_boxplots(data, "response", "Distribution of Response Time by Algorithm")

    # Throughput
    throughput = load_throughput()
    plot_throughput(throughput)
    
if __name__ == "__main__":
    main()