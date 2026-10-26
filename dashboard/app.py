from pathlib import Path
from html import escape
import json
import pandas as pd
import streamlit as st

from insights import (HABITS, FINANCES, MEASURES, GROUPS, AGE_ORDER, QUARTILES, EDUCATION,
    UNITS, label, compare, comparison_insight, context_table, context_insight,
    rate_summary, rate_insight, overview)
from charts import (typical_chart, context_bar_chart, distribution, rate_chart,
                    correlation_chart, income_scatter, axis_title)

st.set_page_config(page_title='Habits or Circumstances?', page_icon='◈', layout='wide')
folder = Path(__file__).resolve().parent
with open(folder / 'theme.json') as file:
    theme = json.load(file)
css = (folder / 'styles.css').read_text()
for name, color in theme.items():
    css = css.replace('{{' + name + '}}', color)
st.markdown('<style>' + css + '</style>', unsafe_allow_html=True)


@st.cache_data
def load_data():
    return pd.read_csv(folder / 'clean_data.csv', keep_default_na=False, na_values=[''])


def html(text):
    st.markdown(text, unsafe_allow_html=True)


def icon(name):
    paths = {
        'bars': '<path d="M4 20V13M10 20V8M16 20V3M22 20V11"/>',
        'overview': '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
        'habits': '<path d="M20 5a8 8 0 1 1-9-2 7 7 0 0 0 9 9 8 8 0 0 1 0-7Z"/>',
        'people': '<circle cx="9" cy="8" r="3"/><path d="M3 21v-3a6 6 0 0 1 12 0v3M16 5a3 3 0 0 1 0 6M18 15a5 5 0 0 1 3 5"/>',
        'clock': '<circle cx="12" cy="12" r="9"/><path d="M12 6v6l4 2"/>',
        'trend': '<path d="M3 18 9 12l4 3 8-11M15 4h6v6M3 21h18"/>',
        'compare': '<circle cx="8" cy="12" r="6"/><circle cx="16" cy="12" r="6"/>',
        'details': '<path d="M6 3h9l4 4v14H6ZM15 3v5h4M9 12h7M9 16h7"/>'}
    return ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" '
            'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + paths[name] + '</svg>')


def heading(title, subtitle=''):
    html(f'<h3 class="chart-title">{escape(title)}</h3><p class="chart-subtitle">{escape(subtitle)}</p>')


def insight(text):
    html(f'<div class="insight"><span>WHAT THIS TELLS US</span><p>{escape(text)}</p></div>')


def section(number, title, subtitle, anchor):
    html(f'<div class="section-head" id="{anchor}"><span>{number}</span><h2>{escape(title)}</h2></div>'
         f'<p class="section-desc">{escape(subtitle)}</p>')


def draw(fig, key):
    st.plotly_chart(fig, key=key, width='stretch', theme=None,
                    config={'displaylogo': False, 'scrollZoom': False})


def reset():
    st.session_state.country = 'All countries'
    st.session_state.ages = (int(df.age.min()), int(df.age.max()))
    st.session_state.education = EDUCATION.copy()
    st.session_state.incomes = QUARTILES.copy()
    st.session_state.statuses = GROUPS.copy()


def details(data, column):
    table = data.groupby('status_label')[column].agg(['count', 'median', 'mean'])
    table = table.reindex([g for g in GROUPS if g in table.index])
    st.dataframe(table.rename(columns={'count': 'Recorded profiles', 'median': 'Typical value',
        'mean': 'Average'}).round(2), width='stretch')
    st.caption('Units: ' + axis_title(column) + '. Typical means the middle value, with half the recorded values on either side.')
    draw(distribution(data, column, theme, height=260), 'spread_' + column)
    st.caption('The box contains the middle half of values. The diamond marks the typical value. Outlier dots are hidden, but their records remain in the analysis.')


