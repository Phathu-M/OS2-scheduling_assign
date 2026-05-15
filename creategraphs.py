import csv
import glob
from collections import defaultdict
import matplotlib.pyplot as plt
import numpy as np

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
                    "patron": int(row["PatronID"]),
                    "waiting": int(row["WaitingTime"]),
                    "turnaround": int(row["TurnaroundTime"]),
                    "response": int(row["ResponseTime"]),
                })

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
    Groups data by (algorithm, number of patrons)
    and computes average metrics.
    """

    grouped = defaultdict(lambda: {
        "waiting": [],
        "turnaround": [],
        "response": []
    })

    for row in data:
        alg = get_algorithm(row["file"])
        patron = row["patron"]

        key = (alg, patron)

        grouped[key]["waiting"].append(row["waiting"])
        grouped[key]["turnaround"].append(row["turnaround"])
        grouped[key]["response"].append(row["response"])

    averages = defaultdict(dict)

    for (alg, patron), values in grouped.items():
        averages[alg][patron] = {
            "waiting": sum(values["waiting"]) / len(values["waiting"]),
            "turnaround": sum(values["turnaround"]) / len(values["turnaround"]),
            "response": sum(values["response"]) / len(values["response"]),
        }

    return averages


# =========================================================
# SECTION 4: PLOTTING FUNCTION (LINE GRAPHS)
# =========================================================
def plot_metric(averages, metric, title):
    plt.figure(figsize=(12, 6))

    for alg in averages:
        x = sorted(averages[alg].keys())
        y = [averages[alg][p][metric] for p in x]
        
        plt.plot(x, y, marker="o", linewidth=2, label=alg)

    plt.xlabel("Number of Patrons")
    plt.ylabel(f"{metric.capitalize()} Time")

    plt.title(title)
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.yscale("log")
    
    y_all = []
    for alg in averages:
        for p in averages[alg]:
            y_all.append(averages[alg][p][metric])

    # zoom into data range
    plt.ylim(min(y_all) * 0.95, max(y_all) * 1.05)

    plt.tight_layout()
    
    plt.savefig(f"results/{metric}_vs_patrons.png", dpi=300)

    plt.show()

# =========================================================
# SECTION 5: LOAD PRECOMPUTED THROUGHPUT
# =========================================================
def load_throughput():
    """
    Reads throughput directly from summary file.
    (Cleaner and more reliable than recomputing)
    """

    throughput = {}

    file_path = "results/summary_throughput.csv"

    with open(file_path, "r") as f:
        reader = csv.DictReader(f)

        for row in reader:
            throughput[row["Algorithm"]] = float(row["Throughput"])

    return throughput


# =========================================================
# SECTION 6: PLOT THROUGHPUT
# =========================================================
def plot_throughput(throughput):
    plt.figure()

    algs = list(throughput.keys())
    values = [throughput[a] for a in algs]

    plt.bar(algs, values)
    plt.yscale("log")

    plt.xlabel("Scheduling Algorithm")
    plt.ylabel("Throughput")
    plt.title("Throughput Comparison")
    plt.grid(axis="y")
    
    plt.savefig("results/throughput.png", dpi=300)

    plt.show()

# =========================================================
# SECTION 7: MAIN EXECUTION PIPELINE
# =========================================================
def main():
    data = load_data()
    averages = aggregate(data)

    # Line graphs
    plot_metric(averages, "waiting", "Waiting Time vs Number of Patrons")
    plot_metric(averages, "turnaround", "Turnaround Time vs Number of Patrons")
    plot_metric(averages, "response", "Response Time vs Number of Patrons")

    # Throughput bar chart
    throughput = load_throughput()
    plot_throughput(throughput)

    plt.show()


if __name__ == "__main__":
    main()