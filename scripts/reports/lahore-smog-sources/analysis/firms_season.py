# Season windows shared by fetch_firms.py and firms_analysis.py.
# 2002-2025: MODIS standard product, 1 Oct-30 Nov. 2026: near-real-time (NRT) data, 1 Oct to CUTOFF_2026 inclusive.
# The analysis enforces the cutoff even if cached input files contain later observations.
import datetime as dt

CUTOFF_2026 = dt.date(2026, 11, 1)


def season_start(year):
    return dt.date(year, 10, 1)


def season_end(year):
    return CUTOFF_2026 if year == CUTOFF_2026.year else dt.date(year, 11, 30)


def in_season(d):
    return season_start(d.year) <= d <= season_end(d.year)


def partial_label(year):
    return f"to {CUTOFF_2026.day} {CUTOFF_2026:%b} (NRT)" if year == CUTOFF_2026.year else ""
