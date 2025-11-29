import json
import os
import matplotlib.pyplot as plt
import numpy as np

# ===============================
# CONFIG: all three datasets
# ===============================
INPUT_JSONS = {
    "small":  "benchmark_results_small.json",
    "medium": "benchmark_results_medium.json",
    "large":  "benchmark_results_large.json"
}

OUTPUT_DIR = "plots_combined"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ===============================
# Helper: Save plot
# ===============================
def save_plot(filename):
    path = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(path, dpi=200, bbox_inches='tight')
    print(f"Saved: {path}")
    plt.close()

# ===============================
# Load all JSONs
# ===============================
datasets = {}

for size, file in INPUT_JSONS.items():
    with open(file, "r") as f:
        datasets[size] = json.load(f)
    print(f"Loaded {len(datasets[size])} queries from {file}")

# ==============================================================
#   SECTION 1 — PER-DATASET PLOTS (cold vs hot per query)
# ==============================================================

for size, data in datasets.items():

    print(f"\nGenerating plots for dataset: {size}")

    size_dir = os.path.join(OUTPUT_DIR, size)
    os.makedirs(size_dir, exist_ok=True)

    def save_local_plot(name):
        save_plot(os.path.join(size, name))

    for entry in data:
        qid = entry["query_id"]
        cold = entry["cold_avg_sec"]
        hot = entry["hot_avg_sec"]

        # ------------------------------
        # Cold vs Hot BAR plot
        # ------------------------------
        plt.figure(figsize=(8,5))
        plt.bar(["Cold (1st run)", "Hot (avg subsequent)"], [cold, hot], color=["red","green"])
        plt.title(f"Query {qid} — Cold vs Hot ({size} dataset)")
        plt.ylabel("Seconds")
        save_plot(f"{size}_query_{qid}_cold_vs_hot_bar.png")

        # ------------------------------
        # Cold vs Hot SCATTER plot
        # (per-parameter values)
        # ------------------------------
        per_param = entry["per_param_results"]
        cold_times = [p["cold_time"] for p in per_param]
        hot_means  = [p["hot_mean"] for p in per_param]
        params     = [p["params"]["userId"] for p in per_param]

        plt.figure(figsize=(10,5))
        plt.scatter(params, cold_times, color="red", label="Cold")
        plt.scatter(params, hot_means,  color="green", label="Hot")
        plt.title(f"Query {qid} — Cold vs Hot by Parameter ({size})")
        plt.xlabel("userId")
        plt.ylabel("Seconds")
        plt.legend()
        plt.grid(True, alpha=0.3)
        save_plot(f"{size}_query_{qid}_cold_vs_hot_scatter.png")

# ==============================================================
#   SECTION 2 — COMPARATIVE PLOTS ACROSS DATASETS
# ==============================================================

print("\nGenerating cross-dataset comparisons")

# ----------------------------------------------
# Average HOT execution per query across datasets
# ----------------------------------------------
all_query_ids = [entry["query_id"] for entry in datasets["small"]]

plt.figure(figsize=(12,6))

for size, data in datasets.items():
    hot_avgs = [entry["hot_avg_sec"] for entry in data]
    plt.plot(all_query_ids, hot_avgs, marker='o', linestyle='--', label=f"{size} (hot)")

plt.title("HOT Execution Time Comparison — Small vs Medium vs Large")
plt.xlabel("Query ID")
plt.ylabel("Avg Execution Time (sec)")
plt.legend()
plt.grid(True, alpha=0.4)
save_plot("all_hot_exec_comparison.png")

# ----------------------------------------------
# Average COLD execution per query across datasets
# ----------------------------------------------
plt.figure(figsize=(12,6))

for size, data in datasets.items():
    cold_avgs = [entry["cold_avg_sec"] for entry in data]
    plt.plot(all_query_ids, cold_avgs, marker='o', linestyle='--', label=f"{size} (cold)")

plt.title("COLD Execution Time Comparison — Small vs Medium vs Large")
plt.xlabel("Query ID")
plt.ylabel("Cold Start Time (sec)")
plt.legend()
plt.grid(True, alpha=0.4)
save_plot("all_cold_exec_comparison.png")

# ==============================================================
#   SECTION 3 — COMBINED BAR CHART (HOT + COLD)
# ==============================================================

width = 0.25
x = np.arange(len(all_query_ids))

plt.figure(figsize=(14,6))

for i, size in enumerate(["small","medium","large"]):
    data = datasets[size]
    cold_vals = [entry["cold_avg_sec"] for entry in data]
    plt.bar(x + i*width, cold_vals, width=width, label=f"{size} (cold)")

plt.xticks(x + width, all_query_ids)
plt.title("COLD Start Time per Query — All Sizes")
plt.xlabel("Query ID")
plt.ylabel("Seconds")
plt.legend()
plt.grid(axis='y', alpha=0.3)
save_plot("cold_all_sizes_bar.png")

plt.figure(figsize=(14,6))

for i, size in enumerate(["small","medium","large"]):
    data = datasets[size]
    hot_vals = [entry["hot_avg_sec"] for entry in data]
    plt.bar(x + i*width, hot_vals, width=width, label=f"{size} (hot)")

plt.xticks(x + width, all_query_ids)
plt.title("HOT Execution Time per Query — All Sizes")
plt.xlabel("Query ID")
plt.ylabel("Seconds")
plt.legend()
plt.grid(axis='y', alpha=0.3)
save_plot("hot_all_sizes_bar.png")

# ==============================================================
#   SECTION 4 — LATEX TABLE FOR ALL DATASETS
# ==============================================================

latex_path = os.path.join(OUTPUT_DIR, "latex_table_all_sizes.tex")

latex = []
latex.append("\\begin{table}[h!]")
latex.append("\\centering")
latex.append("\\begin{tabular}{|c|c|c|c|}")
latex.append("\\hline")
latex.append("\\textbf{Query ID} & \\textbf{Small (hot)} & \\textbf{Medium (hot)} & \\textbf{Large (hot)}\\\\")
latex.append("\\hline")

for q in all_query_ids:
    s = datasets["small"][q-1]["hot_avg_sec"]
    m = datasets["medium"][q-1]["hot_avg_sec"]
    l = datasets["large"][q-1]["hot_avg_sec"]
    latex.append(f"{q} & {s:.4f} & {m:.4f} & {l:.4f}\\\\")
    latex.append("\\hline")

latex.append("\\end{tabular}")
latex.append("\\caption{Hot execution time comparison across datasets.}")
latex.append("\\label{tab:hot_comparison}")
latex.append("\\end{table}")

with open(latex_path, "w") as f:
    f.write("\n".join(latex))

print(f"LaTeX table saved to {latex_path}")
print("\n  All plots and comparisons generated!")
