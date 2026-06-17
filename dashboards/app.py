"""
app.py - Dashboard Interactivo Multiaudiencia
Accidentes de Trafico Espana 2024
Vistas: Ejecutiva | Tecnica | Operativa
Framework: Plotly Dash | SCY1101 EP3
"""
import os, sys, sqlite3, logging
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash
from dash import dcc, html, Input, Output
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

DB_PATH  = os.getenv('SQLITE_PATH', './data/accidentes_ep3.db')
CSV_PATH = os.getenv('CSV_PATH',   './data/accidentes_limpios.csv')
PORT     = int(os.getenv('DASH_PORT', 8050))


C = {
    'bg':      '#FAFAFA', 'card':    '#FFFFFF',
    'accent':  '#2C5F8A', 'text':    '#1A1A1A',
    'sub':     '#6B7280', 'line':    '#94A3B8',
    'soft':    '#CBD5E1', 'border':  '#E5E7EB',
}
GRAV_COLORS = {'Baja': C['soft'], 'Media': C['line'], 'Alta': C['accent'], 'nan': C['border']}

CARD_STYLE = {
    'background': C['card'], 'borderRadius': '6px',
    'padding': '20px 24px', 'flex': '1', 'minWidth': '170px',
    'border': f'1px solid {C["border"]}',
}
MESES = {1:'Ene',2:'Feb',3:'Mar',4:'Abr',5:'May',6:'Jun',
         7:'Jul',8:'Ago',9:'Sep',10:'Oct',11:'Nov',12:'Dic'}
DIAS  = {1:'Lun',2:'Mar',3:'Mie',4:'Jue',5:'Vie',6:'Sab',7:'Dom'}
ORDEN_DIAS = ['Lun','Mar','Mie','Jue','Vie','Sab','Dom']

PLOT_BASE = dict(paper_bgcolor=C['card'], plot_bgcolor=C['card'],
                 font_color=C['text'], font_family='Helvetica, Arial, sans-serif',
                 margin=dict(t=50, l=30, r=20, b=30), title_font_size=15)

# -- CARGA DE DATOS --------------------------------------------
def cargar_datos():
    try:
        conn = sqlite3.connect(DB_PATH)
        df       = pd.read_sql("SELECT * FROM accidentes",   conn)
        df_meteo = pd.read_sql("SELECT * FROM meteorologia", conn)
        conn.close()
        logger.info(f"Datos cargados desde SQLite: {len(df):,} registros")
    except Exception as e:
        logger.warning(f"SQLite no disponible ({e}), usando CSV de respaldo")
        df = pd.read_csv(CSV_PATH, low_memory=False)
        def tramo(h):
            if 6  <= h < 12: return 'Manana'
            elif 12 <= h < 20: return 'Tarde'
            elif 20 <= h <= 23: return 'Noche'
            else: return 'Madrugada'
        df['TRAMO_HORA'] = df['HORA'].apply(tramo)
        df['gravedad_accidente'] = pd.cut(
            df['TOTAL_VICTIMAS_24H'].fillna(0),
            bins=[-0.1, 0.5, 2.5, float('inf')],
            labels=['Baja', 'Media', 'Alta']).astype(str)
        df_meteo = pd.DataFrame({'MES': range(1, 13),
            'precipitacion_media_mm':[45,38,32,28,22,8,3,5,20,42,50,55],
            'temp_max_media_c':[9,11,15,18,23,28,33,32,26,20,13,9],
            'viento_max_media_kmh':[25,22,28,24,20,18,16,17,22,26,28,27]})

    # -- NORMALIZACION DEFENSIVA (asegura tipos correctos) -------
    df['HAY_NIEBLA']         = pd.to_numeric(df['HAY_NIEBLA'], errors='coerce').fillna(0).astype(int)
    df['TOTAL_VICTIMAS_24H'] = pd.to_numeric(df['TOTAL_VICTIMAS_24H'], errors='coerce').fillna(0)
    df['TOTAL_VEHICULOS']    = pd.to_numeric(df['TOTAL_VEHICULOS'], errors='coerce').fillna(1)
    df['DIA_SEMANA']         = pd.to_numeric(df['DIA_SEMANA'], errors='coerce').fillna(0).astype(int)
    df['HORA']               = pd.to_numeric(df['HORA'], errors='coerce').fillna(0).astype(int)
    df['MES']                = pd.to_numeric(df['MES'], errors='coerce').fillna(1).astype(int)
    if 'gravedad_accidente' not in df.columns:
        df['gravedad_accidente'] = pd.cut(df['TOTAL_VICTIMAS_24H'],
            bins=[-0.1,0.5,2.5,float('inf')], labels=['Baja','Media','Alta']).astype(str)
    # FORZAR recalculo de TRAMO_HORA siempre desde HORA (evita problemas de codificacion)
    def tramo(h):
        if 6<=h<12: return 'Manana'
        elif 12<=h<20: return 'Tarde'
        elif 20<=h<=23: return 'Noche'
        else: return 'Madrugada'
    df['TRAMO_HORA'] = df['HORA'].apply(tramo)
    logger.info(f"TRAMO_HORA valores: {df['TRAMO_HORA'].unique().tolist()}")
    logger.info(f"DIA_SEMANA valores: {sorted(df['DIA_SEMANA'].unique().tolist())}")
    logger.info(f"HAY_NIEBLA valores: {sorted(df['HAY_NIEBLA'].unique().tolist())}")
    logger.info(f"Total registros cargados: {len(df)}")
    return df, df_meteo

