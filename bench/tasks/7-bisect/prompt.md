This folder is a git repo. On `main`, `python3 test_total.py` fails; at the first commit it
passed. Find the first commit where the test fails because it computes a wrong result (the
assertion fails). Some commits can't run the test at all (the program crashes before it gets
to the assertion): those are untestable, not bad. Write the full 40-character hash of that
first bad commit to `FIRST_BAD.txt` in this folder and don't commit it. When you finish, the
repo must be on `main`, with no bisect in progress and nothing changed except the new
`FIRST_BAD.txt`.
