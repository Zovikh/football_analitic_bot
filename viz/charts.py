from __future__ import annotations

import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def xg_chart(team: str, values: list[float]) -> bytes:
    fig, ax = plt.subplots(figsize=(8, 4.2), dpi=140)
    xs = list(range(1, len(values) + 1))
    ax.plot(xs, values, marker="o", linewidth=2, color="#1b7f4e")
    ax.fill_between(xs, values, alpha=0.12, color="#1b7f4e")
    ax.set_title(f"xG {team} за последние матчи")
    ax.set_xlabel("Матч")
    ax.set_ylabel("xG")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def seo_chart(query: str, series: list[tuple[str, int]]) -> bytes:
    fig, ax = plt.subplots(figsize=(8, 4.2), dpi=140)
    days = [d[5:] for d, _ in series]
    vals = [v for _, v in series]
    ax.bar(days, vals, color="#1d4e89")
    ax.set_title(f"Интерес: {query}")
    ax.set_ylabel("Индекс")
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return buf.read()
