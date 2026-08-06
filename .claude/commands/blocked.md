Run `poetry run python scripts/scrape_to_prod.py` from the project root (no arguments — this covers every source currently known to be IP-blocked on Railway, see `IP_BLOCKED_SOURCES` in that file).

This scrapes those sources from this machine's network (not Railway's, which they 403) and writes the results straight into the production database via the Railway CLI's public DB connection — `railway` must be logged in and linked to this project first.

After it finishes, report a short summary: for each source, how many listings were found/new/updated/delisted (parse from the SQL echo output or check `scrape_runs`/`listings` directly if the console output is too noisy to read). If a source errors, show the actual error rather than just "it failed" — check `railway logs --service classic-car-insights` if the reason isn't obvious from stdout.