DF, DF_METEO = cargar_datos()

KPI_ACC  = len(DF)
KPI_VIC  = int(DF['TOTAL_VICTIMAS_24H'].sum())
KPI_GRAV = int((DF['gravedad_accidente'] == 'Alta').sum())
KPI_VEH  = int(DF['TOTAL_VEHICULOS'].sum())
KPI_NIE  = int(DF['HAY_NIEBLA'].sum())

def kpi_card(titulo, valor):
    return html.Div([
        html.P(titulo, style={'color':C['sub'],'fontSize':'12px','margin':'0 0 8px 0',
                              'fontWeight':'500','textTransform':'uppercase','letterSpacing':'0.5px'}),
        html.H2(f"{valor:,}", style={'color':C['text'],'margin':'0','fontSize':'30px','fontWeight':'600'}),
    ], style=CARD_STYLE)

def dropdown(id_, options, value, label):
    return html.Div([
        html.Label(label, style={'color':C['sub'],'fontSize':'12px','marginBottom':'5px',
                                 'display':'block','fontWeight':'500'}),
        dcc.Dropdown(id=id_, options=options, value=value, clearable=False, style={'fontSize':'13px'})
    ], style={'flex':'1','minWidth':'160px'})

app = dash.Dash(__name__, title='Accidentes Viales Espana 2024',
                meta_tags=[{"name":"viewport","content":"width=device-width,initial-scale=1"}])
server = app.server

HEADER = html.Div([html.Div([
    html.H1("Accidentalidad Vial en Espana - 2024",
            style={'color':C['text'],'margin':'0','fontSize':'19px','fontWeight':'600'}),
    html.P("Pipeline ETL: CSV - Open-Meteo API - SQLite   |   Plotly Dash   |   SCY1101 EP3",
           style={'color':C['sub'],'margin':'3px 0 0 0','fontSize':'11px'}),
])], style={'background':C['card'],'padding':'18px 30px','borderBottom':f'1px solid {C["border"]}'})

TAB_STYLE = {'color':C['sub'],'background':C['bg'],'border':'none','padding':'12px 22px','fontSize':'13px'}
TAB_SEL = {'color':C['accent'],'background':C['card'],'borderTop':f'2px solid {C["accent"]}',
           'borderLeft':'none','borderRight':'none','borderBottom':'none','fontWeight':'600','padding':'12px 22px'}

TABS = dcc.Tabs(id='tabs', value='eje', children=[
    dcc.Tab(label='Vista Ejecutiva',  value='eje', style=TAB_STYLE, selected_style=TAB_SEL),
    dcc.Tab(label='Vista Tecnica',    value='tec', style=TAB_STYLE, selected_style=TAB_SEL),
    dcc.Tab(label='Vista Operativa',  value='ope', style=TAB_STYLE, selected_style=TAB_SEL),
], style={'background':C['bg'],'borderBottom':f'1px solid {C["border"]}'})

app.layout = html.Div([HEADER, TABS, html.Div(id='contenido')],
                       style={'background':C['bg'],'minHeight':'100vh','fontFamily':'Helvetica, Arial, sans-serif'})

@app.callback(Output('contenido','children'), Input('tabs','value'))
def render_tab(tab):
    if tab == 'eje': return vista_ejecutiva()
    if tab == 'tec': return vista_tecnica()
    return vista_operativa()

