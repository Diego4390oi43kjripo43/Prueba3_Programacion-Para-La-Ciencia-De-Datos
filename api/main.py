"""
main.py - API RESTful interna
Accidentes de Trafico Espana 2024
Framework: FastAPI | SCY1101 EFT
Documentacion automatica: http://localhost:8000/docs
"""
import os, sys, sqlite3, logging
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

DB_PATH  = os.getenv('SQLITE_PATH', './data/accidentes_ep3.db')
CSV_PATH = os.getenv('CSV_PATH',   './data/accidentes_limpios.csv')

app = FastAPI(
    title="API - Accidentes Viales Espana 2024",
    description=(
        "API RESTful que expone los datos procesados por el pipeline ETL "
        "y los modelos de Machine Learning (clasificacion y regresion). "
        "SCY1101 EFT | Diego Gonzalez, Carlos, Ricardo"
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def get_df():
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql("SELECT * FROM accidentes", conn)
        conn.close()
        return df
    except Exception as e:
        logger.warning(f"SQLite no disponible: {e}. Usando CSV.")
        return pd.read_csv(CSV_PATH, low_memory=False)


class AccidenteInput(BaseModel):
    """Datos de entrada para predecir gravedad o victimas de un accidente."""
    HORA: int = 14
    MES: int = 6
    DIA_SEMANA: int = 3
    TOTAL_VEHICULOS: int = 2
    CONDICION_METEO: int = 1
    CONDICION_ILUMINACION: int = 1
    CONDICION_FIRME: int = 1
    TRAZADO_PLANTA: int = 1
    HAY_NIEBLA: int = 0
    TIPO_VIA: int = 3
    TIPO_ACCIDENTE: int = 6

    class Config:
        json_schema_extra = {
            "example": {
                "HORA": 22, "MES": 7, "DIA_SEMANA": 6, "TOTAL_VEHICULOS": 3,
                "CONDICION_METEO": 2, "CONDICION_ILUMINACION": 3, "CONDICION_FIRME": 2,
                "TRAZADO_PLANTA": 1, "HAY_NIEBLA": 1, "TIPO_VIA": 3, "TIPO_ACCIDENTE": 6
            }
        }


@app.get("/", tags=["Estado"])
def root():
    return {"message": "API Accidentes Viales Espana 2024 - SCY1101 EFT",
            "status": "online", "docs": "/docs", "version": "2.0.0"}


@app.get("/health", tags=["Estado"])
def health():
    db_ok = os.path.exists(DB_PATH)
    csv_ok = os.path.exists(CSV_PATH)
    modelos_ok = os.path.exists('./models/modelo_clasificacion.pkl')
    return {
        "status": "healthy" if (db_ok or csv_ok) else "degraded",
        "sqlite": "disponible" if db_ok else "no encontrado",
        "csv_respaldo": "disponible" if csv_ok else "no encontrado",
        "modelos_ml": "disponibles" if modelos_ok else "no entrenados",
    }


@app.get("/kpis", tags=["KPIs"])
def get_kpis():
    df = get_df()
    return {
        "total_accidentes":      int(len(df)),
        "total_victimas_24h":    int(df['TOTAL_VICTIMAS_24H'].sum()),
        "total_vehiculos":       int(df['TOTAL_VEHICULOS'].sum()),
        "accidentes_con_niebla": int(df['HAY_NIEBLA'].sum()),
        "mes_mas_accidentes":    int(df['MES'].value_counts().idxmax()),
        "hora_mas_accidentes":   int(df['HORA'].value_counts().idxmax()),
    }


@app.get("/accidentes/por-mes", tags=["Agrupaciones"])
def por_mes():
    df = get_df()
    return df.groupby('MES').size().reset_index(name='total').to_dict(orient='records')


@app.get("/accidentes/por-hora", tags=["Agrupaciones"])
def por_hora():
    df = get_df()
    return df.groupby('HORA').size().reset_index(name='total').to_dict(orient='records')


@app.get("/accidentes/por-gravedad", tags=["Agrupaciones"])
def por_gravedad():
    df = get_df()
    if 'gravedad_accidente' not in df.columns:
        raise HTTPException(status_code=400, detail="Columna gravedad_accidente no disponible")
    return df.groupby('gravedad_accidente').size().reset_index(name='total').to_dict(orient='records')


@app.get("/accidentes/filtrar", tags=["Filtros"])
def filtrar(mes: Optional[int] = Query(None, ge=1, le=12),
            hay_niebla: Optional[int] = Query(None, ge=0, le=1),
            limit: int = Query(100, ge=1, le=1000)):
    df = get_df()
    if mes is not None: df = df[df['MES'] == mes]
    if hay_niebla is not None: df = df[df['HAY_NIEBLA'] == hay_niebla]
    return {"total_encontrados": int(len(df)),
            "datos": df.head(limit).fillna("").to_dict(orient='records')}


@app.post("/predecir/gravedad", tags=["Machine Learning"])
def endpoint_predecir_gravedad(accidente: AccidenteInput):
    """
    Predice la GRAVEDAD de un accidente (Baja/Media/Alta) usando el modelo de clasificacion.
    """
    try:
        from models.predict import predecir_gravedad
        return predecir_gravedad(accidente.model_dump())
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en prediccion: {e}")


@app.post("/predecir/victimas", tags=["Machine Learning"])
def endpoint_predecir_victimas(accidente: AccidenteInput):
    """
    Predice el NUMERO DE VICTIMAS de un accidente usando el modelo de regresion.
    """
    try:
        from models.predict import predecir_victimas
        return predecir_victimas(accidente.model_dump())
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en prediccion: {e}")


@app.get("/modelos/metricas", tags=["Machine Learning"])
def metricas_modelos():
    """Devuelve las metricas de rendimiento de los modelos entrenados."""
    import json
    ruta = './models/metricas.json'
    if not os.path.exists(ruta):
        raise HTTPException(status_code=503,
            detail="Modelos no entrenados. Ejecuta: python models/train_models.py")
    with open(ruta, encoding='utf-8') as f:
        return json.load(f)
