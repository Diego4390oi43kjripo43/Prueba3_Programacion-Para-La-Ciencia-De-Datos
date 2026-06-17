"""
validate.py — Validación de esquemas y calidad de datos
Pipeline ETL | Accidentes de Tráfico España 2024
"""
import pandas as pd
import logging

logger = logging.getLogger(__name__)

COLUMNAS_REQUERIDAS = [
    'HORA', 'MES', 'DIA_SEMANA', 'TOTAL_VICTIMAS_24H',
    'TOTAL_VEHICULOS', 'CONDICION_METEO', 'CONDICION_ILUMINACION',
    'CONDICION_FIRME', 'TRAZADO_PLANTA', 'HAY_NIEBLA',
    'TIPO_VIA', 'TIPO_ACCIDENTE'
]

RANGOS_VALIDOS = {
    'HORA':       (0, 23),
    'MES':        (1, 12),
    'DIA_SEMANA': (1, 7),
    'HAY_NIEBLA': (0, 1),
}


def validar_columnas(df: pd.DataFrame) -> dict:
    """Verifica que las columnas requeridas existan en el DataFrame."""
    faltantes = [c for c in COLUMNAS_REQUERIDAS if c not in df.columns]
    presentes = [c for c in COLUMNAS_REQUERIDAS if c in df.columns]

    resultado = {
        'columnas_presentes': len(presentes),
        'columnas_faltantes': faltantes,
        'valido': len(faltantes) == 0
    }

    if faltantes:
        logger.warning(f"Columnas faltantes en el dataset: {faltantes}")
    else:
        logger.info("Validación de columnas: TODAS PRESENTES ✓")

    return resultado


def validar_rangos(df: pd.DataFrame) -> dict:
    """Verifica que los valores numéricos estén dentro de rangos válidos."""
    errores = {}

    for col, (min_val, max_val) in RANGOS_VALIDOS.items():
        if col in df.columns:
            fuera_rango = df[(df[col] < min_val) | (df[col] > max_val)]
            if len(fuera_rango) > 0:
                errores[col] = len(fuera_rango)
                logger.warning(
                    f"{col}: {len(fuera_rango)} valores fuera del rango [{min_val}, {max_val}]"
                )

    if not errores:
        logger.info("Validación de rangos: TODO DENTRO DE RANGO ✓")

    return {'errores_por_columna': errores, 'valido': len(errores) == 0}


def reporte_calidad(df: pd.DataFrame) -> dict:
    """Genera un reporte completo de calidad de datos."""
    nulos = df.isnull().sum()
    nulos_dict = {k: int(v) for k, v in nulos[nulos > 0].items()}
    total_celdas = len(df) * len(df.columns)

    reporte = {
        'total_registros':        len(df),
        'total_columnas':         len(df.columns),
        'columnas_con_nulos':     nulos_dict,
        'porcentaje_nulos_total': round(df.isnull().sum().sum() / total_celdas * 100, 2),
        'duplicados':             int(df.duplicated().sum()),
    }

    logger.info(
        f"Calidad: {reporte['total_registros']} registros | "
        f"{reporte['porcentaje_nulos_total']}% nulos | "
        f"{reporte['duplicados']} duplicados"
    )

    return reporte
