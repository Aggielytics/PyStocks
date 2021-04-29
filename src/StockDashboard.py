# Before running this app, install the following
# pip install dash
# pip install dash-bootstrap-components

import dash  # pip install dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
import yfinance as yf
import pandas as pd
from stocks import Stocks
from NewsSentiment import StockNews

myStocks = Stocks()
PLOTLY_LOGO = "https://images.plot.ly/logo/new-branding/plotly-logomark.png"

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY], meta_tags=[
    {"name": "viewport", "content": "width=device-width, initial-scale-1.0"}])


def make_table(dfTable):
    table = dbc.Table.from_dataframe(dfTable, striped=True, bordered=True, responsive=True, hover=True)
    return table


def get_qtr_earnings(ticker):
    dfEr = ticker.quarterly_earnings
    dfEr.reset_index(inplace=True)
    dfEr["Revenue"] = dfEr['Revenue'].apply(lambda x: "${:,.0f} M".format((x / 1000_000)))
    dfEr["Earnings"] = dfEr['Earnings'].apply(lambda x: "${:,.0f} M".format((x / 1000_000)))
    dfEr.sort_index(ascending=False, inplace=True)
    return make_table(dfEr)


def get_analyst_Table(ticker):
    dfr = ticker.recommendations
    dfr.dropna(inplace=True)
    dfr.sort_index(ascending=False, inplace=True)
    dfr = dfr.head(4)
    dfr = dfr[["Firm", "To Grade"]]
    dfr.columns = ["Firm", "Rating"]
    dfr["Date"] = dfr.index
    dfr["Date"] = dfr["Date"].dt.strftime('%m/%d/%Y')
    return make_table(dfr)


def make_news_card(article):
    newsCard = dbc.Card(dbc.CardBody([
        html.H4(article.title, className="card-title"),
        html.P(article.description, className="card-text"),
        dbc.CardLink("View", href=article.url, target="_blank")
    ]), color="light", outline=True, className="w-100 mt-2")
    return newsCard


def get_news_rows(df):
    articles = []
    for row in range(df.shape[0]):
        row = dbc.Row(children=[make_news_card(df.iloc[row])], className="mt-2")
        articles.append(row)

    return articles


def make_card(header, color, info):
    card = dbc.Card(children=[
        dbc.CardHeader(header),
        dbc.CardBody(html.P(info, className="card-text")),
    ], color=color, inverse=True)
    return card


def make_graph_card(openPrice, prevClosePrice, header):
    openfig = go.Figure(go.Indicator(
        mode="number+delta",
        value=openPrice,
        number={'prefix': "$"},
        delta={'position': "top", 'reference': prevClosePrice},
        domain={'x': [0, 1], 'y': [0, 1]},
    ))

    # Create Card with figure
    card = dbc.Card(children=[
        # dbc.CardHeader(header),
        dbc.CardBody(children=[
            html.Div(dcc.Graph(figure=openfig))
        ])
    ])

    return card


def get_stockCards(ticker):
    prevClose = ticker.info['previousClose']
    openPrice = ticker.info['open']
    #print(f"open: {openPrice} close: {prevClose}")
    if prevClose > openPrice:
        priceColor = 'danger'
    else:
        priceColor = "success"
    cards = [
        make_card("Previous Close ", "primary", prevClose),
        make_card("Open", priceColor, openPrice),
        # make_graph_card(openPrice, prevClose, "Today's Open"),
        make_card("Sector", 'secondary', ticker.info['sector']),
        make_card("50d Avg Price", 'info', ticker.info['fiftyDayAverage']),
        make_card("Avg 10d Vol", 'warning', ticker.info['averageVolume10days'])
    ]
    return cards


