# Project Structure — E-SHOP-RECOMMENDATION-NOSQL

This project implements a **Neo4j-based NoSQL recommendation system** for an online shopping site.  
The repository is organized to clearly separate data generation, datasets, queries, and backups.
---

## Key Components

### `create_data.py`
- Generates **synthetic datasets** (`small`, `medium`, `large`) using the Faker library.
- Creates CSVs compatible with Neo4j’s `LOAD CSV` import mechanism.
- Includes configurable scaling parameters and realistic category/product profiles.

### `neo4j_import/`
- Stores CSV data for import into Neo4j.
- Each dataset variant supports performance testing on different scales:
  - `small` → development & debugging.
  - `medium` → intermediate-scale tests.
  - `large` → stress tests for Azure/Aura deployment.

### `queries/`
- Contains saved Cypher queries used for recommendation experiments.
- Useful for reproducibility and benchmarking query performance.

### `dumps/`
- Contains Neo4j `.dump` files for quick database restoration.
- Each dump corresponds to a full database snapshot at a given time.

---

## Typical Workflow

1. **Generate data:**
   ```bash
   python create_data.py
