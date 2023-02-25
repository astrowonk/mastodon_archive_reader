import dash_bootstrap_components as dbc

from dash import Dash, dcc, html, callback_context
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import datetime
import pandas as pd
import sqlite3
from utils import escape_fts
from functools import partial

from pathlib import Path

try:
    from config import archive_dir
except ImportError:
    archive_dir = 'assets'


def my_escape_fts(search):
    search = search.replace("‘", "'").replace("’", "'")
    search = search.replace('“', '"').replace('”', '"')
    if '"' in search or "'" in search:
        return escape_fts(search)
    else:
        return search


def process_bold(x, search=""):
    search = search.replace('"', '')
    idx = x.lower().find(search.lower())
    if idx != -1:
        return ''.join([
            x[0:idx], '**', x[idx:idx + len(search)], '**',
            x[idx + len(search):]
        ])
    return x


parent_dir = Path().absolute().stem
url_base_path_name = f"/dash/{parent_dir}/"

STYLE = {"marginBottom": 20, "marginTop": 20, 'width': '85%'}
STYLE_BANNER = {
    "marginBottom": 20,
    "marginTop": 20,
    'width': '85%',
    'display': 'inline-block',
    'text-align': 'center',
}

with open("about.md", "r") as myfile:
    about_markdown = myfile.read()

app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.COSMO, dbc.icons.BOOTSTRAP],
    url_base_pathname=url_base_path_name,
    title="Mastodon Archive Search",
    suppress_callback_exceptions=True,
    assets_folder=archive_dir,
)
server = app.server
button_class = 'me-1'

main_tab = dbc.Tab([
    dbc.InputGroup([
        dbc.InputGroupText(
            html.I(className="bi bi-search", style={'float': 'left'})),
        dbc.Input(
            id='search-input',
            value='',
            debounce=True,
            placeholder='Full Text Search. For exact phrase use double quotes',
        ),
        dbc.Button("Search")
    ]),
    html.Hr(),
    dbc.InputGroup([
        dbc.InputGroupText(
            html.I(className="bi bi-search", style={'float': 'left'})),
        dbc.Textarea(
            id='sql-input',
            value='',
            persistence=True,
            debounce=True,
            placeholder=
            'Full Database SQL Search, best to query or join with full_data for all fields.',
        ),
        dbc.Button("Run SQL")
    ]),
    dbc.Spinner(html.Div(id='output')),
],
                   label="Reader",
                   tab_id='reader-tab')

settings_tab = dbc.Tab(label="Settings", style=STYLE)
about_tab = dbc.Tab(dcc.Markdown(about_markdown), label="About", style=STYLE)

app.layout = dbc.Container(
    dbc.Tabs(
        [
            main_tab,
            # settings_tab,
            about_tab,
        ],
        active_tab='reader-tab'),
    style=STYLE)


def make_card(row, host):
    myurl = f"{host}/authorize_interaction?uri={row['object_url']}"
    current_tz = datetime.datetime.now().astimezone().tzinfo
    #  row['date'] = pd.to_datetime(row['object_published'])
    mydate = pd.to_datetime(row['object_published']).astimezone(
        current_tz).strftime("%b %-d, %Y %-I:%M%p")

    card_content = [
        dbc.CardHeader([
            html.Div([
                dcc.Markdown(f"Score {row['score']:.2f}, Date: {mydate}"),
            ], )
        ]),
        dbc.CardBody([
            #  html.H5(row['title'], className="card-title"),
            dcc.Markdown(row['markdown_content'], className="card-text"),
            dbc.CardLink("Permalink", href=row['object_url'], target='_blank')
        ]),
    ]
    if the_urls := row['attachment_urls']:
        for url in the_urls.split(','):
            card_content.append(
                dbc.CardImg(src=app.get_asset_url(url[1:]),
                            top=True,
                            style={
                                'height': '15vw',
                                'width': '100%',
                                'object-fit': 'scale-down'
                            }))

    return dbc.Card(card_content,
                    style={
                        'margin-bottom': '2em',
                    },
                    className="w-85 mb-3")


@app.callback(Output('output', 'children'), Input('search-input', 'value'),
              Input('sql-input', 'value'))
def update_output(search, sql):
    """Gets the data from local storage and actually makes the web site"""

    thecontext = callback_context.triggered[0]['prop_id'].split('.')[0]
    print(thecontext)

    if thecontext == 'search-input' and search:
        with sqlite3.connect('main.db') as con:
            df = pd.read_sql(
                f"select bm25(search_data) as score, text_content,fd.* from search_data sd left join full_data fd on fd.int_id = sd.int_id where text_content match ? order by score ",
                con=con,
                params=[
                    my_escape_fts(search),
                ])
    elif thecontext == 'sql-input' and sql:
        with sqlite3.connect('file:main.db?mode=ro', uri=True) as con:
            df = pd.read_sql(sql, con=con)
            df['score'] = 0

    if not (search or sql):
        raise PreventUpdate

    if df.empty:
        return html.H4("No Results", style=STYLE)

    myprocessbold = partial(process_bold, search=search)
    df['markdown_content'] = df['markdown_content'].map(myprocessbold)
    api_base_url = f"https://vmst.io"

    mydata = df.to_dict('records')

    return dbc.Container(
        [dbc.Row([dbc.Col(make_card(x, api_base_url))]) for x in mydata],
        style=STYLE)


if __name__ == "__main__":
    app.run_server(debug=True)
