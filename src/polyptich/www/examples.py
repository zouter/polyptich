from pathlib import Path
import argparse

from . import components
from .overview import OverviewGrid
from .page import Page


def write_examples(path=None, overwrite=True):
    """Write built-in polyptich.www examples into a www folder.

    When *path* is omitted, examples are written to
    ``polyptich.paths.get_www() / "polyptich_examples"``.
    """
    if path is None:
        from polyptich import paths

        path = paths.get_www() / "polyptich_examples"
    root = Path(path)
    root.mkdir(parents=True, exist_ok=True)

    write_component_library(root / "component_library", overwrite=overwrite)
    write_overview_grid(root / "dataset_overview", overwrite=overwrite)
    return root


def write_component_library(path, overwrite=True):
    page = Page(path, title="polyptich.www Component Library", overwrite=overwrite)
    intro = page.section("HTML-first Components")
    intro.add_html(
        components.callout(
            "Reports are generated as HTML. Use add_html() for arbitrary markup, "
            "or use component helpers for common layouts.",
            title="Composable HTML",
        )
    )
    intro.add_html(
        components.grid(
            components.card("Plain cards can hold arbitrary HTML.", title="Card"),
            components.card(
                components.image(
                    "https://placehold.co/640x360?text=Preview",
                    alt="Preview image",
                    caption="Images can be remote URLs or report-relative assets.",
                ),
                title="Image Card",
            ),
            components.card(
                "The whole card links to another report, file, or external page.",
                title="Linked Card",
                href="../dataset_overview/",
            ),
            columns="3",
        )
    )

    manuscript = page.section("Manuscript-style Blocks")
    manuscript.add_html(
        components.grid(
            components.thumbnail_card(
                "Dataset Overview",
                href="../dataset_overview/",
                media="https://placehold.co/640x360?text=Overview",
                image_label="Dynamic endpoint",
                description="A linked thumbnail card inspired by manuscript overview pages.",
                badges=["Overview", "Lazy", "Filterable"],
            ),
            components.panel(
                components.key_value_table(
                    {
                        "Report type": "HTML-first",
                        "Dynamic endpoints": "Supported",
                        "Tables": "Server-backed",
                    }
                ),
                title="Summary",
            ),
            columns="2",
        )
    )
    manuscript.add_html(
        components.grid(
            components.progress_list(
                [
                    {"label": "HTML", "percent": 70, "value": "70%"},
                    {"label": "JSON", "percent": 20, "value": "20%"},
                    {"label": "Assets", "percent": 10, "value": "10%"},
                ],
                title="Composition",
                collapsible=True,
            ),
            components.matrix_table(
                values=[[1.0, 0.72, 0.28], [0.72, 1.0, 0.41], [0.28, 0.41, 1.0]],
                row_labels=["A", "B", "C"],
                col_labels=["A", "B", "C"],
                title="Matrix Table",
            ),
            columns="2",
        )
    )
    page.write()
    return page


def write_overview_grid(path, overwrite=True):
    overview = OverviewGrid(
        path,
        title="polyptich.www OverviewGrid",
        description="A dynamic overview endpoint with server-side filtering, sorting, and lazy loading.",
        filters=[
            {"key": "modality", "label": "Modality", "options": ["RNA", "ATAC"]},
            {"key": "cells", "label": "Cells", "type": "range"},
        ],
        sorts=[
            {"key": "title", "label": "Title"},
            {"key": "cells", "label": "Cells"},
        ],
        page_size=12,
        overwrite=overwrite,
    )

    for index in range(36):
        modality = "RNA" if index % 2 == 0 else "ATAC"
        overview.add_item(
            title=f"Dataset {index + 1}",
            href=f"../datasets/dataset_{index + 1}/",
            description=f"{modality} dataset with lazy overview loading.",
            media=f"https://placehold.co/640x360?text=Dataset+{index + 1}",
            badges=[modality, "QC"],
            values={"modality": modality, "cells": 1000 + index * 125},
        )
    return overview


def main(argv=None):
    parser = argparse.ArgumentParser(description="Write built-in polyptich.www examples.")
    parser.add_argument("path", nargs="?", help="Output folder. Defaults to www/polyptich_examples in the current project.")
    parser.add_argument("--no-overwrite", action="store_true", help="Do not remove existing example report folders.")
    args = parser.parse_args(argv)
    root = write_examples(args.path, overwrite=not args.no_overwrite)
    print(root)
