# Guia de Despliegue - Sistema End-to-End

### SCY1101 EP3 | Accidentes de Trafico Espana 2024

---

## Requisitos previos

- Python 3.11 o superior
- Docker Desktop (para la opcion con contenedores)
- El archivo `accidentes_limpios.csv` colocado en la carpeta `/data/`

---

## Opcion A - Ejecucion local (sin Docker)

### Paso 1: Instalar dependencias
```bash
pip install -r requirements.txt
```

### Paso 2: Colocar el dataset
Copiar `accidentes_limpios.csv` dentro de la carpeta `data/`.

### Paso 3: Ejecutar el pipeline ETL
```bash
python etl/pipeline.py
```
Esto crea la base de datos SQLite con los datos procesados. Solo se ejecuta una vez.

### Paso 4: Iniciar la API (en una terminal nueva)
```bash
uvicorn api.main:app --reload --port 8000
```

### Paso 5: Iniciar el dashboard (en otra terminal nueva)
```bash
python dashboards/app.py
```

### Paso 6: Acceder
- Dashboard: http://localhost:8050
- API: http://localhost:8000/docs

---

## Opcion B - Despliegue con Docker (recomendado)

### Paso 1: Abrir Docker Desktop
Esperar a que el motor de Docker este corriendo (icono de la ballena estable).

### Paso 2: Colocar el dataset
Copiar `accidentes_limpios.csv` dentro de la carpeta `data/`.

### Paso 3: Levantar todo el sistema
```bash
docker-compose up --build
```
Este unico comando construye las tres imagenes, ejecuta el pipeline ETL, y levanta la API y el dashboard automaticamente.

### Paso 4: Acceder
- Dashboard: http://localhost:8050
- API: http://localhost:8000/docs

### Paso 5: Detener el sistema
```bash
docker-compose down
```

---

## Ejecutar las pruebas automatizadas

```bash
pytest tests/ -v
```

Esto ejecuta los 34 tests (18 del ETL y 16 de la API) y muestra el resultado de cada uno.

---

## Solucion de problemas comunes

| Problema | Solucion |
|----------|----------|
| "uvicorn no se reconoce" | Usar `python -m uvicorn api.main:app --reload --port 8000` |
| "No module named dotenv" | Ejecutar `pip install python-dotenv` |
| Error al instalar pandas | Quitar los numeros de version del requirements.txt |
| Docker: "cannot connect" | Abrir Docker Desktop y esperar a que arranque |
| Docker: error con apt-get / curl | Ya corregido en el Dockerfile.etl actual |
| Dataset no encontrado | Verificar que el CSV este en la carpeta `data/` |

---

*SCY1101 - Programacion para la Ciencia de Datos | Duoc UC 2025*
