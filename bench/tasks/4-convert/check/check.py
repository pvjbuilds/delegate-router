import sys, json, pathlib; got=json.loads(pathlib.Path(sys.argv[1],"people.json").read_text())
assert got==[{"name":"Asha Rao","city":"Pune","joined":"2026-01-04","score":88},{"name":"Mehta, Dev","city":"Mumbai","joined":"2025-11-30","score":None},{"name":"Li Wei","city":"Remote","joined":"2026-03-15","score":91}], got
