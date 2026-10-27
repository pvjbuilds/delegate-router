In this folder, create `semver_range.py` with `satisfies(version: str, range_: str) -> bool`.
Standard library only. Do not write tests. Raise ValueError for an invalid version or range.

Versions: `MAJOR.MINOR.PATCH`, optionally `-PRERELEASE`. Each number is `0` or has no leading
zero. PRERELEASE is dot-separated identifiers of `[0-9A-Za-z-]`, none empty. No leading `v`.

Order (SemVer 2.0): compare MAJOR, MINOR, PATCH numerically. A version with a prerelease is
lower than the same version without one. Prerelease identifiers compare left to right: both
numeric → numerically; both non-numeric → ASCII order; numeric is lower than non-numeric; if
all shared identifiers are equal, the shorter list is lower.

Ranges: one or more sets joined by `||` (spaces around it optional); a version satisfies the
range if it satisfies any set. A set is one or more comparators separated by whitespace; a
version satisfies a set if it satisfies every comparator in it (and the prerelease rule below).
Leading and trailing whitespace is ignored.

A comparator is an optional operator (`=`, `>`, `>=`, `<`, `<=`, `^`, `~`) directly followed by
a partial version: `X`, `X.Y` or `X.Y.Z`, where any part may be `x`, `X` or `*`; once a part is
a wildcard, every later part must be a wildcard or absent. A prerelease is allowed only on a
full `X.Y.Z` with no wildcard. `*` alone (or with `=`) matches every version. Let a missing or
wildcard part be "unset":
- `=` or no operator: `1.2.3` is exactly 1.2.3; `1.2` or `1.2.x` is >=1.2.0 <1.3.0; `1` is
  >=1.0.0 <2.0.0.
- `>=`: unset parts become 0. `<`: unset parts become 0 (`<1.2` is <1.2.0).
- `>`: `>1.2.3` as written; `>1.2` is >=1.3.0; `>1` is >=2.0.0.
- `<=`: `<=1.2.3` as written; `<=1.2` is <1.3.0; `<=1` is <2.0.0.
- `~`: `~1.2.3` is >=1.2.3 <1.3.0; `~1.2` is >=1.2.0 <1.3.0; `~1` is >=1.0.0 <2.0.0.
- `^`: >= the version with unset parts as 0, and < the next bump of the left-most part that is
  set and non-zero; if every set part is zero, bump the last set part. So `^1.2.3` is
  >=1.2.3 <2.0.0, `^0.2.3` is >=0.2.3 <0.3.0, `^0.0.3` is >=0.0.3 <0.0.4, `^1.2` is
  >=1.2.0 <2.0.0, `^0.0` is >=0.0.0 <0.1.0, `^0.x` is >=0.0.0 <1.0.0.
Upper bounds carry no prerelease (`<2.0.0` means below 2.0.0 itself).

Prerelease rule: a version that has a prerelease satisfies a set only if, in addition, some
comparator in that set was written as a full `X.Y.Z-PRERELEASE` with the same MAJOR, MINOR and
PATCH as the version.
