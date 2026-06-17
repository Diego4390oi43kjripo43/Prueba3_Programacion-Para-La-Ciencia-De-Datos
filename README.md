#  Sistema de Análisis de Accidentalidad Vial — España 2024
### Evaluación Parcial N°3 — SCY1101 Programación para la Ciencia de Datos
**Docente:** Mauricio González V. | **Duoc UC 2025**

---

##  Descripción del Proyecto

Sistema **End-to-End** de análisis de accidentalidad vial que integra tres fuentes de datos en un pipeline ETL automatizado, expone los datos mediante una API RESTful y los visualiza a través de un dashboard interactivo multiaudiencia, todo completamente containerizado con Docker.

| Componente | Tecnología | Puerto |
|------------|-----------|--------|
| Pipeline ETL | Python + SQLite | — |
| API RESTful | FastAPI | 8000 |
| Dashboard | Plotly Dash | 8050 |
| Containerización | Docker + docker-compose | — |

---

##  Equipo

| Integrante | Rol | Responsabilidades |
|-----------|-----|------------------|
| **Diego González** | Líder / Product Owner | Documentación, diagramas arquitectura, README, coordinación ágil |
| **Carlos Contreras** | Data Engineer | Pipeline ETL, Docker, SQLite, pruebas unitarias |
| **Ricardo Leon** | Data Analyst | API RESTful, Dashboard Dash, vistas multiaudiencia |

---

##  Estructura del Proyecto

```
proyecto-ep3/
├── 📁 etl/
│   ├── pipeline.py          ← Orquestador principal del ETL
│   ├── extract_csv.py       ← Fuente 1: accidentes_limpios.csv
│   ├── extract_api.py       ← Fuente 2: Open-Meteo API REST
│   ├── load_db.py           ← Fuente 3: SQLite (post-ETL)
│   └── validate.py          ← Validación de esquemas y calidad
├── 📁 dashboards/
│   └── app.py               ← Dashboard Plotly Dash (3 vistas)
├── 📁 api/
│   └── main.py              ← API RESTful FastAPI
├── 📁 docker/
│   ├── Dockerfile.etl       ← Imagen Docker para ETL
│   ├── Dockerfile.dashboard ← Imagen Docker para Dashboard
│   └── Dockerfile.api       ← Imagen Docker para API
├── 📁 tests/
│   ├── conftest.py          ← Fixtures compartidos
│   ├── test_etl.py          ← 14 tests del pipeline ETL
│   └── test_api.py          ← 15 tests de la API RESTful
├── 📁 data/                 ← Dataset CSV + base de datos SQLite
├── 📁 docs/                 ← Diagramas de arquitectura
├── 📁 repo/                 ← Evidencia de uso de Git
├── docker-compose.yml       ← Orquestación de los 3 servicios
├── requirements.txt         ← Dependencias Python
├── .env                     ← Variables de entorno
└── README.md                ← Este archivo
```

---

##  Las 3 Fuentes de Datos

### Fuente 1 — CSV Estático
- **Archivo:** `accidentes_limpios.csv`
- **Registros:** 101.995 accidentes viales
- **Variables clave:** HORA, MES, DIA_SEMANA, TOTAL_VICTIMAS_24H, TOTAL_VEHICULOS, HAY_NIEBLA, TIPO_VIA, TIPO_ACCIDENTE
- **Variables derivadas:** TRAMO_HORA (Mañana/Tarde/Noche/Madrugada), gravedad_accidente (Baja/Media/Alta)

### Fuente 2 — API REST (Open-Meteo Archive)
- **URL:** `https://archive-api.open-meteo.com/v1/archive`
- **Sin API key** — completamente gratuita y pública
- **Datos:** Precipitación, temperatura máxima, viento máximo por ciudad española
- **Ciudades:** Madrid, Barcelona, Valencia, Sevilla, Zaragoza
- **Resultado:** Datos meteorológicos medios mensuales para 2024

### Fuente 3 — Base de Datos SQLite
- **Archivo:** `data/accidentes_ep3.db`
- **Tablas:** `accidentes`, `meteorologia`
- **Vista:** `accidentes_enriquecidos` (JOIN accidentes + meteorología por MES)
- **Índices:** MES, HORA, HAY_NIEBLA (optimización de consultas)

