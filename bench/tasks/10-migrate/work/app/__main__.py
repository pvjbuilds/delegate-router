from . import api, billing, boot, cache, db, hooks, jobs, report


boot.start()
db.open_db()
cache.miss("user:7")
jobs.run()
hooks.run()
api.handle()
report.build()
billing.charge()
