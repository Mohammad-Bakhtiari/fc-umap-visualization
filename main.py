import json
from math import pi

from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

import numpy as np
from numpy import pi, sin, cos
from plotly.tools import DEFAULT_PLOTLY_COLORS
from sklearn.datasets import load_iris
from sklearn.decomposition import PCA

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__, external_stylesheets=external_stylesheets)

styles = {
    'pre': {
        'border': 'thin lightgrey solid',
        'overflowX': 'scroll'
    }
}

app.layout = html.Div([
    html.H1('Visualization App'),
    dcc.Tabs(id="tabs-ct", value='tab-confounders', children=[
        dcc.Tab(label='Confounders', value='tab-confounders'),
        dcc.Tab(label='Distances', value='tab-distances'),
        dcc.Tab(label='Clustering Quality', value='tab-clustering-quality'),
        dcc.Tab(label='Scree plot', value='tab-scree-plot'),
        # dcc.Tab(label='Scatter plot', value='tab-scatter-plot'),
    ]),
    html.Div(id='tabs-content-ct')
])

local_data_df = pd.read_csv("data/localData_.csv", delimiter=";", skiprows=0, index_col=0)
distance_df = pd.read_csv("data/distanceMatrix.csv", delimiter=" ", skiprows=0, index_col=0)


@app.callback(Output('tabs-content-ct', 'children'),
              Input('tabs-ct', 'value'))
def render_content(tab):
    if tab == 'tab-confounders':
        return renderConfounders()
    elif tab == 'tab-distances':
        return renderDistances()
    elif tab == 'tab-clustering-quality':
        return renderClusteringQuality()
    elif tab == 'tab-scree-plot':
        return renderScreePlot()
    elif tab == 'tab-scatter-plot':
        return renderScatterPlot()


def renderConfounders():
    return html.Div([
        html.P("K:"),
        dcc.Dropdown([2, 3], 2, id='k-confounders'),
        dcc.Graph(
            id='confounders-scatter',
        ),
    ])


@app.callback(
    Output('confounders-scatter', 'figure'),
    Input('k-confounders', 'value'))
def filter_k_confounders(value):
    confounding_df = pd.read_csv(f'data/all_confounders_{value}.csv', delimiter=",", skiprows=0)
    cluster_values_list = confounding_df.cluster.unique()
    fig = go.Figure()
    for i in cluster_values_list:
        color = DEFAULT_PLOTLY_COLORS[i]
        fig.add_trace(
            go.Scatter(
                x=confounding_df[confounding_df['cluster'] == i]['x'],
                y=confounding_df[confounding_df['cluster'] == i]['y'],
                mode='markers',
                name=f'Cluster {i}',
                marker={
                    "size": 10,
                    "color": color,
                }
            )
        )
        path = confidence_ellipse(confounding_df[confounding_df['cluster'] == i]['x'],
                                  confounding_df[confounding_df['cluster'] == i]['y'])
        fig.add_shape(
            type='path',
            path=path,
            line={'dash': 'dot'},
            line_color=color,
            fillcolor=color,
            opacity=0.2
        )

    fig.update_layout(
        title="Confounders",
        showlegend=True,
        legend={
            "title": "Clusters",
        },
    )
    return fig


def renderDistances():
    return html.Div([
        html.P("Labels included:"),
        dcc.Dropdown(
            id='labels',
            options=[{'label': x, 'value': x}
                     for x in distance_df.columns],
            value=distance_df.columns.tolist(),
            multi=True,
        ),
        dcc.Graph(id="distance_graph"),
    ])


@app.callback(
    Output("distance_graph", "figure"),
    [Input("labels", "value")])
def filter_heatmap(cols):
    data = {
        'z': distance_df[cols].values.tolist(),
        'x': distance_df[cols].columns.tolist(),
        'y': distance_df[cols].index.tolist()
    }
    layout = go.Layout(
        title='Distance matrix',
    )
    fig = go.Figure(data=go.Heatmap(data), layout=layout)
    return fig


def renderClusteringQuality():
    return html.Div([
        html.P("K:"),
        dcc.Dropdown([2, 3], 2, id='k-labels'),
        dcc.Graph(id="cluster_quality_graph"),
    ])


@app.callback(
    Output('cluster_quality_graph', 'figure'),
    Input('k-labels', 'value'))
def filter_k_label(value):
    df_silhouette = pd.read_csv(f'data/results/K_{str(value)}/silhouette.csv', delimiter=';')
    df_silhouette = df_silhouette.sort_values(["cluster", "y"], ascending=(True, False)).reset_index()
    avg_value = "{:.2f}".format(df_silhouette['y'].mean())
    cluster_values_list = df_silhouette.cluster.unique()

    fig = go.Figure()
    for i in cluster_values_list:
        fig.add_trace(
            go.Bar(
                y=df_silhouette[df_silhouette['cluster'] == i]['y'],
                x=df_silhouette[df_silhouette['cluster'] == i].index,
                name=f'Cluster {i}',
                marker={
                    "line": {
                        "width": 0,
                    },
                }
            )
        )
    # Add avg line on top
    fig.add_shape(
        type="line",
        x0=0, y0=avg_value, x1=df_silhouette['x'].max(), y1=avg_value,
        line=dict(
            color="Red",
            width=2,
            dash="dashdot",
        )
    )
    fig.update_layout(
        title=f'Clusters silhouette plot<br>Average silhouette width: {str(avg_value)}',
        xaxis={
            "title": "",
            "showticklabels": False,
        },
        yaxis={"title": "Silhouette width Si"},
        bargap=0.0,
        showlegend=True,
        legend={
            "title": "Clusters",
        },
    )
    return fig