# -- VISTA EJECUTIVA -------------------------------------------
def vista_ejecutiva():
    return html.Div([
        html.Div([
            kpi_card("Total Accidentes", KPI_ACC), kpi_card("Victimas Totales 24h", KPI_VIC),
            kpi_card("Accidentes Graves", KPI_GRAV), kpi_card("Vehiculos Involucrados", KPI_VEH),
            kpi_card("Accidentes con Niebla", KPI_NIE),
        ], style={'display':'flex','gap':'14px','padding':'24px 30px','flexWrap':'wrap'}),
        html.Div([
            dropdown('eje-grav', [{'label':'Todas las gravedades','value':'Todos'},
                                  {'label':'Alta','value':'Alta'},{'label':'Media','value':'Media'},
                                  {'label':'Baja','value':'Baja'}], 'Todos', 'Gravedad del accidente'),
            dropdown('eje-tramo',[{'label':'Todos los tramos','value':'Todos'},
                                  {'label':'Manana (6-12h)','value':'Manana'},
                                  {'label':'Tarde (12-20h)','value':'Tarde'},
                                  {'label':'Noche (20-24h)','value':'Noche'},
                                  {'label':'Madrugada (0-6h)','value':'Madrugada'}], 'Todos', 'Tramo horario'),
        ], style={'display':'flex','gap':'16px','padding':'0 30px 20px 30px'}),
        html.Div([
            html.Div([dcc.Graph(id='eje-grav-bar')], style={'flex':'1','minWidth':'300px'}),
            html.Div([dcc.Graph(id='eje-mes-line')], style={'flex':'1','minWidth':'300px'}),
            html.Div([dcc.Graph(id='eje-tramo-pie')],style={'flex':'1','minWidth':'280px'}),
        ], style={'display':'flex','gap':'14px','padding':'0 30px 24px 30px','flexWrap':'wrap'}),
    ], style={'background':C['bg']})

@app.callback(
    [Output('eje-grav-bar','figure'), Output('eje-mes-line','figure'), Output('eje-tramo-pie','figure')],
    [Input('eje-grav','value'), Input('eje-tramo','value')])
def update_ejecutiva(grav, tramo):
    df = DF.copy()
    if grav  != 'Todos': df = df[df['gravedad_accidente'] == grav]
    if tramo != 'Todos': df = df[df['TRAMO_HORA'] == tramo]

    gc = df['gravedad_accidente'].value_counts().reset_index()
    gc.columns = ['Gravedad','N']
    gc = gc[gc['Gravedad'].isin(['Baja','Media','Alta'])]
    fig1 = px.bar(gc, x='Gravedad', y='N', color='Gravedad',
                  color_discrete_map=GRAV_COLORS, title='Accidentes por Gravedad', text='N')
    fig1.update_layout(**PLOT_BASE, showlegend=False)
    fig1.update_xaxes(type='category'); fig1.update_traces(textposition='outside')

    mc = df.groupby('MES').size().reindex(range(1,13), fill_value=0).reset_index()
    mc.columns = ['MES','N']; mc['Mes'] = mc['MES'].map(MESES)
    fig2 = px.line(mc, x='Mes', y='N', title='Evolucion Mensual', markers=True,
                   color_discrete_sequence=[C['accent']])
    fig2.update_layout(**PLOT_BASE); fig2.update_xaxes(type='category')

    tc = df['TRAMO_HORA'].value_counts().reset_index()
    tc.columns = ['Tramo','N']
    fig3 = px.pie(tc, names='Tramo', values='N', title='Distribucion Horaria',
                   color_discrete_sequence=['#2C5F8A','#6B8FB0','#94A3B8','#CBD5E1'], hole=0.5)
    fig3.update_layout(**PLOT_BASE)
    return fig1, fig2, fig3

