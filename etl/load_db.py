"""
load_db.py — Carga de datos en base de datos SQLite
Fuente 3: SQLite — almacenamiento post-ETL optimizado
Pipeline ETL | Accidentes de Tráfico España 2024
"""
import sqlite3
import pandas as pd
import logging
import os

logger = logging.getLogger(__name__)

DB_PATH = os.getenv('SQLITE_PATH', './data/accidentes_ep3.db')


def crear_conexion(ruta: str = DB_PATH) -> sqlite3.Connection:
    """Crea y retorna una conexión a la base de datos SQLite."""
    os.makedirs(os.path.dirname(os.path.abspath(ruta)), exist_ok=True)
    conn = sqlite3.connect(ruta)
    conn.execute("PRAGMA journal_mode=WAL")   # Mejor rendimiento concurrente
    conn.execute("PRAGMA synchronous=NORMAL")
    logger.info(f"[SQLite] Conexión establecida: {ruta}")
    return conn


def cargar_accidentes(df: pd.DataFrame, conn: sqlite3.Connection) -> None:
    """Carga el dataset de accidentes transformado en SQLite."""
    df.to_sql('accidentes', conn, if_exists='replace', index=False, chunksize=5000)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_mes  ON accidentes(MES)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_hora ON accidentes(HORA)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_niebla ON accidentes(HAY_NIEBLA)")
    conn.commit()
    logger.info(f"[SQLite] Tabla 'accidentes' cargada: {len(df):,} registros ✓")


def cargar_meteorologia(df: pd.DataFrame, conn: sqlite3.Connection) -> None:
    """Carga los datos meteorológicos mensuales en SQLite."""
    df.to_sql('meteorologia', conn, if_exists='replace', index=False)
    conn.commit()
    logger.info(f"[SQLite] Tabla 'meteorologia' cargada: {len(df)} registros ✓")


def crear_vista_enriquecida(conn: sqlite3.Connection) -> None:
    """Crea vista SQL que une accidentes + meteorología por mes."""
    conn.execute("DROP VIEW IF EXISTS accidentes_enriquecidos")
    conn.execute("""
        CREATE VIEW accidentes_enriquecidos AS
        SELECT
            a.*,
            m.precipitacion_media_mm,
            m.temp_max_media_c,
            m.viento_max_media_kmh
        FROM accidentes a
        LEFT JOIN meteorologia m ON a.MES = m.MES
    """)
    conn.commit()
    logger.info("[SQLite] Vista 'accidentes_enriquecidos' creada ✓")


def consultar_kpis(conn: sqlite3.Connection) -> dict:
    """Consulta y retorna los KPIs principales desde SQLite."""
    cur = conn.cursor()
    kpis = {}

    cur.execute("SELECT COUNT(*) FROM accidentes")
    kpis['total_accidentes'] = cur.fetchone()[0]

    cur.execute("SELECT COALESCE(SUM(TOTAL_VICTIMAS_24H), 0) FROM accidentes")
    kpis['total_victimas_24h'] = int(cur.fetchone()[0])

    cur.execute("SELECT COALESCE(SUM(TOTAL_VEHICULOS), 0) FROM accidentes")
    kpis['total_vehiculos'] = int(cur.fetchone()[0])

    cur.execute("SELECT COUNT(*) FROM accidentes WHERE HAY_NIEBLA = 1")
    kpis['accidentes_con_niebla'] = cur.fetchone()[0]

    cur.execute("SELECT MES, COUNT(*) n FROM accidentes GROUP BY MES ORDER BY n DESC LIMIT 1")
    row = cur.fetchone()
    kpis['mes_peak'] = int(row[0]) if row else 0

    return kpis
