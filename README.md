# PIRULETA - Overlay 3.1

Aplicación de escritorio para Windows para personalizar un overlay de Rocket League y mostrarlo en OBS.
Recibe tiempo, goles, jugadores, turbo, estadísticas y acciones desde la Stats API del juego.
Se conecta y reconecta automáticamente.

## Índice

- [Abrir e instalar](#abrir-e-instalar)
- [Conectar Rocket League (solo la primera vez)](#conectar-rocket-league-solo-la-primera-vez)
- [Mostrarlo en OBS](#mostrarlo-en-obs)
- [Pestañas](#pestañas)
- [Ajustes](#ajustes)
- [Elementos](#elementos)
- [Diseño y estadísticas](#diseño-y-estadísticas)
- [Publicidad](#publicidad)
  - [Patrocinadores rotativos](#patrocinadores-rotativos)
  - [Patrocinadores de jugadas](#patrocinadores-de-jugadas)
- [Perfiles y actualización](#perfiles-y-actualización)
- [Historial](#historial)
- [Contribuidores](#contribuidores)

## Abrir e instalar

- Abre **Piruleta - Overlay.exe**, el acceso directo del escritorio o **Abrir Piruleta.cmd**. El launcher abre el ejecutable de su misma carpeta.
- El ejecutable incluye el diseño, fuentes, logos e iconos necesarios. No requiere instalar Python.
- Mantén la aplicación abierta durante la retransmisión.
- Descargar o clonar el repositorio proporciona el código fuente; el ejecutable se genera aparte. Consulta Generar el ejecutable al final.

Si junto al ejecutable existen `overlay.html`, `boost-animation.js` o archivos de `assets`, la app utiliza esas versiones. Si faltan, utiliza las integradas. El último perfil se guarda en `ultimo_perfil.json`, junto a la aplicación.

## Conectar Rocket League (solo la primera vez)

Al abrir la aplicación, busca automáticamente Rocket League en las instalaciones de Epic Games y Steam (incluidas sus bibliotecas adicionales) y activa su Stats API. Antes de cambiar el archivo guarda una copia `.piruleta-…bak` en la misma carpeta. Si ya está configurado, no crea otra copia ni vuelve a escribirlo.

Si no encuentra el juego en el primer inicio, te pedirá seleccionar su carpeta de instalación. Puedes cancelar y seguir usando la vista previa. En **Ajustes → Configurar conexión al juego…** puedes repetir el proceso cuando quieras. La app recuerda la ubicación y comprueba la configuración al abrirse, también después de una actualización del juego.

Si Rocket League estaba abierto al activar la API, **ciérralo y vuelve a abrirlo**. Si Windows impide modificar el archivo, abre una vez la app como administrador y repite la configuración. No instala complementos ni requiere Python. El juego debe estar instalado en el mismo ordenador; copiar el ejecutable a otro equipo no copia Rocket League.

Como alternativa, con el juego cerrado puedes editar `TAGame/Config/TAStatsAPI.ini` o `DefaultStatsAPI.ini` dentro de su instalación, guardando antes una copia:

```ini
[TAGame.MatchStatsExporter_TA]
PacketSendRate=10
Port=49123
WebPort=49124
```

Inicia el juego y entra como espectador en un partido privado para recibir todos los datos de jugadores. La app utiliza TCP local, normalmente `127.0.0.1:49123`. Los puertos TCP y WebSocket deben ser distintos. Si necesitas otro puerto TCP, puedes guardar `api_port` en un perfil JSON.

El overlay se muestra durante partidos privados online, locales o LAN; se oculta fuera de ellos y si deja de recibir datos. La vista previa utiliza datos ficticios y funciona sin tener un partido abierto.

Referencia: [Stats API de Rocket League](https://www.rocketleague.com/developer/stats-api?lang=en).

## Mostrarlo en OBS

1. Abre la app y pulsa **Copiar URL para OBS**.
2. Añade una **Fuente de navegador** sobre la captura del juego.
3. Pega la URL y configura **1920 × 1080**.
4. Mantén abierta la app. Tras actualizar el programa, actualiza también la fuente de navegador de OBS.

La URL habitual es `http://127.0.0.1:18765/overlay`. Si ese puerto está ocupado, la app elige otro: usa la URL que copia el botón. No añadas `?preview=1` a la fuente de emisión. El servidor solo escucha en el ordenador local.

## Pestañas

| Pestaña | Contenido |
| --- | --- |
| **Ajustes** | Formato BO1, BO2, BO3, BO4, BO5 o BO7; textos; Equipo azul y Equipo naranja; nombres, escudos y victorias de serie. Reiniciar serie, cambiar lados y borrar nombres y escudos, configuración conexión al juego. |
| **Elementos** | Activar o desactivar los diferentes elementos del overlay. |
| **Diseño** | Colores, estilos, tipografía y escala en la mitad izquierda; Fondos en la derecha. |
| **Cámaras** | Nombres de jugadores y enlaces de visualización OBS Ninja / VDO.Ninja. |
| **Publicidad** | Patrocinadores rotativos, poner el intervalo de muestra de cada uno, patrocinadores de jugadas y botones para previsualizar repetición y prórroga. |

**Aplicar cambios** publica los campos editados. Las casillas, selectores y botones de color se aplican al usarlos. **Guardar perfil** y **Cargar perfil** permanecen en la barra inferior.

Las pestañas Posiciones y CSS libre se han eliminado. Los perfiles anteriores mantienen los ajustes guardados; las posiciones que coincidían con los valores antiguos por defecto se adaptan a la distribución actual.

## Ajustes

La pestaña reúne la información del partido y los datos de ambos equipos:

- **Configurar conexión al juego…:** permite elegir la carpeta de Rocket League y preparar su API. Úsalo si la detección automática no encontró el juego o si lo has cambiado de ubicación.
- **Formato de la serie:** BO1, BO2, BO3, BO4, BO5 o BO7. Adapta los huecos de victorias y el cálculo del partido actual. BO2 y BO4 admiten empate al agotar las partidas; BO4 muestra cuatro huecos y las series impares muestran los necesarios para ganar. Si el resultado actual no cabe en un formato menor, primero debes reiniciar la serie.
- **Texto de arriba** y **Texto de abajo:** muestran literalmente lo que escribas en las franjas superior e inferior. Admiten `[GAME]` para el partido actual y `[SERIE]` para el número del formato. Por ejemplo, `PARTIDO [GAME] | AL MEJOR DE [SERIE]` puede mostrar `PARTIDO 2 | AL MEJOR DE 5`. Escribe ambos comandos en mayúsculas.
- **Reiniciar serie:** pone a cero las victorias de ambos equipos. No modifica los goles del partido que envía el juego.
- **Cambiar equipos de lado:** intercambia nombres, escudos, colores y victorias. Tiempo, goles y jugadores siguen los lados azul y naranja que envía Rocket League.
- **Borrar nombres y escudos:** vacía esos datos de los dos equipos sin reiniciar sus victorias.

En las cajas **Equipo azul** y **Equipo naranja** puedes editar:

- **Victorias de serie:** los botones **+** y **−** permiten corregir el resultado. La suma automática al terminar cada partido se activa en Elementos. Debajo de las cajas se indica el objetivo de victorias y si la serie ha terminado o ha quedado empatada.
- **Nombre del equipo:** escribe el nombre que quieres mostrar en el overlay y pulsa **Aplicar cambios**.
- **Subir escudo… / Quitar escudo:** selecciona o elimina el logo de ese equipo. Se admiten PNG o JPEG de hasta 4 MB; la caja muestra una miniatura del escudo cargado.
- **Goles del partido · API:** muestra el resultado recibido del juego. Es informativo: los goles, el tiempo y la prórroga se sincronizan automáticamente y no se editan aquí.

## Elementos

Una casilla marcada activa la función y una desmarcada la oculta o desactiva. Los controles se organizan en General, Cámaras y Publicidad.

### General

| Opción | Función |
| --- | --- |
| **Escudos de equipos** | Muestra u oculta los logos del marcador principal. |
| **Turbo de todos los jugadores** | Muestra las tarjetas laterales con nombres, turbo y barras de cada jugador. |
| **Turbo del jugador en cámara** | Muestra el indicador inferior del jugador que sigue el realizador. El valor cero se muestra como 0 y los cambios de turbo se animan suavemente. |
| **Iconos de acciones** | Activa los avisos de gol, asistencia, parada, tiro y demolición sobre las tarjetas de los jugadores. |
| **Barra de repetición de gol** | Muestra al goleador y al asistente con sus iconos, junto con la velocidad en km/h. Si el gol no tiene asistencia, el goleador aparece centrado. Si la cortina está activada, la barra aparece después. |
| **Sumar victorias automáticamente (API)** | Añade la victoria de serie al equipo ganador al terminar cada partido. Puedes corregir las victorias en Ajustes. |
| **Mostrar estadísticas** | Muestra los datos del jugador observado. El selector permite elegir **Rectángulo** o **Barra compacta**. |
| **Cortina de gol** | Activa una animación de tres segundos, una sola vez al marcar el gol, ocultando temporalmente el marcador. Puedes elegir **Torneo Piruleta**, **Bigness League** o **RCS**, independientemente del estilo del marcador. **Probar cortina** abre una vista previa. |

Los iconos de acciones duran 4,5 segundos. Aparecen en el extremo opuesto al nombre y sustituyen temporalmente al número de turbo. Tiro y gol pueden aparecer juntos. En una demolición, el atacante muestra la bomba y la víctima muestra el aviso con ambos nombres y el color del atacante. Los PNG originales están incluidos localmente; su procedencia se recoge en `assets/action-icons-source.txt`.

### Cámaras: activación y configuración

En **Elementos → Cámaras** se activan los modos:

- **Cámara estadísticas:** muestra la cámara del jugador observado junto a sus estadísticas.
- **Cámaras turbos:** muestra las cámaras de los jugadores debajo de sus tarjetas laterales. Este modo y Cámara estadísticas son excluyentes: activar uno desactiva el otro.
- **Mostrar cámaras turbos durante 6,5 s al terminar la repetición:** muestra temporalmente las cámaras laterales después de la replay. Si estaba activa Cámara estadísticas, se oculta durante esos 6,5 segundos y vuelve después. Las cámaras se precargan para reducir la espera.

Los enlaces se introducen en la pestaña **Cámaras**, que dispone de **ocho filas** con los campos **Jugador** y **Enlace (?view=...)**. Escribe el nombre tal como aparece en Rocket League y su enlace HTTPS de visualización OBS Ninja / VDO.Ninja con `?view=...`; las mayúsculas no afectan a la coincidencia. El nombre identifica al jugador al que corresponde la cámara, no es solo una etiqueta para el realizador. No uses enlaces de emisión `push` ni de director. Pulsa **Aplicar cambios** tras editar las filas.

Las cámaras se reciben sin audio y llenan su marco, recortando la imagen si es necesario para evitar bandas laterales. El nombre y turbo conservan su fondo; la zona que rodea la cámara es transparente. Con las seis cámaras visibles, el turbo inferior de angular, classic y rounded adapta su tamaño para evitar superposiciones; la cámara de estadísticas por sí sola no activa esa reducción.

Durante la repetición se ocultan el marcador, los turbos, las estadísticas y las cámaras; pueden permanecer la barra de repetición y su publicidad. La vista previa muestra las cámaras configuradas o marcos de ejemplo.

### Publicidad: activación

Las casillas **Publicidad rotativa**, **Publicidad en repetición** y **Publicidad en prórroga** permiten activar cada ubicación por separado. Desactivarlas no borra los nombres ni los logos. Sus contenidos, intervalos y pruebas se configuran en la pestaña [Publicidad](#publicidad).

## Diseño y estadísticas

La pestaña Diseño se divide en **Colores** y **Estilos, tipografía y escala** a la izquierda, y **Fondos** a la derecha.

- **Colores:** los botones **Equipo azul**, **Coral**, **Equipo naranja**, **Fondo** y **Texto** cambian la paleta del marcador. El selector permite introducir el color en hexadecimal, por ejemplo `#53A1A8`, o elegirlo visualmente. Azul y naranja identifican los lados: puedes asignarles otros colores.
- **Estilo:** elige **angular**, **rounded** o **classic**. El estilo inicial es rounded con Verdana. En angular, la barra inferior respeta la inclinación del marcador.
- **Tipografía:** selecciona Montserrat, Arial, Segoe UI, Verdana, Trebuchet MS o Impact. Montserrat está incluida. **Importar fuente…** admite archivos TTF, OTF, WOFF o WOFF2 de hasta 16 MB y añade la fuente al selector, dejándola seleccionada.
- **Escala (%):** ajusta el tamaño general del overlay entre el 50 % y el 150 %. Pulsa **Aplicar cambios** tras editar el valor, o confirma con Intro.
- **Fondos por equipo:** los seis selectores permiten asignar por separado el fondo de **Turbo · equipo A/B**, **Estadísticas · equipo A/B** y **Jugadores equipo A/B**. A corresponde al lado azul y B al naranja. Cada selector utiliza un color de la paleta: Fondo principal, Equipo A, Color central, Equipo B o Color del texto. Así, turbo y estadísticas cambian de fondo al observar un jugador del otro equipo; las tarjetas laterales usan el fondo de su lado. Si modificas el color de la paleta, los fondos vinculados se actualizan también.
- **Fondo del marcador en degradado (desmarcado: plano):** activa el degradado del marcador principal o utiliza colores planos.

Las estadísticas se activan y su formato se elige en **Elementos → Mostrar estadísticas**. **Rectángulo** sustituye al nombre anterior Actual; **Barra compacta** distribuye los datos horizontalmente. Muestran nombre, puntos, goles, tiros, asistencias y salvadas del jugador observado según los datos disponibles de la API; no copian la selección de estadísticas del menú del juego.

Por defecto las estadísticas se anclan a los bordes izquierdo e inferior y mantienen su posición al activar las cámaras. El turbo inferior se muestra completo con 12 px de margen. Las tarjetas laterales quedan pegadas a los bordes y sus franjas de color tienen 5 px de grosor.

## Publicidad

En Elementos puedes activar por separado **Publicidad rotativa**, **Publicidad en repetición** y **Publicidad en prórroga**. Desactivar una no borra sus nombres ni logos.

### Patrocinadores rotativos

Por defecto hay **3 anuncios**. El intervalo, admite de 3 a 60 segundos.

- **Añadir patrocinador rotativo** añade una fila, hasta un máximo de **8**.
- **Quitar último patrocinador** elimina siempre la última fila, hasta un mínimo de **2**.
- Los botones se desactivan al alcanzar el límite correspondiente.
- Cada fila admite nombre, logo o ambos. **Añadir logo… / Cambiar logo…** permite seleccionar la imagen y **Quitar logo** elimina solo esa imagen. Dejar la fila sin nombre ni logo la excluye de la rotación.
- Pulsa **Aplicar cambios** después de editar nombres, logos, intervalo o número de filas. Quitar la última fila elimina sus datos; desactivar Publicidad rotativa solo la oculta.
- El panel tiene el mismo ancho y escala que las tarjetas de jugadores. Su posición se adapta al aparecer las cámaras.

### Patrocinadores de jugadas

- **Repetición:** cartel con fondo, PATROCINADO POR y el logo, cerca de la barra inferior. Su franja usa el color del equipo goleador.
- **Prórroga:** cartel con fondo, PRORROGA, subtítulo patrocinada por y logo. Su franja usa el color de Fondo principal. Solo aparece durante el countdown del kickoff de overtime; en ese momento se ocultan el turbo inferior, las estadísticas y su cámara, que vuelven después.

Las filas **Prórroga** y **Repetición** permiten escribir un nombre y añadir, cambiar o quitar el logo. Estos carteles dan prioridad al logo cuando está disponible. Los logos admiten PNG o JPEG de hasta 4 MB. Pulsa **Aplicar cambios** para publicar las ediciones. Usa **Vista previa de prórroga** y **Vista previa de repetición** para comprobar ambos casos sin alterar el partido. En `assets/patrocinate-aqui.png` tienes un banner transparente de ejemplo para seleccionar como logo.

## Perfiles y actualización

**Guardar perfil…** aplica los cambios y permite elegir un archivo JSON con la configuración. **Cargar perfil…** recupera ese archivo y actualiza los controles y el overlay. Los perfiles guardan nombres, logos, diseño, colores, cámaras, patrocinadores, resultado de serie y opciones de visibilidad. Las filas adicionales de publicidad se conservan al guardar y cargar. Los perfiles anteriores se adaptan al formato actual.

Al cerrar la app se guarda el último estado en `ultimo_perfil.json`, junto al ejecutable, y se recupera en la siguiente apertura. Las fuentes importadas se guardan aparte en `%LOCALAPPDATA%/PiruletaOverlay/fonts`: si trasladas un perfil a otro ordenador, importa allí también sus fuentes personalizadas.

Para actualizar, cierra la app, sustituye el ejecutable y los archivos externos si los usas, y vuelve a abrir desde el launcher o acceso directo. Actualiza la fuente de OBS y vuelve a abrir las vistas previas que estuvieran abiertas.

## Historial

Consulta [CHANGELOG.md](CHANGELOG.md). La versión 3.1 añade el asistente y los iconos de gol y asistencia a la barra de repetición.

## Contribuidores

[<img src="https://avatars.githubusercontent.com/u/113421203?v=4" width=115><br><sub>Bruno Reboredo Álvarez</sub>](https://github.com/Brunoo652) 
