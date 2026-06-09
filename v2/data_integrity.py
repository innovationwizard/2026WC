"""
P0 — Data Integrity & Provenance (the Dirty George guard)
=========================================================
Runs on data load. Implements "doesn't fail silently AND doesn't drop data":
  - counts every dropped / defaulted / coerced row (no silent loss),
  - fails LOUD on critical issues (unmatched WC team, future-dated leakage),
  - flags non-critical anomalies (missing squad value, duplicates),
  - emits a provenance summary (rows in → usable → dropped, with reasons).

Targets the silent-failure points found in the v1 audit (2026-06-07):
  unscored rows dropped silently · defaultdict(1500) for unknown teams ·
  missing squad value rendered as phantom €0M · no leakage guard.
"""
import pandas as pd


class IntegrityReport:
    def __init__(self, rows_in: int):
        self.rows_in = rows_in
        self.dropped = {}   # reason -> count
        self.flags = []     # non-critical anomalies (surfaced, not fatal)
        self.errors = []    # critical -> abort the run

    def drop(self, reason: str, n: int):
        if n:
            self.dropped[reason] = self.dropped.get(reason, 0) + int(n)

    def flag(self, msg: str):
        self.flags.append(msg)

    def error(self, msg: str):
        self.errors.append(msg)

    @property
    def rows_dropped(self) -> int:
        return sum(self.dropped.values())

    def summary(self):
        print("  ── Data integrity (P0) ──")
        print(f"    rows in:      {self.rows_in:,}")
        for reason, n in self.dropped.items():
            print(f"    dropped {n:>6,} — {reason}")
        print(f"    rows usable:  {self.rows_in - self.rows_dropped:,}")
        for f in self.flags:
            print(f"    ⚠ FLAG:  {f}")
        for e in self.errors:
            print(f"    ✗ ERROR: {e}")
        if not self.flags and not self.errors:
            print("    ✓ no anomalies")

    def assert_ok(self):
        if self.errors:
            raise ValueError("P0 data-integrity FAILED — aborting:\n  - " + "\n  - ".join(self.errors))


def audit_load(df: pd.DataFrame, wc_teams, today: pd.Timestamp, squad_values=None) -> IntegrityReport:
    """Validate the loaded match dataframe and return a provenance report.
    Critical issues populate `errors` (caller should `assert_ok()`)."""
    rep = IntegrityReport(len(df))

    # Coerced/unparseable dates (to_datetime may have produced NaT).
    n_nat = int(df['date'].isna().sum())
    if n_nat:
        rep.error(f"{n_nat} rows have unparseable dates (NaT)")

    # Duplicate fixtures (same day, same two teams) — flag, not fatal.
    dups = int(df.duplicated(subset=['date', 'home_team', 'away_team']).sum())
    if dups:
        rep.flag(f"{dups} duplicate (date, home, away) fixtures")

    # Unscored rows get dropped downstream by the team-view — COUNT them (don't drop silently).
    unscored = int(df['home_score'].isna().sum())
    rep.drop('unscored (future fixtures / not yet played)', unscored)

    # LEAKAGE TRIPWIRE: a future-dated row carrying a score would contaminate training
    # and turn a "prediction" into a retrodiction. Hard error.
    future_scored = df[(df['date'] > today) & df['home_score'].notna()]
    if len(future_scored):
        sample = future_scored[['date', 'home_team', 'away_team']].head(3).to_dict('records')
        rep.error(f"LEAKAGE: {len(future_scored)} future-dated row(s) carry scores (e.g. {sample})")

    # WC team coverage: every tournament team must resolve to a real CSV identity,
    # else it silently defaults to Elo 1500 and zero features. Fail loud.
    teams_in_csv = set(df['home_team']) | set(df['away_team'])
    missing = sorted(t for t in wc_teams if t not in teams_in_csv)
    if missing:
        rep.error(f"{len(missing)} WC team(s) not in results.csv (would silently default to Elo 1500): {missing}")

    # Squad-value coverage — non-fatal flag; these render as null/"—", never phantom €0M.
    if squad_values is not None:
        miss_val = sorted(t for t in wc_teams if t not in squad_values)
        if miss_val:
            rep.flag(f"squad value missing for {len(miss_val)} WC team(s) → null (NOT €0M): {miss_val}")

    return rep
