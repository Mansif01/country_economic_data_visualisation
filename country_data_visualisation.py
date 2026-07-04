# %%
import pandas as pd
import altair as alt

df = pd.read_csv('country_economics_data.csv')


# %%
df.head()

# %%
df.columns

# %%
df.isnull().sum()

# %%
df = df.dropna(subset=['Population', 'Inflation Rate', 'Interest Rate','GDP Growth'])

# %%
pip install altair vega_datasets

# %%
df.columns

# %%
import pandas as pd
import altair as alt
from vega_datasets import data


region_domain = sorted(df['Region'].unique().tolist())
region_scale = alt.Scale(domain=region_domain,  range=[
      '#0072B2',
      '#E69F00',
      '#009E73',
      '#CC79A7',
      '#D55E00'
    ])

# CONFIGURATION
MAP_WIDTH = 800
MAP_HEIGHT = 450
BAR_WIDTH = 800
BAR_HEIGHT = 450


SCATTER_WIDTH = 800
SCATTER_HEIGHT = 450

#  SELECTIONS
select_region = alt.selection_point(fields=['Region'])


# This ensures everything is visible by default.
select_country = alt.selection_point(fields=['Name'], empty=True)

# COLORS & CONDITIONS

color_cond_bar = alt.condition(
    select_country,
    alt.value('steelblue'),
    alt.value('lightgray')
)

color_cond_scatter = alt.condition(
    select_country,
    alt.Color('Region:N', scale=region_scale, legend=None),
    alt.value('lightgray')
)


size_scatter = alt.value(150)


opacity_cond_scatter = alt.condition(select_country, alt.value(1.0), alt.value(0.8))

map_opacity = alt.condition(select_country, alt.value(1.0), alt.value(0.2))

# VISUALIZATION VIEWS

# VIEW 1: MAP
topo_country_shapes = alt.topo_feature(data.world_110m.url, 'countries')
basemap = alt.layer(
    alt.Chart(alt.sphere()).mark_geoshape(fill='white'),
    alt.Chart(alt.graticule()).mark_geoshape(stroke='LightGray', strokeWidth=0.5)
)
map_layer = (
    alt.Chart(topo_country_shapes).mark_geoshape(stroke='white', strokeWidth=0.5)
    .transform_lookup(
        lookup='id',
        from_=alt.LookupData(data=df, key='ID', fields=['Name', 'Region', 'GDP'])
    )
    .transform_calculate(
        Gdp_String="format(datum['GDP'], '$,.0f') + ' B'"
    )
    .encode(
        color=alt.Color('GDP:Q', scale=alt.Scale(scheme='viridis'), legend=alt.Legend(title="GDP", orient='bottom')),
        opacity=map_opacity,
        tooltip=[alt.Tooltip('Name:N'), alt.Tooltip('Region:N'), alt.Tooltip('Gdp_String:N', title='GDP')]
    )
    .add_params(select_country, select_region)
    .transform_filter(select_region)
)
final_map = (basemap + map_layer).project('equalEarth').properties(
    width=MAP_WIDTH, height=MAP_HEIGHT,
    title={
    "text": "Global GDP Distribution",
    "fontSize": 16,
    "fontWeight": "bold"
}
)


# Legend
legend = alt.Chart(df).mark_point(size=100, filled=True).encode(
    y=alt.Y('Region:N', axis=alt.Axis(orient='right', title='Filter by Region'), sort=None),
    color=alt.Color('Region:N', scale=region_scale, legend=None),
    shape=alt.Shape('Region:N', legend=None)
).add_params(select_region).properties(
    title={
        "text": "Regions",
        "fontSize": 14,
        "fontWeight": "bold"
    },
    width=50,
    height=MAP_HEIGHT
)

# Base Chart
base_scatter = alt.Chart(df).encode(
    x=alt.X('GDP:Q', scale=alt.Scale(type="log"), title='GDP (Log Scale)'),
    y=alt.Y('Population:Q', scale=alt.Scale(type="log"), title='Population (Log Scale)')
)

# The Points
points = base_scatter.mark_point(filled=True).transform_calculate(
    Population_String="format(datum['Population'], ',.0f') + ' M'"
).encode(
    color=color_cond_scatter,
    size=size_scatter,
    opacity=opacity_cond_scatter,
    shape=alt.Shape('Region:N', legend=None),
    tooltip=[
        alt.Tooltip('Name:N'),
        alt.Tooltip('GDP:Q', format='$,.0f'),
        alt.Tooltip('Population_String:N', title='Population')
    ]
)

