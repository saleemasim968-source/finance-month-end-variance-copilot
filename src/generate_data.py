"""Generate the synthetic month-end cost data for three fictional wafer fabs (WBS 2.1).

Writes the raw site files, wafer volumes and FX rates described in document 04 section 3,
including the planted business events and data issues of document 04 section 5.
Each site file is deliberately different in layout, language, unit and currency.

All data is synthetic. The cost structure is illustrative, not benchmarked.
The output is deterministic: the same seed always produces the same files.

Run: python src/generate_data.py
"""

import csv
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEED = 20261010

PERIODS = [f"2026-{month:02d}" for month in range(1, 10)]
MONTH_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep"]

GROUP_AREAS = ["Lithography", "Etch", "Diffusion", "Facilities"]
GROUP_ACCOUNTS = ["Personnel", "Depreciation", "Energy", "Materials", "Maintenance", "External services"]

# Share of each account that moves with wafer volume (document 04 section 3.2).
VARIABLE_SHARE = {
    "Personnel": 0.0,
    "Depreciation": 0.0,
    "Energy": 0.3,
    "Materials": 0.9,
    "Maintenance": 0.2,
    "External services": 0.0,
}

# Monthly plan cost in EUR for a site of scale 1.0, by group area and group account.
BASE_PLAN_EUR = {
    "Lithography": {"Personnel": 900_000, "Depreciation": 1_800_000, "Energy": 140_000,
                    "Materials": 700_000, "Maintenance": 300_000, "External services": 120_000},
    "Etch": {"Personnel": 650_000, "Depreciation": 1_100_000, "Energy": 110_000,
             "Materials": 550_000, "Maintenance": 250_000, "External services": 90_000},
    "Diffusion": {"Personnel": 600_000, "Depreciation": 900_000, "Energy": 120_000,
                  "Materials": 450_000, "Maintenance": 200_000, "External services": 80_000},
    "Facilities": {"Personnel": 400_000, "Depreciation": 500_000, "Energy": 600_000,
                   "Materials": 50_000, "Maintenance": 150_000, "External services": 200_000},
}

# Local structures per site: (local code, local name) per group account, local cost centre per area.
SITES = {
    "FAB_NORTH": {
        "scale": 1.0,
        "plan_wafers": 20_000,
        "accounts": {
            "Personnel": ("400000", "Personnel expenses"),
            "Depreciation": ("410000", "Depreciation"),
            "Energy": ("420000", "Energy and utilities"),
            "Materials": ("430000", "Production materials"),
            "Maintenance": ("440000", "Maintenance and repair"),
            "External services": ("450000", "External services"),
        },
        "cost_centres": {"Lithography": "CC1010", "Etch": "CC1020", "Diffusion": "CC1030", "Facilities": "CC1900"},
    },
    "FAB_ALPS": {
        "scale": 0.8,
        "plan_wafers": 15_000,
        "accounts": {
            "Personnel": ("6000", "Personalaufwand"),
            "Depreciation": ("6100", "Abschreibungen"),
            "Energy": ("6200", "Energie (Strom, Wärme)"),
            "Materials": ("6300", "Fertigungsmaterial"),
            "Maintenance": ("6400", "Instandhaltung"),
            "External services": ("6500", "Fremdleistungen"),
        },
        "cost_centres": {"Lithography": "KST-210", "Etch": "KST-220", "Diffusion": "KST-230", "Facilities": "KST-900"},
    },
    "FAB_ASIA": {
        "scale": 0.9,
        "plan_wafers": 25_000,
        "accounts": {
            "Personnel": ("P100", "Staff costs"),
            "Depreciation": ("D200", "Depreciation - equipment"),
            "Energy": ("U300", "Utilities"),
            "Materials": ("M400", "Direct materials"),
            "Maintenance": ("R500", "Repairs and maintenance"),
            "External services": ("S600", "Contract services"),
        },
        "cost_centres": {"Lithography": "MY-LIT", "Etch": "MY-ETC", "Diffusion": "MY-DIF", "Facilities": "MY-FAC"},
    },
}

