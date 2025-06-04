
# IMPORTS
import dash
from dash import dcc, html, dash_table, Input, Output
import pandas as pd
import plotly.express as px

# CHARGEMENT DES DONNÉES
df = pd.read_csv("transactions_analysees_anomalies.csv")

# INITIALISATION DE L'APPLICATION
app = dash.Dash(__name__)
app.title = "Détection d'anomalies - Transactions Bancaires"

# LAYOUT DU TABLEAU DE BORD
app.layout = html.Div([
    html.H1("Analyse des anomalies dans les transactions bancaires", style={'textAlign': 'center'}),

    html.Div([
        html.Div([
            html.H3("Nombre total de transactions :"),
            html.P(f"{len(df):,}")
        ], style={'width': '48%', 'display': 'inline-block'}),

        html.Div([
            html.H3("Nombre d'anomalies détectées :"),
            html.P(f"{df['anomaly'].sum():,}")
        ], style={'width': '48%', 'display': 'inline-block'})
    ], style={'padding': '20px'}),

    html.Hr(),

    html.Div([
        html.Label("Filtrer par pays d'origine :"),
        dcc.Dropdown(
            options=[{"label": p, "value": p} for p in sorted(df["Pays_Origine"].unique())],
            id="filtre_pays_origine",
            placeholder="Choisir un pays",
            multi=False
        ),

        html.Label("Filtrer par pays de destination :"),
        dcc.Dropdown(
            options=[{"label": p, "value": p} for p in sorted(df["Pays_Destination"].unique())],
            id="filtre_pays_destination",
            placeholder="Choisir un pays",
            multi=False
        ),

        html.Br(),
        html.Label("Seuil de score d’anomalie (max) :"),
        dcc.Slider(
            id='slider_score',
            min=df['anomaly_score'].min(),
            max=df['anomaly_score'].max(),
            value=df['anomaly_score'].min(),
            step=0.001,
            marks=None,
            tooltip={"placement": "bottom", "always_visible": True}
        )
    ], style={'padding': '20px'}),

    html.Hr(),

    dcc.Graph(id="histogramme_anomalie"),

    html.Hr(),

    html.H2("Transactions suspectes", style={'textAlign': 'center'}),
    dash_table.DataTable(
        id="table_anomalies",
        columns=[{"name": col, "id": col} for col in [
            "Date", "Nom_Emetteur", "Nom_Destinataire", "Montant",
            "Pays_Origine", "Pays_Destination", "anomaly_score"
        ]],
        page_size=10,
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left'},
    )
])

# CALLBACK POUR METTRE À JOUR LE TABLEAU DE BORD
@app.callback(
    [Output("histogramme_anomalie", "figure"),
     Output("table_anomalies", "data")],
    [Input("filtre_pays_origine", "value"),
     Input("filtre_pays_destination", "value"),
     Input("slider_score", "value")]
)
def update_dashboard(pays_origine, pays_destination, score_max):
    filtered_df = df[df["anomaly"] == 1]
    filtered_df = filtered_df[filtered_df["anomaly_score"] <= score_max]

    if pays_origine:
        filtered_df = filtered_df[filtered_df["Pays_Origine"] == pays_origine]
    if pays_destination:
        filtered_df = filtered_df[filtered_df["Pays_Destination"] == pays_destination]

    fig = px.histogram(filtered_df, x="anomaly_score", nbins=50,
                       title="Distribution des scores d’anomalie",
                       labels={"anomaly_score": "Score d’anomalie"})

    return fig, filtered_df.to_dict("records")

# LANCEMENT DE L'APPLICATION
if __name__ == '__main__':
    app.run(debug=True)

