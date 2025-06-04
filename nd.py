import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import base64
import io
from datetime import datetime
from dash.exceptions import PreventUpdate

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
app.title = "Analyse Universelle de Transferts Bancaires"

# Layout avec configuration flexible
app.layout = dbc.Container([
    dbc.Row(dbc.Col(html.H1("Analyse et détection d'anomalies", 
                           className="text-center my-4"))),
    
    # Section Configuration
    dbc.Row([
        dbc.Col([
            html.H4("Configuration des colonnes", className="mb-3"),
            
            dbc.Label("Colonne Montant:"),
            dcc.Dropdown(id='col-montant', placeholder="Sélectionnez la colonne"),
            
            dbc.Label("Colonne Date (optionnel):"),
            dcc.Dropdown(id='col-date', placeholder="Sélectionnez la colonne"),
            
            dbc.Label("Colonnes Catégorielles (optionnel):"),
            dcc.Dropdown(id='col-categories', multi=True, placeholder="Sélectionnez les colonnes"),
            
            html.Hr(),
            
            dbc.Label("Paramètres du modèle:"),
            dbc.InputGroup([
                dbc.InputGroupText("Contamination:"),
                dbc.Input(id='contamination', type='number', value=0.01, step=0.01, min=0.001, max=0.5)
            ], className="mb-3"),
        ], md=4),
        
        # Section Upload
        dbc.Col([
            dcc.Upload(
                id='upload-data',
                children=html.Div([
                    'Glissez-déposez un fichier CSV ou Excel',
                    html.Br(),
                    '(colonnes requises: montant et date)'
                ]),
                style={
                    'height': '200px',
                    'borderStyle': 'dashed',
                    'textAlign': 'center',
                    'padding': '40px'
                }
            ),
            html.Div(id='file-info', className="mt-3"),
            dbc.Button("Lancer l'Analyse", id='run-analysis', color="primary", className="mt-3", disabled=True)
        ], md=8)
    ], className="mb-4"),
    
    # Résultats
    dbc.Tabs([
        dbc.Tab(label="Aperçu des Données", tab_id="tab-data"),
        dbc.Tab(label="Anomalies Détectées", tab_id="tab-anomalies"),
        dbc.Tab(label="Visualisation", tab_id="tab-viz")
    ], id="tabs", active_tab="tab-data"),
    
    html.Div(id="tab-content", className="p-3"),
    
    # Stockage
    dcc.Store(id='store-original-data'),
    dcc.Store(id='store-processed-data')
], fluid=True)

