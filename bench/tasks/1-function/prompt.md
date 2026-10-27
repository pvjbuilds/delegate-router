In this folder, create `duration.py` with a function `parse_duration(text: str) -> int` that returns seconds.
Input is like "1h30m", "45s", "2h", "1h5m10s", "90m"; units h, m, s in that order, each optional but at least one.
Raise ValueError for anything else ("", "5x", "1m1h", "h"). Standard library only. Do not write tests.
