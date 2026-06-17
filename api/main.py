"""
main.py — API RESTful interna
Accidentes de Tráfico España 2024
Framework: FastAPI | SCY1101 EP3
Documentación automática: http://localhost:8000/docs
"""
import os, sys, sqlite3, logging
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

DB_PATH  = os.getenv('SQLITE_PATH', './data/accidentes_ep3.db')
CSV_PATH = os.getenv('CSV_PATH',   './data/accidentes_limpios.csv')

# ── APP FASTAPI ───────────────────────────────────────────────
app = FastAPI(
    title="API — Accidentes Viales España 2024",
    description=(
        "API RESTful que expone los datos procesados por el pipeline ETL. "
        "Conecta el backend (SQLite) con el dashboard Plotly Dash. "
        "SCY1101 EP3 | Diego González, Carlos Contreras, Ricardo Leon"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


def get_df() -> pd.DataFrame:
    """Obtiene el DataFrame desde SQLite o CSV de respaldo."""
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql("SELECT * FROM accidentes", conn)
        conn.close()
        return df
    except Exception as e:
        logger.warning(f"SQLite no disponible: {e}. Usando CSV.")
        return pd.read_csv(CSV_PATH, low_memory=False)


# ── ENDPOINTS ─────────────────────────────────────────────────

@app.get("/", tags=["Estado"])
def root():
    """Endpoint raíz — verifica que la API está en línea."""
    return {
        "message": "API Accidentes Viales España 2024 — SCY1101 EP3",
        "status":  "online",
        "docs":    "/docs",
    }


@app.get("/health", tags=["Estado"])
def health():
    """Health check del sistema."""
    db_ok = os.path.exists(DB_PATH)
    csv_ok = os.path.exists(CSV_PATH)
    return {
        "status":       "healthy" if (db_ok or csv_ok) else "degraded",
        "sqlite":       "disponible" if db_ok else "no encontrado",
        "csv_respaldo": "disponible" if csv_ok else "no encontrado",
    }


@app.get("/kpis", tags=["KPIs"])
def get_kpis():
    """
    Retorna los KPIs principales del dataset.

    Usado por la Vista Ejecutiva del dashboard.
    """
    df = get_df()
    return {
        "total_accidentes":       int(len(df)),
        "total_victimas_24h":     int(df['TOTAL_VICTIMAS_24H'].sum()),
        "total_vehiculos":        int(df['TOTAL_VEHICULOS'].sum()),
        "accidentes_con_niebla":  int(df['HAY_NIEBLA'].sum()),
        "mes_mas_accidentes":     int(df['MES'].value_counts().idxmax()),
        "hora_mas_accidentes":    int(df['HORA'].value_counts().idxmax()),
        "dia_mas_accidentes":     int(df['DIA_SEMANA'].value_counts().idxmax()),
    }


@app.get("/accidentes/por-mes", tags=["Agrupaciones"])
def por_mes():
    """Retorna el conteo de accidentes agrupado por mes (1-12)."""
    df = get_df()
    resultado = df.groupby('MES').size().reset_index(name='total')
    return resultado.to_dict(orient='records')


@app.get("/accidentes/por-hora", tags=["Agrupaciones"])
def por_hora():
    """Retorna la distribución de accidentes por hora del día (0-23)."""
    df = get_df()
    resultado = df.groupby('HORA').size().reset_index(name='total')
    return resultado.to_dict(orient='records')


@app.get("/accidentes/por-dia", tags=["Agrupaciones"])
def por_dia():
    """Retorna accidentes agrupados por día de la semana (1=Lunes, 7=Domingo)."""
    df = get_df()
    dias = {1:'Lunes',2:'Martes',3:'Miércoles',4:'Jueves',5:'Viernes',6:'Sábado',7:'Domingo'}
    resultado = df.groupby('DIA_SEMANA').size().reset_index(name='total')
    resultado['dia_nombre'] = resultado['DIA_SEMANA'].map(dias)
    return resultado.to_dict(orient='records')


@app.get("/accidentes/por-niebla", tags=["Agrupaciones"])
def por_niebla():
    """Retorna comparativa de accidentes con y sin niebla."""
    df = get_df()
    resultado = df.groupby('HAY_NIEBLA').size().reset_index(name='total')
    resultado['descripcion'] = resultado['HAY_NIEBLA'].map({0:'Sin niebla', 1:'Con niebla'})
    return resultado.to_dict(orient='records')


@app.get("/accidentes/filtrar", tags=["Filtros"])
def filtrar(
    mes:       Optional[int] = Query(None, ge=1,  le=12,   description="Mes (1-12)"),
    hay_niebla:Optional[int] = Query(None, ge=0,  le=1,    description="0=sin niebla, 1=con niebla"),
    tipo_via:  Optional[int] = Query(None,                  description="Código de tipo de vía"),
    limit:     int           = Query(100,  ge=1,  le=1000,  description="Máximo de registros"),
):
    """
    Filtra accidentes por parámetros específicos.
    Usado por la Vista Técnica del dashboard.
    """
    df = get_df()

    if mes is not None:
        df = df[df['MES'] == mes]
    if hay_niebla is not None:
        df = df[df['HAY_NIEBLA'] == hay_niebla]
    if tipo_via is not None:
        if 'TIPO_VIA' not in df.columns:
            raise HTTPException(status_code=400, detail="Columna TIPO_VIA no disponible")
        df = df[df['TIPO_VIA'] == tipo_via]

    return {
        "filtros_aplicados": {
            "mes": mes, "hay_niebla": hay_niebla, "tipo_via": tipo_via
        },
        "total_encontrados": int(len(df)),
        "datos": df.head(limit).fillna("").to_dict(orient='records'),
    }


@app.get("/meteorologia", tags=["Meteorología"])
def get_meteorologia():
    """Retorna los datos meteorológicos mensuales extraídos de Open-Meteo API."""
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql("SELECT * FROM meteorologia", conn)
        conn.close()
        return df.to_dict(orient='records')
    except Exception:
        from etl.extract_api import _datos_respaldo
        return _datos_respaldo().to_dict(orient='records')
