"""
predict.py - Modulo de prediccion con los modelos de ML
Examen Final Transversal (EFT) | SCY1101

Carga los modelos serializados y expone funciones de prediccion
que seran usadas por los endpoints de la API.
"""
import os, logging
import joblib
import numpy as np

logger = logging.getLogger(__name__)

MODELS_DIR = os.getenv('MODELS_DIR', './models')

FEATURES = ['HORA', 'MES', 'DIA_SEMANA', 'TOTAL_VEHICULOS',
            'CONDICION_METEO', 'CONDICION_ILUMINACION', 'CONDICION_FIRME',
            'TRAZADO_PLANTA', 'HAY_NIEBLA', 'TIPO_VIA', 'TIPO_ACCIDENTE']

# Cache de modelos (se cargan una sola vez)
_cache = {}


def _cargar_modelo(nombre):
    """Carga un modelo serializado desde disco (con cache)."""
    if nombre not in _cache:
        ruta = f'{MODELS_DIR}/{nombre}.pkl'
        if not os.path.exists(ruta):
            raise FileNotFoundError(
                f"Modelo {nombre} no encontrado. Ejecuta primero: python models/train_models.py")
        _cache[nombre] = joblib.load(ruta)
        logger.info(f"Modelo cargado: {nombre}")
    return _cache[nombre]


def predecir_gravedad(datos: dict) -> dict:
    """
    Predice la gravedad de un accidente (Baja/Media/Alta).

    Args:
        datos: diccionario con las 11 features del accidente

    Returns:
        dict con la prediccion y la probabilidad
    """
    modelo = _cargar_modelo('modelo_clasificacion')
    scaler = _cargar_modelo('scaler_clasificacion')

    # Construir vector de features en el orden correcto
    X = np.array([[datos.get(f, 0) for f in FEATURES]])
    X_scaled = scaler.transform(X)

    pred = modelo.predict(X_scaled)[0]
    proba = modelo.predict_proba(X_scaled)[0]
    clases = modelo.classes_

    probabilidades = {clase: round(float(p), 4) for clase, p in zip(clases, proba)}

    return {
        'gravedad_predicha': str(pred),
        'probabilidades': probabilidades,
        'features_usadas': datos,
    }


def predecir_victimas(datos: dict) -> dict:
    """
    Predice el numero de victimas de un accidente.

    Args:
        datos: diccionario con las 11 features del accidente

    Returns:
        dict con el numero estimado de victimas
    """
    modelo = _cargar_modelo('modelo_regresion')
    scaler = _cargar_modelo('scaler_regresion')

    X = np.array([[datos.get(f, 0) for f in FEATURES]])
    X_scaled = scaler.transform(X)

    pred = modelo.predict(X_scaled)[0]

    return {
        'victimas_estimadas': round(float(pred), 2),
        'features_usadas': datos,
    }