# The Regression Line
trend_line = base_scatter.transform_regression(
    'GDP', 'Population',
    method='pow'
).mark_line(
    color='black',
    strokeDash=[5,5],
    size=2
)

# Combine
view2 = (
    (points + trend_line)
    .add_params(select_country, select_region)
    .transform_filter(select_region)
    .properties(
        width=SCATTER_WIDTH,
        height=SCATTER_HEIGHT,
        title={"text": "Economic Size vs Population", "fontSize": 16}
    )
)




# VIEW 3: SCATTER PLOT 2


base_stability = alt.Chart(df).encode(
    x=alt.X('Interest Rate:Q', scale=alt.Scale(type='symlog'), title='Interest Rate (Symlog scale)'),
    y=alt.Y('Inflation Rate:Q', scale=alt.Scale(type='symlog'), title='Inflation Rate (Symlog scale)')
)


points_stability = base_stability.mark_point(filled=True).transform_calculate(
    Interest_String="format(datum['Interest Rate'], '.2f') + '%'",
    Inflation_String="format(datum['Inflation Rate'], '.2f') + '%'"
).encode(
    color=color_cond_scatter,
    size=size_scatter,
    opacity=opacity_cond_scatter,
    shape=alt.Shape('Region:N', legend=None),
    tooltip=[
        alt.Tooltip('Name:N'),
        alt.Tooltip('Interest_String:N', title='Interest Rate'),
        alt.Tooltip('Inflation_String:N', title='Inflation Rate')
    ]
)


line_stability = base_stability.transform_regression(
    'Interest Rate', 'Inflation Rate',
    method='linear'
).mark_line(
    color='black',
    strokeDash=[5,5],
    size=2,
    opacity=0.8
)


view3 = (
    (points_stability + line_stability)
    .add_params(select_country, select_region)
    .transform_filter(select_region)
    .properties(
        width=SCATTER_WIDTH, height=SCATTER_HEIGHT,
        title={"text": "Interest Rate vs Inflation Rate", "fontSize": 16}
    )
)




# VIEW 4: BAR CHART
view4 = (
    alt.Chart(df)
    .mark_bar()
    .transform_calculate(
        GdpGrowth_String="format(datum['GDP Growth'], '.2f') + '%'"
    )
    .transform_filter(select_region)
    .transform_window(
        rank='rank()',
        sort=[alt.SortField('GDP Growth', order='descending')]
    )
    .transform_filter(
        alt.datum.rank <= 20
    )
    .encode(
        x=alt.X('GDP Growth:Q', title='Annual GDP Growth (%)'),
        y=alt.Y('Name:N', sort='-x', title=None, axis=alt.Axis(labelLimit=180)),
        opacity=alt.condition(select_country, alt.value(1), alt.value(0.2)),
        color=alt.condition(
            select_country,
            alt.Color('Region:N', scale=region_scale, legend=None),
            alt.value('lightgray')
        ),
        tooltip=[alt.Tooltip('Name:N'), alt.Tooltip('GdpGrowth_String:N', title='GDP Growth')]
    )
    .add_params(select_country)
    .properties(
        width=BAR_WIDTH,
        height=MAP_HEIGHT,
        title={
            "text": "Top 20 Countries by GDP Growth",
            "fontSize": 16
        }
    )
)








spacer_vertical = alt.Chart(pd.DataFrame({'x': [0]})).mark_text(text='').properties(width=1, height=40)



# Top Row: Map + Bar Chart
top_row = alt.hconcat(
    final_map,
    view4,
    spacing=10  # Gap between Map and Bar
)

# Bottom Row: Spacer + Scatter 1 + Scatter 2 + Legend

bottom_row = alt.hconcat(
    view2,
    view3,
    legend,
    spacing=50  # Gap between Scatter plots
)

# 3. Final Assembly
dashboard = alt.vconcat(
    spacer_vertical, # Space below title
    top_row,
    spacer_vertical, # Space between rows
    bottom_row
).configure_view(
    stroke=None
).configure_title(
    fontSize=20,
    anchor='middle', # Centers the main title
    font='Segoe UI'
).resolve_scale(
    color='independent'
).properties(
    title={
        "text": "Global Economic Dashboard",
        "fontSize": 24,
        "fontWeight": "bold",
        "anchor": "middle",
    }
)

dashboard.save('my_dashboard.html')


