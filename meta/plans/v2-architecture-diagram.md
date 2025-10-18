# Hoopstat Haus v2 Architecture Diagram (Stateless JSON-First)

This diagram reflects ADR-027: initial public access via small, precomputed JSON artifacts served directly from S3. MCP is optional later.

```mermaid
graph TB
    subgraph "Ingestion (Bronze)"
        BRONZE_APP["Bronze Ingestion App\nPython + Docker\n• Pull nba-api data\n• Write raw JSON/Parquet"]
    end

    subgraph "Processing (Silver)"
        SILVER_JOBS["Silver Processing\n• Cleaning\n• Schema enforcement\n• Deduplication"]
    end

    subgraph "Analytics (Gold)"
        GOLD_JOBS["Gold Analytics\n• Aggregations\n• Advanced metrics\n• Business models"]
        SERVED["Gold-served (Projection)\nS3 JSON Artifacts\n• player_daily\n• team_daily\n• top_lists\n• index/latest.json"]
    end

    subgraph "Public Access"
        S3_PUBLIC["S3 Public Read + CORS\n(optional CDN)"]
        OPTIONAL_MCP["Optional Later: MCP via API GW + Lambda\nreads served/ or analytics storage"]
    end

    BRONZE_APP --> SILVER_JOBS --> GOLD_JOBS --> SERVED --> S3_PUBLIC
    SERVED -.-> OPTIONAL_MCP
```