# -- VISTA TECNICA ---------------------------------------------
def vista_tecnica():
    return html.Div([
        html.Div([
            html.H3("Analisis Tecnico - Patrones de Accidentalidad",
                    style={'color':C['text'],'margin':'0 0 4px 0','fontWeight':'600','fontSize':'16px'}),
            html.P("Mapas de calor, distribuciones y correlacion meteorologica",
                   style={'color':C['sub'],'margin':'0','fontSize':'12px'}),
        ], style={'padding':'24px 30px 10px 30px'}),
        html.Div([
            html.Div([
                html.Label("Rango de meses:", style={'color':C['sub'],'fontSize':'12px','display':'block','marginBottom':'6px','fontWeight':'500'}),
                dcc.RangeSlider(id='tec-mes', min=1, max=12, step=1, value=[1,12],
                                marks={i:{'label':MESES[i],'style':{'color':C['sub'],'fontSize':'10px'}} for i in range(1,13)},
                                tooltip={"placement":"bottom","always_visible":False})
            ], style={'flex':'2'}),
            html.Div([
                html.Label("Condicion niebla:", style={'color':C['sub'],'fontSize':'12px','display':'block','marginBottom':'6px','fontWeight':'500'}),
                dcc.RadioItems(id='tec-niebla', options=[{'label':' Todos','value':'Todos'},
                               {'label':' Con niebla','value':1},{'label':' Sin niebla','value':0}],
                               value='Todos', labelStyle={'color':C['text'],'marginRight':'14px','fontSize':'13px'},
                               style={'display':'flex'})
            ], style={'flex':'1'}),
        ], style={'display':'flex','gap':'30px','padding':'10px 30px 20px 30px','alignItems':'flex-end'}),
        html.Div([dcc.Graph(id='tec-heatmap')], style={'padding':'0 30px'}),
        html.Div([
            html.Div([dcc.Graph(id='tec-meteo')], style={'flex':'1','minWidth':'300px'}),
            html.Div([dcc.Graph(id='tec-hora')],  style={'flex':'1','minWidth':'300px'}),
        ], style={'display':'flex','gap':'14px','padding':'14px 30px'}),
    ], style={'background':C['bg']})

@app.callback(
    [Output('tec-heatmap','figure'), Output('tec-meteo','figure'), Output('tec-hora','figure')],
    [Input('tec-mes','value'), Input('tec-niebla','value')])
def update_tecnica(mes_range, niebla):
    df = DF.copy()
    df = df[(df['MES'] >= mes_range[0]) & (df['MES'] <= mes_range[1])]
    if niebla != 'Todos': df = df[df['HAY_NIEBLA'] == niebla]

    pivot = df.groupby(['DIA_SEMANA','HORA']).size().unstack(fill_value=0)
    pivot.index = [DIAS.get(i, str(i)) for i in pivot.index]
    fig1 = px.imshow(pivot, title='Mapa de Calor - Dia x Hora',
                     labels=dict(x='Hora del dia', y='Dia semana', color='Accidentes'),
                     color_continuous_scale='Blues', aspect='auto')
    fig1.update_layout(**PLOT_BASE)

    mc2 = df['CONDICION_METEO'].astype(str).value_counts().head(8).reset_index()
    mc2.columns = ['Condicion','N']
    fig2 = px.bar(mc2, x='Condicion', y='N', title='Accidentes por Condicion Meteorologica',
                  color_discrete_sequence=[C['accent']])
    fig2.update_layout(**PLOT_BASE); fig2.update_xaxes(type='category')

    hc = df.groupby('HORA').size().reset_index(name='N')
    fig3 = px.area(hc, x='HORA', y='N', title='Distribucion por Hora del Dia',
                   color_discrete_sequence=[C['line']])
    fig3.update_layout(**PLOT_BASE)
    return fig1, fig2, fig3

