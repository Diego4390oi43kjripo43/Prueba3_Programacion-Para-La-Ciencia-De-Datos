"""
pipeline.py — Orquestador principal del pipeline ETL
Integra las 3 fuentes de datos y carga SQLite
Pipeline ETL | Accidentes de Tráfico España 2024

Uso:
    python etl/pipeline.py
"""
import logging
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Agregar raíz del proyecto al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from etl.extract_csv import extraer_csv, transformar_accidentes
from etl.extract_api import extraer_datos_meteorologicos
from etl.load_db    import crear_conexion, cargar_accidentes, cargar_meteorologia, crear_vista_enriquecida, consultar_kpis
from etl.validate   import validar_columnas, validar_rangos, reporte_calidad

# ── Configuración de logging ─────────────────────────────────
os.makedirs('./data', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('./data/etl.log', mode='a', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

CSV_PATH = os.getenv('CSV_PATH', './data/accidentes_limpios.csv')
DB_PATH  = os.getenv('SQLITE_PATH', './data/accidentes_ep3.db')


def ejecutar_pipeline() -> bool:
    """
    Ejecuta el pipeline ETL completo en 3 fases:
        Fase 1 — Extracción y transformación del CSV (Fuente 1)
        Fase 2 — Extracción de datos meteorológicos via API (Fuente 2)
        Fase 3 — Carga y almacenamiento en SQLite (Fuente 3)

    Returns:
        True si el pipeline completó exitosamente, False si hubo error.
    """
    logger.info("=" * 65)
    logger.info("  PIPELINE ETL — ACCIDENTES DE TRÁFICO ESPAÑA 2024")
    logger.info("  SCY1101 EP3 | Diego González, Carlos _____, Ricardo _____")
    logger.info("=" * 65)

    try:
        # ── FASE 1: CSV ──────────────────────────────────────────
        logger.info("FASE 1 ▶ Extrayendo y transformando dataset CSV...")

        df_raw = extraer_csv(CSV_PATH)

        # Validación de calidad
        resultado_cols = validar_columnas(df_raw)
        if not resultado_cols['valido']:
            logger.warning(f"Columnas faltantes: {resultado_cols['columnas_faltantes']}")

        resultado_rangos = validar_rangos(df_raw)
        reporte = reporte_calidad(df_raw)
        logger.info(f"Calidad: {reporte['porcentaje_nulos_total']}% nulos | {reporte['duplicados']} duplicados")

        df_accidentes = transformar_accidentes(df_raw)
        logger.info(f"FASE 1 ✓ — {len(df_accidentes):,} registros procesados")

        # ── FASE 2: API ──────────────────────────────────────────
        logger.info("FASE 2 ▶ Extrayendo datos meteorológicos (Open-Meteo API)...")
        df_meteo = extraer_datos_meteorologicos(anio=2024)
        logger.info(f"FASE 2 ✓ — {len(df_meteo)} registros meteorológicos mensuales")

        # ── FASE 3: SQLite ───────────────────────────────────────
        logger.info("FASE 3 ▶ Cargando datos en base de datos SQLite...")
        conn = crear_conexion(DB_PATH)
        cargar_accidentes(df_accidentes, conn)
        cargar_meteorologia(df_meteo, conn)
        crear_vista_enriquecida(conn)

        kpis = consultar_kpis(conn)
        conn.close()

        logger.info(f"FASE 3 ✓ — Base de datos lista: {DB_PATH}")
        logger.info("─" * 65)
        logger.info("KPIs finales:")
        logger.info(f"  Total accidentes :  {kpis['total_accidentes']:>10,}")
        logger.info(f"  Total víctimas   :  {kpis['total_victimas_24h']:>10,}")
        logger.info(f"  Total vehículos  :  {kpis['total_vehiculos']:>10,}")
        logger.info(f"  Con niebla       :  {kpis['accidentes_con_niebla']:>10,}")
        logger.info(f"  Mes peak         :  {kpis['mes_peak']:>10}")
        logger.info("=" * 65)
        logger.info("PIPELINE ETL COMPLETADO EXITOSAMENTE ✓")
        logger.info("=" * 65)
        return True

    except FileNotFoundError as e:
        logger.error(f"Archivo no encontrado: {e}")
        logger.error("Asegúrate de copiar accidentes_limpios.csv en la carpeta /data/")
        return False
    except Exception as e:
        logger.error(f"ERROR en pipeline: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    exito = ejecutar_pipeline()
    sys.exit(0 if exito else 1)
