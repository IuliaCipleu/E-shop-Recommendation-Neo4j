import pandas as pd
import time
import os
import json
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ========= CONFIG (from .env) =========
URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USER")
PASSWORD = os.getenv("NEO4J_PASSWORD")

if not URI or not USERNAME or not PASSWORD:
    raise ValueError("Missing Neo4j credentials in .env file")


QUERY_FILE = "queries/neo4j_query_saved_cypher_2025-11-22.csv"   # CSV with parametric queries
OUTPUT_JSON = "benchmark_results_small.json"

RUNS_PER_QUERY = 5                   # Run each query N times
USER_IDS = list(range(1, 501))      # parameters to test (e.g. user_id)
REGIONS = ["EU", "US", "ASIA", "AFRICA", "LATAM"]    # optional param set
# ==========================


driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

# Load queries
queries = pd.read_csv(QUERY_FILE)["query"].dropna().tolist()
df = pd.read_csv(QUERY_FILE).dropna(subset=["query"])
queries = df[df["id"] > 3]["query"].tolist()


results = []

def run_one(session, query, params):
    """Run a single parametric Cypher and return execution time."""
    start = time.perf_counter()
    session.run(query, params).consume()
    end = time.perf_counter()
    return end - start


with driver.session() as session:

    for qid, query in enumerate(queries, start=1):
        print(f" Query {qid}: {query}")

        per_param_times = []

        # Loop over all parameter combinations
        for user_id in USER_IDS:
            # Example parameters – use whatever your queries need
            params = {
                "userId": user_id,
                "region": REGIONS[user_id % len(REGIONS)]
            }

            # Run each query RUNS_PER_QUERY times
            times = []
            for _ in range(RUNS_PER_QUERY):
                t = run_one(session, query, params)
                times.append(t)

            # Store per-parameter timing
            per_param_times.append({
                "params": params,
                "runs": times,
                "mean": sum(times) / len(times)
            })

        # Compute aggregated metrics for this query
        all_means = [x["mean"] for x in per_param_times]
        overall_mean = sum(all_means) / len(all_means)

        results.append({
            "query_id": qid,
            "query": query,
            "runs_per_query": RUNS_PER_QUERY,
            "parameter_count": len(USER_IDS),
            "overall_mean_sec": overall_mean,
            "per_param_results": per_param_times
        })

driver.close()

# Save results to JSON
with open(OUTPUT_JSON, "w") as f:
    json.dump(results, f, indent=4)

print(f"\nBenchmark complete! Saved results to {OUTPUT_JSON}")
