# Pipelines

Fabric Notebook-based orchestration for Skill-Lync warehouse.

## `daily_refresh.py`

**Schedule:** 05:00 IST daily.

**Rebuilds in parallel:**
- `dim.User` (from `sql/12_dim_user.sql`)
- `fact.Final_Table` (from `sql/08_fact_final_table.sql`)
- `fact.CallDetail` (from `sql/10_fact_call_detail.sql`)

**Flow:**
1. **Freshness gate** — aborts if `dbo.ActivityBase` max `created_at` is more than 1 day behind today IST. Prevents rebuilding on stale source data.
2. **Parallel rebuild** — 3 jobs via `ThreadPoolExecutor`.
3. **Post-check** — verifies `fact.Final_Table` has fresh data + sane row count.

Any failure raises, which the Fabric Pipeline catches.

### Fabric setup

1. **Upload `daily_refresh.py` to your Fabric workspace** as a notebook (File → Import).
2. **Set env vars in the notebook's default lakehouse / workspace settings:**
   - `POWERBI_CLIENT_ID` — service principal app ID
   - `POWERBI_CLIENT_SECRET` — service principal secret (store in Azure Key Vault and reference)
   - `REPO_SQL_DIR` — path where `sql/*.sql` files are accessible from the notebook (OneLake Files or lakehouse attachment)
3. **Sync the git repo** to the Fabric workspace (Workspace settings → Git integration) so `sql/*.sql` files are readable at `REPO_SQL_DIR`.
4. **Wrap the notebook in a Data Pipeline:**
   - Activity 1: Notebook activity → `daily_refresh`
   - Activity 2: Office 365 Outlook "Send email" on Activity 1's failure output
     - To: `<your-email>`
     - Subject: `Skill-Lync Daily Refresh FAILED — @{utcnow()}`
     - Body: include `@{activity('daily_refresh').output.error.message}`
5. **Schedule the Data Pipeline** at 05:00 IST daily.

### What does NOT get refreshed here

- `sql/00–07` — prep VIEWs (auto-recompute on query, no daily rebuild needed).
- `sql/11_dim_calendar.sql` — static dates, one-time.
- Semantic model / DAX measures — no refresh needed; DirectLake reads the rebuilt tables.