# Random noise bands. Both stay well inside the 5 % materiality thresholds,
# so only the planted events below can produce a flag.
PLAN_NOISE = 0.03     # month-to-month variation of plan cost and plan wafers
SPEND_NOISE = 0.02    # actual cost versus flexed budget
VOLUME_NOISE = 0.025  # actual wafers versus plan wafers

# Planted business events (document 04 section 5).
TOOL_DOWN = {"site": "FAB_NORTH", "period": "2026-05", "area": "Lithography",
             "account": "Maintenance", "extra_eur": 480_000}
ENERGY_SPIKE = {"site": "FAB_ALPS", "periods": {"2026-07", "2026-08"}, "account": "Energy", "uplift": 0.22}
WEAK_LOADING = {"site": "FAB_ASIA", "periods": {"2026-07", "2026-08", "2026-09"}, "shortfall": 0.14}

# Planted data issues (document 04 section 5).
MISSING_ACTUAL = {"site": "FAB_ALPS", "period": "2026-09", "area": "Etch", "account": "External services"}
DUPLICATE_LINE = {"site": "FAB_ASIA", "period": "2026-06", "area": "Etch", "account": "Materials"}

FX_BASE_MYR_PER_EUR = 5.00


def generate_fx_rates(rng):
    return {period: round(FX_BASE_MYR_PER_EUR + rng.uniform(-0.10, 0.10), 4) for period in PERIODS}


def generate_volumes(rng):
    """Plan and actual wafers per site and period."""
    volumes = {}
    for site, spec in SITES.items():
        for period in PERIODS:
            plan = round(spec["plan_wafers"] * (1 + rng.uniform(-PLAN_NOISE, PLAN_NOISE)))
            deviation = rng.uniform(-VOLUME_NOISE, VOLUME_NOISE)
            if site == WEAK_LOADING["site"] and period in WEAK_LOADING["periods"]:
                deviation = -WEAK_LOADING["shortfall"] + deviation / 2.5
            volumes[site, period] = (plan, round(plan * (1 + deviation)))
    return volumes


def generate_cost_lines(rng, volumes):
    """One line per site, period, area and account with plan and actual in EUR."""
    lines = []
    for site, spec in SITES.items():
        for period in PERIODS:
            plan_wafers, actual_wafers = volumes[site, period]
            volume_ratio = actual_wafers / plan_wafers
            for area in GROUP_AREAS:
                for account in GROUP_ACCOUNTS:
                    plan = BASE_PLAN_EUR[area][account] * spec["scale"] * (1 + rng.uniform(-PLAN_NOISE, PLAN_NOISE))
                    plan = round(plan, 2)
                    share = VARIABLE_SHARE[account]
                    flexed = plan * ((1 - share) + share * volume_ratio)
                    noise = rng.uniform(-SPEND_NOISE, SPEND_NOISE)
                    actual = flexed * (1 + noise)

                    if (site, period, area, account) == (TOOL_DOWN["site"], TOOL_DOWN["period"],
                                                         TOOL_DOWN["area"], TOOL_DOWN["account"]):
                        actual += TOOL_DOWN["extra_eur"]
                    if (site == ENERGY_SPIKE["site"] and period in ENERGY_SPIKE["periods"]
                            and account == ENERGY_SPIKE["account"]):
                        actual = flexed * (1 + ENERGY_SPIKE["uplift"] + noise)

                    missing = (site, period, area, account) == (MISSING_ACTUAL["site"], MISSING_ACTUAL["period"],
                                                                MISSING_ACTUAL["area"], MISSING_ACTUAL["account"])
                    lines.append({
                        "site": site, "period": period, "area": area, "account": account,
                        "plan_eur": plan, "actual_eur": None if missing else round(actual, 2),
                    })
    return lines


def _local(line):
    spec = SITES[line["site"]]
    code, name = spec["accounts"][line["account"]]
    return spec["cost_centres"][line["area"]], code, name


def _writer(handle, delimiter=","):
    return csv.writer(handle, delimiter=delimiter, lineterminator="\n")


