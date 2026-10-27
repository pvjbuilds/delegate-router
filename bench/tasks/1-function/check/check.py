import sys; sys.path.insert(0, sys.argv[1]); from duration import parse_duration as p
assert p("1h30m")==5400 and p("45s")==45 and p("2h")==7200 and p("1h5m10s")==3910 and p("90m")==5400
for bad in ["", "5x", "1m1h", "h", "1h1h"]:
    try: p(bad)
    except ValueError: continue
    raise AssertionError(bad)