def renderScreePlot():
    return html.H1("Scree plot")


def renderScatterPlot():
    df = pd.DataFrame({
        "x": [1, 2, 1, 2],
        "y": [1, 2, 3, 4],
        "customdata": [1, 2, 3, 4],
        "fruit": ["apple", "apple", "orange", "orange"]
    })

    fig = px.scatter(df, x="x", y="y", color="fruit", custom_data=["customdata"])

    fig.update_layout(clickmode='event+select')

    fig.update_traces(marker_size=20)

    return html.Div([
        dcc.Graph(
            id='basic-interactions',
            figure=fig
        ),

        html.Div(className='row', children=[
            html.Div([
                dcc.Markdown("""
                    **Hover Data**

                    Mouse over values in the graph.
                """),
                html.Pre(id='hover-data', style=styles['pre'])
            ], className='three columns'),

            html.Div([
                dcc.Markdown("""
                    **Click Data**

                    Click on points in the graph.
                """),
                html.Pre(id='click-data', style=styles['pre']),
            ], className='three columns'),

            html.Div([
                dcc.Markdown("""
                    **Selection Data**

                    Choose the lasso or rectangle tool in the graph's menu
                    bar and then select points in the graph.

                    Note that if `layout.clickmode = 'event+select'`, selection data also
                    accumulates (or un-accumulates) selected data if you hold down the shift
                    button while clicking.
                """),
                html.Pre(id='selected-data', style=styles['pre']),
            ], className='three columns'),

            html.Div([
                dcc.Markdown("""
                    **Zoom and Relayout Data**

                    Click and drag on the graph to zoom or click on the zoom
                    buttons in the graph's menu bar.
                    Clicking on legend items will also fire
                    this event.
                """),
                html.Pre(id='relayout-data', style=styles['pre']),
            ], className='three columns')
        ])
    ])


@app.callback(
    Output('hover-data', 'children'),
    Input('basic-interactions', 'hoverData'))
def display_hover_data(hoverData):
    return json.dumps(hoverData, indent=2)


@app.callback(
    Output('click-data', 'children'),
    Input('basic-interactions', 'clickData'))
def display_click_data(clickData):
    return json.dumps(clickData, indent=2)


@app.callback(
    Output('selected-data', 'children'),
    Input('basic-interactions', 'selectedData'))
def display_selected_data(selectedData):
    return json.dumps(selectedData, indent=2)


@app.callback(
    Output('relayout-data', 'children'),
    Input('basic-interactions', 'relayoutData'))
def display_relayout_data(relayoutData):
    return json.dumps(relayoutData, indent=2)


def confidence_ellipse(x, y, n_std=1.96, size=100):
    """
        Get the covariance confidence ellipse of *x* and *y*.
        Parameters
        ----------
        x, y : array-like, shape (n, )
            Input data.
        n_std : float
            The number of standard deviations to determine the ellipse's radiuses.
        size : int
            Number of points defining the ellipse
        Returns
        -------
        String containing an SVG path for the ellipse

        References (H/T)
        ----------------
        https://matplotlib.org/3.1.1/gallery/statistics/confidence_ellipse.html
        https://community.plotly.com/t/arc-shape-with-path/7205/5
        """
    if x.size != y.size:
        raise ValueError("x and y must be the same size")

    cov = np.cov(x, y)
    pearson = cov[0, 1] / np.sqrt(cov[0, 0] * cov[1, 1])
    # Using a special case to obtain the eigenvalues of this
    # two-dimensional dataset.
    ell_radius_x = np.sqrt(1 + pearson)
    ell_radius_y = np.sqrt(1 - pearson)
    theta = np.linspace(0, 2 * np.pi, size)
    ellipse_coords = np.column_stack([ell_radius_x * np.cos(theta), ell_radius_y * np.sin(theta)])

    # Calculating the stdandard deviation of x from
    # the squareroot of the variance and multiplying
    # with the given number of standard deviations.
    x_scale = np.sqrt(cov[0, 0]) * n_std
    x_mean = np.mean(x)

    # calculating the stdandard deviation of y ...
    y_scale = np.sqrt(cov[1, 1]) * n_std
    y_mean = np.mean(y)

    translation_matrix = np.tile([x_mean, y_mean], (ellipse_coords.shape[0], 1))
    rotation_matrix = np.array([[np.cos(np.pi / 4), np.sin(np.pi / 4)],
                                [-np.sin(np.pi / 4), np.cos(np.pi / 4)]])
    scale_matrix = np.array([[x_scale, 0],
                             [0, y_scale]])
    ellipse_coords = ellipse_coords.dot(rotation_matrix).dot(scale_matrix) + translation_matrix

    path = f'M {ellipse_coords[0, 0]}, {ellipse_coords[0, 1]}'
    for k in range(1, len(ellipse_coords)):
        path += f'L{ellipse_coords[k, 0]}, {ellipse_coords[k, 1]}'
    path += ' Z'
    return path


if __name__ == '__main__':
    app.run_server(debug=True)
