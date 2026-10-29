# Entrega final de gestion de eventos

## Documentos de entrega

- informe/Informe_Tecnico_Eventos.docx: informe editable integrado.
- informe/Informe_Tecnico_Eventos.pdf: version de lectura del mismo informe.
- presentacion/Presentacion_Eventos.pptx: 15 diapositivas con notas y graficos editables.
- docs/Guion_Defensa.md: recorrido oral, demo y preguntas probables.
- docs/anexo/postman_id_malformado.png y postman_id_inexistente.png: capturas reales
  de los casos esperados422 y404 suministradas por el usuario.

Fuentes y resultados permanecen en analisis/, api/, scripts/, postman/ y docs/.
Commits previamente comprobados:3cb55a7 y b881392. No se incluyen secretos,
backups de MongoDB ni el entorno virtual en este paquete de documentos.

El informe usa los resultados reales 22eventos/201inscripciones. Distingue la carga
inicial20/200, los planes de indices medidos antes de la demo y los cortes de los
indicadores posteriores. El notebook se ejecuto:6celdas de codigo,0errores.

## Revision previa a entregar

Abrir Word/PDF y PPTX en la PC. Agregar los nombres de los integrantes si la
portada institucional los exige; no se inventaron nombres. La presentacion se
verifico con renderizado y validacion del archivo, no abriendo Microsoft PowerPoint.
Revisar notas y practicar la demo sin recargar la base.

El provisionamiento de volumen virgen esta documentado pero no se ejecuto; si
el profesor exige esa prueba adicional, realizarla en un volumen/proyecto de
prueba separado, no eliminando el volumen actual. Se probo down/up SIN -v sobre
el volumen existente. No se realizaron pruebas de concurrencia o recuperacion.

## Incorporacion y publicacion desde la PC

El instalador solo copia documentos y capturas; no modifica la base ni crea
commits. Primero revisar:

```powershell
git --no-pager status --short
```

Luego, en la rama cambio-modelo-y-estructura:

```powershell
git add -- informe presentacion/Presentacion_Eventos.pptx docs/Guion_Defensa.md docs/anexo/postman_id_malformado.png docs/anexo/postman_id_inexistente.png ENTREGA_FINAL.md
git --no-pager diff --cached --stat
git commit -m "Agrega informe tecnico presentacion y guion de defensa"
git push -u origin cambio-modelo-y-estructura
```

Solo publicar la rama de trabajo; no fusionar ni empujar main. Revisar codigo de
salida de cada comando antes del siguiente. El push debe ejecutarse con una
cuenta con permisos del repositorio AleBrascaucc/Proyecto_NoSQL_Eventos.
Si se rechaza por permisos, conservar los commits locales y pedir acceso al
propietario; no se afirma que se publico hasta ver la confirmacion de Git.

## Criterio de cierre

Archivos integrados, revision local, commit creado y rama publicada. A la fecha
de generacion de este paquete, los ultimos pasos requieren ejecucion en la PC:
la integracion GitHub de esta sesion tiene lectura pero devolvio403 al escribir.

El paquete de cierre incluye publicar_rama.ps1 para revisar rutas, crear el commit
y publicar solo cambio-modelo-y-estructura, sin fusionar main.
