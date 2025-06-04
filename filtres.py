# IMPORTS OPTIMISÉS
import dash
from dash import dcc, html, dash_table, Input, Output, callback
import pandas as pd
import plotly.express as px
from datetime import datetime

# CHARGEMENT DES DONNÉES (OPTIMISÉ)
df = pd.read_csv("transactions_analysees_anomalies.csv", parse_dates=['Date'])
df_filtered = df[df['anomaly'] == 1].copy()  # Pré-filtrage

# INITIALISATION DE L'APP (AVEC CACHE)
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "Filtre avancée de détection d'anomalies"

# STYLE PERSONNALISÉ
styles = {
    'filter-box': {
        'border': '1px solid #ddd',
        'borderRadius': '5px',
        'padding': '15px',
        'margin': '10px',
        'backgroundColor': '#f9f9f9'
    },
    'filter-row': {
        'display': 'flex',
        'justifyContent': 'space-between',
        'marginBottom': '15px'
    },
    'filter-col': {
        'width': '48%',
        'display': 'inline-block'
    },
    'slider-container': {
        'padding': '20px 10px'
    }
}

# LAYOUT AMÉLIORÉ
app.layout = html.Div([
    html.H1("Détection des anomalies financières", style={'textAlign': 'center', 'color': '#2c3e50'}),
    
    # SECTION FILTRES
    html.Div([
        html.Div([
            # PREMIÈRE LIGNE DE FILTRES
            html.Div([
                html.Div([
                    html.Label("Pays d'origine", style={'fontWeight': 'bold'}),
                    dcc.Dropdown(
                        id="filtre_pays_origine",
                        options=[{'label': 'Tous', 'value': 'all'}] + 
                                [{"label": p, "value": p} for p in sorted(df["Pays_Origine"].unique())],
                        multi=True,
                        placeholder="Sélectionnez...",
                        style={'marginTop': '5px'}
                    )
                ], style=styles['filter-col']),
                
                html.Div([
                    html.Label("Pays de destination", style={'fontWeight': 'bold'}),
                    dcc.Dropdown(
                        id="filtre_pays_destination",
                        options=[{'label': 'Tous', 'value': 'all'}] + 
                                [{"label": p, "value": p} for p in sorted(df["Pays_Destination"].unique())],
                        multi=True,
                        placeholder="Sélectionnez...",
                        style={'marginTop': '5px'}
                    )
                ], style=styles['filter-col'])
            ], style=styles['filter-row']),
            
            # SLIDER MONTANT
            html.Div([
                html.Label("Plage de montant", style={'fontWeight': 'bold'}),
                dcc.RangeSlider(
                    id="filtre_montant",
                    min=df['Montant'].min(),
                    max=df['Montant'].max(),
                    step=10,
                    value=[df['Montant'].min(), df['Montant'].max()],
                    marks={int(df['Montant'].min()): str(int(df['Montant'].min())),
                           int(df['Montant'].max()): str(int(df['Montant'].max()))},
                    tooltip={"placement": "bottom", "always_visible": False}
                )
            ], style=styles['slider-container']),
            
            # DATE PICKER
            html.Div([
                html.Label("Plage de dates", style={'fontWeight': 'bold'}),
                dcc.DatePickerRange(
                    id="filtre_date",
                    start_date=df["Date"].min(),
                    end_date=df["Date"].max(),
                    min_date_allowed=df["Date"].min(),
                    max_date_allowed=df["Date"].max(),
                    display_format='YYYY-MM-DD',
                    style={'marginTop': '5px'}
                )
            ], style={'marginBottom': '15px'}),
            
            # SLIDER SCORE ANOMALIE
            html.Div([
                html.Label("Score d'anomalie", style={'fontWeight': 'bold'}),
                dcc.RangeSlider(
                    id='filtre_score',
                    min=0,
                    max=1,
                    step=0.01,
                    value=[0, 1],
                    marks={0: '0', 0.5: '0.5', 1: '1'},
                    tooltip={"placement": "bottom", "always_visible": False}
                )
            ], style=styles['slider-container']),
            
            # RECHERCHE NOM
            html.Div([
                html.Label("Recherche par nom", style={'fontWeight': 'bold'}),
                dcc.Input(
                    id="filtre_nom",
                    type="text",
                    placeholder="Entrez un nom...",
                    debounce=True,
                    style={
                        'width': '100%',
                        'padding': '8px',
                        'borderRadius': '4px',
                        'border': '1px solid #ddd'
                    }
                )
            ])
        ], style=styles['filter-box'])
    ]),
    
    # VISUALISATION
    dcc.Loading(
        id="loading-graph",
        type="circle",
        children=[
            dcc.Graph(
                id="histogramme_anomalie",
                style={'height': '400px'}
            )
        ]
    ),
    
    # TABLEAU
    html.H2("Transactions suspectes", style={'marginTop': '30px'}),
    dcc.Loading(
        id="loading-table",
        type="circle",
        children=[
            dash_table.DataTable(
                id="table_anomalies",
                columns=[{"name": col, "id": col} for col in [
                    "Date", "Nom_Emetteur", "Nom_Destinataire", "Montant",
                    "Pays_Origine", "Pays_Destination", "anomaly_score"
                ]],
                page_size=15,
                style_table={
                    'overflowX': 'auto',
                    'boxShadow': '0 0 5px #eee'
                },
                style_header={
                    'backgroundColor': '#2c3e50',
                    'color': 'white',
                    'fontWeight': 'bold'
                },
                style_cell={
                    'textAlign': 'left',
                    'padding': '10px',
                    'whiteSpace': 'normal',
                    'height': 'auto'
                },
                filter_action='native',
                sort_action='native'
            )
        ]
    )
])