# Callback pour mettre à jour les sélecteurs de colonnes
@callback(
    [Output('col-montant', 'options'),
     Output('col-date', 'options'),
     Output('col-categories', 'options'),
     Output('file-info', 'children'),
     Output('run-analysis', 'disabled')],
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def update_column_selectors(contents, filename):
    if contents is None:
        raise PreventUpdate
    
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    
    try:
        if 'csv' in filename.lower():
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        else:
            df = pd.read_excel(io.BytesIO(decoded))
            
        cols = [{'label': col, 'value': col} for col in df.columns]
        
        file_info = html.Div([
            html.B(f"Fichier chargé: {filename}"),
            html.Br(),
            html.Span(f"{len(df)} lignes, {len(df.columns)} colonnes"),
            html.Br(),
            dbc.Alert("Veuillez configurer les colonnes avant l'analyse", 
                      color="warning", className="mt-2")
        ])
        
        return cols, cols, cols, file_info, True
    
    except Exception as e:
        return [], [], [], html.Div(f"Erreur: {str(e)}", className="text-danger"), True

# Callback pour lancer l'analyse
@callback(
    [Output('store-processed-data', 'data'),
     Output('tab-content', 'children', allow_duplicate=True),
     Output('run-analysis', 'disabled')],
    Input('run-analysis', 'n_clicks'),
    [State('store-original-data', 'data'),
     State('col-montant', 'value'),
     State('col-date', 'value'),
     State('col-categories', 'value'),
     State('contamination', 'value')],
    prevent_initial_call=True
)
def run_analysis(n_clicks, json_data, montant_col, date_col, cat_cols, contamination):
    if n_clicks is None or json_data is None or montant_col is None:
        raise PreventUpdate
    
    df = pd.read_json(io.StringIO(json_data), orient='split')
    
    # Préparation des données
    try:
        features = [montant_col]
        
        # Feature engineering pour la date si disponible
        if date_col and date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            df['jour_semaine'] = df[date_col].dt.dayofweek
            df['mois'] = df[date_col].dt.month
            features += ['jour_semaine', 'mois']
        
        # Encodage des catégories si spécifiées
        if cat_cols:
            for col in cat_cols:
                if col in df.columns:
                    df[col+'_enc'] = pd.factorize(df[col])[0]
                    features.append(col+'_enc')
        
        # Vérification que le montant est numérique
        df[montant_col] = pd.to_numeric(df[montant_col], errors='coerce')
        df = df.dropna(subset=[montant_col])
        
        # Normalisation
        scaler = StandardScaler()
        X = scaler.fit_transform(df[features])
        
        # Détection d'anomalies
        model = IsolationForest(contamination=float(contamination), random_state=42)
        df['anomaly_score'] = model.fit_predict(X)
        df['anomaly'] = np.where(df['anomaly_score'] < 0, 1, 0)
        
        # Sauvegarde des résultats
        results = df.to_json(date_format='iso', orient='split')
        
        # Affichage initial
        preview = dbc.Card([
            dbc.CardHeader("Aperçu des données analysées"),
            dbc.CardBody(create_data_table(df))
        ])
        
        return results, preview, True
    
    except Exception as e:
        error = dbc.Alert(f"Erreur lors de l'analyse: {str(e)}", color="danger")
        return None, error, False

# Affichage des onglets
@callback(
    Output('tab-content', 'children'),
    Input('tabs', 'active_tab'),
    State('store-processed-data', 'data')
)
def display_tab(active_tab, processed_data):
    if processed_data is None:
        return dbc.Alert("Veuvez d'abord charger et analyser des données", color="info")
    
    df = pd.read_json(io.StringIO(processed_data), orient='split')
    
    if active_tab == "tab-data":
        return create_data_table(df)
    elif active_tab == "tab-anomalies":
        anomalies = df[df['anomaly'] == 1]
        return create_anomalies_table(anomalies)
    elif active_tab == "tab-viz":
        return create_visualizations(df)

def create_data_table(df):
    return dash.dash_table.DataTable(
        data=df.to_dict('records'),
        columns=[{'name': col, 'id': col} for col in df.columns],
        page_size=15,
        style_table={'overflowX': 'auto'}
    )

def create_anomalies_table(df):
    return html.Div([
        html.H4(f"{len(df)} anomalies détectées"),
        dash.dash_table.DataTable(
            data=df.to_dict('records'),
            columns=[{'name': col, 'id': col} for col in df.columns],
            page_size=15,
            style_table={'overflowX': 'auto'}
        )
    ])

def create_visualizations(df):
    montant_col = [col for col in df.columns if 'montant' in col.lower()][0]
    
    return html.Div([
        dbc.Row([
            dbc.Col(dcc.Graph(
                figure={
                    'data': [{
                        'x': df.index,
                        'y': df[montant_col],
                        'mode': 'markers',
                        'marker': {
                            'color': df['anomaly'],
                            'colorscale': [[0, 'blue'], [1, 'red']]
                        }
                    }],
                    'layout': {
                        'title': 'Montants des Transactions (Rouge = Anomalies)',
                        'xaxis': {'title': 'Index'},
                        'yaxis': {'title': 'Montant'}
                    }
                }
            ), md=6),
            dbc.Col(dcc.Graph(
                figure={
                    'data': [{
                        'x': df[montant_col],
                        'type': 'histogram',
                        'name': 'Distribution'
                    }],
                    'layout': {
                        'title': 'Distribution des Montants',
                        'xaxis': {'title': 'Montant'},
                        'yaxis': {'title': 'Fréquence'}
                    }
                }
            ), md=6)
        ])
    ])

if __name__ == '__main__':
    app.run(debug=True, port=8053)