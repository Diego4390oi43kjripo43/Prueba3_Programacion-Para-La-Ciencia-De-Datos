"""
extract_api.py — Extracción de datos meteorológicos históricos
Fuente 2: Open-Meteo Archive API (gratuita, sin API key)
Pipeline ETL | Accidentes de Tráfico España 2024
"""
import requests
import pandas as pd
import logging
import os

logger = logging.getLogger(__name__)

BASE_URL = os.getenv('OPENMETEO_URL', 'https://archive-api.open-meteo.com/v1/archive')

# Ciudades representativas de España con coordenadas
CIUDADES_ESPANA = {
    'Madrid':    (40.4168, -3.7038),
    'Barcelona': (41.3851,  2.1734),
    'Valencia':  (39.4699, -0.3763),
    'Sevilla':   (37.3891, -5.9845),
    'Zaragoza':  (41.6488, -0.8891),
}


def extraer_datos_meteorologicos(anio: int = 2024) -> pd.DataFrame:
    """
    Extrae datos meteorológicos históricos diarios por ciudad española.
    Los agrega a nivel mensual para unirlos con el dataset de accidentes.

    Args:
        anio: Año a consultar (default 2024)

    Returns:
        DataFrame mensual con precipitación, temperatura y viento medios
    """
    registros = []

    for ciudad, (lat, lon) in CIUDADES_ESPANA.items():
        try:
            params = {
                'latitude':   lat,
                'longitude':  lon,
                'start_date': f'{anio}-01-01',
                'end_date':   f'{anio}-12-31',
                'daily':      'precipitation_sum,temperature_2m_max,windspeed_10m_max',
                'timezone':   'Europe/Madrid'
            }

            logger.info(f"[API] Consultando Open-Meteo para {ciudad}...")
            resp = requests.get(BASE_URL, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            daily = data.get('daily', {})

            for i, fecha in enumerate(daily.get('time', [])):
                mes = int(fecha[5:7])
                registros.append({
                    'ciudad':            ciudad,
                    'mes':               mes,
                    'precipitacion_mm':  daily['precipitation_sum'][i] or 0.0,
                    'temp_max_c':        daily['temperature_2m_max'][i] or 0.0,
                    'viento_max_kmh':    daily['windspeed_10m_max'][i] or 0.0,
                })

            logger.info(f"[API] {ciudad}: {len(daily.get('time', []))} días extraídos ✓")

        except requests.exceptions.Timeout:
            logger.error(f"[API] Timeout consultando {ciudad}. Continuando...")
        except requests.exceptions.RequestException as e:
            logger.error(f"[API] Error para {ciudad}: {e}. Continuando...")

    if not registros:
        logger.warning("[API] Sin datos de la API. Usando datos de respaldo estáticos.")
        return _datos_respaldo()

    df = pd.DataFrame(registros)

    # Agregar a nivel mensual (promedio nacional)
    df_mensual = (
        df.groupby('mes')
        .agg(
            precipitacion_media_mm=('precipitacion_mm', 'mean'),
            temp_max_media_c=('temp_max_c', 'mean'),
            viento_max_media_kmh=('viento_max_kmh', 'mean')
        )
        .reset_index()
        .rename(columns={'mes': 'MES'})
    )

    df_mensual = df_mensual.round(2)
    logger.info(f"[API] Datos meteorológicos: {len(df_mensual)} meses procesados ✓")
    return df_mensual


def _datos_respaldo() -> pd.DataFrame:
    """Datos meteorológicos estáticos de respaldo si la API no responde."""
    return pd.DataFrame({
        'MES':                    list(range(1, 13)),
        'precipitacion_media_mm': [45, 38, 32, 28, 22, 8, 3, 5, 20, 42, 50, 55],
        'temp_max_media_c':       [9,  11, 15, 18, 23, 28, 33, 32, 26, 20, 13,  9],
        'viento_max_media_kmh':   [25, 22, 28, 24, 20, 18, 16, 17, 22, 26, 28, 27],
    })