def createStockTimeline(dfHistoryMax):
    df = dfHistoryMax
    # Reseting the index
    df = df.reset_index()
    df.rename(columns={'index': 'Date'}, inplace=True)
    # Converting the datatype to float
    for i in ['Open', 'High', 'Close', 'Low', "Volume"]:
        df[i] = df[i].astype('float64')

    fig = go.Figure(go.Scatter(x=df['Date'], y=df['High'], mode='lines', line=dict(color='#2B3C4D', width=1)))
    fig.update_xaxes(rangeslider_visible=True, rangeselector=dict(
        buttons=list([
            dict(count=1, label="1m", step="month", stepmode="backward"),
            dict(count=6, label="6m", step="month", stepmode="backward"),
            dict(count=1, label="YTD", step="year", stepmode="todate"),
            dict(count=1, label="1y", step="year", stepmode="backward"),
            dict(step="all")
        ])
    ), type="date"
                     )
    fig.update_layout(
        dragmode="zoom",
        title='Stock Price',
        title_font_size=22,
        title_x=.5,
        hovermode="x unified",
        legend=dict(traceorder="reversed"),
        template="plotly_white",
        height=400,
        margin=dict(
            t=50,
            b=50
        ),
    )

    figVol = go.Figure([go.Scatter(x=df['Date'], y=df['Volume'], mode='lines', line=dict(color='#F39C12', width=1))])
    figVol.update_xaxes(rangeslider_visible=True, rangeselector=dict(
        buttons=list([
            dict(count=1, label="1m", step="month", stepmode="backward"),
            dict(count=6, label="6m", step="month", stepmode="backward"),
            dict(count=1, label="YTD", step="year", stepmode="todate"),
            dict(count=1, label="1y", step="year", stepmode="backward"),
            dict(step="all")
        ])
    ), type="date"
                        )
    figVol.update_layout(
        dragmode="zoom",
        title='Stock Volume',
        title_font_size=22,
        title_x=.5,
        hovermode="x unified",
        legend=dict(traceorder="reversed"),
        template="plotly_white",
        height=250,
        margin=dict(
            t=50,
            b=50
        ),
    )
    return fig, figVol


search_bar = dbc.Row(
    [
        dbc.Col(dbc.Input(type="search", placeholder="Search Symbol", id="search_input")),
        dbc.Col(
            dbc.Button("Search", color="primary", className="ml-2", id="searchbtn"),
            width="auto",
        ),
    ],
    no_gutters=True,
    className="ml-auto flex-nowrap mt-3 mt-md-0",
    align="center",
)

favorite_bar = dbc.Row(
    [
        dbc.Col(
            dcc.Dropdown("dropdown_ticker", options=myStocks.get_Stocks_html_options(), value="TSLA"),
            width="auto",
            style={"width": "100%"}
        ),
    ],
    no_gutters=True,
    className="ml-auto flex-nowrap mt-3 mt-md-0",
    align="center",
    style={"width": "30%"}
)

app.layout = html.Div([
    # Nav Bar, favorites
    html.Div([
        dbc.Navbar(
            [
                html.A(
                    # Use row and col to control vertical alignment of logo / brand
                    dbc.Row(
                        [
                            dbc.Col(html.Img(src=PLOTLY_LOGO, height="30px")),
                            dbc.Col(dbc.NavbarBrand("PyStocks", className="ml-2")),
                        ],
                        align="center",
                        no_gutters=True,
                    ),
                    href="https://plot.ly",
                ),
                dbc.NavbarToggler(id="navbar-toggler"),
                dbc.Collapse(favorite_bar, id="navbar-collapse", navbar=True),
            ],
        ),
    ]),

    # Stock search
    html.Div([
        search_bar,
    ], className="navigation mt-2"),

    # Stock low,high Cards
    html.Div([
        dbc.CardDeck(id="info-cardgroup", className="cards"),
    ], className="info-group mt-2"),

    # Stock graph
    html.Div([
        # Graphs
        dbc.Card(className="mr-1 mt-2", children=[
            dbc.CardBody([
                html.Img(id="logo", height="80px"),
                html.H4(className="card-title", id="graph-company"),
                html.Div(className='eight columns div-for-charts',
                         children=[dcc.Graph(id='graphs-stock', config={'displayModeBar': False}, animate=False)]
                         ),
                html.Div(className='eight columns div-for-charts',
                         children=[dcc.Graph(id='graphs-stock-vol', config={'displayModeBar': False}, animate=False)]
                         ),
                # dbc.Button("Volume", color="success", className="mr-1"),graphs-stock-vol
            ])
        ], outline=True),
    ]),

    # Company financials and analyst ratings
    html.Div([
        dbc.Row([
            dbc.Col([
                html.H4("Analyst Ratings"),
                html.Div(id="analyst-table"),
            ], className="buy"),
            dbc.Col([
                html.H4("Quaterly Earnings"),
                html.Div(id="earning-table"),
            ], className="earnings"),
        ])
    ], className="firm-table mt-2"),

    # company information
    html.Div([
        # company info
        dbc.Card(className="mr-1 mt-2", children=[
            dbc.CardBody(
                [
                    html.H4("Company Information", className="header card-title"),
                    html.P(id="description", className="description-ticker card-text"),
                    html.Div(children=[], id="badge-sentiment"),
                ])
        ], outline=True),
    ], className="content mt-2"),

    # News feed
    html.Div([
        dbc.Container(children=[
                dbc.Row(children=[
                html.H4("News"),
                html.Div(id="news-articles", className="news mr-1"),
            ])
        ]),
    ], className="news-feed mx-2 mt-2"),

    # hidden data-exachange-callback
    html.Div(id='intermediate-value', style={'display': 'none'}),
    # dcc.Store inside the app that stores the intermediate value
    dcc.Store(id='ticker-intermediate-value'),
], className="container mt-2")


