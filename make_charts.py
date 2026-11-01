"""
Who uses the most electricity and water in the US - and where do data centres fit?

Sources (all public):
  * EIA, Electric Power Annual, Table 2.2 - retail sales by end-use sector, 2025
    https://www.eia.gov/electricity/annual/html/epa_02_02.html
  * EIA, Manufacturing Energy Consumption Survey (MECS) 2022, Table 5.1 -
    electricity (net demand) by manufacturing industry, downloaded XLSX
    https://www.eia.gov/consumption/manufacturing/data/2022/
  * LBNL, United States Data Center Energy Usage Report: 2025 Update (2026) and
    the 2024 edition via DOE press release - US data-centre electricity + water
    https://www.energy.gov/articles/doe-releases-new-report-evaluating-increase-electricity-demand-data-centers
  * USGS, Estimated Use of Water in the United States in 2015 (Circular 1441)
    https://pubs.usgs.gov/publication/cir1441
  * Company sustainability reports (Google 2025, Microsoft FY2025, Meta 2024,
    Equinix 2025, Apple FY2025, Amazon 2025, Alibaba FY2026) via
    https://thefrontierwire.com/data/ai-water-and-energy-use/companies.csv

Outputs: output/fig1_electricity.png, output/fig2_water.png, output/chart_data.csv
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

BASE = Path(__file__).resolve().parent
OUT = BASE / "output"
OUT.mkdir(exist_ok=True)
DATA = BASE / "data"

# ---------------------------------------------------------------- palette ----
C_ELEC = "#1F4E79"      # electricity bars
C_ELEC_LT = "#9DC3E6"   # electricity, secondary
C_DC = "#C0392B"        # data centres (the thing people ask about)
C_DC_LT = "#E8A79F"
C_WATER = "#0B6E4F"     # water bars
C_WATER_LT = "#8AC4AE"
C_GREY = "#4A5568"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "axes.edgecolor": "#B9BEC6",
        "axes.labelcolor": C_GREY,
        "text.color": "#1A202C",
        "xtick.color": C_GREY,
        "ytick.color": "#1A202C",
        "figure.facecolor": "white",
        "axes.facecolor": "white",
    }
)

# ------------------------------------------------------------------ data -----
# EIA Electric Power Annual table 2.2, 2025, terawatt-hours (= billion kWh)
ELEC_SECTOR_2025 = {
    "Residential\n(homes)": 1519.2,
    "Commercial\n(offices, shops,\ndata centres)": 1503.3,
    "Industrial\n(factories,\nrefineries, mining)": 1050.1,
    "Transportation\n(transit, EV\ncharging)": 7.3,
}

# LBNL: US data-centre electricity, terawatt-hours
DC_ELEC = {"2018": 76.0, "2023": 176.0, "2024": 192.0}
DC_ELEC_SHARE_2024 = 4.7  # % of all US electricity
DC_ELEC_2030 = (521, 649, 843)  # low / reference / high, TWh
DC_ELEC_SHARE_2030 = (9.5, 11.8, 15.3)

# USGS 2015 withdrawals, billion gallons per day
WATER_WITHDRAWALS = {
    "Thermoelectric power plants\n(cooling water)": 133.0,
    "Irrigation (crops)": 118.0,
    "Public supply\n(homes & businesses)": 39.0,
    "Self-supplied industrial\n(factories pumping their own)": 14.8,
    "Aquaculture (fish farming)": 7.55,
    "Mining": 4.00,
    "Self-supplied domestic\n(private wells)": 3.48,
    "Livestock": 2.00,
}
WATER_TOTAL_BGAL_D = 322.0

# LBNL: US data-centre water, billion litres per year
DC_WATER = {
    "direct_2023": 66.0,        # on-site cooling & humidification (17.4 bn gallons)
    "direct_2014": 21.2,
    "indirect_2023": 800.0,     # water consumed generating their electricity
    "direct_intensity": 0.375,  # L/kWh, on-site
    "indirect_intensity": 4.52,  # L/kWh, upstream at power plants
}
LITRES_PER_GAL = 3.78541


def company_table() -> pd.DataFrame:
    """Most recent company-reported figures (see module docstring for sources)."""
    rows = [
        # company, period, electricity TWh, withdrawal Mm3, consumption Mm3, note
        ("Google", "2025", 43.6, 55.6, 41.1, ""),
        ("Microsoft", "FY2025\n(Jul-Jun)", 37.0, 13.3, 8.2, ""),
        ("Meta", "2024", 18.4, 5.6, 3.1, ""),
        ("Alibaba", "FY2026", 9.3, None, 17.5, ""),
        ("Equinix", "2025", 8.3, 6.0, 4.6, ""),
        ("Apple", "FY2025", 3.7, None, 6.8, "total water use,\nno split"),
        ("Amazon", "2025", None, 9.4, None, "withdrawal only"),
    ]
    return pd.DataFrame(
        rows,
        columns=["company", "period", "elec_twh", "withdraw_m3", "consume_m3", "note"],
    )


def mecs_industry_table() -> pd.DataFrame:
    """Electricity by manufacturing subsector, MECS 2022 (TWh)."""
    raw = pd.read_csv(DATA / "mecs_electricity_by_industry.csv", dtype={"naics": str})
    raw = raw[raw["naics"].str.len() == 3].copy()
    names = {
        "311": "Food",
        "312": "Beverages & tobacco",
        "313": "Textiles",
        "314": "Textile products",
        "315": "Apparel",
        "316": "Leather products",
        "321": "Wood products",
        "322": "Paper",
        "323": "Printing",
        "324": "Petroleum & coal refining",
        "325": "Chemicals",
        "326": "Plastics & rubber",
        "327": "Nonmetallic minerals\n(cement, glass, lime)",
        "331": "Primary metals\n(steel, aluminium)",
        "332": "Fabricated metal products",
        "333": "Machinery",
        "334": "Computer & electronics\n(semiconductors, servers)",
        "335": "Electrical equipment",
        "336": "Transportation equipment\n(vehicles, aerospace)",
        "337": "Furniture (withheld by EIA)",
        "339": "Miscellaneous",
    }
    raw["industry"] = raw["naics"].map(names).fillna(raw["label"])
    # 'Q' = withheld by EIA for confidentiality -> drop
    raw = raw[
        raw["million_kwh"].apply(lambda v: str(v).replace(".", "").replace("-", "").isdigit())
    ].copy()
    raw["twh"] = raw["million_kwh"].astype(float) / 1000.0
    return raw[["naics", "industry", "twh"]].sort_values("twh", ascending=False)


# --------------------------------------------------------------- helpers -----
def style_axes(ax):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color("#B9BEC6")
    ax.spines["bottom"].set_color("#B9BEC6")
    ax.grid(axis="x", color="#E6E9EF", linewidth=0.9, zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(axis="both", length=0, labelsize=9.5)


def bar_labels(ax, bars, values, fmt="{:.0f}", pad_frac=0.019, color="#1A202C", size=9.5):
    xmax = ax.get_xlim()[1]
    for bar, val in zip(bars, values):
        ax.text(
            bar.get_width() + xmax * pad_frac,
            bar.get_y() + bar.get_height() / 2,
            fmt.format(val),
            va="center",
            ha="left",
            fontsize=size,
            color=color,
            fontweight="bold",
        )


def panel_title(ax, title, sub=None):
    """Bold panel title with an optional grey subtitle underneath it."""
    if sub:
        n = sub.count("\n") + 1
        ax.text(0.0, 1.020, sub, transform=ax.transAxes, fontsize=9.2,
                color=C_GREY, va="bottom", ha="left")
        ax.text(0.0, 1.020 + 0.031 * n + 0.028, title, transform=ax.transAxes,
                fontsize=12.5, fontweight="bold", va="bottom", ha="left")
    else:
        ax.text(0.0, 1.020, title, transform=ax.transAxes, fontsize=12.5,
                fontweight="bold", va="bottom", ha="left")


def source_note(fig, text, y=0.012):
    fig.text(0.008, y, text, fontsize=7.9, color="#5A6472", ha="left", va="bottom")


# =========================================================== FIGURE 1 ========
def figure_electricity():
    sectors = sorted(ELEC_SECTOR_2025.items(), key=lambda kv: -kv[1])
    ind = mecs_industry_table().head(12)
    comp = company_table().sort_values("elec_twh", ascending=False, na_position="last")

    fig, axes = plt.subplots(
        1,
        3,
        figsize=(17.2, 8.2),
        gridspec_kw={"width_ratios": [1.0, 1.28, 1.0], "wspace": 0.42},
    )
    fig.suptitle(
        "US electricity: who uses the most, and where data centres actually sit",
        x=0.008,
        y=0.975,
        ha="left",
        fontsize=19,
        fontweight="bold",
    )
    fig.text(
        0.008,
        0.928,
        "US retail power sales were about 4,080 TWh in 2025. Data centres used about 192 TWh in 2024 "
        "- 4.7% of all US electricity, but more than any single manufacturing industry in the country.",
        ha="left",
        fontsize=11.2,
        color=C_GREY,
    )

    # ---------------------------------------------------------------- (a) ----
    ax = axes[0]
    style_axes(ax)
    ys = list(range(len(sectors)))[::-1]
    labels = [k for k, _ in sectors]
    vals = [v for _, v in sectors]
    bars = ax.barh(ys, vals, height=0.6, color=C_ELEC, zorder=3)
    bar_labels(ax, bars, vals, "{:,.0f}")
    dc_bar = ax.barh(-1.35, DC_ELEC["2024"], height=0.6, color=C_DC, zorder=3)
    bar_labels(ax, dc_bar, [DC_ELEC["2024"]], "{:,.0f}", color=C_DC)
    ax.set_yticks(ys + [-1.35])
    ax.set_yticklabels(labels + ["All US data centres\n(2024 estimate)"], fontsize=9.5)
    for tick in ax.get_yticklabels()[-1:]:
        tick.set_color(C_DC)
        tick.set_fontweight("bold")
    ax.set_xlim(0, 1900)
    ax.set_xlabel("terawatt-hours per year (TWh)")
    ax.axhline(-0.65, color="#D5DAE2", linewidth=1, linestyle=(0, (4, 3)))
    ax.text(
        1900 * 0.985,
        -1.35,
        "4.7% of all\nUS electricity",
        ha="right",
        va="center",
        fontsize=9,
        color=C_DC,
        fontweight="bold",
    )
    panel_title(
        ax,
        "(a) By end-use sector",
        "EIA books data centres inside 'commercial'\n(and some in 'industrial'), not as their own sector",
    )

    # ---------------------------------------------------------------- (b) ----
    ax = axes[1]
    style_axes(ax)
    names = ["All US data centres\n(2024, for scale)"] + list(ind["industry"])
    vals = [DC_ELEC["2024"]] + list(ind["twh"])
    ys = list(range(len(names)))[::-1]
    colors = [C_DC] + [C_ELEC] * len(ind)
    bars = ax.barh(ys, vals, height=0.66, color=colors, zorder=3)
    bar_labels(ax, bars, vals, "{:,.0f}")
    ax.set_yticks(ys)
    ax.set_yticklabels(names, fontsize=9.2)
    for tick in ax.get_yticklabels()[:1]:
        tick.set_color(C_DC)
        tick.set_fontweight("bold")
    ax.set_xlim(0, 235)
    ax.set_xlabel("terawatt-hours per year (TWh)")
    panel_title(
        ax,
        "(b) By manufacturing industry",
        "Chemicals, steel and food are the heaviest industrial users;\none data-centre fleet out-consumes any one of them",
    )

    # ---------------------------------------------------------------- (c) ----
    ax = axes[2]
    style_axes(ax)
    comp_plot = comp.dropna(subset=["elec_twh"])
    names = list(comp_plot["company"])
    vals = list(comp_plot["elec_twh"])
    ys = list(range(len(names) + 1))[::-1][: len(names)]
    bars = ax.barh(ys, vals, height=0.62, color=C_ELEC_LT, zorder=3)
    bar_labels(ax, bars, vals, "{:.1f}")
    ax.set_yticks(list(range(len(names) + 1))[::-1])
    ax.set_yticklabels(names + ["Amazon"], fontsize=9.5)
    ax.text(
        2,
        0.42,
        "no electricity total disclosed",
        va="center",
        ha="left",
        fontsize=8.8,
        color=C_GREY,
        style="italic",
    )
    ax.set_xlim(0, 215)
    ax.set_xlabel("terawatt-hours per year (TWh)")
    ax.axvline(DC_ELEC["2024"], color=C_DC, linewidth=1.4, linestyle=(0, (4, 3)), zorder=4)
    ax.text(
        DC_ELEC["2024"] - 5,
        2.0,
        "192 TWh = every\nUS data centre, 2024",
        ha="right",
        va="center",
        fontsize=8.6,
        color=C_DC,
        fontweight="bold",
    )
    panel_title(
        ax,
        "(c) The companies, self-reported",
        "Company totals are global (data centres + offices),\nso they overlap with the US 192 TWh, not added to it",
    )

    source_note(
        fig,
        "Sources: EIA Electric Power Annual table 2.2 (2025 sales) | EIA MECS 2022 table 5.1, electricity used by manufacturing "
        "industry (net demand for electricity; the furniture subsector is withheld by EIA)\n"
        "LBNL United States Data Center Energy Usage Report 2025 Update via DOE (192 TWh = 4.7% of US electricity in 2024) | "
        "company sustainability reports: Google 2025, Microsoft FY2025, Meta 2024, Alibaba FY2026, Equinix 2025, Apple FY2025; "
        "Amazon publishes no electricity total.",
    )
    fig.subplots_adjust(left=0.105, right=0.985, top=0.79, bottom=0.115)
    out = OUT / "fig1_electricity.png"
    fig.savefig(out, dpi=200)
    plt.close(fig)
    return out


# =========================================================== FIGURE 2 ========
def figure_water():
    cats = sorted(WATER_WITHDRAWALS.items(), key=lambda kv: -kv[1])
    dc_direct_bgal_d = DC_WATER["direct_2023"] / LITRES_PER_GAL / 365.0
    dc_total_bgal_d = (DC_WATER["direct_2023"] + DC_WATER["indirect_2023"]) / LITRES_PER_GAL / 365.0

    fig, axes = plt.subplots(
        1,
        3,
        figsize=(17.2, 8.0),
        gridspec_kw={"width_ratios": [1.1, 1.0, 1.0], "wspace": 0.40},
    )
    fig.suptitle(
        "US water: power plants and farms dominate, data centres are a rounding error",
        x=0.008,
        y=0.975,
        ha="left",
        fontsize=19,
        fontweight="bold",
    )
    fig.text(
        0.008,
        0.928,
        "The US withdraws about 322 billion gallons a day. All of the country's data centres use roughly "
        "0.05 Bgal/d directly - about one part in 7,000.",
        ha="left",
        fontsize=11.2,
        color=C_GREY,
    )

    # ---------------------------------------------------------------- (a) ----
    ax = axes[0]
    style_axes(ax)
    labels = [k for k, _ in cats]
    vals = [v for _, v in cats]
    ys = list(range(len(vals)))[::-1]
    bars = ax.barh(ys, vals, height=0.62, color=C_WATER, zorder=3)
    bar_labels(ax, bars, vals, "{:,.1f}", size=9.2)
    ax.barh(-1.35, dc_direct_bgal_d, height=0.62, color=C_DC, zorder=3)
    ax.plot([dc_direct_bgal_d], [-1.35], marker="D", ms=6, color=C_DC, zorder=4)
    ax.text(
        26,
        -1.35,
        f"All US data centres:\n{dc_direct_bgal_d:.2f} Bgal/d direct,\n"
        f"{dc_total_bgal_d:.2f} Bgal/d including\nthe power-plant water",
        va="center",
        ha="left",
        fontsize=9,
        color=C_DC,
        fontweight="bold",
        linespacing=1.35,
    )
    ax.set_yticks(ys + [-1.35])
    ax.set_yticklabels(labels + ["All US data centres\n(2024, for scale)"], fontsize=9.2)
    for tick in ax.get_yticklabels()[-1:]:
        tick.set_color(C_DC)
        tick.set_fontweight("bold")
    ax.axhline(-0.7, color="#D5DAE2", linewidth=1, linestyle=(0, (4, 3)))
    ax.set_ylim(-2.15, 7.6)
    ax.set_xlim(0, 168)
    ax.set_xlabel("billion gallons per day withdrawn (2015)")
    panel_title(
        ax,
        "(a) By category of use",
        "USGS 2015 national estimate; 90% of it is\npower plants plus irrigation",
    )

    # ---------------------------------------------------------------- (b) ----
    ax = axes[1]
    style_axes(ax)
    rows = [
        ("Indirect: power plants\nthat serve them (2023)",
         DC_WATER["indirect_2023"], C_WATER_LT),
        ("Direct: on-site cooling\n& humidification (2023)",
         DC_WATER["direct_2023"], C_WATER),
        ("Direct, 2014", DC_WATER["direct_2014"], "#C9DCD4"),
    ]
    ys = list(range(len(rows)))[::-1]
    bars = ax.barh(ys, [r[1] for r in rows], height=0.55,
                   color=[r[2] for r in rows], zorder=3)
    bar_labels(ax, bars, [r[1] for r in rows], "{:,.0f}", size=9.5)
    ax.set_yticks(ys)
    ax.set_yticklabels([r[0] for r in rows], fontsize=9.2)
    ax.set_xlim(0, 1010)
    ax.set_xlabel("billion litres per year")
    ax.text(
        0.98,
        0.03,
        "Direct = 17.4 bn gallons a year. That is 3x\n2014, but still 0.015% of US withdrawals.\n\n"
        "Indirect is about 12x bigger: the power\nstations behind the servers.\n\n"
        "For scale, thermoelectric plants withdraw\n133 bn gallons per DAY.",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=8.9,
        color=C_GREY,
        bbox=dict(boxstyle="round,pad=0.55", facecolor="#F5F8F7", edgecolor="#CBD8D3"),
    )
    panel_title(
        ax,
        "(b) Inside the data-centre footprint",
        "Most data-centre water is not at the data centre -\nit is upstream at the power station",
    )

    # ---------------------------------------------------------------- (c) ----
    ax = axes[2]
    style_axes(ax)
    order = ["Google", "Alibaba", "Microsoft", "Amazon", "Apple", "Equinix", "Meta"]
    comp = company_table().set_index("company").loc[order].reset_index()
    ys = list(range(len(comp)))[::-1]
    h = 0.36
    wd = comp["withdraw_m3"].tolist()
    cs = comp["consume_m3"].tolist()
    ax.barh([y + h / 2 for y in ys], [v if v else 0 for v in wd], height=h,
            color=C_WATER_LT, zorder=3, label="withdrawal (water taken in)")
    ax.barh([y - h / 2 for y in ys], [v if v else 0 for v in cs], height=h,
            color=C_WATER, zorder=3, label="consumption (evaporated / not returned)")
    for y, w, c, note in zip(ys, wd, cs, comp["note"]):
        if note:
            w0 = 0.0 if pd.isna(w) else float(w)
            c0 = 0.0 if pd.isna(c) else float(c)
            ax.text(max(w0, c0) + 1.4, y,
                    note.replace("\n", " "), va="center", ha="left",
                    fontsize=8.3, color=C_GREY, style="italic")
    ax.set_yticks(ys)
    ax.set_yticklabels(
        [f"{c}  ({p.replace(chr(10), ' ')})" for c, p in
         zip(comp["company"], comp["period"])],
        fontsize=9.2,
    )
    ax.set_xlim(0, 100)
    ax.set_xlabel("billion litres per year (= million m3 per year)")
    ax.legend(frameon=False, fontsize=8.6, loc="upper right", bbox_to_anchor=(1.0, 1.0))
    panel_title(
        ax,
        "(c) The companies, self-reported",
        "Google is the biggest reported water user; Amazon and\nApple each publish only one of the two numbers",
    )

    source_note(
        fig,
        "Sources: USGS Circular 1441, Estimated Use of Water in the United States in 2015 (withdrawals in Bgal/d; 'industrial' = "
        "self-supplied factories only) | LBNL United States Data Center Energy Usage Report: direct water consumption\n"
        "66 bn L (17.4 bn gal) in 2023 vs 21 bn L in 2014, indirect 800 bn L; 0.375 L/kWh on site vs 4.52 L/kWh upstream | "
        "company sustainability reports: Google 2025, Microsoft FY2025, Meta 2024, Equinix 2025, Alibaba FY2026,\n"
        "Apple FY2025 (total water use, no withdrawal/consumption split), Amazon 2025 (withdrawal only). Reporting boundaries "
        "differ - this is not a like-for-like league table.",
    )
    fig.subplots_adjust(left=0.135, right=0.985, top=0.79, bottom=0.15)
    out = OUT / "fig2_water.png"
    fig.savefig(out, dpi=200)
    plt.close(fig)
    return out


def export_data():
    """Everything plotted, in one tidy CSV so the numbers can be checked."""
    rows = []
    for k, v in ELEC_SECTOR_2025.items():
        rows.append(dict(chart="electricity", group="end-use sector",
                         label=k.replace("\n", " "), value=v, unit="TWh", year=2025,
                         source="EIA Electric Power Annual table 2.2"))
    for _, r in mecs_industry_table().iterrows():
        rows.append(dict(chart="electricity", group="manufacturing industry",
                         label=r["industry"].replace("\n", " "), value=round(r["twh"], 1),
                         unit="TWh", year=2022, source="EIA MECS 2022 table 5.1"))
    for year, v in DC_ELEC.items():
        rows.append(dict(chart="electricity", group="data centres",
                         label="All US data centres", value=v, unit="TWh",
                         year=int(year), source="LBNL 2024 report / 2025 Update"))
    comp = company_table()
    for _, r in comp.iterrows():
        year = r["period"].replace("\n", " ")
        if pd.notna(r["elec_twh"]):
            rows.append(dict(chart="electricity", group="company (self-reported)",
                             label=r["company"], value=r["elec_twh"], unit="TWh",
                             year=year, source="company sustainability report"))
        if pd.notna(r["withdraw_m3"]):
            rows.append(dict(chart="water", group="company (self-reported)",
                             label=r["company"], value=r["withdraw_m3"],
                             unit="million m3 withdrawn", year=year,
                             source="company sustainability report"))
        if pd.notna(r["consume_m3"]):
            rows.append(dict(chart="water", group="company (self-reported)",
                             label=r["company"], value=r["consume_m3"],
                             unit="million m3 consumed", year=year,
                             source="company sustainability report"))
    for k, v in WATER_WITHDRAWALS.items():
        rows.append(dict(chart="water", group="category of use",
                         label=k.replace("\n", " "), value=v,
                         unit="Bgal/day withdrawn", year=2015,
                         source="USGS Circular 1441"))
    for label, key in (("direct consumption", "direct_2023"),
                       ("indirect consumption", "indirect_2023"),
                       ("direct consumption", "direct_2014")):
        rows.append(dict(chart="water", group="data centres", label=label,
                         value=DC_WATER[key], unit="billion litres/year",
                         year=int(key[-4:]), source="LBNL 2024 report"))
    out = OUT / "chart_data.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    return out


if __name__ == "__main__":
    for path in (figure_electricity(), figure_water(), export_data()):
        print("wrote", path)
