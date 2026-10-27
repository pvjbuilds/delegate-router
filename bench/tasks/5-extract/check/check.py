import sys, json, pathlib; f=json.loads(pathlib.Path(sys.argv[1],"facts.json").read_text())
assert f=={"renewal_date":"2027-03-14","budget_lakh":42.5,"migration_vendor":"Kestrel Systems","golive_blocker_owner":"Ritu Sen"}, f
