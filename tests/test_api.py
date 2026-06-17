"""
test_api.py — Tests automatizados de la API RESTful
Ejecutar: pytest tests/ -v
SCY1101 EP3 | Accidentes de Tráfico España 2024
"""
import sys, pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from fastapi.testclient import TestClient
    from api.main import app
    client = TestClient(app)
    API_OK = True
except Exception as e:
    API_OK = False
    print(f"API no disponible para tests: {e}")


@pytest.mark.skipif(not API_OK, reason="API no disponible en este entorno")
class TestAPIEndpoints:

    def test_root_status_200(self):
        """El endpoint raíz debe retornar 200."""
        r = client.get("/")
        assert r.status_code == 200

    def test_root_mensaje(self):
        """El endpoint raíz debe contener el mensaje correcto."""
        r = client.get("/")
        assert "API" in r.json()["message"]
        assert r.json()["status"] == "online"

    def test_health_status_200(self):
        """El health check debe retornar 200."""
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_tiene_status(self):
        """El health check debe tener el campo 'status'."""
        r = client.get("/health")
        assert "status" in r.json()

    def test_kpis_status_200(self):
        """Los KPIs deben retornar 200."""
        r = client.get("/kpis")
        assert r.status_code == 200

    def test_kpis_tiene_campos(self):
        """Los KPIs deben tener todos los campos requeridos."""
        r = client.get("/kpis")
        data = r.json()
        campos = ['total_accidentes', 'total_victimas_24h',
                  'total_vehiculos', 'mes_mas_accidentes', 'hora_mas_accidentes']
        for campo in campos:
            assert campo in data, f"Campo faltante: {campo}"

    def test_kpis_total_accidentes_positivo(self):
        """El total de accidentes debe ser positivo."""
        r = client.get("/kpis")
        assert r.json()["total_accidentes"] > 0

    def test_por_mes_retorna_lista(self):
        """por-mes debe retornar una lista."""
        r = client.get("/accidentes/por-mes")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_por_mes_maximo_12(self):
        """por-mes no puede tener más de 12 elementos."""
        r = client.get("/accidentes/por-mes")
        assert len(r.json()) <= 12

    def test_por_hora_retorna_lista(self):
        """por-hora debe retornar una lista."""
        r = client.get("/accidentes/por-hora")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_por_hora_maximo_24(self):
        """por-hora no puede tener más de 24 elementos."""
        r = client.get("/accidentes/por-hora")
        assert len(r.json()) <= 24

    def test_filtrar_mes_valido(self):
        """Filtrar por mes válido debe retornar 200."""
        r = client.get("/accidentes/filtrar?mes=6")
        assert r.status_code == 200

    def test_filtrar_tiene_total(self):
        """El endpoint filtrar debe retornar total_encontrados."""
        r = client.get("/accidentes/filtrar?mes=1")
        assert "total_encontrados" in r.json()

    def test_filtrar_mes_invalido_retorna_422(self):
        """Un mes fuera del rango 1-12 debe retornar error 422."""
        r = client.get("/accidentes/filtrar?mes=13")
        assert r.status_code == 422

    def test_filtrar_limit_respetado(self):
        """El parámetro limit debe ser respetado."""
        r = client.get("/accidentes/filtrar?limit=5")
        data = r.json()
        assert len(data['datos']) <= 5

    def test_por_niebla_retorna_lista(self):
        """por-niebla debe retornar una lista."""
        r = client.get("/accidentes/por-niebla")
        assert r.status_code == 200
        assert isinstance(r.json(), list)
