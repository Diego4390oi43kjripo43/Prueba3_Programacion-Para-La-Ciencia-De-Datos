"""
extract_csv.py — Extracción y transformación del dataset base
Fuente 1: accidentes_limpios.csv (101.995 registros)
Pipeline ETL | Accidentes de Tráfico España 2024
"""
import pandas as pd
import logging
import os

logger = logging.getLogger(__name__)


def extraer_csv(ruta: str) -> pd.DataFrame:
    """
    Extrae el dataset base de accidentes desde un archivo CSV.

    Args:
        ruta: Ruta al archivo accidentes_limpios.csv

    Returns:
        DataFrame con los datos crudos

    Raises:
        FileNotFoundError: Si el archivo no existe
        ValueError: Si el archivo está vacío
    """
    if not os.path.exists(ruta):
        raise FileNotFoundError(f"Dataset no encontrado en: {ruta}")

    logger.info(f"[FUENTE 1] Leyendo CSV: {ruta}")
    df = pd.read_csv(ruta, low_memory=False)

    if df.empty:
        raise ValueError("El archivo CSV está vacío.")

    logger.info(f"[FUENTE 1] Dataset cargado: {len(df):,} registros | {len(df.columns)} columnas")
    return df


def transformar_accidentes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica transformaciones y crea variables derivadas sobre el dataset.

    Variables derivadas creadas:
        - TRAMO_HORA: Franja horaria (Madrugada/Mañana/Tarde/Noche)
        - gravedad_accidente: Nivel de gravedad (Baja/Media/Alta)

    Args:
        df: DataFrame crudo

    Returns:
        DataFrame transformado y enriquecido
    """
    df = df.copy()

    # ── Variable derivada 1: TRAMO_HORA ─────────────────────
    def asignar_tramo(hora: int) -> str:
        """Clasifica la hora en franja horaria."""
        if 6 <= hora < 12:
            return 'Mañana'
        elif 12 <= hora < 20:
            return 'Tarde'
        elif 20 <= hora <= 23:
            return 'Noche'
        else:
            return 'Madrugada'

    if 'HORA' in df.columns:
        df['TRAMO_HORA'] = df['HORA'].apply(asignar_tramo)
        logger.info("Variable derivada TRAMO_HORA creada ✓")

    # ── Variable derivada 2: gravedad_accidente ──────────────
    if 'TOTAL_VICTIMAS_24H' in df.columns:
        df['gravedad_accidente'] = pd.cut(
            df['TOTAL_VICTIMAS_24H'].fillna(0),
            bins=[-0.1, 0.5, 2.5, float('inf')],
            labels=['Baja', 'Media', 'Alta']
        ).astype(str)
        logger.info("Variable derivada gravedad_accidente creada ✓")

    # ── Relleno de nulos ─────────────────────────────────────
    df['HAY_NIEBLA']          = df['HAY_NIEBLA'].fillna(0).astype(int)
    df['TOTAL_VICTIMAS_24H']  = df['TOTAL_VICTIMAS_24H'].fillna(0)
    df['TOTAL_VEHICULOS']     = df['TOTAL_VEHICULOS'].fillna(1)

    logger.info(f"Transformación completada. Shape final: {df.shape}")
    return df
