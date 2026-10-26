"""Compact Plotly figures. Computations use all known values, never a drawing sample."""
import numpy as np
import plotly.graph_objects as go
from insights import GROUPS, AGE_ORDER, QUARTILES, UNITS, label


def style(fig, theme, height=340):
    fig.update_layout(template='plotly_white', height=height,
        font=dict(family='Arial, sans-serif', color=theme['text'], size=13),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=10, r=22, t=25, b=22),
        legend=dict(title='', orientation='h', y=-.2, x=0),
        hoverlabel=dict(bgcolor='white', font_size=13), hovermode='closest')
    fig.update_xaxes(showgrid=False, zeroline=False, automargin=True)
    fig.update_yaxes(gridcolor='rgba(23,50,77,.08)', zeroline=False, automargin=True)
    return fig


def empty_chart(message, theme, height=340):
    fig = go.Figure()
    fig.add_annotation(text=message, x=.5, y=.5, xref='paper', yref='paper', showarrow=False,
                       font=dict(size=15, color=theme['muted']))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return style(fig, theme, height)


def distribution(data, column, theme, height=340):
    """Precomputed boxes keep the dashboard quick without sampling values."""
    fig = go.Figure()
    for name, color in zip(GROUPS, [theme['secondary'], theme['primary']]):
        values = data.loc[data.status_label == name, column].dropna()
        if values.empty:
            continue
        q1, median, q3 = values.quantile([.25, .5, .75])
        iqr = q3 - q1
        lower = values[values >= q1 - 1.5*iqr].min()
        upper = values[values <= q3 + 1.5*iqr].max()
        fig.add_trace(go.Box(name=name, x=[name], q1=[q1], median=[median], q3=[q3],
            lowerfence=[lower], upperfence=[upper], boxpoints=False, width=.4,
            marker_color=color, line=dict(color=color, width=2), fillcolor=color,
            opacity=.78, hoverinfo='skip'))
        missing = int(data.loc[data.status_label == name, column].isna().sum())
        # A median marker gives a single useful tooltip instead of five box labels.
        fig.add_trace(go.Scatter(x=[name], y=[median], mode='markers', name=name,
            marker=dict(symbol='diamond', size=11, color=color, line=dict(color='white', width=1.5)),
            customdata=[[len(values), values.mean(), q1, q3, missing]],
            hovertemplate=(f'<b>{name}</b><br>Median: %{{y:.2f}} {UNITS[column]}'
                '<br>Middle 50%: %{customdata[2]:.2f}–%{customdata[3]:.2f}'
                '<br>Mean: %{customdata[1]:.2f}<br>Known values: %{customdata[0]:,}'
                '<br>Missing values: %{customdata[4]:,}<extra></extra>')))
    if not fig.data:
        return empty_chart('No known values for this measure.', theme, height)
    style(fig, theme, height)
    fig.update_layout(showlegend=False)
    fig.update_yaxes(title=f'{label(column)} ({UNITS[column]})')
    if column in ['savings_rate_percent', 'investment_rate_percent', 'housing_cost_percent']:
        fig.update_yaxes(ticksuffix='%')
    return fig


def rate_chart(data, summary, column, theme, display_names=None):
    if data.millionaire_status.nunique() < 2:
        return empty_chart('Select both wealth groups<br>to compare millionaire shares.', theme)
    if summary.empty:
        return empty_chart('No categories available.', theme)
    names = summary[column].map(display_names) if display_names else summary[column].astype(str)
    fig = go.Figure(go.Bar(x=summary.share, y=names, orientation='h',
        marker=dict(color=[theme['accent'] if n >= 30 else theme['muted'] for n in summary.records],
                    opacity=[1 if n >= 30 else .35 for n in summary.records], cornerradius=5),
        text=summary.share.map(lambda v: f'{v:.0f} in 100'), textposition='outside', cliponaxis=False,
        customdata=summary[['records','millionaires']].values,
        hovertemplate='%{y}<br>%{x:.1f} in every 100 are millionaires<br>%{customdata[1]:,} of %{customdata[0]:,} profiles<extra></extra>'))
    style(fig, theme, 340)
    fig.update_xaxes(title='Millionaires in every 100 profiles', range=[0, 115], ticksuffix='', dtick=25)
    fig.update_yaxes(autorange='reversed', showgrid=False)
    fig.add_vline(x=data.millionaire_status.mean()*100, line_dash='dot', line_color=theme['secondary'])
    return fig


