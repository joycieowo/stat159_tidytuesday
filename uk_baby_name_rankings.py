"""
TidyTuesday 2026-06-16: UK Baby Names
Question: How does the ranking of most popular names compare between the
three datasets (England & Wales, Northern Ireland, Scotland)?
 
What this script does
---------------------
1. Loads the three CSVs from the TidyTuesday GitHub repo.
2. Tables the top-N names per region, by sex, for the latest year all three cover.
3. Measures agreement between regions: top-N overlap (Jaccard) and Spearman
   rank correlation of names that appear in both regions.
4. Tracks top-N overlap over time for each pair of regions.
5. Saves charts (PNG) and summary tables (CSV).
 
Requirements: pip install pandas matplotlib scipy
Usage:        python uk_baby_name_rankings.py
"""
 
from itertools import combinations
from pathlib import Path
 
import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import spearmanr
 
BASE = "https://raw.githubusercontent.com/rfordatascience/tidytuesday/main/data/2026/2026-06-16/"
FILES = {
    "England & Wales": "england_wales_names.csv",
    "Northern Ireland": "ni_names.csv",
    "Scotland": "scotland_names.csv",
}
TOP_N = 10          # size of the "top names" list for tables / overlap
CORR_TOP = 100      # names ranked within this in at least one region used for correlation
OUT = Path("output")
OUT.mkdir(exist_ok=True)
 
 
# --------------------------------------------------------------------------
# Load + tidy
# --------------------------------------------------------------------------
def load_all() -> pd.DataFrame:
    frames = []
    for region, fname in FILES.items():
        df = pd.read_csv(BASE + fname)
        df["Region"] = region
        frames.append(df)
    data = pd.concat(frames, ignore_index=True)
 
    # Harmonise: NI/Scotland strip accents, E&W may not. Normalise names so the
    # same name matches across regions.
    data["Name"] = (
        data["Name"]
        .astype(str)
        .str.strip()
        .str.normalize("NFKD")
        .str.encode("ascii", "ignore")
        .str.decode("ascii")
        .str.upper()
    )
    data["Sex"] = data["Sex"].str.title()
    data = data.dropna(subset=["Rank"])
    data["Rank"] = data["Rank"].astype(float)
 
    # Re-aggregating after accent stripping could create duplicates; keep best rank.
    data = (
        data.sort_values("Rank")
        .drop_duplicates(["Region", "Year", "Sex", "Name"], keep="first")
    )
    return data
 
 
# --------------------------------------------------------------------------
# Analysis helpers
# --------------------------------------------------------------------------
def top_names(data: pd.DataFrame, year: int, n: int = TOP_N) -> pd.DataFrame:
    """Wide table: rows = rank position, columns = region, for each sex."""
    rows = []
    for (sex, region), g in data[data["Year"] == year].groupby(["Sex", "Region"]):
        g = g.nsmallest(n, "Rank")  # ties can yield slightly more than n
        for _, r in g.iterrows():
            rows.append((sex, region, int(r["Rank"]), r["Name"].title(), int(r["Number"])))
    out = pd.DataFrame(rows, columns=["Sex", "Region", "Rank", "Name", "Number"])
    return out
 
 
def jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if (a | b) else float("nan")
 
 
def pairwise_agreement(data: pd.DataFrame, year: int) -> pd.DataFrame:
    """Top-N overlap and Spearman correlation for every pair of regions."""
    rows = []
    d = data[data["Year"] == year]
    for sex in ["Girl", "Boy"]:
        ds = d[d["Sex"] == sex]
        for r1, r2 in combinations(FILES, 2):
            a = ds[ds["Region"] == r1].set_index("Name")["Rank"]
            b = ds[ds["Region"] == r2].set_index("Name")["Rank"]
 
            top_a = set(a[a <= TOP_N].index)
            top_b = set(b[b <= TOP_N].index)
 
            # Names in the top CORR_TOP of either region and present in both lists
            cand = set(a[a <= CORR_TOP].index) | set(b[b <= CORR_TOP].index)
            both = sorted(cand & set(a.index) & set(b.index))
            rho = spearmanr(a[both], b[both]).correlation if len(both) > 2 else float("nan")
 
            rows.append(
                {
                    "Year": year,
                    "Sex": sex,
                    "Pair": f"{r1} vs {r2}",
                    f"Shared in top {TOP_N}": len(top_a & top_b),
                    f"Jaccard top {TOP_N}": round(jaccard(top_a, top_b), 2),
                    "Names compared": len(both),
                    "Spearman rho": round(rho, 3),
                }
            )
    return pd.DataFrame(rows)
 
 
