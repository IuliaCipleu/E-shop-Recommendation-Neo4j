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

    for entry in data:
        qid = entry["query_id"]
        per_param = entry["per_param_results"]

        # --- recompute "true" cold & hot ---
        if per_param:
            true_cold = per_param[0]["cold_time"]
            hot_means = [p["hot_mean"] for p in per_param]
            true_hot = sum(hot_means) / len(hot_means)
        else:
            true_cold = 0.0
            true_hot = 0.0

        # ------------------------------
        # Cold vs Hot BAR plot
        # ------------------------------
        plt.figure(figsize=(8,5))
        plt.bar(["Cold (1st ever)", "Hot (avg)"], [true_cold, true_hot],
                color=["red","green"])
        plt.title(f"Query {qid} — Cold vs Hot ({size} dataset)", fontsize=14)
        plt.ylabel("Seconds", fontsize=12)
        save_plot(f"{size}_query_{qid}_cold_vs_hot_bar.png")

        # ------------------------------
        # Cold vs Hot SCATTER plot
        # ------------------------------
        cold_times = [per_param[0]["cold_time"]] if per_param else []
        hot_means_per_param  = [p["hot_mean"] for p in per_param]
        params = [p["params"]["userId"] for p in per_param]

        plt.figure(figsize=(10,5))
        # mark the true cold point as a star if present
        if params:
            plt.scatter([params[0]], [per_param[0]["cold_time"]],
                        color="red", label="Cold (first run)", marker="*",
                        s=80)
        plt.scatter(params, hot_means_per_param,
                    color="green", label="Hot (per user)", alpha=0.7)
        plt.title(f"Query {qid} — Cold vs Hot by Parameter ({size})", fontsize=14)
        plt.xlabel("userId", fontsize=12)
        plt.ylabel("Seconds", fontsize=12)
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

# recompute per-query hot using per_param_results
def get_true_hot(entry):
    per_param = entry["per_param_results"]
    if not per_param:
        return 0.0
    hot_means = [p["hot_mean"] for p in per_param]
    return sum(hot_means) / len(hot_means)

def get_true_cold(entry):
    per_param = entry["per_param_results"]
    if not per_param:
        return 0.0
    return per_param[0]["cold_time"]


plt.figure(figsize=(12,5))
for size, data in datasets.items():
    hot_avgs = [get_true_hot(e) for e in data]
    plt.plot(all_query_ids, hot_avgs, marker='o', linestyle='--', label=f"{size} (hot)")

plt.title("HOT Execution Time Comparison — Small vs Medium vs Large", fontsize=14)
plt.xlabel("Query ID", fontsize=12)
plt.ylabel("Avg Execution Time (sec)", fontsize=12)
plt.legend()
plt.grid(True, alpha=0.4)
save_plot("all_hot_exec_comparison.png")

# ----------------------------------------------
# Average COLD execution per query across datasets
# ----------------------------------------------
plt.figure(figsize=(12,5))
for size, data in datasets.items():
    cold_vals = [get_true_cold(e) for e in data]
    plt.plot(all_query_ids, cold_vals, marker='o', linestyle='--', label=f"{size} (cold)")

plt.title("COLD Execution Time Comparison — Small vs Medium vs Large", fontsize=14)
plt.xlabel("Query ID", fontsize=12)
plt.ylabel("Cold Start Time (sec)", fontsize=12)
plt.legend()
plt.grid(True, alpha=0.4)
save_plot("all_cold_exec_comparison.png")

# ==============================================================
#   SECTION 3 — COMBINED BAR CHART (HOT + COLD)
# ==============================================================
# ----------------------------------------------
# Helper functions for true cold/hot per entry
# ----------------------------------------------
def true_cold(entry):
    per_param = entry["per_param_results"]
    if not per_param:
        return 0.0
    # Only the VERY FIRST cold_time is truly cold
    return per_param[0]["cold_time"]

def true_hot(entry):
    per_param = entry["per_param_results"]
    if not per_param:
        return 0.0
    hot_means = [p["hot_mean"] for p in per_param]
    return sum(hot_means) / len(hot_means)


# ==============================================================
#   FIXED SECTION 3 — COMBINED BAR CHART (HOT + COLD)
# ==============================================================

width = 0.25
x = np.arange(len(all_query_ids))

# ---------- COLD BAR CHART ----------
plt.figure(figsize=(12,5))

for i, size in enumerate(["small", "medium", "large"]):
    data = datasets[size]
    cold_vals = [true_cold(entry) for entry in data]
    plt.bar(x + i*width, cold_vals, width=width, label=f"{size} (cold)")

plt.xticks(x + width, all_query_ids)
plt.title("TRUE COLD Start Time per Query — All Dataset Sizes", fontsize=14)
plt.xlabel("Query ID", fontsize=12)
plt.ylabel("Seconds", fontsize=12)
plt.legend()
plt.grid(axis='y', alpha=0.3)
save_plot("cold_all_sizes_bar.png")


# ---------- HOT BAR CHART ----------
plt.figure(figsize=(12,5))

for i, size in enumerate(["small", "medium", "large"]):
    data = datasets[size]
    hot_vals = [true_hot(entry) for entry in data]
    plt.bar(x + i*width, hot_vals, width=width, label=f"{size} (hot)")

plt.xticks(x + width, all_query_ids)
plt.title("TRUE HOT Execution Time per Query — All Dataset Sizes", fontsize=14)
plt.xlabel("Query ID", fontsize=12)
plt.ylabel("Seconds", fontsize=12)
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
