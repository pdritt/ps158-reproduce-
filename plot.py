"""Reproduce Growing wealth gap from downloaded SCF household records."""
from pathlib import Path
import csv
import io
import zipfile
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MultipleLocator

ROOT = Path(__file__).resolve().parent
YEARS = list(range(1989, 2026, 3))

def weighted_median(records):
    ordered = sorted(records)
    total = sum(weight for _, weight in ordered)
    if not ordered or total <= 0:
        raise ValueError('No positively weighted observations')
    running = 0
    for value, weight in ordered:
        running += weight
        if running >= total / 2:
            return value
    raise AssertionError('Weighted median not found')

def calculate():
    result = []
    for year in YEARS:
        path = ROOT / 'data' / f'scf{year}.csv'
        if not path.exists():
            raise FileNotFoundError(f'{path}: run python get_data.py first')
        groups = {'BA or more': [], 'HS or less': []}
        with path.open(newline='', encoding='utf-8-sig') as stream:
            for raw in csv.DictReader(stream):
                row = {k.upper(): v for k, v in raw.items()}
                if float(row['KIDS']) <= 0:
                    continue
                education = int(float(row['EDCL']))
                group = 'BA or more' if education == 4 else 'HS or less' if education in (1, 2) else None
                if group:
                    value, weight = float(row['NETWORTH']), float(row['WGT']) / 5
                    if weight > 0:
                        groups[group].append((value, weight))
        result.append({'year': year, **{g: weighted_median(v) for g, v in groups.items()}})
    return result

def main():
    rows = calculate()
    with (ROOT / 'medians.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=['year', 'BA or more', 'HS or less'])
        writer.writeheader()
        writer.writerows(rows)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 15})
    fig, ax = plt.subplots(figsize=(15, 12))
    fig.subplots_adjust(left=.15, right=.93, top=.82, bottom=.19)
    fig.text(.025, .965, 'Growing wealth gap', fontsize=28, fontweight='bold', va='top')
    fig.text(.025, .915, 'Median net worth by parental education, in constant (2025) dollars, 1989–2025', fontsize=19, va='top')
    ax.axvspan(2013, 2026, color='#f0f0f0', zorder=0)
    ax.text(2013.4, 685000, 'Added since Putnam (2015)\n2016–2025', va='top', fontsize=14, color='#666666')
    for group, color in [('BA or more', '#202020'), ('HS or less', '#999999')]:
        values = [r[group] for r in rows]
        ax.plot(YEARS, values, color=color, lw=4, solid_capstyle='round', label=group)
        ax.annotate(f'${values[-1]/1000:.0f}K', (2025, values[-1]), xytext=(12, 0),
                    textcoords='offset points', va='center', color='#444444', fontsize=16)
    ax.set_xlim(1988, 2026)
    ceiling = max(700000, ((max(r['BA or more'] for r in rows) // 100000) + 1) * 100000)
    ax.set_ylim(0, ceiling)
    ax.set_xticks(YEARS)
    ax.yaxis.set_major_locator(MultipleLocator(100000))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'${x:,.0f}'))
    ax.set_ylabel('Median family net worth', fontsize=19, fontweight='bold')
    ax.grid(axis='y', color='#dddddd', linewidth=1.2)
    ax.set_axisbelow(True)
    for side in ['top', 'right']:
        ax.spines[side].set_visible(False)
    for side in ['bottom', 'left']:
        ax.spines[side].set_color('#666666')
    ax.tick_params(colors='#444444')
    ax.legend(loc='upper left', bbox_to_anchor=(.02, .98), fancybox=False,
              framealpha=1, edgecolor='#bbbbbb', fontsize=20)
    fig.text(.025, .09, 'Families with a child of the reference person living at home. Education of the SCF reference person.\n'
             'Inflation-adjusted with the R-CPI-U-RS (September of each survey year), as in the Federal Reserve’s SCF tables.',
             fontsize=12, color='#666666', va='top')
    fig.text(.025, .035, 'Source: Survey of Consumer Finances, Federal Reserve Board. https://www.federalreserve.gov/econres/scfindex.htm',
             fontsize=12, color='#666666', va='top')
    fig.savefig(ROOT / 'figure.png', dpi=150, facecolor='white')
    for row in rows:
        print(f"{row['year']}: BA or more ${row['BA or more']:,.0f}; HS or less ${row['HS or less']:,.0f}")

if __name__ == '__main__':
    main()
