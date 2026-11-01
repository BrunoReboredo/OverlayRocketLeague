# Piruleta Studio · Rocket League Overlay

Aplicación de escritorio para Windows que permite diseñar y controlar un marcador de Rocket League para retransmisiones. Incluye la identidad visual del Torneo Piruleta y una fuente transparente para OBS.

El marcador recibe **goles, tiempo, prórroga, jugadores y estadísticas desde la Stats API oficial de Rocket League**. La aplicación intenta conectarse al abrir y vuelve a intentarlo si el juego está cerrado o se pierde la conexión.

Es un proyecto independiente inspirado en las funciones públicas de BARL. No necesita instalar BARL ni BakkesMod.

## Requisitos

- Windows y **Python 3.11 o posterior**, con Tkinter.
- Rocket League para PC, instalado en el mismo ordenador, para los datos en directo.
- OBS Studio para mostrar el marcador durante una emisión.

No requiere instalar paquetes con `pip`. Todavía no hay instalador ni ejecutable independiente: la aplicación se ejecuta con Python.

## Instalación

1. Instala [Python para Windows](https://www.python.org/downloads/windows/). Asegúrate de incluir Tkinter y de que los comandos `python` y `pythonw` estén disponibles en el equipo.
2. Descarga este repositorio desde **Code → Download ZIP** y descomprímelo, o clónalo:

   ```bash
   git clone https://github.com/BrunoReboredo/OverlayRocketLeague.git
   cd OverlayRocketLeague
   ```

3. Abre **Abrir Piruleta.cmd** con doble clic.

También puedes abrir una terminal en la carpeta del proyecto y ejecutar:

```bash
python app.py
```

Conserva la carpeta `assets` y los archivos de la aplicación juntos. Mantén Piruleta Studio abierto mientras uses el marcador en OBS.

## Conectar con Rocket League

### Activación desde la aplicación

La API debe estar habilitada en el juego para que envíe los datos del partido. Este paso se hace una vez por instalación, salvo que una actualización o reinstalación cambie su configuración.

1. **Cierra Rocket League**.
2. En Piruleta Studio, pulsa **Activar API en el juego…**.
3. Dentro de la carpeta de instalación de Rocket League, entra en `TAGame/Config` y selecciona `TAStatsAPI.ini`. Si no existe, selecciona `DefaultStatsAPI.ini`.
4. La aplicación guarda una copia de seguridad junto al archivo, con un nombre como `DefaultStatsAPI.ini.piruleta-….bak`, y activa el envío de datos a 10 actualizaciones por segundo.
5. Inicia Rocket League y entra en un partido. Para disponer de los datos de turbo de los jugadores, usa el modo espectador.

La aplicación se conectará automáticamente. Cuando reciba las actualizaciones del partido, su barra inferior mostrará **«En directo · tiempo y goles sincronizados con Rocket League»**.

El botón conserva un puerto TCP válido que ya esté configurado y conecta con él durante esa sesión. **Al volver a abrir la aplicación, el puerto vuelve a 49123**: si usas uno diferente, introdúcelo en **Puerto TCP** y pulsa **Conectar**.

### Activación manual

Con el juego cerrado, edita `TAGame/Config/TAStatsAPI.ini` o, si no existe, `DefaultStatsAPI.ini`. En la sección correspondiente, utiliza:

```ini
[TAGame.MatchStatsExporter_TA]
PacketSendRate=10
Port=49123
WebPort=49124
```

Si la sección ya existe, actualiza sus valores. Los puertos TCP y WebSocket deben ser diferentes. Piruleta Studio utiliza la conexión **TCP**, normalmente en `127.0.0.1:49123`.

Inicia o reinicia el juego tras cambiar el archivo. En la aplicación, comprueba el puerto y pulsa **Conectar** si es necesario.

La configuración y la disponibilidad de los datos están descritas en la [documentación oficial de Stats API](https://www.rocketleague.com/developer/stats-api?lang=en).

## Añadir el marcador a OBS

1. Abre Piruleta Studio y pulsa **Copiar URL para OBS**.
2. En la escena de OBS, añade una **Fuente de navegador**.
3. Pega la URL y configura el tamaño en **1920 × 1080**.
4. Coloca la fuente por encima de la captura de Rocket League.

La dirección habitual es:

```text
http://127.0.0.1:18765/overlay
```

El fondo es transparente. Si el puerto está ocupado, la aplicación utiliza otro y muestra la URL correcta en su barra inferior: usa siempre **Copiar URL para OBS**.

**Abrir vista previa** muestra el diseño completo, incluidas las estadísticas y el turbo, con un fondo ilustrativo y datos de ejemplo. Esta vista no desconecta la API ni cambia el partido real. Para OBS, utiliza la URL sin `?preview=1`.

La conexión está pensada para usar la aplicación, Rocket League y OBS en el mismo ordenador. El servidor del marcador solo escucha en la dirección local.

## Personalizar el diseño

| Pestaña | Opciones |
| --- | --- |
| **Textos** | Edición manual del nombre del torneo, ronda, partido de la serie, nombres de equipos y escudos. |
| **Diseño** | Colores, estilo angular, redondeado o clásico, tipografía, escala, opacidad y posición del marcador superior. |
| **Fondos** | Fondo del turbo, caja de estadísticas y jugadores de cada equipo, vinculados a los colores de la paleta principal. |
| **Elementos** | Checks para escudos, jugadores, estadísticas, turbo, marca, avisos y conteo automático de victorias. Check marcado = función activa. |
| **Posiciones** | Coordenadas y escala de los paneles de jugadores, estadísticas, turbo, marca y avisos. |
| **CSS libre** | Estilos propios para ajustar detalles adicionales del overlay. Es opcional. |

Pulsa **Aplicar diseño** después de editar campos de texto, números, posiciones o CSS. Los colores y las casillas se aplican al instante.

Las posiciones usan un lienzo de 1920 × 1080: X aumenta hacia la derecha e Y hacia abajo. Los escudos admiten PNG y JPG de menos de 1,4 MB. En **Control del partido → Formato de la serie**, elige **BO1, BO2, BO3, BO4, BO5 o BO7**; el marcador adapta sus indicadores de victoria y su texto al instante.

El marcador parte del borde superior. El turbo del jugador observado tiene una escala inicial del 120 %. Los paneles laterales muestran el turbo de todos los jugadores, con nombre, valor numérico y barra; el equipo derecho aparece reflejado. El turbo cero se muestra como **0**. Los mensajes de gol y de su autor están desactivados; el resultado sigue actualizándose desde la API.

En **Fondos**, elige **Fondo principal**, **Equipo A**, **Color central**, **Equipo B** o **Color del texto** para cada panel. Al cambiar la paleta en **Diseño**, los fondos vinculados se actualizan también. El texto se adapta a los fondos claros para conservar la legibilidad. Estas opciones se guardan en los perfiles.

El esquema dentro del panel resume el marcador. Para comprobar el resultado completo, usa la vista previa del navegador.

## Funcionamiento durante un partido

### Modo automático

Es el modo que se activa al abrir la aplicación o pulsar **Conectar**.

- Los goles, el tiempo y la prórroga siguen los datos que envía Rocket League. No se hace avanzar un reloj independiente.
- El tiempo y la prórroga no tienen controles manuales: se reciben exclusivamente de la API. Los botones manuales de goles quedan deshabilitados mientras esté activa la conexión automática.
- Los paneles muestran los jugadores y el jugador en cámara cuando el juego facilita esos datos.
- Si faltan datos recientes, el estado deja de indicar «En directo». El reloj conserva el último dato recibido hasta que lleguen nuevas actualizaciones.
- Si se cierra el juego o se pierde la conexión, la aplicación vuelve a intentar conectarse.

Los nombres y escudos de los equipos son los que configures en Piruleta Studio. **Equipo 1 corresponde al lado azul del juego y Equipo 2 al naranja**. Ajusta la identidad de los equipos si cambian de lado.

### Resultado de la serie

Con **Sumar victorias automáticamente (API)** activado, el evento de final de partido suma una victoria al equipo ganador y actualiza el número de partido de la serie. El mismo identificador de partido solo cuenta una vez durante la sesión de la aplicación.

La serie termina al conseguir la mayoría de victorias o alcanzar el máximo de partidas del formato. BO2 admite 1–1 y BO4 admite 2–2; el marcador muestra **EMPATE**. Los formatos impares requieren 1, 2, 3 o 4 victorias para BO1, BO3, BO5 y BO7, respectivamente. Los indicadores se adaptan al objetivo de cada formato. Una serie terminada no sigue sumando partidos automáticamente; reiníciala para comenzar otra.

Los botones de serie permiten corregir las victorias incluso en modo automático. **Reiniciar serie** pone sus victorias a cero y el número de partido a uno; no reinicia el partido dentro del juego.

### Modo manual y muestra

Pulsa **Desconectar / modo manual** para habilitar la edición manual de goles. El tiempo y la prórroga siguen sin ser editables. Estos controles solo cambian el overlay.

**Abrir vista previa** permite comprobar todo el diseño con datos de ejemplo, incluidas la tarjeta de estadísticas, las barras de todos los jugadores y el indicador circular de turbo. La conexión automática sigue activa y OBS conserva los datos reales.

## Guardar y recuperar perfiles

- **Guardar perfil…** exporta el diseño y el resultado de serie a un archivo JSON. Los escudos importados se incluyen en ese archivo.
- **Cargar perfil…** recupera un perfil exportado.
- Al cerrar la aplicación, el perfil actual se guarda en `ultimo_perfil.json` y se recupera al abrir.

Los perfiles no guardan el estado completo del partido ni el puerto de conexión. `ultimo_perfil.json` se excluye de Git para mantener la configuración personal fuera del repositorio.

## Solución de problemas

| Problema | Qué comprobar |
| --- | --- |
| No se abre la ventana | Ejecuta `python app.py` desde una terminal para ver el error. Comprueba Python 3.11 o posterior y Tkinter con `python -m tkinter`. |
| Aparece «Esperando Rocket League» | Comprueba que la API esté activada, el puerto coincida y el juego se haya reiniciado tras cambiar la configuración. |
| Está conectado pero no recibe datos | Entra en un partido y comprueba que `PacketSendRate` sea mayor que cero. Los datos se emiten mientras hay un partido en curso. |
| No aparecen las barras de turbo | Comprueba el modo espectador y que los paneles estén activados en **Elementos**. Algunos datos solo se emiten como espectador. |
| No se puede guardar la configuración del juego | Comprueba los permisos de escritura del archivo seleccionado. El botón necesita poder crear la copia y modificar el INI. |
| OBS no muestra el marcador | Mantén la aplicación abierta, copia de nuevo su URL y revisa que la fuente esté visible por encima de la captura. |
| La fuente tiene un fondo ilustrativo | Quita `?preview=1` de la URL de OBS. |
| No puedo editar el tiempo | Es intencionado: el tiempo y la prórroga proceden exclusivamente del juego. Para editar goles, pulsa **Desconectar / modo manual**. |

## Estado del proyecto

La recepción de datos, la configuración del INI y la fuente del overlay tienen pruebas automáticas. La sincronización del reloj, los goles, las estadísticas y el turbo se ha comprobado con un partido real y en la vista previa de OBS.

Esta versión no incluye instalador independiente, editor con arrastre, escenas de prepartido ni importación de temas de BARL. Tampoco modifica la apariencia del balón dentro del juego.

## Desarrollo

Desde la carpeta del proyecto, ejecuta las pruebas con:

```bash
python -m unittest -v
```

Las pruebas de conexión necesitan permitir conexiones locales.

| Archivo | Función |
| --- | --- |
| `app.py` | Panel de escritorio, recepción TCP, estado del partido y servidor local para OBS. |
| `api_config.py` | Activación de Stats API y copia de seguridad del INI. |
| `overlay.html` | Diseño del marcador que se muestra en OBS. |
| `assets/` | Recursos visuales del torneo. |
| `test_app.py` | Pruebas automáticas. |

Referencia de inspiración: [BARL](https://lndrlndr.github.io/BARL/).