df = load_data()
# These income cutoffs always come from the full file, even after filtering.
edges = df.total_annual_income.quantile([.25, .5, .75]).tolist()
income_names = dict(zip(QUARTILES, [f'Under ${edges[0]/1000:.1f}K',
    f'${edges[0]/1000:.1f}–{edges[1]/1000:.1f}K', f'${edges[1]/1000:.1f}–{edges[2]/1000:.1f}K',
    f'Over ${edges[2]/1000:.1f}K']))
if 'country' not in st.session_state:
    reset()

with st.sidebar:
    html('<div class="side-brand"><span class="brand-mark">' + icon('bars') +
         '</span><span>Habits or<br>Circumstances?</span></div>')
    links = [('overview','Overview','overview'), ('habits','Everyday routines','habits'),
             ('trend','Money & background','money'), ('compare','Similar backgrounds','context'),
             ('details','Explore the data','details')]
    html('<nav class="side-nav">' + ''.join(f'<a href="#{anchor}">{icon(name)}<span>{text}</span></a>'
         for name,text,anchor in links) + '</nav>')
    st.caption('Compare daily routines, income, and financial behaviors across wealth groups.')
    country = st.selectbox('Country', ['All countries'] + sorted(df.country.unique()), key='country')
    ages = st.slider('Age range', int(df.age.min()), int(df.age.max()), key='ages')
    statuses = st.multiselect('Wealth groups', GROUPS, key='statuses')
    with st.expander('Income & education'):
        incomes = st.multiselect('Yearly income', QUARTILES, format_func=lambda q: income_names[q], key='incomes')
        education = st.multiselect('Education', EDUCATION, key='education')
    st.button('Reset selection', on_click=reset, width='stretch')

filtered = df[df.age.between(*ages) & df.income_quartile.isin(incomes)
              & df.education_level.isin(education) & df.status_label.isin(statuses)].copy()
if country != 'All countries':
    filtered = filtered[filtered.country == country]
with st.sidebar:
    html(f'<div class="side-count">{len(filtered):,}<small>profiles in your selection</small></div>')
    st.progress(len(filtered)/len(df))
    st.caption('Millionaire = net worth of at least $1 million. All money values are in USD.')

if filtered.empty:
    html('<div class="empty-state"><h1>No profiles match these filters</h1><p>Add groups or widen the age range.</p></div>')
    st.button('Start with all profiles', on_click=reset, type='primary')
    st.stop()

story = overview(filtered)
share = filtered.millionaire_status.mean()*100
n_m = int(filtered.millionaire_status.sum())
chips = [country, f'Ages {ages[0]}–{ages[1]}', 'All income bands' if len(incomes)==4 else ', '.join(income_names[q] for q in incomes),
         'All education levels' if len(education)==6 else ', '.join(education),
         'Both wealth groups' if len(statuses)==2 else statuses[0]]
html('<div class="topbar"><span class="workspace-label">HABITS, MONEY, AND BACKGROUND</span>'
     f'<span class="data-badge">{icon("overview")}<span>{len(df):,} profiles in the dataset</span></span>'
     '<span class="live-badge">● Filters update the story</span></div>')
html('<div class="hero" id="overview"><div><h1>Habits or <em>Circumstances?</em></h1>'
     '<p>What differs between millionaire and non-millionaire profiles: everyday routines, money behaviors, or background?</p></div>'
     f'<div class="hero-takeaway"><span>YOUR SELECTED PICTURE</span><strong>{escape(story["headline"])}</strong></div></div>'
     '<div class="selection-strip"><b>VIEWING</b>' + ''.join(f'<span>{escape(c)}</span>' for c in chips) + '</div>')
metrics = [('people','Profiles in view',f'{len(filtered):,}','One row describes one profile'),
    ('compare','Millionaire profiles',f'{share:.1f}%',f'{n_m:,} profiles in this selection'),
    ('clock','Typical age',f'{filtered.age.median():.0f} years','The middle age in this selection'),
    ('trend','Typical yearly income',f'${filtered.total_annual_income.median():,.0f}','Money received over a year')]
