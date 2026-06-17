# Manual de Usuario - Dashboard de Accidentalidad Vial

### SCY1101 EP3 | Accidentes de Trafico Espana 2024

---

## 1. Que es este sistema

Este sistema permite analizar de forma visual e interactiva los accidentes de trafico ocurridos en Espana durante 2024. Los datos provienen de un dataset oficial de 101.995 accidentes, enriquecido con informacion meteorologica obtenida de una API externa.

El sistema esta pensado para tres tipos de usuario distintos, cada uno con su propia vista dentro del dashboard.

---

## 2. Como acceder al dashboard

Una vez que el sistema esta corriendo (ver Guia de Despliegue), abrir un navegador web e ingresar a:

```
http://localhost:8050
```

La API con su documentacion esta disponible en:

```
http://localhost:8000/docs
```

---

## 3. Las tres vistas del dashboard

El dashboard se divide en tres pestanas en la parte superior. Cada una esta disenada para una audiencia diferente.

### Vista Ejecutiva
Pensada para gerentes y directivos que necesitan una mirada rapida y general.

Contiene:
- Cinco tarjetas con los indicadores principales (total de accidentes, victimas, accidentes graves, vehiculos y casos con niebla)
- Un grafico de barras con la distribucion por gravedad
- Un grafico de la evolucion mensual de accidentes
- Un grafico circular con la distribucion por tramo horario

Controles disponibles: filtro por gravedad y filtro por tramo horario.

### Vista Tecnica
Pensada para analistas de datos que necesitan profundizar en los patrones.

Contiene:
- Un mapa de calor que cruza el dia de la semana con la hora del dia
- Un grafico de accidentes por condicion meteorologica
- Un grafico de distribucion por hora del dia

Controles disponibles: deslizador de rango de meses y selector de condicion de niebla.

### Vista Operativa
Pensada para equipos de emergencia y gestion de trafico que necesitan informacion accionable.

Contiene:
- Tres tarjetas de alerta rapida (hora pico, casos con niebla, mes pico)
- Un grafico de accidentes por dia de la semana
- Un grafico comparativo de gravedad segun haya niebla o no

Controles disponibles: casillas para activar tramos horarios y selector de niebla.

---

## 4. Como usar los filtros

Todos los filtros funcionan en tiempo real. Al cambiar un valor en un menu desplegable, deslizador o casilla, los graficos se actualizan automaticamente sin necesidad de recargar la pagina.

- Los menus desplegables permiten elegir una sola opcion.
- El deslizador de meses permite seleccionar un rango arrastrando los extremos.
- Las casillas permiten activar o desactivar varios tramos a la vez.

---

## 5. Interpretacion de los datos principales

| Indicador | Significado |
|-----------|-------------|
| Total Accidentes | Cantidad total de accidentes registrados en 2024 |
| Victimas Totales 24h | Suma de personas afectadas en las primeras 24 horas |
| Accidentes Graves | Accidentes con gravedad Alta (mas de 2 victimas) |
| Vehiculos Involucrados | Suma total de vehiculos en todos los accidentes |
| Accidentes con Niebla | Accidentes ocurridos con presencia de niebla |

---

*SCY1101 - Programacion para la Ciencia de Datos | Duoc UC 2025*
