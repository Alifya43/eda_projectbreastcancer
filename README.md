# Patient Insights Dashboard

This project contains a Streamlit dashboard based on the fields and analysis in `eda_project.ipynb`.

> The notebook analyzes breast cancer patient records, not e-commerce transactions. It expects `/content/Breast_Cancer.csv`; that CSV was not included in this project folder.

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

Upload the notebook's CSV from the dashboard sidebar, or place `Breast_Cancer.csv` next to `app.py` for automatic loading. The dashboard uses the available columns, so views for missing fields are omitted or display a short explanation.

The sidebar filters the cohort by patient status, stage, race, marital status, receptor status, age, and tumor size. Tabs cover cohort overview, recorded months and tumor size, receptor and lymph node comparisons, and filtered records with CSV export.

The charts are descriptive summaries of the dataset and do not establish causation or predict an individual's outcome.
"# eda_project_breastcancerinsight" 
