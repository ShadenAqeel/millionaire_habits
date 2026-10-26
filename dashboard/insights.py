"""Readable calculations for the three questions. All use the supplied selection."""
import numpy as np
import pandas as pd

HABITS = ['sleep_duration_hours', 'exercise_hours_per_week', 'books_read_per_year',
          'deep_work_hours_per_day', 'social_media_hours_per_day']
FINANCES = ['savings_rate_percent', 'investment_rate_percent', 'housing_cost_percent']
BACKGROUND = ['total_annual_income', 'age']
MEASURES = HABITS + FINANCES + BACKGROUND
GROUPS = ['Non-millionaire', 'Millionaire']
AGE_ORDER = ['20–34', '35–49', '50–64', '65–85']
QUARTILES = ['Q1 lowest', 'Q2', 'Q3', 'Q4 highest']
EDUCATION = ['High School', 'Some College', 'Bachelor', 'Master', 'PhD', 'Professional']
MIN_GROUP = 30
SMALL_GAP = 0.20
LABELS = {
    'sleep_duration_hours': 'Sleep', 'exercise_hours_per_week': 'Exercise',
    'books_read_per_year': 'Reading', 'deep_work_hours_per_day': 'Deep work',
    'social_media_hours_per_day': 'Social media', 'savings_rate_percent': 'Savings rate',
    'investment_rate_percent': 'Investment rate', 'housing_cost_percent': 'Housing cost share',
    'total_annual_income': 'Annual income', 'age': 'Age', 'age_band': 'Age group',
    'income_quartile': 'Income group', 'savings_quartile': 'Savings-rate group',
    'education_level': 'Education', 'status_label': 'Wealth group', 'millionaire_status': 'Millionaire status',
    'country': 'Country', 'person_id': 'Profile ID',
}
UNITS = {'sleep_duration_hours': 'hours / night', 'exercise_hours_per_week': 'hours / week',
         'books_read_per_year': 'books / year', 'deep_work_hours_per_day': 'hours / day',
         'social_media_hours_per_day': 'hours / day', 'savings_rate_percent': '% of income',
         'investment_rate_percent': '% of income', 'housing_cost_percent': '% of income',
         'total_annual_income': 'USD / year', 'age': 'years'}


def label(column):
    return LABELS.get(column, column.replace('_', ' ').capitalize())


def value_text(value, column):
    if pd.isna(value):
        return 'unavailable'
    if column == 'total_annual_income':
        return f'${value:,.0f}'
    if column in FINANCES:
        return f'{value:.1f}%'
    if column == 'books_read_per_year':
        return f'{value:,.1f} books / year'
    return f'{value:.1f} {UNITS.get(column, "")}'.strip()


def compare(data, column):
    """Median gap in original units; standardized mean gap for context.

    Below 0.20 pooled standard deviations is a display convention, not a test
    of significance or equivalence, or evidence about real populations.
    """
    a = data.loc[data.status_label == GROUPS[0], column].dropna()
    b = data.loc[data.status_label == GROUPS[1], column].dropna()
    result = {'column': column, 'non_count': len(a), 'millionaire_count': len(b),
              'non_median': a.median(), 'millionaire_median': b.median(),
              'non_mean': a.mean(), 'millionaire_mean': b.mean(),
              'gap': b.median() - a.median(), 'effect': np.nan,
              'eligible': min(len(a), len(b)) >= MIN_GROUP, 'reason': ''}
    if result['eligible']:
        pooled = np.sqrt(((len(a)-1)*a.var() + (len(b)-1)*b.var()) / (len(a)+len(b)-2))
        if pooled > 0:
            result['effect'] = (b.mean() - a.mean()) / pooled
        elif a.mean() == b.mean():
            result['effect'] = 0.0
    if min(len(a), len(b)) < MIN_GROUP:
        result['reason'] = 'small_group'
    elif pd.isna(result['effect']):
        result['reason'] = 'no_within_group_spread'
    result['eligible'] = bool(result['eligible'] and pd.notna(result['effect']))
    return result


def comparison_table(data, columns=MEASURES):
    return pd.DataFrame([compare(data, column) for column in columns])


