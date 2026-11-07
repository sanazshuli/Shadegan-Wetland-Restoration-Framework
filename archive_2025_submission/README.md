# Archived workflow of the original submission (2025)

`Codes_project_Shadegan_archived_2025.ipynb` is the Google Colab notebook that produced the restoration-priority exports and maps of the original submission. It is kept unchanged as the object of the audit.

The other archived files are in the repository root: `scripts/`, `notebooks/`, `data/reported_restoration_confusion_matrix.csv` and the PNG maps. They also belong to the original submission.

Known problems (details in the main README and in the revised manuscript):
- wrong WorldCover codes in the priority rules (10, 70, 100 instead of 80, 90);
- NDVI/NDWI clause written in the inverted direction;
- strategy classifier trained on rule-derived labels, with no samples for "General Restoration";
- an RF–SVM comparison was reported but never carried out.

Use `revision_2026/` for any new work.
