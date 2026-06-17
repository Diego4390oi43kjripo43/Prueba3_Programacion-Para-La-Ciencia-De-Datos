"""
conftest.py — Fixtures compartidos para todos los tests
SCY1101 EP3 | Accidentes de Tráfico España 2024
"""
import sys, pytest, pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def df_muestra():
    """DataFrame de muestra que simula el dataset de accidentes."""
    return pd.DataFrame({
        'HORA':                [3,  8, 14, 22, 10, 16],
        'MES':                 [1,  2,  3,  4,  5,  6],
        'DIA_SEMANA':          [1,  2,  3,  4,  5,  6],
        'TOTAL_VICTIMAS_24H':  [0,  1,  2,  5,  0,  1],
        'TOTAL_VEHICULOS':     [1,  2,  1,  3,  2,  1],
        'CONDICION_METEO':     [1,  1,  2,  2,  1,  3],
        'CONDICION_ILUMINACION':[1, 2,  1,  3,  2,  1],
        'CONDICION_FIRME':     [1,  1,  2,  1,  1,  2],
        'TRAZADO_PLANTA':      [1,  2,  3,  1,  2,  3],
        'HAY_NIEBLA':          [0,  0,  1,  0,  0,  1],
        'TIPO_VIA':            [1,  2,  3,  1,  2,  1],
        'TIPO_ACCIDENTE':      [1,  2,  1,  3,  2,  1],
    })


@pytest.fixture
def df_con_nulos():
    """DataFrame con valores nulos para tests de limpieza."""
    return pd.DataFrame({
        'HORA':                [8,  None, 14],
        'MES':                 [1,  2,    None],
        'DIA_SEMANA':          [1,  2,    3],
        'TOTAL_VICTIMAS_24H':  [None, 1,  2],
        'TOTAL_VEHICULOS':     [1,  None,  1],
        'CONDICION_METEO':     [1,  1,    2],
        'CONDICION_ILUMINACION':[1, 2,    1],
        'CONDICION_FIRME':     [1,  1,    2],
        'TRAZADO_PLANTA':      [1,  2,    3],
        'HAY_NIEBLA':          [None, 0,  1],
        'TIPO_VIA':            [1,  2,    3],
        'TIPO_ACCIDENTE':      [1,  2,    1],
    })