def overlap_over_time(data: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for sex in ["Girl", "Boy"]:
        ds = data[data["Sex"] == sex]
        years = sorted(set.intersection(*[set(ds[ds["Region"] == r]["Year"]) for r in FILES]))
        for y in years:
            dy = ds[ds["Year"] == y]
            tops = {r: set(dy[(dy["Region"] == r) & (dy["Rank"] <= TOP_N)]["Name"]) for r in FILES}
            for r1, r2 in combinations(FILES, 2):
                rows.append(
                    {
                        "Year": y,
                        "Sex": sex,
                        "Pair": f"{r1} vs {r2}",
                        "Jaccard": jaccard(tops[r1], tops[r2]),
                    }
                )
    return pd.DataFrame(rows)
 
 
# --------------------------------------------------------------------------
# Plots
# --------------------------------------------------------------------------
def plot_overlap_over_time(ot: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), sharey=True)
    for ax, sex in zip(axes, ["Girl", "Boy"]):
        for pair, g in ot[ot["Sex"] == sex].groupby("Pair"):
            ax.plot(g["Year"], g["Jaccard"], marker="o", ms=3, label=pair)
        ax.set_title(f"{sex}s: overlap of top {TOP_N} names")
        ax.set_xlabel("Year")
        ax.set_ylim(0, 1)
        ax.grid(alpha=0.3)
    axes[0].set_ylabel("Jaccard similarity (1 = identical top list)")
    axes[1].legend(fontsize=8, loc="lower right")
    fig.suptitle("How similar are the most popular names across UK nations?")
    fig.tight_layout()
    fig.savefig(OUT / "top_name_overlap_over_time.png", dpi=150)
    plt.close(fig)
 
 
def plot_rank_scatter(data: pd.DataFrame, year: int) -> None:
    pairs = list(combinations(FILES, 2))
    fig, axes = plt.subplots(2, 3, figsize=(15, 9))
    d = data[data["Year"] == year]
    for i, sex in enumerate(["Girl", "Boy"]):
        ds = d[d["Sex"] == sex]
        for j, (r1, r2) in enumerate(pairs):
            ax = axes[i, j]
            a = ds[ds["Region"] == r1].set_index("Name")["Rank"]
            b = ds[ds["Region"] == r2].set_index("Name")["Rank"]
            both = a.index.intersection(b.index)
            both = [n for n in both if a[n] <= CORR_TOP or b[n] <= CORR_TOP]
            ax.scatter(a[both], b[both], s=14, alpha=0.6)
            lim = CORR_TOP * 3
            ax.plot([1, lim], [1, lim], "k--", lw=0.8)
            ax.set_xscale("log")
            ax.set_yscale("log")
            ax.set_xlim(0.8, lim)
            ax.set_ylim(0.8, lim)
            ax.set_xlabel(f"Rank in {r1}")
            ax.set_ylabel(f"Rank in {r2}")
            ax.set_title(f"{sex}s, {year}")
            # label names with the biggest disagreement
            diff = (a[both] - b[both]).abs().sort_values(ascending=False).head(4).index
            for n in diff:
                ax.annotate(n.title(), (a[n], b[n]), fontsize=7, xytext=(3, 3),
                            textcoords="offset points")
            ax.grid(alpha=0.3, which="both")
    fig.suptitle(f"Rank vs rank across nations ({year}); dashed line = same rank")
    fig.tight_layout()
    fig.savefig(OUT / "rank_vs_rank_scatter.png", dpi=150)
    plt.close(fig)
 
 
def plot_top_table(tops: pd.DataFrame, year: int) -> None:
    """Side-by-side tables of the top names per region."""
    fig, axes = plt.subplots(2, 1, figsize=(11, 9))
    for ax, sex in zip(axes, ["Girl", "Boy"]):
        t = tops[(tops["Sex"] == sex) & (tops["Rank"] <= TOP_N)]
        wide = t.pivot_table(index="Rank", columns="Region", values="Name", aggfunc=lambda s: " / ".join(s))
        wide = wide[list(FILES)]
        ax.axis("off")
        ax.set_title(f"Top {TOP_N} {sex.lower()}s' names, {year}", fontweight="bold")
        tbl = ax.table(cellText=wide.values, rowLabels=wide.index, colLabels=wide.columns,
                       loc="center", cellLoc="center")
        tbl.auto_set_font_size(False)
        tbl.set_fontsize(10)
        tbl.scale(1, 1.4)
    fig.tight_layout()
    fig.savefig(OUT / "top_names_table.png", dpi=150)
    plt.close(fig)
 
 
# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main() -> None:
    data = load_all()
 
    # Latest year covered by all three datasets (E&W stops at 2024 in the cleaning script)
    year = min(data[data["Region"] == r]["Year"].max() for r in FILES)
    print(f"Comparing regions for {year} (latest year in all three datasets)\n")
 
    tops = top_names(data, year)
    tops.to_csv(OUT / f"top_{TOP_N}_names_{year}.csv", index=False)
    for sex in ["Girl", "Boy"]:
        wide = (
            tops[(tops["Sex"] == sex) & (tops["Rank"] <= TOP_N)]
            .pivot_table(index="Rank", columns="Region", values="Name", aggfunc=lambda s: " / ".join(s))
            [list(FILES)]
        )
        print(f"Top {TOP_N} {sex.lower()}s' names, {year}")
        print(wide.to_string(), "\n")
 
    agree = pairwise_agreement(data, year)
    agree.to_csv(OUT / f"pairwise_agreement_{year}.csv", index=False)
    print("Pairwise agreement")
    print(agree.to_string(index=False), "\n")
 
    ot = overlap_over_time(data)
    ot.to_csv(OUT / "overlap_over_time.csv", index=False)
 
    plot_top_table(tops, year)
    plot_overlap_over_time(ot)
    plot_rank_scatter(data, year)
    print(f"Saved tables and charts to ./{OUT}/")
 
 
if __name__ == "__main__":
    main()