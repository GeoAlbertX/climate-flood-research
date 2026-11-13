"""Shared figure style. Every figure is stamped with its data source."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import MaxNLocator  # noqa: E402

BLUE, ORANGE, GREY, RED, GREEN, PURPLE = "#2563eb", "#ea580c", "#6b7280", "#dc2626", "#16a34a", "#7c3aed"

plt.rcParams.update({
    "figure.dpi": 110, "savefig.dpi": 150, "font.size": 10, "axes.titlesize": 12,
    "axes.titleweight": "bold", "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25, "legend.frameon": False,
})


def finish(fig, path, source, demo=False):
    note = f"Data: {source}"
    if demo:
        note = "SYNTHETIC DEMO DATA — NOT REAL — for code testing only"
        fig.text(0.5, 0.5, "DEMO DATA", fontsize=60, color="red", alpha=0.12,
                 ha="center", va="center", rotation=25)
    for ax in fig.axes:                                   # whole-number year ticks
        lo, hi = ax.get_xlim()
        if 1900 < lo < 2100 and ax.get_xscale() == "linear":
            ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    fig.text(0.01, 0.005, note, fontsize=7, color=GREY, ha="left", va="bottom")
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
