# Habits or Circumstances?

Shaden Alghamdi's EDA project. It compares everyday routines, money behaviors, and background across millionaire and non-millionaire profiles, then checks the patterns within age and income bands.

Main question: What does this dataset reveal about everyday habits compared with financial behaviors and background factors among millionaire and non-millionaire profiles?

The Millionaire Habits Dataset contains 100,000 profiles with routines, income, saving, investing, education, and wealth status. Its 274 columns let us compare a familiar habits story with financial and background information. We use the full CSV and keep a focused table for the dashboard.

I chose it because the question is easy to relate to, and a weak habit result is still an answer worth reporting. I expect financial behaviors and background to add context, but the plots will decide what we can say.

## Run locally

Use Python 3.12. From this folder:

```bash
python -m pip install -r requirements.txt
python -m streamlit run dashboard/app.py
```

The dashboard uses the included cleaned CSV. No account, API key, or dataset download is needed.

## Files

- `Millionaire_Habits_EDA.ipynb`: analysis, cleaning, outputs, and plots.
- `dashboard/`: app, helper files, cleaned data, and editable `theme.json`.
- `presentation/`: seven slides.

[Dataset source](https://www.kaggle.com/datasets/datascikhan/millionaire-habits-dataset)
The profiles are synthetic; the findings describe this file and show associations, not causes or advice for becoming wealthy -sadly-.
