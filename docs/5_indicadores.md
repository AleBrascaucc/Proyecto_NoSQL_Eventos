# 5. Indicadores ejecutados

Los tres indicadores se ejecutaron contra gestion_eventos el 29/10/2026. La base
informo 22 eventos y 201 inscripciones. El notebook quedo guardado con seis celdas
de codigo ejecutadas y cero errores. Ver 6_resultados.md para resultados y limites.

| Indicador | Poblacion y unidad | Resultado observado |
|---|---|---|
| I1 Demanda | Selecciones de actividades en inscripciones confirmadas; agrupar por evento y codigo | 147 selecciones en 35 pares; 152 confirmadas, 52 sin actividad |
| I2 Ocupacion | Confirmadas/capacidad por evento publicado o finalizado | 17 eventos; 143/682; global 20,97%; promedio simple 25,12% |
| I3 Recaudacion bruta | Sumar importe por mes UTC de inscripcion, incluyendo canceladas | Agosto 234000; septiembre 0; octubre 555000; total 789000 |

I1 e I2 tienen poblaciones diferentes: I2 excluye los eventos cancelados. Las nueve
confirmadas del cancelado original explican 152 frente a 143. Selecciones no es
asistencia ni cantidad de personas unicas entre eventos.

I3 incluye las 49 canceladas, con importe registrado de 144000 incluido sin deducir.
No se registran reembolsos ni costos: no representa ingreso neto ni ganancia.
Septiembre tiene una inscripcion de importe cero. Decimal se conserva en calculos;
float se usa solo al graficar.

## Archivos y reproduccion

- analisis/i1_demanda.py: tabla, barras completas e interpretacion.
- analisis/i2_ocupacion.py: tabla y porcentajes; distingue global de promedio simple.
- analisis/i3_recaudacion.py: tabla, lineas e interpretacion.
- analisis/analisis.ipynb: las tres secciones ejecutadas.
- analisis/resultados/: CSV, corte.json, interpretaciones y PNG/SVG por ejecucion.

Cada indicador usa su propia instantanea snapshot, sin escrituras en MongoDB.
Los cortes no son un snapshot compartido entre indicadores. Las ejecuciones de
scripts y notebook se conservan en carpetas separadas; no se borran las anteriores.
Los dos graficos son barras para I1 y lineas para I3; PNG y SVG son dos formatos
de una misma figura. No se agregan figuras para inflar la cantidad de indicadores.

Con Docker iniciado, desde la raiz y con dependencias de analisis instaladas:

```powershell
.\.venv\Scripts\python.exe .\analisis\i1_demanda.py
.\.venv\Scripts\python.exe .\analisis\i2_ocupacion.py
.\.venv\Scripts\python.exe .\analisis\i3_recaudacion.py
```

Cada ejecucion agrega resultados locales con nuevo corte y no modifica la base.
Consultar README para preparar el entorno y ejecutar el notebook con su kernel.
