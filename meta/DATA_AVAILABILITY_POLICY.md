# Data Availability Policy

This document defines the data sharing policy for the Hoopstat Haus project, clarifying what data is publicly available and what remains private.

## Upstream Attribution

The Hoopstat Haus project sources its basketball data from the `stats.nba.com` service, accessed through the community-maintained `nba_api` Python library. This data represents publicly available basketball statistics and information that the NBA makes accessible through their official statistics endpoints.

Our use of this data source is documented in [ADR-013](adr/ADR-013-nba_api_data.md), which outlines the decision-making process and considerations for selecting this data provider. We acknowledge and appreciate the NBA's role in making comprehensive basketball statistics publicly accessible.

## Non-Commercial Use

The Hoopstat Haus project and all associated data are intended for **educational and non-commercial purposes only**. This project serves as:

- A learning platform for basketball analytics and data engineering techniques
- An open-source resource for academic research and educational exploration
- A demonstration of modern data infrastructure and machine learning applications in sports analytics

Any commercial use of the project's code, data, or derived insights should be pursued with appropriate consideration of underlying data licensing terms and the NBA's usage policies.

## Platform vs Instance Distinction

**The Platform** refers to the open-source codebase and infrastructure of Hoopstat Haus available on GitHub. This includes all code, documentation, and architectural designs that enable anyone to deploy their own basketball analytics environment.

**The Instance** refers to the specific deployment and service running at `hoopstat.haus`. This instance contains processed data, trained models, and curated datasets that provide value to users of the hosted service.

## Publicly Available Data

Our driving principle for data sharing is simple: **"If I got it for free, I'll share it for free."**

The data we make publicly available represents a **derived dataset** that we create through processing, cleaning, and enhancing basketball statistics. While the underlying source information consists of **public domain facts** about basketball games and player performance (scores, statistics, game outcomes, etc.), our contribution lies in the curation, processing, and analytical value we add to this foundational data.

All derived datasets that we create from publicly available, free sources will be made available to the community under appropriate open licenses. This commitment reflects our belief in contributing back to the basketball analytics ecosystem while respecting the factual nature of the underlying sports data.

### Aggregated Data Availability

Aggregated data from our "Gold" layer will be made publicly available through a future API. This will include processed, cleaned, and enhanced basketball statistics that provide value while respecting our data sources.

<!-- AI_UPDATE_MARKER: Please update this language once we formalize our medallion architecture. Currently using temporary placeholder language for bronze/silver/gold data layers. -->

### Licensing

All publicly available data will be released under the **Creative Commons Attribution-ShareAlike 4.0 International License (CC BY-SA 4.0)**. This license allows for:

- **Sharing** — copying and redistributing the data in any medium or format
- **Adapting** — remixing, transforming, and building upon the data

Under the following terms:
- **Attribution** — appropriate credit must be given to Hoopstat Haus
- **ShareAlike** — any derivative works must be distributed under the same license

## Private Assets

Certain assets and data layers remain private to maintain the unique value proposition of the `hoopstat.haus` instance and to respect computational investments and licensing constraints.

### Examples of Private Assets

- **Trained model weights** — Machine learning models that have been trained on our infrastructure
- **Sentiment analysis datasets** — Processed social media and commentary data with privacy considerations
- **Raw and intermediate data layers** — Bronze and Silver layer data that may contain unprocessed or partially processed information
- **Third-party licensed data** — Any data obtained from commercial APIs or sources under "do not redistribute" licensing terms

### Justification for Privacy

These assets remain private due to:

1. **Computational cost** — Significant resources were invested in training and processing these assets
2. **Unique value preservation** — Maintaining competitive advantages for the hosted `hoopstat.haus` service
3. **Licensing compliance** — Respecting the terms of third-party data providers
4. **Privacy considerations** — Protecting individual privacy in unprocessed social media and commentary data

## Future Considerations

This policy may evolve as the project grows and as we establish partnerships with data providers. Any changes will be communicated transparently and with appropriate notice to the community.

---

*Last updated: 2025*  
*For questions about this policy, please open an issue in the GitHub repository.*