# Coding standards

Preserve original source attribution. Every new or modified Python, JavaScript, HTML or CSS file starts with an appropriate comment recording actual author model, date, purpose and SRP/DRY review. JSON must remain comment-free.

Search and reuse before creating utilities. Record substantive changes in a dated plan under docs/plans before coding and in CHANGELOG afterward. Implement real integrations, never fabricated data or placeholder behavior. Keep game rules in their source modules and shared runtime loading in tools/runtime.py. Keep game IDs opaque on evaluation surfaces.

Verify the behavior actually changed. Reset/action smoke checks are not full-game solvability checks. Record scope and failures honestly. Do not commit credentials, personal data, generated rollouts, environments or caches. Keep large data outside this checkout. Stage only intended paths and inspect diffs before commits.
