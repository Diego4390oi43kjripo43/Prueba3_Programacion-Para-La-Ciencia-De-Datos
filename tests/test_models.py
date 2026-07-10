"""
test_models.py - Tests automatizados de los modelos de ML
Ejecutar: pytest tests/ -v
SCY1101 EFT | Accidentes de Trafico Espana 2024
"""
import sys, os
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

MODELOS_EXISTEN = os.path.exists('./models/modelo_clasificacion.pkl')


@pytest.fixture
def caso_ejemplo():
    """Un accidente de ejemplo para las predicciones."""
    return {
        'HORA': 22, 'MES': 7, 'DIA_SEMANA': 6, 'TOTAL_VEHICULOS': 3,
        'CONDICION_METEO': 2, 'CONDICION_ILUMINACION': 3, 'CONDICION_FIRME': 2,
        'TRAZADO_PLANTA': 1, 'HAY_NIEBLA': 1, 'TIPO_VIA': 3, 'TIPO_ACCIDENTE': 6
    }


class TestFeatures:
    def test_features_definidas(self):
        """La lista de features debe tener 11 variables."""
        from models.predict import FEATURES
        assert len(FEATURES) == 11

    def test_features_contiene_hora(self):
        """HORA debe estar entre las features."""
        from models.predict import FEATURES
        assert 'HORA' in FEATURES


@pytest.mark.skipif(not MODELOS_EXISTEN, reason="Modelos no entrenados aun")
class TestPredicciones:
    def test_gravedad_retorna_clase_valida(self, caso_ejemplo):
        """La prediccion de gravedad debe ser Baja, Media o Alta."""
        from models.predict import predecir_gravedad
        r = predecir_gravedad(caso_ejemplo)
        assert r['gravedad_predicha'] in ['Baja', 'Media', 'Alta']

    def test_gravedad_tiene_probabilidades(self, caso_ejemplo):
        """La prediccion debe incluir probabilidades."""
        from models.predict import predecir_gravedad
        r = predecir_gravedad(caso_ejemplo)
        assert 'probabilidades' in r
        assert len(r['probabilidades']) == 3

    def test_probabilidades_suman_uno(self, caso_ejemplo):
        """Las probabilidades deben sumar aproximadamente 1."""
        from models.predict import predecir_gravedad
        r = predecir_gravedad(caso_ejemplo)
        suma = sum(r['probabilidades'].values())
        assert abs(suma - 1.0) < 0.01

    def test_victimas_retorna_numero_positivo(self, caso_ejemplo):
        """La prediccion de victimas debe ser un numero positivo."""
        from models.predict import predecir_victimas
        r = predecir_victimas(caso_ejemplo)
        assert r['victimas_estimadas'] > 0

    def test_victimas_es_float(self, caso_ejemplo):
        """El numero de victimas debe ser un valor numerico."""
        from models.predict import predecir_victimas
        r = predecir_victimas(caso_ejemplo)
        assert isinstance(r['victimas_estimadas'], (int, float))