def comparison_insight(data, column):
    row = compare(data, column)
    if row['reason'] == 'no_within_group_spread':
        return 'Each group has a different fixed value. The usual spread-based comparison is unavailable, so check the displayed values directly.'
    if not row['eligible']:
        return (f'We need at least 30 known values in each wealth group to compare. '
                f'This selection has {row["non_count"]:,} non-millionaire and {row["millionaire_count"]:,} millionaire values.')
    a, b = row['non_median'], row['millionaire_median']
    if column in HABITS:
        phrases = {
            'sleep_duration_hours': ('sleep', 'hours a night'),
            'exercise_hours_per_week': ('exercise', 'hours a week'),
            'books_read_per_year': ('read', 'books a year'),
            'deep_work_hours_per_day': ('do focused work for', 'hours a day'),
            'social_media_hours_per_day': ('use social media for', 'hours a day')}
        verb, unit = phrases[column]
        if abs(a-b) < .05:
            fact = f'Both groups typically {verb} about {a:g} {unit}. '
        else:
            fact = f'Typical values are {b:g} {unit} for millionaires and {a:g} for non-millionaires. '
        if abs(row['effect']) < SMALL_GAP:
            return fact + 'This does not support a special millionaire routine in this selection.'
        return fact + 'The averages differ more in this selection. Compare similar age and income groups before generalizing.'
    if column == 'savings_rate_percent':
        if abs(row['gap']) < .05:
            return 'Both groups typically save the same share of their income. Saving does not distinguish the typical profiles in this selection.'
        direction = 'more' if row['gap'] > 0 else 'less'
        text = f'Millionaire profiles typically save ${abs(row["gap"]):.2f} {direction} per $100 earned. '
        table = context_table(data, column)
        good = table[table.eligible]
        same = (good.gap * row['gap'] > 0).all() if not good.empty else False
        if same and good.records.sum() / len(data) >= .5:
            return text + 'The same direction appears within comparable age and income bands.'
        return text + 'Use the age-and-income comparison to see how much this pattern depends on the selection.'
    if column == 'housing_cost_percent':
        if abs(row['gap']) < .05:
            return 'Both groups typically use the same share of income for housing. The share combines housing costs with earnings.'
        direction = 'less' if row['gap'] < 0 else 'more'
        return (f'Millionaire profiles typically use ${abs(row["gap"]):.2f} {direction} from each $100 of income for housing. '
                'That share can change because of housing costs, earnings, or both.')
    if column == 'investment_rate_percent':
        if abs(row['gap']) < .05:
            return 'Both groups typically allocate the same share of income to investing. This measure describes contributions, not investment returns.'
        direction = 'more' if row['gap'] > 0 else 'less'
        return (f'Millionaire profiles typically allocate ${abs(row["gap"]):.2f} {direction} per $100 earned to investing. '
                'That shows how income is allocated, not how well investments perform.')
    if column == 'total_annual_income':
        return 'Income measures money earned in a year. Millionaire status measures accumulated wealth, so high earnings and high net worth are related but different.'
    return 'Age changes the wealth comparison. These profiles show different life stages, not the same people becoming wealthier over time.'


def context_table(data, column):
    """Compare wealth groups inside fixed full-file age and income bands."""
    rows = []
    for (age, income), part in data.groupby(['age_band', 'income_quartile'], observed=True, sort=False):
        row = compare(part, column)
        row.update(age_band=str(age), income_quartile=str(income), records=len(part))
        rows.append(row)
    return pd.DataFrame(rows, columns=['age_band', 'income_quartile', 'records', 'column',
        'non_count', 'millionaire_count', 'non_median', 'millionaire_median',
        'non_mean', 'millionaire_mean', 'gap', 'effect', 'eligible'])


def context_insight(data, column, table=None):
    table = context_table(data, column) if table is None else table
    good = table[table.eligible] if not table.empty else table
    if good.empty:
        return 'There are not enough profiles from both wealth groups within these income bands. Widen the selection to make this comparison.'
    coverage = good.records.sum() / len(data)
    name = label(column).lower()
    if column in HABITS:
        small = int((good.effect.abs() < SMALL_GAP).sum())
        if small == len(good):
            text = f'{label(column)} still looks similar on average within these income bands. The everyday-routine comparison is not simply hiding an income difference.'
        else:
            text = f'{label(column)} differs more in some income bands than others. A single overall comparison misses that variation.'
    else:
        up, down = (good.gap > .05).sum(), (good.gap < -.05).sum()
        if up == len(good) or down == len(good):
            direction = 'higher' if up == len(good) else 'lower'
            text = f'The typical {name} remains {direction} for millionaire profiles across every income band with enough observations. The overall gap is not only a difference between broad income bands.'
        else:
            text = f'The {name} gap changes across income bands. That makes the overall contrast less useful without knowing who is being compared.'
    if coverage < .5:
        text += ' This comparison covers fewer than half of the selected profiles.'
    return text