html('<div class="metric-grid">' + ''.join(f'<div class="metric-card metric-{name}"><span class="metric-icon">{icon(name)}</span>'
     f'<div><div class="metric-label">{title}</div><div class="metric-value">{value}</div><div class="metric-note">{note}</div></div></div>'
     for name,title,value,note in metrics) + '</div>')
html('<div class="story-grid">' + ''.join(f'<div class="story-card story-{i}"><div class="card-kicker">QUESTION {i+1}</div>'
     f'<div class="card-value">{escape(value)}</div><h3>{escape(title)}</h3><p>{escape(text)}</p></div>'
     for i,(value,title,text) in enumerate(story['cards'])) + '</div>')
if filtered.millionaire_status.nunique() < 2:
    st.info('Only one wealth group is selected. Add the other group to compare. The displayed millionaire share follows that filter.')
elif filtered.status_label.value_counts().min() < 30:
    st.info('One wealth group has fewer than 30 profiles. Its values are visible, but there are too few to interpret a comparison.')

section('01','Do millionaires have different everyday routines?', 'Choose a routine. Each bar shows a typical value for one wealth group.', 'habits')
habit = st.selectbox('Which routine would you like to compare?', HABITS, format_func=label, key='habit')
left,right = st.columns([1.15,1],gap='large')
with left,st.container(border=True,key='panel_habit'):
    heading(label(habit),axis_title(habit))
    draw(typical_chart(filtered,habit,theme),'habit_typical')
    st.caption('Typical = the middle recorded value. Hover for group sizes and the range containing the middle half of values.')
with right:
    insight(comparison_insight(filtered,habit))
    with st.expander('See the values and their spread'):
        details(filtered,habit)

section('02','What do money behaviors and background add?', 'Saving, earning, and having wealth are different measures. Compare them in their own units.', 'money')
left,right = st.columns(2,gap='large')
with left,st.container(border=True,key='panel_finance'):
    financial = st.selectbox('Choose a money behavior',FINANCES,format_func=label,key='financial')
    heading(label(financial),axis_title(financial))
    draw(typical_chart(filtered,financial,theme),'financial_typical')
    insight(comparison_insight(filtered,financial))
    with st.expander('See the values and their spread'):
        details(filtered,financial)
with right,st.container(border=True,key='panel_rates'):
    grouping = st.selectbox('Compare the wealth split by',['income_quartile','age_band','education_level','savings_quartile'],format_func=label,key='grouping')
    order = AGE_ORDER if grouping=='age_band' else EDUCATION if grouping=='education_level' else QUARTILES
    summary = rate_summary(filtered,grouping,order)
    names = income_names if grouping=='income_quartile' else None
    heading('How many are millionaires in each group?','Each bar shows millionaires out of every 100 profiles in that category.')
    draw(rate_chart(filtered,summary,grouping,theme,display_names=names),'background_rates')
    insight(rate_insight(filtered,grouping,summary))
    with st.expander('Check the group sizes'):
        st.dataframe(summary.rename(columns={grouping:label(grouping),'records':'Profiles','millionaires':'Millionaires','share':'Millionaires per 100'}).round(1),hide_index=True,width='stretch')
        st.caption('Faint bars have fewer than 30 profiles and are excluded from the takeaway. Income and savings bands keep the full-dataset cutoffs.')

section('03','Does the pattern remain with similar backgrounds?', 'Choose a life stage, then compare the wealth groups within the same broad income bands.', 'context')
left,right = st.columns([1.2,1],gap='large')
with left:
    measure = st.selectbox('What would you like to check?',FINANCES+HABITS,format_func=label,key='context_measure')
with right:
    available = [a for a in AGE_ORDER if a in filtered.age_band.values]
    if st.session_state.get('context_age') not in available:
        st.session_state.context_age = '50–64' if '50–64' in available else available[0]
    age = st.selectbox('Life stage to compare',available,key='context_age',format_func=lambda a:'Ages '+a)