def write_fab_north(path, lines):
    """English layout, comma-separated, EUR, period as 2026-01."""
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = _writer(handle)
        writer.writerow(["period", "cost_center", "account_code", "account_name", "plan", "actual"])
        for line in lines:
            cost_centre, code, name = _local(line)
            writer.writerow([line["period"], cost_centre, code, name,
                             f"{line['plan_eur']:.2f}", f"{line['actual_eur']:.2f}"])


def _teur(amount_eur):
    return f"{amount_eur / 1000:.3f}".replace(".", ",")


def write_fab_alps(path, lines):
    """German layout, semicolon-separated, decimal comma, thousands of EUR, period as 01.2026."""
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = _writer(handle, delimiter=";")
        writer.writerow(["Periode", "Kostenstelle", "Kontonummer", "Kontobezeichnung", "Plan_TEUR", "Ist_TEUR"])
        for line in lines:
            cost_centre, code, name = _local(line)
            year, month = line["period"].split("-")
            actual = "" if line["actual_eur"] is None else _teur(line["actual_eur"])
            writer.writerow([f"{month}.{year}", cost_centre, code, name, _teur(line["plan_eur"]), actual])


def write_fab_asia(path, lines, fx_rates):
    """GL export, comma-separated, MYR, period as Jan-26, plan (BUD) and actual (ACT) as separate rows."""
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = _writer(handle)
        writer.writerow(["Period", "CC", "GL Account", "GL Description", "Version", "Amount"])
        for line in lines:
            cost_centre, code, name = _local(line)
            rate = fx_rates[line["period"]]
            month = int(line["period"][5:])
            period_label = f"{MONTH_ABBR[month - 1]}-26"
            budget_row = [period_label, cost_centre, code, name, "BUD", f"{line['plan_eur'] * rate:.2f}"]
            actual_row = [period_label, cost_centre, code, name, "ACT", f"{line['actual_eur'] * rate:.2f}"]
            writer.writerow(budget_row)
            writer.writerow(actual_row)
            if (line["period"], line["area"], line["account"]) == (DUPLICATE_LINE["period"], DUPLICATE_LINE["area"],
                                                                   DUPLICATE_LINE["account"]):
                writer.writerow(actual_row)  # planted data issue: line exported twice


def write_volumes(path, volumes):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = _writer(handle)
        writer.writerow(["site", "period", "plan_wafers", "actual_wafers"])
        for (site, period), (plan, actual) in volumes.items():
            writer.writerow([site, period, plan, actual])


def write_fx_rates(path, fx_rates):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = _writer(handle)
        writer.writerow(["period", "myr_per_eur"])
        for period, rate in fx_rates.items():
            writer.writerow([period, f"{rate:.4f}"])


def main(root=ROOT):
    """Write all generated files below root and return their paths."""
    rng = random.Random(SEED)
    raw_dir = Path(root) / "data" / "raw"
    reference_dir = Path(root) / "data" / "reference"
    raw_dir.mkdir(parents=True, exist_ok=True)
    reference_dir.mkdir(parents=True, exist_ok=True)

    fx_rates = generate_fx_rates(rng)
    volumes = generate_volumes(rng)
    lines = generate_cost_lines(rng, volumes)

    def site_lines(site):
        return [line for line in lines if line["site"] == site]

    paths = {
        "fab_north": raw_dir / "fab_north_costs.csv",
        "fab_alps": raw_dir / "fab_alps_kosten.csv",
        "fab_asia": raw_dir / "fab_asia_gl_export.csv",
        "volumes": raw_dir / "wafer_volumes.csv",
        "fx_rates": reference_dir / "fx_rates.csv",
    }
    write_fab_north(paths["fab_north"], site_lines("FAB_NORTH"))
    write_fab_alps(paths["fab_alps"], site_lines("FAB_ALPS"))
    write_fab_asia(paths["fab_asia"], site_lines("FAB_ASIA"), fx_rates)
    write_volumes(paths["volumes"], volumes)
    write_fx_rates(paths["fx_rates"], fx_rates)
    return paths


if __name__ == "__main__":
    for name, path in main().items():
        with path.open(encoding="utf-8") as handle:
            rows = sum(1 for _ in handle) - 1
        print(f"{name:<10} {rows:>4} rows  {path.relative_to(ROOT)}")
