from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np

# Match timestamps like 09.02.2026 12:23 in the DeployBot block.
DATE_PATTERN = re.compile(r"\b(\d{2}\.\d{2}\.\d{4} \d{2}:\d{2})\b")


def extract_deploy_times(path: Path) -> list[dt.datetime]:
    # Read the whole file once to allow a small lookahead window.
    lines = path.read_text(encoding="utf-8").splitlines()
    times: list[dt.datetime] = []

    for i, line in enumerate(lines):
        if line.strip() != "DeployBot":
            continue

        # Search a short window after the DeployBot marker for a timestamp line.
        # The date can appear on the same line as an em dash or the next line.
        for j in range(i, min(i + 6, len(lines))):
            match = DATE_PATTERN.search(lines[j])
            if match:
                timestamp = dt.datetime.strptime(match.group(1), "%d.%m.%Y %H:%M")
                times.append(timestamp)
                break

    # De-duplicate while preserving order to avoid double-counting.
    seen: set[dt.datetime] = set()
    unique_times: list[dt.datetime] = []
    for timestamp in times:
        if timestamp in seen:
            continue
        seen.add(timestamp)
        unique_times.append(timestamp)

    return unique_times


def add_annotation(
    ax: plt.Axes,
    times: list[dt.datetime],
    y: list[int],
    annotation_date: dt.datetime,
    title: str,
    xytext: tuple[float, float],
) -> None:
    """Add an annotation to a specific deployment in the plot.
    
    Args:
        ax: The matplotlib axes to annotate.
        times: List of deployment timestamps.
        y: List of deployment indices.
        annotation_date: The timestamp of the deployment to annotate.
        title: The annotation text.
        xytext: Offset from the data point in points (x, y).
    """
    if annotation_date in times:
        idx = times.index(annotation_date)
        time = times[idx]
        y_val = y[idx]
        
        ax.annotate(
            title,
            xy=(time, y_val),
            xytext=xytext,
            textcoords="offset points",
            ha="left",
            fontsize=10,
            color="green",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="green", alpha=0.8),
            arrowprops=dict(arrowstyle="->", color="green", lw=1.5),
        )


def main() -> None:
    # Locate history.txt next to this script.
    history_path = Path(__file__).with_name("history.txt")
    times = extract_deploy_times(history_path)
    if not times:
        raise SystemExit("No DeployBot timestamps found in history.txt")

    # Sort for a clean, chronological plot.
    times.sort()
    y = list(range(1, len(times) + 1))

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.scatter(times, y, s=20, alpha=0.85)

    # Fit a linear trend (deploys per day) and plot it.
    x = mdates.date2num(times)
    slope, intercept = np.polyfit(x, y, 1)
    y_fit = slope * x + intercept
    ax.plot(times, y_fit, color="red", linewidth=1.5)
    ax.text(
        0.02,
        0.98,
        f"Linear Fit: {slope:.2f} deploys/day",
        transform=ax.transAxes,
        ha="left",
        va="top",
        color="red",
        fontsize=12,
    )
    ax.set_title("KSA Deployments Over Time")
    ax.set_xlabel("Date")
    ax.set_ylabel("Deployment Index")
    ax.grid(True, alpha=0.3)

    # Example annotation: mark an important deployment
    annotation_date = dt.datetime.strptime("10.12.2025 05:15", "%d.%m.%Y %H:%M")
    add_annotation(ax, times, y, annotation_date, "Ground Clutter", (0, -100))

    annotation_date = dt.datetime.strptime("30.01.2026 02:50", "%d.%m.%Y %H:%M")
    add_annotation(ax, times, y, annotation_date, "Planetary Rings", (-50, -100))

    annotation_date = dt.datetime.strptime("12.11.2025 14:44", "%d.%m.%Y %H:%M")
    add_annotation(ax, times, y, annotation_date, "Kittens", (0, -50))

    # Use concise date labels that adapt to the time span.
    locator = mdates.AutoDateLocator()
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))

    fig.autofmt_xdate()
    fig.tight_layout()
    output_path = Path(__file__).with_name("deploy_times.png")
    fig.savefig(output_path, dpi=200)


if __name__ == "__main__":
    main()
