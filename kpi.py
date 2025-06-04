from dash import Dash, html, dcc
import dash_bootstrap_components as dbc

# Création de l'application
app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

# Contenu de chaque dashboard
dashboard_data = {
    "Vue Générale des Transactions": [
        ("Montant Total", "Total cumulé des montants transférés"),
        ("Nombre de transactions", "Nombre total de lignes de transaction"),
        ("Montant Moyen", "Moyenne des montants"),
        ("Taux de réussite", "Pourcentage des transactions réussies")
    ],
    "Analyse par Agence": [
        ("Montant Émis", "Total des montants envoyés par les agences émettrices"),
        ("Nombre total de transactions", "Nombre de toutes les transactions (émises + reçues)"),
        ("Transactions Réussies", "Nombre de transactions avec le statut 'Réussie'"),
        ("Transactions reçues", "Nombre de transactions reçues par les agences destinataires")
    ],
    "Analyse des Gros Transferts": [
        ("Total Gros Transferts", "Nombre de transactions supérieures à 10M"),
        ("Montant Total des Gros Transferts", "Somme de tous les montants > 10M"),
        ("Montant annuel des Gros Transferts", "Montant total des gros transferts par an"),
        ("Montant Émis - Gros Transferts", "Total des montants envoyés supérieurs au seuil"),
        ("Montant Reçu - Gros Transferts", "Montant total des gros transferts reçus")
    ]
}

# Fonction pour générer une carte KPI + description
def generate_dashboard(kpi_list):
    return dbc.Container([
        dbc.Row([
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader(kpi),
                    dbc.CardBody(html.P(description, className="card-text"))
                ], className="mb-4 shadow-sm", style={"minHeight": "120px"}),
                width=6
            ) for kpi, description in kpi_list
        ])
    ], fluid=True)

# Layout avec onglets
app.layout = dbc.Container([
    html.H2("Indicateurs Clés de Performance", className="my-4 text-center"),
    dcc.Tabs([
        dcc.Tab(label=dashboard, children=[generate_dashboard(kpis)])
        for dashboard, kpis in dashboard_data.items()
    ])
], fluid=True)

# Lancement de l'application
if __name__ == '__main__':
    app.run(debug=True, port=8052)