part = filtered[filtered.age_band==age]
contexts = context_table(part,measure)
with st.container(border=True,key='panel_context'):
    heading(f'{label(measure)} among ages {age}', 'Both wealth groups, compared inside each income band')
    draw(context_bar_chart(contexts,measure,theme,income_names),'context_bars')
    insight(context_insight(part,measure,contexts))
    st.caption(f'{len(part):,} selected profiles are in this age band. Empty bands lack 30 recorded values in each wealth group. Broad bands do not make the profiles identical.')
with st.expander('Check all age and income comparisons'):
    all_context = context_table(filtered,measure)
    st.dataframe(all_context[['age_band','income_quartile','non_count','millionaire_count','non_median','millionaire_median','eligible']].rename(columns={
        'age_band':'Age band','income_quartile':'Income band','non_count':'Non-millionaire profiles','millionaire_count':'Millionaire profiles',
        'non_median':'Typical non-millionaire value','millionaire_median':'Typical millionaire value','eligible':'Enough values'}).round(2),hide_index=True,width='stretch')

section('↳','Explore the data behind the answers','Records, summaries, and methods are here when you want a closer look.', 'details')
with st.expander('Selected records and summary statistics'):
    columns = ['person_id','country','age','education_level','status_label','total_annual_income','savings_rate_percent',habit]
    st.dataframe(filtered[list(dict.fromkeys(columns))].head(100),hide_index=True,width='stretch')
    st.caption('First 100 matches in source order. The download contains every matching row.')
    statistic = st.selectbox('Summarize a measure',MEASURES,format_func=label,key='statistic')
    values = filtered[statistic].dropna()
    st.dataframe(pd.DataFrame([{'Recorded profiles':len(values),'Typical value':values.median(),'Average':values.mean(),
        'Smallest':values.min(),'Largest':values.max()}]).round(2),hide_index=True,width='stretch')
    st.caption('Units: '+UNITS[statistic]+'. Unknown values are left out only from the calculation needing them.')
    st.download_button('Download selected profiles',filtered.to_csv(index=False).encode(),
        file_name='selected_profiles.csv',mime='text/csv',key='download',type='primary')
with st.expander('How the measures relate'):
    st.caption('The numbers describe a linear relationship from −1 to +1, not a percentage. Green means values tend to rise together; gold means they tend to move in opposite directions. Pale cells show a weaker linear relationship.')
    draw(correlation_chart(filtered,MEASURES+['millionaire_status'],theme),'correlations')
with st.expander('Income and age together'):
    draw(income_scatter(filtered,theme),'income_age')
    insight(comparison_insight(filtered,'total_annual_income'))
    st.caption(f'Up to 2,500 profiles are drawn with a fixed random seed for readability. Every summary uses all matching values. The log income axis gives equal space to equal proportional changes.')
with st.expander('About the dataset and these comparisons'):
    st.markdown('''The Millionaire Habits Dataset contains 100,000 synthetic profiles from Kaggle. The findings describe this file and show associations, not causes or proven advice for becoming wealthy.

**How to read it:** “Typical” means the middle recorded value. A millionaire has net worth of at least $1 million; income is money earned in a year. Dollar values are USD.

**Comparisons:** we need 30 recorded values per wealth group before interpreting a difference. “Little average separation” means the difference in averages is small relative to variation within groups. This is a descriptive rule, not proof that no relationship exists.

**Data choices:** unknown reading values remain blank. Income outliers and negative savings rates remain in the data. Income and age bands stay fixed as filters change.''')
html('<div class="footer">Habits or Circumstances? · Shaden Alghamdi · Unit 3 EDA</div>')
st.link_button('Dataset source on Kaggle ↗','https://www.kaggle.com/datasets/datascikhan/millionaire-habits-dataset')
