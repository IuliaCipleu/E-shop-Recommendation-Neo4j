import json
import os
import matplotlib.pyplot as plt
import numpy as np

INPUT_JSON = "benchmark_results_small.json"
OUTPUT_DIR = "plots_small"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================
# Load benchmark data
# ============================
with open(INPUT_JSON, "r") as f:
    data = json.load(f)

print(f"Loaded {len(data)} queries from {INPUT_JSON}")

# ============================
# Helper: Save plots nicely
# ============================
def save_plot(filename):
    path = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(path, dpi=200, bbox_inches='tight')
    print(f"Saved: {path}")
    plt.close()

# ============================
# Generate plots per query
# ============================
for entry in data:
    qid = entry["query_id"]
    query = entry["query"]
    per_param = entry["per_param_results"]

    # Extract data
    means = [p["mean"] for p in per_param]
    params = [p["params"]["userId"] for p in per_param]

    # ============================
    # 1. LINE PLOT (mean vs param)
    # ============================
    plt.figure(figsize=(10,5))
    plt.plot(params, means, marker='.')
    plt.title(f"Query {qid} — Mean Execution Time per Parameter")
    plt.xlabel("userId")
    plt.ylabel("Time (sec)")
    plt.grid(True, linestyle="--", alpha=0.5)
    save_plot(f"query_{qid}_lineplot.png")

    # ============================
    # 2. BOX PLOT (distribution)
    # ============================
    plt.figure(figsize=(6,6))
    plt.boxplot(means, vert=True, patch_artist=True)
    plt.title(f"Query {qid} — Execution Time Distribution")
    plt.ylabel("Mean time (sec)")
    save_plot(f"query_{qid}_boxplot.png")

    # ============================
    # 3. HISTOGRAM
    # ============================
    plt.figure(figsize=(10,5))
    plt.hist(means, bins=20, color="skyblue", edgecolor="black")
    plt.title(f"Query {qid} — Histogram of Execution Times")
    plt.xlabel("Mean time (sec)")
    plt.ylabel("Frequency")
    save_plot(f"query_{qid}_histogram.png")

    # ============================
    # 4. SCATTER (performance cloud)
    # ============================
    plt.figure(figsize=(10,5))
    plt.scatter(params, means, s=10, alpha=0.6)
    plt.title(f"Query {qid} — Performance Scatter")
    plt.xlabel("userId")
    plt.ylabel("Time (sec)")
    plt.grid(True, linestyle="--", alpha=0.5)
    save_plot(f"query_{qid}_scatter.png")


print("\n All plots generated and saved in the 'plots' folder.")

############################################
# OVERALL SUMMARY PLOTS
############################################

query_ids = [entry["query_id"] for entry in data]
overall_means = [entry["overall_mean_sec"] for entry in data]

# =============== 1. BAR CHART ===============
plt.figure(figsize=(12,6))
plt.bar(query_ids, overall_means, color="steelblue")
plt.title("Average Execution Time Per Query")
plt.xlabel("Query ID")
plt.ylabel("Mean Time (sec)")
plt.grid(axis='y', alpha=0.4)
save_plot("overall_bar_mean_per_query.png")

# =============== 2. BOX PLOT ===============
plt.figure(figsize=(12,6))
box_data = [ [p["mean"] for p in entry["per_param_results"]] for entry in data ]
plt.boxplot(box_data, labels=query_ids, patch_artist=True)
plt.title("Execution Time Distribution Per Query")
plt.xlabel("Query ID")
plt.ylabel("Mean Execution Time (sec)")
save_plot("overall_boxplot_per_query.png")

# =============== 3. LINE PLOT ===============
plt.figure(figsize=(12,6))
plt.plot(query_ids, overall_means, marker='o', linestyle='--')
plt.title("Trend of Average Query Time")
plt.xlabel("Query ID")
plt.ylabel("Mean Time (sec)")
plt.grid(True, linestyle="--", alpha=0.5)
save_plot("overall_line_mean_per_query.png")

# =============== 4. HEATMAP ===============
plt.figure(figsize=(10,6))

# Normalize means for color scale
norm = (np.array(overall_means) - min(overall_means)) / (max(overall_means)-min(overall_means)+1e-9)

plt.imshow([norm], cmap="viridis", aspect="auto")
plt.colorbar(label="Normalized Execution Time")

plt.yticks([])
plt.xticks(range(len(query_ids)), query_ids)
plt.title("Execution Time Heatmap (Normalized)")
save_plot("overall_heatmap_per_query.png")

############################################
# GENERATE LATEX TABLE (overall mean times)
############################################

latex_output = f"{OUTPUT_DIR}\latex_table_queries.tex"

with open(INPUT_JSON, "r") as f:
    data = json.load(f)

rows = []
for entry in data:
    qid = entry["query_id"]
    query = entry["query"].replace("\n", " ")  # flatten for table
    mean_time = entry["overall_mean_sec"]

    rows.append((qid, query, mean_time))

# Build LaTeX table
latex = []
latex.append("\\begin{table}[h!]")
latex.append("\\centering")
latex.append("\\begin{tabular}{|c|p{8cm}|c|}")
latex.append("\\hline")
latex.append("\\textbf{Query ID} & \\textbf{Query (truncated)} & \\textbf{Avg Time (s)}\\\\")
latex.append("\\hline")

for qid, query, mean_time in rows:
    q_short = query[:60] + "..." if len(query) > 60 else query
    latex.append(f"{qid} & {q_short} & {mean_time:.4f}\\\\")
    latex.append("\\hline")

latex.append("\\end{tabular}")
latex.append("\\caption{Average execution time per query on Neo4j AuraDB.}")
latex.append("\\label{tab:query_benchmark}")
latex.append("\\end{table}")

# Save LaTeX
with open(latex_output, "w") as f:
    f.write("\n".join(latex))

print(f"LaTeX table saved to {latex_output}")