def rate_summary(data, column, order):
    result = data.groupby(column, observed=True).millionaire_status.agg(
        records='size', millionaires='sum', share='mean').reset_index()
    result['share'] *= 100
    return result.set_index(column).reindex([v for v in order if v in result[column].values]).reset_index()


def rate_insight(data, column, summary):
    if data.millionaire_status.nunique() < 2:
        return 'Only one wealth group is selected. Select both groups to compare the wealth split.'
    good = summary[summary.records >= MIN_GROUP]
    if len(good) < 2:
        return 'At least two categories need 30 profiles each. Widen the selection to compare groups.'
    if good.share.max() - good.share.min() < 2:
        return 'The wealth split is similar across these groups. This background factor adds little distinction in your current selection.'
    if column == 'income_quartile':
        top = good[good[column] == 'Q4 highest']
        if not top.empty:
            non = 100 - top.iloc[0]['share']
            return (f'Even in the highest income band, about {non:.0f} in every 100 profiles are not millionaires. '
                    'High earnings do not automatically mean high accumulated wealth.')
        return 'The wealth split changes with income. Earnings provide context, but an income band does not determine a profile’s wealth group.'
    if column == 'age_band':
        return 'The wealth split changes across age groups. Comparing similar life stages helps us read the financial-behavior differences more carefully.'
    if column == 'education_level':
        return 'Education groups have different wealth splits. Their income and age can differ too, so this chart cannot tell us what adding a qualification would change.'
    return 'The wealth split varies across saving groups. The next comparison checks whether the saving pattern remains among profiles with similar income and age.'


def overview(data):
    habits = comparison_table(data, HABITS)
    valid = habits[habits.eligible]
    finance = compare(data, 'savings_rate_percent')
    table = context_table(data, 'savings_rate_percent')
    good = table[table.eligible] if not table.empty else table
    if data.millionaire_status.nunique() < 2:
        headline = 'One group tells only part of the story.'
    elif len(valid) < 5:
        headline = 'A broader selection is needed to compare.'
    elif (valid.effect.abs() < SMALL_GAP).all() and finance['eligible'] and abs(finance['effect']) >= SMALL_GAP:
        headline = 'Similar routines. A different money story.'
    elif (valid.effect.abs() < SMALL_GAP).all():
        headline = 'Daily routines look similar in this selection.'
    else:
        headline = 'The pattern changes with the people selected.'
    if len(valid) < 5:
        routine = ('More profiles needed', 'Do daily routines differ?', 'Include enough profiles from both wealth groups to compare all five routines.')
    else:
        count = int((valid.effect.abs() < SMALL_GAP).sum())
        routine = ('Routines look alike' if count == 5 else 'A mixed routine picture', 'Do daily routines differ?',
            'The five everyday routines look much alike across wealth groups in these comparisons.' if count == 5 else
            'Some routines differ more in this selection. Choose one below to see which group differs and by how much.')
    if finance['eligible']:
        gap = finance['gap']
        value = f'${abs(gap):.2f} ' + ('more' if gap >= .05 else 'less' if gap <= -.05 else 'difference')
        money = (value, 'Saved from every $100 earned',
            'The gap between typical millionaire and non-millionaire savings rates. Income and existing wealth may affect saving capacity.')
    else:
        money = ('More profiles needed', 'Do money behaviors differ?', 'Choose enough profiles from both wealth groups to compare saving rates.')
    if good.empty:
        context = ('Comparison unavailable', 'Does the pattern survive similar backgrounds?', 'Widen the filters so both wealth groups appear within age and income bands.')
    else:
        up, down = (good.gap > .05).sum(), (good.gap < -.05).sum()
        consistent = up == len(good) or down == len(good)
        coverage = good.records.sum()/len(data)
        context = ('Savings gap remains' if consistent and coverage >= .5 else 'Context changes the story',
            'Among similar age and income groups',
            f'The saving rate stays {"higher" if up == len(good) else "lower"} for millionaire profiles across the age and income groups with enough observations.' if consistent else
            'The saving gap varies across groups. Explore a life stage below to see where the pattern changes.')
    return {'headline': headline, 'cards': [routine, money, context]}