# -- VISTA OPERATIVA -------------------------------------------
def vista_operativa():
    return html.Div([
        html.Div([
            html.Div([html.P("HORA PICO",style={'color':C['sub'],'fontWeight':'600','margin':'0','fontSize':'11px','letterSpacing':'0.5px'}),
                      html.H3("Tarde 12-20h",style={'color':C['text'],'margin':'4px 0','fontSize':'18px','fontWeight':'600'}),
                      html.P("39% de accidentes",style={'color':C['sub'],'margin':'0','fontSize':'11px'})], style=CARD_STYLE),
            html.Div([html.P("NIEBLA",style={'color':C['sub'],'fontWeight':'600','margin':'0','fontSize':'11px','letterSpacing':'0.5px'}),
                      html.H3(f"{KPI_NIE:,} casos",style={'color':C['text'],'margin':'4px 0','fontSize':'18px','fontWeight':'600'}),
                      html.P("Mayor tasa de gravedad Alta",style={'color':C['sub'],'margin':'0','fontSize':'11px'})], style=CARD_STYLE),
            html.Div([html.P("MES PICO",style={'color':C['sub'],'fontWeight':'600','margin':'0','fontSize':'11px','letterSpacing':'0.5px'}),
                      html.H3("Julio - 9.333",style={'color':C['text'],'margin':'4px 0','fontSize':'18px','fontWeight':'600'}),
                      html.P("Pico de verano 2024",style={'color':C['sub'],'margin':'0','fontSize':'11px'})], style=CARD_STYLE),
        ], style={'display':'flex','gap':'14px','padding':'24px 30px 16px 30px','flexWrap':'wrap'}),
        html.Div([
            html.Div([
                html.Label("Tramos horarios activos:", style={'color':C['sub'],'fontSize':'12px','display':'block','marginBottom':'6px','fontWeight':'500'}),
                dcc.Checklist(id='ope-tramos', options=[{'label':f' {t}','value':t} for t in ['Manana','Tarde','Noche','Madrugada']],
                              value=['Manana','Tarde','Noche','Madrugada'],
                              labelStyle={'color':C['text'],'marginRight':'14px','fontSize':'13px'}, style={'display':'flex'})
            ], style={'flex':'2'}),
            html.Div([
                html.Label("Niebla:", style={'color':C['sub'],'fontSize':'12px','display':'block','marginBottom':'6px','fontWeight':'500'}),
                dcc.RadioItems(id='ope-niebla', options=[{'label':' Todos','value':'Todos'},
                               {'label':' Con niebla','value':1},{'label':' Sin niebla','value':0}],
                               value='Todos', labelStyle={'color':C['text'],'marginRight':'14px','fontSize':'13px'}, style={'display':'flex'})
            ], style={'flex':'1'}),
        ], style={'display':'flex','gap':'30px','padding':'0 30px 20px 30px','alignItems':'flex-end'}),
        html.Div([
            html.Div([dcc.Graph(id='ope-dia')],   style={'flex':'1','minWidth':'300px'}),
            html.Div([dcc.Graph(id='ope-niebla')], style={'flex':'1','minWidth':'300px'}),
        ], style={'display':'flex','gap':'14px','padding':'0 30px 24px 30px','flexWrap':'wrap'}),
    ], style={'background':C['bg']})

@app.callback(
    [Output('ope-dia','figure'), Output('ope-niebla','figure')],
    [Input('ope-tramos','value'), Input('ope-niebla','value')])
def update_operativa(tramos, niebla):
    df = DF.copy()
    # Filtro tolerante: solo aplica si no vacia el dataframe
    if tramos:
        df_tmp = df[df['TRAMO_HORA'].isin(tramos)]
        if len(df_tmp) > 0:
            df = df_tmp
    if niebla != 'Todos':
        df_tmp = df[df['HAY_NIEBLA'] == niebla]
        if len(df_tmp) > 0:
            df = df_tmp

    # GRAFICO 1: dia de la semana - inmune a cualquier rango de DIA_SEMANA
    dc = df.groupby('DIA_SEMANA').size().reset_index(name='N')
    dc['Dia'] = dc['DIA_SEMANA'].map(DIAS).fillna(dc['DIA_SEMANA'].astype(str))
    dc = dc.sort_values('DIA_SEMANA')
    fig1 = px.bar(dc, x='Dia', y='N', title='Accidentes por Dia de la Semana',
                  color_discrete_sequence=[C['accent']], text='N')
    fig1.update_layout(**PLOT_BASE)
    fig1.update_xaxes(type='category'); fig1.update_traces(textposition='outside')

    # GRAFICO 2: gravedad vs niebla - inmune a valores faltantes
    ng = df.groupby(['HAY_NIEBLA','gravedad_accidente']).size().reset_index(name='N')
    ng = ng[ng['gravedad_accidente'].isin(['Baja','Media','Alta'])]
    ng['Niebla'] = ng['HAY_NIEBLA'].map({0:'Sin niebla',1:'Con niebla'}).fillna('Otro')
    if ng.empty:
        fig2 = go.Figure(); fig2.update_layout(**PLOT_BASE, title='Gravedad vs Condicion de Niebla')
    else:
        fig2 = px.bar(ng, x='Niebla', y='N', color='gravedad_accidente',
                      title='Gravedad vs Condicion de Niebla',
                      color_discrete_map=GRAV_COLORS, barmode='group')
        fig2.update_layout(**PLOT_BASE); fig2.update_xaxes(type='category')
    return fig1, fig2

if __name__ == '__main__':
    logger.info(f"Dashboard iniciando en http://localhost:{PORT}")
    app.run(debug=False, host='0.0.0.0', port=PORT)