def income_scatter(data, theme):
    sample = data.sample(n=min(2500, len(data)), random_state=42)
    fig = go.Figure()
    for group, color in zip(GROUPS, [theme['secondary'], theme['primary']]):
        part = sample[sample.status_label == group]
        fig.add_trace(go.Scattergl(x=part.age, y=part.total_annual_income, mode='markers',
            name=group, marker=dict(color=color, size=5, opacity=.4),
            hovertemplate=group+'<br>Age: %{x} years<br>Annual income: $%{y:,.0f}<extra></extra>'))
    style(fig, theme, 370)
    fig.update_xaxes(title='Age (years)')
    fig.update_yaxes(title='Annual income (USD · log scale)', type='log', tickprefix='$', tickformat='~s')
    return fig


def correlation_chart(data, columns, theme):
    corr = data[columns].corr()
    names = [label(c) for c in columns]
    counts = np.array([[data[[a,b]].dropna().shape[0] if a != b else data[a].notna().sum()
                        for b in columns] for a in columns])
    fig = go.Figure(go.Heatmap(z=corr.values, x=names, y=names, zmin=-1, zmax=1,
        colorscale=[[0, theme['accent']], [.5, '#FFFFFF'], [1, theme['primary']]],
        customdata=counts, text=corr.round(2).values, texttemplate='%{text}',
        textfont=dict(size=10), xgap=2, ygap=2, hoverongaps=False,
        hovertemplate='%{y} × %{x}<br>Pearson correlation: %{z:+.3f}<br>Known pairs: %{customdata:,}<extra></extra>',
        colorbar=dict(title='r', thickness=10)))
    style(fig, theme, 560)
    fig.update_xaxes(tickangle=-40)
    fig.update_yaxes(autorange='reversed', showgrid=False)
    return fig


def axis_title(column):
    names = {'savings_rate_percent': 'Saved from each $100 of income',
             'investment_rate_percent': 'Invested from each $100 of income',
             'housing_cost_percent': 'Housing cost from each $100 of income',
             'sleep_duration_hours': 'Hours of sleep a night',
             'exercise_hours_per_week': 'Hours of exercise a week',
             'books_read_per_year': 'Books read in a year',
             'deep_work_hours_per_day': 'Hours of focused work a day',
             'social_media_hours_per_day': 'Hours of social media a day'}
    return names.get(column, label(column))


def typical_chart(data, column, theme, height=300):
    """Show a familiar value first; full distributions remain in the details."""
    fig = go.Figure()
    names, values, counts, colors, middle = [], [], [], [], []
    for name, color in zip(GROUPS, [theme['secondary'], theme['primary']]):
        known = data.loc[data.status_label == name, column].dropna()
        if known.empty:
            continue
        names.append(name)
        values.append(known.median())
        counts.append(len(known))
        colors.append(color)
        middle.append([len(known), known.quantile(.25), known.quantile(.75)])
    if not values:
        return empty_chart('No recorded values in this selection.', theme, height)
    money = column in ['savings_rate_percent', 'investment_rate_percent', 'housing_cost_percent']
    text = [(f'${v:.1f}' if money else f'{v:g}') for v in values]
    fig.add_trace(go.Bar(x=names, y=values, marker=dict(color=colors, cornerradius=5),
        width=.48, text=text, textposition='outside', cliponaxis=False, customdata=middle,
        hovertemplate=('<b>%{x}</b><br>Typical value: %{y:.2f}<br>Recorded profiles: %{customdata[0]:,}'
            '<br>Middle half of values: %{customdata[1]:.2f}–%{customdata[2]:.2f}<extra></extra>')))
    style(fig, theme, height)
    fig.update_layout(showlegend=False)
    low, high = min(0, min(values)*1.2), max(1, max(values)*1.22)
    fig.update_yaxes(title=axis_title(column), range=[low, high], tickprefix='$' if money else '')
    return fig


def context_bar_chart(table, column, theme, income_names):
    if table.empty or not table.eligible.any():
        return empty_chart('More profiles needed in both wealth groups.', theme)
    ordered = table.set_index('income_quartile').reindex(QUARTILES)
    fig = go.Figure()
    for group, value_column, count_column, color in [
        ('Non-millionaire','non_median','non_count',theme['secondary']),
        ('Millionaire','millionaire_median','millionaire_count',theme['primary'])]:
        values = ordered[value_column].where(ordered.eligible.eq(True))
        fig.add_trace(go.Bar(name=group, x=[income_names[q] for q in QUARTILES], y=values,
            marker=dict(color=color,cornerradius=4), customdata=ordered[[count_column]].values,
            hovertemplate=group+'<br>%{x} annual income<br>Typical value: %{y:.2f}<br>Recorded profiles: %{customdata[0]:,}<extra></extra>'))
    style(fig,theme,350)
    money = column in ['savings_rate_percent','investment_rate_percent','housing_cost_percent']
    fig.update_layout(barmode='group',bargap=.3)
    fig.update_yaxes(title=axis_title(column),rangemode='tozero',tickprefix='$' if money else '')
    fig.update_xaxes(title='Annual income band (USD)')
    return fig
