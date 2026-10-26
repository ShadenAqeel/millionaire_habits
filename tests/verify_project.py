"""Run from the project folder: python tests/verify_project.py."""
from pathlib import Path
import sys
import json
import numpy as np
import pandas as pd
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'dashboard'))
from insights import (HABITS, FINANCES, MEASURES, GROUPS, AGE_ORDER, QUARTILES,
    compare, comparison_table, comparison_insight, context_table, context_insight,
    rate_summary, rate_insight, overview)
from charts import typical_chart, context_bar_chart, rate_chart


def run():
    data = pd.read_csv(ROOT/'dashboard/clean_data.csv',keep_default_na=False,na_values=[''])
    theme = json.loads((ROOT/'dashboard/theme.json').read_text())
    assert data.shape == (100000,21)
    assert data.person_id.is_unique
    assert data.books_read_per_year.isna().sum() == 4149
    assert data.millionaire_status.sum() == 42492
    assert data.age_band.notna().all()
    expected = pd.read_csv(ROOT/'results/comparison_summary.csv').set_index('column').sort_index()
    actual = comparison_table(data).set_index('column').sort_index()
    for column in expected.columns:
        if column=='eligible':
            assert actual[column].equals(expected[column])
        else:
            np.testing.assert_allclose(actual[column],expected[column],rtol=1e-10,atol=1e-10)
    saved = pd.read_csv(ROOT/'results/context_comparisons.csv')
    cell_checks = 0
    for measure in FINANCES+HABITS:
        actual = context_table(data,measure).set_index(['age_band','income_quartile']).sort_index()
        expected = saved[saved.column==measure].set_index(['age_band','income_quartile']).sort_index()
        for column in ['non_count','millionaire_count','gap','effect']:
            np.testing.assert_allclose(actual[column],expected[column],rtol=1e-10,atol=1e-10,equal_nan=True)
        assert actual.eligible.equals(expected.eligible)
        cell_checks += len(actual)
    # Chart heights must be the actual typical values, not difference scores.
    fig = typical_chart(data,'savings_rate_percent',theme)
    np.testing.assert_allclose(fig.data[0].y,[24.1,31.7])
    fig = typical_chart(data,'books_read_per_year',theme)
    np.testing.assert_allclose(fig.data[0].y,[10,10])
    local = context_table(data[data.age_band=='20–34'],'savings_rate_percent')
    fig = context_bar_chart(local,'savings_rate_percent',theme,dict(zip(QUARTILES,QUARTILES)))
    assert np.isnan(fig.data[0].y[0]) and np.isnan(fig.data[1].y[0])
    for trace,column in zip(fig.data,['non_median','millionaire_median']):
        wanted = local.set_index('income_quartile').reindex(QUARTILES)
        np.testing.assert_allclose(trace.y,wanted[column].where(wanted.eligible),equal_nan=True)
    rates = rate_summary(data,'income_quartile',QUARTILES)
    np.testing.assert_allclose(rate_chart(data,rates,'income_quartile',theme).data[0].x,rates.share)
    corr = pd.read_csv(ROOT/'results/correlations.csv',index_col=0)
    np.testing.assert_allclose(corr,data[MEASURES+['millionaire_status']].corr(),atol=1e-10)
    assert 'about 10 books a year' in comparison_insight(data,'books_read_per_year')
    assert '$7.60 more' in comparison_insight(data,'savings_rate_percent')
    assert 'about 22 in every 100' in rate_insight(data,'income_quartile',rates)
    one = data[data.status_label=='Millionaire']
    assert 'One group' in overview(one)['headline']
    assert 'need at least 30' in comparison_insight(one,HABITS[0])
    assert 'not enough profiles' in context_insight(one,FINANCES[0])
    assert context_table(data.head(0),FINANCES[0]).empty
    assert not compare(data.head(5),HABITS[0])['eligible']
    missing = data.copy(); missing[HABITS[2]] = np.nan
    assert not compare(missing,HABITS[2])['eligible']
    constant = data.copy(); constant[HABITS[0]] = 8.0
    assert compare(constant,HABITS[0])['effect']==0
    constant.loc[constant.status_label=='Millionaire',HABITS[0]] = 9.0
    assert 'fixed value' in comparison_insight(constant,HABITS[0])
    reverse = data.copy(); reverse.savings_rate_percent *= -1
    assert 'less' in comparison_insight(reverse,'savings_rate_percent')
    assert 'less' in overview(reverse)['cards'][1][0]
    assert 'lower for millionaire' in context_insight(reverse,'savings_rate_percent')
    scenarios = [data[data.country==c] for c in sorted(data.country.unique())]
    scenarios += [data[data.age.between(20,25)],data[data.age.between(65,85)],data[data.income_quartile=='Q1 lowest']]
    for part in scenarios:
        medians = part.groupby('status_label').savings_rate_percent.median()
        if len(medians)==2:
            np.testing.assert_allclose(compare(part,'savings_rate_percent')['gap'],medians['Millionaire']-medians['Non-millionaire'])
        for measure in HABITS+FINANCES:
            assert len(comparison_insight(part,measure).split())<=60
            assert len(context_insight(part,measure).split())<=65
        assert overview(part)['headline']
    # Exercise every filter, the main selectors, empty data, and reset.
    app = AppTest.from_file(str(ROOT/'dashboard/app.py'),default_timeout=60).run()
    assert not app.exception,[e.message for e in app.exception]
    assert any('Similar routines.' in e.value for e in app.markdown)
    assert sum('synthetic' in e.value.lower() for e in app.markdown)==1
    app.selectbox(key='country').set_value(sorted(data.country.unique())[0]).run()
    app.slider(key='ages').set_range(35,64).run()
    app.multiselect(key='incomes').set_value(['Q2','Q3']).run()
    app.multiselect(key='education').set_value(['Bachelor','Master']).run()
    app.selectbox(key='habit').set_value('books_read_per_year').run()
    app.selectbox(key='financial').set_value('housing_cost_percent').run()
    app.selectbox(key='grouping').set_value('education_level').run()
    app.selectbox(key='context_measure').set_value('deep_work_hours_per_day').run()
    app.selectbox(key='context_age').set_value('35–49').run()
    assert not app.exception,[e.message for e in app.exception]
    app.multiselect(key='statuses').set_value(['Millionaire']).run()
    assert not app.exception
    assert any('One group tells' in e.value for e in app.markdown)
    app.multiselect(key='education').set_value([]).run()
    assert not app.exception
    assert any('No profiles match' in e.value for e in app.markdown)
    app.button[0].click().run()
    assert not app.exception
    assert app.multiselect(key='statuses').value==GROUPS
    app.slider(key='ages').set_range(20,25).run()
    assert not app.exception
    assert app.selectbox(key='context_age').value=='20–34'
    app.button[0].click().run()
    assert not app.exception
    notebook = json.loads((ROOT/'Millionaire_Habits_EDA.ipynb').read_text())
    code = [c for c in notebook['cells'] if c['cell_type']=='code']
    assert len(code)==33
    assert all(c.get('execution_count') for c in code)
    assert not any(o['output_type']=='error' for c in code for o in c.get('outputs',[]))
    return {'status':'passed','rows':len(data),'focused_columns':data.shape[1],
        'notebook_code_cells':len(code),'overall_measure_comparisons':len(MEASURES),
        'age_income_measure_comparisons':cell_checks,'filtered_scenarios':len(scenarios),
        'streamlit_reruns':15,'edge_cases':['empty','one group','small group','all missing',
        'equal constants','different constants','reversed savings'],
        'checks':['notebook and dashboard agreement','actual-value chart labels',
                  'filter-responsive explanations','reset','limited source disclosure']}

if __name__=='__main__':
    result = run()
    (ROOT/'results/verification.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