# CALLBACK OPTIMISÉ
@callback(
    [Output("histogramme_anomalie", "figure"),
     Output("table_anomalies", "data")],
    [Input("filtre_pays_origine", "value"),
     Input("filtre_pays_destination", "value"),
     Input("filtre_montant", "value"),
     Input("filtre_score", "value"),
     Input("filtre_nom", "value"),
     Input("filtre_date", "start_date"),
     Input("filtre_date", "end_date")]
)
def update_dashboard(pays_origine, pays_destination, montant_range, score_range, nom_recherche, date_start, date_end):
    # Copie du DataFrame pré-filtré
    dff = df_filtered.copy()
    
    # Application des filtres
    if pays_origine and 'all' not in pays_origine:
        dff = dff[dff["Pays_Origine"].isin(pays_origine)]
    
    if pays_destination and 'all' not in pays_destination:
        dff = dff[dff["Pays_Destination"].isin(pays_destination)]
    
    dff = dff[
        (dff["Montant"] >= montant_range[0]) & 
        (dff["Montant"] <= montant_range[1])
    ]
    
    dff = dff[
        (dff["anomaly_score"] >= score_range[0]) & 
        (dff["anomaly_score"] <= score_range[1])
    ]
    
    if date_start and date_end:
        dff = dff[
            (dff["Date"] >= pd.to_datetime(date_start)) & 
            (dff["Date"] <= pd.to_datetime(date_end))
        ]
    
    if nom_recherche:
        nom = nom_recherche.lower()
        dff = dff[
            dff["Nom_Emetteur"].str.lower().str.contains(nom, na=False) |
            dff["Nom_Destinataire"].str.lower().str.contains(nom, na=False)
        ]
    
    # Création du graphique
    fig = px.histogram(
        dff,
        x="anomaly_score",
        nbins=30,
        title="Distribution des scores d'anomalie",
        labels={"anomaly_score": "Score d'anomalie"},
        color_discrete_sequence=['#e74c3c']
    )
    
    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='#f9f9f9',
        margin={'t': 40}
    )
    
    return fig, dff.to_dict('records')

# LANCEMENT
if __name__ == '__main__':
	app.run(debug=True, port=8051)
