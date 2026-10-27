In `app/`, change `app.logger.log(level, msg)` to `log(msg, level="info")`: message first,
level second and optional, same parameter names, same validation. Update every use of it in
`app/` so that `python3 -m app` prints exactly what it prints now and
`python3 -m doctest app/logger.py` passes. `app.audit.log` is a different function: leave it
and its callers as they are. Don't add or delete files.
