# %%
import polyptich as pp
import polyptich.www as www


overview = www.OverviewGrid(
    pp.paths.get_www() / "dataset_overview",
    title="Dataset Overview",
    description="A dynamic overview page with server-side filtering, sorting, and paged loading.",
    filters=[
        {"key": "modality", "label": "Modality", "options": ["RNA", "ATAC"]},
        {"key": "cells", "label": "Cells", "type": "range"},
    ],
    sorts=[
        {"key": "title", "label": "Title"},
        {"key": "cells", "label": "Cells"},
    ],
    page_size=12,
)

for index in range(60):
    modality = "RNA" if index % 2 == 0 else "ATAC"
    overview.add_item(
        title=f"Dataset {index + 1}",
        href=f"../datasets/dataset_{index + 1}/",
        description=f"{modality} dataset with lazy overview loading.",
        media=f"https://placehold.co/640x360?text=Dataset+{index + 1}",
        badges=[modality, "QC"],
        values={
            "modality": modality,
            "cells": 1000 + index * 125,
        },
    )
# %%
