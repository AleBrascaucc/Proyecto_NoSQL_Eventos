# I1. Demanda por actividad

Corte de ejecucion UTC: 2026-10-29T21:46:46.955263+00:00.
Base consultada: 22 eventos y 201 inscripciones.

Hay **152 inscripciones confirmadas**, de las cuales **52** no seleccionaron actividades.
Se registran **147 selecciones** distribuidas en **35 pares de evento y actividad**.

La mayor demanda observada es de **8 selecciones**:
- Emprendimientos 3 — ACT-01: Emprendimientos práctico.

## Interpretacion y limites

La unidad es una seleccion por evento y actividad. No son asistentes efectivos ni personas unicas entre eventos.
Una inscripcion puede elegir varias actividades: la suma de selecciones puede superar el numero de inscriptos que eligieron alguna.
Se agrupa por evento y codigo, porque ACT-01 de un evento no es la misma actividad que ACT-01 de otro.
I1 filtra estado de inscripcion, no estado del evento. Puede incluir demanda historica de un evento cancelado si conserva confirmadas.
Las actividades sin selecciones no aparecen como grupos; el grafico muestra todos los grupos con demanda positiva, sin recortar a un top.
Estos datos ficticios permiten demostrar la tecnica; no justifican inferencias sobre demanda real del mercado.
La inscripcion cancelada de la demo queda excluida por el filtro; los eventos sin inscripciones no aportan selecciones.
