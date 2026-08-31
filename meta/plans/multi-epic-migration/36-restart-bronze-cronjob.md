# feat: Restart bronze cronjob and validate data pipeline

## What do you want to build?

Enable the scheduled bronze ingestion workflow in hoopstat-data and validate that the full data pipeline (Bronze → Silver → Gold → Health) runs successfully end-to-end in the new repository.

## Acceptance Criteria

- [ ] The `daily-ingestion.yml` workflow's `schedule` trigger is uncommented/enabled in hoopstat-data
- [ ] A manual trigger of the bronze ingestion workflow succeeds
- [ ] Bronze data is written to the correct S3 bucket/prefix
- [ ] Silver processing is triggered (manually or automatically) and succeeds
- [ ] Gold analytics processing runs and produces served artifacts
- [ ] The health aggregator runs and produces `pipeline_health.json`
- [ ] The db-compiler runs and produces DuckDB/SQLite artifacts
- [ ] All artifacts are accessible via the gold layer CloudFront endpoint
- [ ] The frontend dashboard displays fresh data from the new pipeline
- [ ] The health dashboard shows green/healthy status
- [ ] The scheduled cron trigger fires at the expected time (verify within 24 hours)

## Implementation Notes (Optional)

**Pipeline startup sequence:**
The pipeline stages have dependencies. Start them in order:
1. **Bronze ingestion** — Enable cron, trigger manually to get initial data
2. **Silver processing** — Trigger manually after bronze completes
3. **Gold analytics** — Trigger manually after silver completes
4. **Health aggregator** — Trigger manually after gold completes
5. **DB compiler** — Trigger manually after gold completes

After the manual run validates everything, enable the scheduled triggers:
- Bronze: daily cron (same schedule as hoopstat-haus)
- Silver: triggered after bronze (via workflow_run or schedule)
- Gold: triggered after silver
- Health aggregator: triggered after gold
- DB compiler: triggered after gold (may be less frequent)

**Monitoring:**
After enabling the cron:
- Monitor CloudWatch logs for errors in the first few runs
- Check S3 bucket sizes to verify data is being written
- Check the frontend dashboard to verify data freshness
- Check the health dashboard for any pipeline issues

**Data seeding:**
If the new S3 buckets are empty, the first pipeline run may need special handling:
- Bronze ingestion should work normally (it fetches from the NBA API)
- Silver processing needs bronze data to exist
- Gold analytics needs silver data to exist

A full pipeline run from scratch may take longer than a normal incremental run. Plan accordingly.

**Fallback:**
If the pipeline fails in the new repo:
- The old hoopstat-haus pipeline is still running (until Epic 8)
- The frontend can still read from the old gold layer data
- Debug and fix in hoopstat-data without time pressure
