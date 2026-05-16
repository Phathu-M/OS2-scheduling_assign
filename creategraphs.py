import csv
import glob
from collections import defaultdict
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
                # Skip separator lines
                if row["RunID"].startswith("SEPARATOR"):
                    continue
                
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
    Reads SEPARATOR lines from CSV files to assign correct
    patron count and run ID to each row.
    """
    files = glob.glob("results/output_*.csv")
    patron_map = {}  # maps (file, arrival_time) to patron_count

    for file in files:
        current_patrons = None
        current_arrivals = []
        
        with open(file, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("SEPARATOR"):
                    parts = line.split(",")
                    current_patrons = int(parts[1])
                elif line.startswith("RunID") or line == "":
                    continue
                else:
                    parts = line.split(",")
                    if len(parts) >= 8 and current_patrons is not None:
                        try:
                            arrival = int(parts[2])
                            patron_map[(file, arrival)] = current_patrons
                        except:
                            continue

    for row in data:
        key = (row["file"], row["arrival"])
        row["patron_count"] = patron_map.get(key, -1)
        row["run_id"] = row["patron_count"]

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
    data = assign_run_ids(data)

    # Group by (algorithm, file, patron_count)
    grouped = defaultdict(lambda: {
        "waiting": [],
        "turnaround": [],
        "response": [],
        "patrons": set(),
        "patron_count": 0
    })

    for row in data:
        alg = get_algorithm(row["file"])
        key = (alg, row["file"], row["patron_count"])
        grouped[key]["waiting"].append(row["waiting"])
        grouped[key]["turnaround"].append(row["turnaround"])
        grouped[key]["response"].append(row["response"])
        grouped[key]["patrons"].add(row["patron"])
        grouped[key]["patron_count"] = row["patron_count"]

    # Average per (algorithm, patron_count)
    averages = defaultdict(lambda: defaultdict(lambda: {
        "waiting": [], "turnaround": [], "response": []
    }))

    for (alg, file, patron_count), values in grouped.items():
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
        "FCFS": "#E91212",
        "SJF": "#639922",
        "Priority": "#EF9F27",
        "MLFQ": "#5B2D8E"
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
    plt.yscale("linear")
    plt.xlim(left=0)   
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
    colors = ["#E91212", "#639922", "#EF9F27", "#5B2D8E"]
    
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
        "FCFS": "#E91212",
        "SJF": "#639922",
        "PRIORITY": "#EF9F27",
        "MLFQ": "#5B2D8E"
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
    plt.xlim(left=0)
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