---

##  KPIs del Dataset

| KPI | Valor |
|-----|-------|
| Total accidentes | 101.995 |
| Víctimas totales (24h) | 136.427 |
| Vehículos involucrados | 176.330 |
| Accidentes con niebla | 7.482 |
| Mes pico | Julio (9.333 acc.) |

---

##  Instalación y Ejecución

### Opción A — Ejecución Local

```bash
# 1. Clonar repositorio
git clone https://github.com/Diego4390oi43kjripo43/Proyecto_EP3.git
cd Proyecto_EP3

# 2. Copiar dataset
cp /ruta/a/accidentes_limpios.csv ./data/

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar pipeline ETL
python etl/pipeline.py

# 5. Iniciar API (nueva terminal)
uvicorn api.main:app --reload --port 8000

# 6. Iniciar Dashboard (nueva terminal)
python dashboards/app.py
```

### Opción B — Docker (Recomendada)

```bash
# 1. Copiar dataset
cp /ruta/a/accidentes_limpios.csv ./data/

# 2. Levantar todos los servicios
docker-compose up --build

# Dashboard: http://localhost:8050
# API:       http://localhost:8000/docs
```

---

##  Tests Automatizados

```bash
# Ejecutar todos los tests
pytest tests/ -v

# Con reporte de cobertura
pytest tests/ -v --tb=short

# Solo tests del ETL
pytest tests/test_etl.py -v

# Solo tests de la API
pytest tests/test_api.py -v
```

**Cobertura de tests:**
- `test_etl.py`: 14 tests (transformación, validación, API de respaldo)
- `test_api.py`: 15 tests (endpoints, filtros, estructura de respuestas)

---

##  Endpoints de la API

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Estado de la API |
| GET | `/health` | Health check del sistema |
| GET | `/kpis` | KPIs principales (Vista Ejecutiva) |
| GET | `/accidentes/por-mes` | Accidentes agrupados por mes |
| GET | `/accidentes/por-hora` | Distribución horaria |
| GET | `/accidentes/por-dia` | Accidentes por día de la semana |
| GET | `/accidentes/por-niebla` | Comparativa con/sin niebla |
| GET | `/accidentes/filtrar` | Filtros dinámicos (mes, niebla, tipo_via) |
| GET | `/meteorologia` | Datos meteorológicos mensuales |
| GET | `/docs` | Documentación automática Swagger UI |

---

##  Dashboard — Vistas por Audiencia

###  Vista Ejecutiva
KPI cards (accidentes, víctimas, gravedad, vehículos, niebla) + gráfico de barras por gravedad + evolución mensual + distribución por tramo horario. Filtros: gravedad y tramo.

###  Vista Técnica
Heatmap de accidentes por DIA_SEMANA × HORA + distribución por condición meteorológica + área chart por hora del día. Filtros: rango de meses (slider) y condición de niebla.

###  Vista Operativa
Panel de alertas rápidas (hora pico, niebla, mes peak) + barras por día de la semana + comparativa gravedad vs niebla. Filtros: tramos activos (checklist) y niebla.

---

##  Flujo de Trabajo Git

```
main
 └── develop
      ├── feature/etl-pipeline      → Carlos
      ├── feature/dashboard         → Ricardo
      ├── feature/api-rest          → Ricardo
      ├── feature/docker-config     → Carlos
      └── feature/docs-readme       → Diego
```

**Convenciones de commits:**
```
feat: nueva funcionalidad
fix: corrección de bug
docs: cambios en documentación
test: añadir o modificar tests
chore: tareas de configuración
```

---

##  Referencias

- Plotly Dash Documentation: https://dash.plotly.com
- FastAPI Documentation: https://fastapi.tiangolo.com
- Open-Meteo API: https://open-meteo.com
- Docker Documentation: https://docs.docker.com
- Pandas Documentation: https://pandas.pydata.org

---

*SCY1101 — Programación para la Ciencia de Datos | Duoc UC 2025 | EP3*