# call back for storing Graph-Stocks
@app.callback(
    [
        Output("graphs-stock", "figure"),
        Output("graphs-stock-vol", "figure"),
    ],
    [
        Input('ticker-intermediate-value', 'data')
    ]
)
def update_volums_price_graphs(jsonified_history_data):
    # get the graph for stock
    dfHistoryMax = pd.read_json(jsonified_history_data, orient='split')
    fig, figVol = createStockTimeline(dfHistoryMax)
    return fig, figVol


# call back for content
@app.callback(
    # outputs
    [
        Output("description", "children"),
        Output("logo", "src"),
        Output("info-cardgroup", "children"),
        Output("search_input", "value"),
        Output("graph-company", "children"),
        Output("analyst-table", "children"),
        Output("earning-table", "children"),
        Output('intermediate-value', 'children'),
        Output('ticker-intermediate-value', 'data'),
    ],
    # inputs
    [
        Input("dropdown_ticker", "value"),
        Input("searchbtn", "n_clicks"),
    ],
    State('search_input', 'value'),
)
def update_data(dropDownValue, buttonClicks, searchSymbol):
    symbol = "IBM"
    if (dropDownValue == None and buttonClicks == None and searchSymbol == None):
        # prevent update for first instance
        raise PreventUpdate
    elif (dropDownValue != None and searchSymbol == None):
        symbol = dropDownValue
    elif (dropDownValue != None and searchSymbol != ""):
        symbol = searchSymbol
    elif (searchSymbol == ""):
        symbol = dropDownValue

    try:
        ticker = yf.Ticker(symbol)
        dfHistory = ticker.history(period="3y")
        storeJson = dfHistory.to_json(date_format='iso', orient='split')
        company_information = ticker.info

        # save information in dataframe
        dfStockCompleteInfo = pd.DataFrame().from_dict(company_information, orient="index").T
        dfPartial = dfStockCompleteInfo[["logo_url", "shortName", "longBusinessSummary"]]
        desc = dfPartial["longBusinessSummary"].values[0]
        logo = dfPartial["logo_url"].values[0]
        company = dfPartial["shortName"].values[0]

        cards = get_stockCards(ticker)
        atbl = get_analyst_Table(ticker)
        earn = get_qtr_earnings(ticker)

        return desc, logo, cards, "", company, atbl, earn, company, storeJson

    except:
        print("invalid symbol")
        raise PreventUpdate


# callback for News
@app.callback(
    # outputs
    [
        Output("news-articles", "children"),
        Output("badge-sentiment", "children")
    ],
    # inputs
    [
        Input("intermediate-value", "children"),
    ],
)
def update_news_artilces(company):
    news = StockNews()
    dfNews = news.getNewsArticles(company, 6, 30)
    newsCards = get_news_rows(dfNews)
    sentiment, sentimentScore = news.get_sentiment_score()
    if sentimentScore >= 0:
        color = "success"
    else:
        color = "danger"

    badge = dbc.Button([sentiment, dbc.Badge(str(sentimentScore), color="light", className="ml-1")],color=color,)
    return newsCards, badge


# add callback for toggling the collapse on small screens
@app.callback(
    Output("navbar-collapse", "is_open"),
    [Input("navbar-toggler", "n_clicks")],
    [State("navbar-collapse", "is_open")],
)
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open


if __name__ == "__main__":
    app.run_server(debug=False, host='0.0.0.0', port=8080)
    # app.run_server(debug=True)
