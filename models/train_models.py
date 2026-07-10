"""
train_models.py - Entrenamiento de modelos de Machine Learning
Examen Final Transversal (EFT) | SCY1101
Accidentes de Trafico Espana 2024

Genera dos modelos:
  1. CLASIFICACION: predice la gravedad del accidente (Baja/Media/Alta)
  2. REGRESION: predice el numero de victimas en 24h

Uso:
    python models/train_models.py
"""
import os, sys, logging, json
from pathlib import Path

import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                             f1_score, confusion_matrix, classification_report,
                             mean_absolute_error, mean_squared_error, r2_score)

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

CSV_PATH   = os.getenv('CSV_PATH', './data/accidentes_limpios.csv')
MODELS_DIR = './models'

# Variables predictoras (features) comunes a ambos modelos
FEATURES = ['HORA', 'MES', 'DIA_SEMANA', 'TOTAL_VEHICULOS',
            'CONDICION_METEO', 'CONDICION_ILUMINACION', 'CONDICION_FIRME',
            'TRAZADO_PLANTA', 'HAY_NIEBLA', 'TIPO_VIA', 'TIPO_ACCIDENTE']


def cargar_y_preparar():
    """Carga el dataset y prepara las variables predictoras."""
    logger.info(f"Cargando dataset desde {CSV_PATH}")
    df = pd.read_csv(CSV_PATH, low_memory=False)

    # Limpiar nulos en las features
    for col in FEATURES:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    logger.info(f"Dataset preparado: {len(df):,} registros | {len(FEATURES)} features")
    return df


def entrenar_clasificacion(df):
    """
    Modelo de CLASIFICACION: predice gravedad_accidente (Baja/Media/Alta).
    Usa DecisionTree + RandomForest, optimiza con GridSearchCV.
    """
    logger.info("=" * 60)
    logger.info("MODELO 1: CLASIFICACION - Gravedad del accidente")
    logger.info("=" * 60)

    X = df[FEATURES]
    y = df['gravedad_accidente']

    # Escalado
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Particion 80/20 estratificada (mantiene proporcion de clases)
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42, stratify=y)

    # --- Modelo A: Decision Tree con GridSearchCV ---
    logger.info("Optimizando Decision Tree con GridSearchCV...")
    param_grid = {
        'max_depth': [5, 10, 15],
        'min_samples_split': [2, 5, 10],
        'criterion': ['gini', 'entropy'],
    }
    grid = GridSearchCV(
        DecisionTreeClassifier(random_state=42, class_weight='balanced'),
        param_grid, cv=3, scoring='f1_macro', n_jobs=-1)
    grid.fit(X_train, y_train)
    tree_best = grid.best_estimator_
    logger.info(f"Mejores parametros: {grid.best_params_}")

    # --- Modelo B: Random Forest (comparacion) ---
    logger.info("Entrenando Random Forest...")
    rf = RandomForestClassifier(n_estimators=100, random_state=42,
                                 class_weight='balanced', n_jobs=-1)
    rf.fit(X_train, y_train)

    # Evaluar ambos
    resultados = {}
    for nombre, modelo in [('DecisionTree', tree_best), ('RandomForest', rf)]:
        y_pred = modelo.predict(X_test)
        resultados[nombre] = {
            'accuracy':  round(accuracy_score(y_test, y_pred), 4),
            'precision': round(precision_score(y_test, y_pred, average='macro', zero_division=0), 4),
            'recall':    round(recall_score(y_test, y_pred, average='macro', zero_division=0), 4),
            'f1':        round(f1_score(y_test, y_pred, average='macro', zero_division=0), 4),
        }
        logger.info(f"{nombre}: {resultados[nombre]}")

    # Elegir el mejor por F1
    mejor = max(resultados, key=lambda k: resultados[k]['f1'])
    modelo_final = tree_best if mejor == 'DecisionTree' else rf
    logger.info(f"MEJOR MODELO CLASIFICACION: {mejor}")

    # Matriz de confusion del mejor
    y_pred = modelo_final.predict(X_test)
    cm = confusion_matrix(y_test, y_pred, labels=['Baja','Media','Alta'])
    logger.info(f"Matriz de confusion:\n{cm}")

    # Importancia de variables
    importancias = dict(zip(FEATURES, modelo_final.feature_importances_.round(4)))
    importancias = dict(sorted(importancias.items(), key=lambda x: x[1], reverse=True))

    # Serializar modelo + scaler
    joblib.dump(modelo_final, f'{MODELS_DIR}/modelo_clasificacion.pkl')
    joblib.dump(scaler,       f'{MODELS_DIR}/scaler_clasificacion.pkl')
    logger.info("Modelo de clasificacion guardado: modelo_clasificacion.pkl")

    return {
        'tipo': 'clasificacion',
        'mejor_modelo': mejor,
        'resultados': resultados,
        'matriz_confusion': cm.tolist(),
        'importancia_variables': importancias,
        'mejores_hiperparametros': grid.best_params_,
    }


def entrenar_regresion(df):
    """
    Modelo de REGRESION: predice TOTAL_VICTIMAS_24H (numero de victimas).
    Usa LinearRegression + RandomForestRegressor.
    """
    logger.info("=" * 60)
    logger.info("MODELO 2: REGRESION - Numero de victimas")
    logger.info("=" * 60)

    X = df[FEATURES]
    y = df['TOTAL_VICTIMAS_24H']

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42)

    resultados = {}
    modelos = {
        'LinearRegression': LinearRegression(),
        'RandomForestRegressor': RandomForestRegressor(
            n_estimators=100, random_state=42, n_jobs=-1, max_depth=10),
    }
    for nombre, modelo in modelos.items():
        modelo.fit(X_train, y_train)
        y_pred = modelo.predict(X_test)
        resultados[nombre] = {
            'mae':  round(mean_absolute_error(y_test, y_pred), 4),
            'rmse': round(np.sqrt(mean_squared_error(y_test, y_pred)), 4),
            'r2':   round(r2_score(y_test, y_pred), 4),
        }
        logger.info(f"{nombre}: {resultados[nombre]}")

    # Mejor por R2
    mejor = max(resultados, key=lambda k: resultados[k]['r2'])
    modelo_final = modelos[mejor]
    logger.info(f"MEJOR MODELO REGRESION: {mejor}")

    joblib.dump(modelo_final, f'{MODELS_DIR}/modelo_regresion.pkl')
    joblib.dump(scaler,       f'{MODELS_DIR}/scaler_regresion.pkl')
    logger.info("Modelo de regresion guardado: modelo_regresion.pkl")

    return {
        'tipo': 'regresion',
        'mejor_modelo': mejor,
        'resultados': resultados,
    }


def main():
    os.makedirs(MODELS_DIR, exist_ok=True)
    df = cargar_y_preparar()

    reporte = {
        'clasificacion': entrenar_clasificacion(df),
        'regresion':     entrenar_regresion(df),
    }

    # Guardar reporte de metricas en JSON
    with open(f'{MODELS_DIR}/metricas.json', 'w', encoding='utf-8') as f:
        json.dump(reporte, f, indent=2, ensure_ascii=False)

    logger.info("=" * 60)
    logger.info("ENTRENAMIENTO COMPLETADO - metricas.json generado")
    logger.info("=" * 60)
    return reporte


if __name__ == '__main__':
    main()
