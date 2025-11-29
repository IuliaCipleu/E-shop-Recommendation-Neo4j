import pandas as pd
import time
import os
import json
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ========= CONFIG =========
URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USER")
PASSWORD = os.getenv("NEO4J_PASSWORD")

if not URI or not USERNAME or not PASSWORD:
    raise ValueError("Missing Neo4j credentials in .env file")

QUERY_FILE = "queries/neo4j_query_saved_cypher_2025-11-22.csv"
OUTPUT_JSON = "benchmark_results_medium.json"

RUNS_PER_QUERY = 1        # number of hot-cache runs
# Fetch real user_ids first
driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

with driver.session() as session:
    real_user_ids = session.run("MATCH (u:User) RETURN u.user_id AS id").value()

# Select 50 distinct random ones
import random
USER_IDS = random.sample(real_user_ids, k=50)

REGIONS = ["EU", "US", "ASIA", "AFRICA", "LATAM"]
# ==========================

# Load only queries with id > 3
df = pd.read_csv(QUERY_FILE).dropna(subset=["query"])
queries = df[df["id"] > 3]["query"].tolist()
# ----- MOVE LAST 2 FIRST -----
if len(queries) >= 2:
    last_two = queries[-2:]      # last 2 queries
    rest = queries[:-2]          # all except last 2
    queries = last_two + rest    # new order

results = []

def run_one(session, query, params):
    """Run a single parametric Cypher and return execution time."""
    start = time.perf_counter()
    session.run(query, params).consume()
    end = time.perf_counter()
    return end - start


with driver.session() as session:
    for qid, query in enumerate(queries, start=1):
        driver.close()
        driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

        print(f"\n=== Query {qid} ===")

        per_param_times = []

        for user_id in USER_IDS:
            params = {
                "userId": user_id,
                "region": REGIONS[user_id % len(REGIONS)]
            }

            # --------- COLD RUN (first time) ---------
            cold_time = run_one(session, query, params)

            # --------- HOT RUNS ---------
            hot_times = []
            for _ in range(RUNS_PER_QUERY):
                hot_times.append(run_one(session, query, params))

            per_param_times.append({
                "params": params,
                "cold_time": cold_time,
                "hot_times": hot_times,
                "hot_mean": sum(hot_times) / len(hot_times)
            })

        # Compute aggregated metrics for this query
        cold_avg = sum([x["cold_time"] for x in per_param_times]) / len(per_param_times)
        hot_avg = sum([x["hot_mean"] for x in per_param_times]) / len(per_param_times)

        results.append({
            "query_id": qid,
            "query": query,
            "total_params": len(USER_IDS),
            "cold_avg_sec": cold_avg,
            "hot_avg_sec": hot_avg,
            "per_param_results": per_param_times
        })

driver.close()

# Save results to JSON
with open(OUTPUT_JSON, "w") as f:
    json.dump(results, f, indent=4)

print(f"\nBenchmark complete! Saved results to {OUTPUT_JSON}")
