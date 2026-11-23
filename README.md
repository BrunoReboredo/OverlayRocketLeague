# Piruleta - Overlay 1.2.5

La versión **1.2.5** corrige la velocidad de replay, permite mostrar tiro y gol juntos, mejora los avisos de demolición y repara la apertura de la vista previa. Consulta el [historial de cambios](CHANGELOG.md).

Aplicación de escritorio para Windows que permite diseñar y controlar un marcador de Rocket League para retransmisiones. Incluye la identidad visual del Torneo Piruleta y una fuente transparente para OBS.

El marcador recibe **goles, tiempo, prórroga, jugadores y estadísticas desde la Stats API oficial de Rocket League**. La aplicación intenta conectarse al abrir y vuelve a intentarlo si el juego está cerrado o se pierde la conexión.

Es un proyecto independiente inspirado en las funciones públicas de BARL. No necesita instalar BARL ni BakkesMod.

## Requisitos

- Windows. El ejecutable incluye lo necesario y no requiere instalar Python.
- Rocket League para PC, instalado en el mismo ordenador, para los datos en directo.
- OBS Studio para mostrar el marcador durante una emisión.

Abre **Piruleta - Overlay.exe** o el acceso directo. **Abrir Piruleta.cmd** inicia ese mismo ejecutable, sin abrir Python ni una consola de Python.

## Instalación

1. Abre **Piruleta - Overlay.exe**. Desde 1.2.5 el ejecutable incluye el diseño, las fuentes y los iconos necesarios. El ejecutable se genera localmente; descargar solo el código del repositorio no lo incluye.
2. Descarga este repositorio desde **Code → Download ZIP** y descomprímelo, o clónalo:

   ```bash
   git clone https://github.com/BrunoReboredo/OverlayRocketLeague.git
   cd OverlayRocketLeague
   ```

3. Abre **Abrir Piruleta.cmd** con doble clic.

Para desarrollar a partir del código fuente se necesita Python 3.11 o posterior con Tkinter:

```bash
python app.py
```

Mantén Piruleta - Overlay abierto mientras uses el marcador en OBS. Si existen `overlay.html`, `boost-animation.js` o archivos de `assets` junto al ejecutable, la app usa esas versiones; si faltan, utiliza las integradas. Los perfiles y la configuración siguen guardándose por separado.

## Conectar con Rocket League

### Activación inicial de la API

La API debe estar habilitada en el juego para que envíe los datos del partido. Este paso se hace una vez por instalación, salvo que una actualización o reinstalación cambie su configuración.

1. **Cierra Rocket League**.
2. Dentro de su carpeta de instalación, entra en `TAGame/Config` y haz una copia de seguridad de `TAStatsAPI.ini` o, si no existe, de `DefaultStatsAPI.ini`.
3. Configura los valores indicados a continuación y guarda el archivo.
4. Inicia Rocket League y entra en un partido. Para disponer de los datos de turbo de los jugadores, usa el modo espectador.

La aplicación se conectará automáticamente. Cuando reciba las actualizaciones del partido, su barra inferior mostrará **«En directo · tiempo y goles sincronizados con Rocket League»**.

La versión 0.2 no tiene apartado de conexión ni modo manual. Utiliza el puerto 49123 por defecto. Si tu instalación usa otro, puedes establecer el campo `api_port` en un perfil JSON y cargarlo; el puerto se conserva al guardar el perfil.

### Activación manual

Con el juego cerrado, edita `TAGame/Config/TAStatsAPI.ini` o, si no existe, `DefaultStatsAPI.ini`. En la sección correspondiente, utiliza:

```ini
[TAGame.MatchStatsExporter_TA]
PacketSendRate=10
Port=49123
WebPort=49124
```

Si la sección ya existe, actualiza sus valores. Los puertos TCP y WebSocket deben ser diferentes. Piruleta - Overlay utiliza la conexión **TCP**, normalmente en `127.0.0.1:49123`.

Inicia o reinicia el juego tras cambiar el archivo. Piruleta - Overlay conecta y reconecta automáticamente.

La configuración y la disponibilidad de los datos están descritas en la [documentación oficial de Stats API](https://www.rocketleague.com/developer/stats-api?lang=en).

## Añadir el marcador a OBS

1. Abre Piruleta - Overlay y pulsa **Copiar URL para OBS**.
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
| **Ajustes** | Texto de arriba y Texto de abajo, nombres de equipos y escudos. Usa `[GAME]` en cualquiera de los dos textos para mostrar el número de partido de la serie y `[SERIE]` para mostrar el número del formato BO. |
| **Diseño** | Colores, estilo angular, redondeado, clásico o RCK, tipografía, escala, opacidad y posición del marcador superior. |
| **Fondos** | Fondos de turbo y estadísticas independientes para los equipos A y B: cambian automáticamente con el jugador en cámara. Fondos de jugadores vinculados a Diseño y opción de marcador degradado o plano. |
| **Elementos** | Escudos, jugadores, estadísticas, turbo, barra de repetición, cortina de gol y conteo automático de victorias. |
| **Cámaras** | Cámaras de estadísticas y turbos, enlaces de hasta ocho jugadores y activación automática durante 6,5 segundos tras la replay. |
| **Posiciones** | Coordenadas y escala de los paneles de jugadores, estadísticas, turbo, marca y avisos. |
| **CSS libre** | Estilos propios para ajustar detalles adicionales del overlay. Es opcional. |

Pulsa **Aplicar diseño** después de editar campos de texto, números, posiciones o CSS. Los colores y las casillas se aplican al instante.

Las posiciones usan un lienzo de 1920 × 1080: X aumenta hacia la derecha e Y hacia abajo. Los escudos admiten PNG y JPG de hasta 4 MB. En **Ajustes → Formato de la serie**, elige **BO1, BO2, BO3, BO4, BO5 o BO7**; el marcador adapta sus indicadores de victoria y su texto al instante.

El marcador parte del borde superior. El turbo del jugador observado tiene una escala inicial del 120 %. Los paneles laterales muestran el turbo de todos los jugadores, con nombre, valor numérico y barra; el equipo derecho aparece reflejado. El turbo cero se muestra como **0**. Los mensajes de gol y de su autor están desactivados; el resultado sigue actualizándose desde la API.

En **Fondos**, elige **Fondo principal**, **Equipo A**, **Color central**, **Equipo B** o **Color del texto** para cada panel. Al cambiar la paleta en **Diseño**, los fondos vinculados se actualizan también. El texto se adapta a los fondos claros para conservar la legibilidad. Estas opciones se guardan en los perfiles.

El esquema dentro del panel resume el marcador. Para comprobar el resultado completo, usa la vista previa del navegador.

**Cambiar equipos de lado**, en **Ajustes**, intercambia nombres, logos, colores y victorias de serie. También intercambia los fondos vinculados de las tarjetas de jugadores. Los goles y la información de los jugadores siguen correspondiendo a los lados azul y naranja que comunica el juego. Puedes usarlo después de que los equipos cambien de lado en Rocket League. Al pulsarlo dos veces se recupera la distribución original.

Todos los indicadores de turbo interpolan su valor durante 200 ms: los números, barras y círculo cambian de forma progresiva. Al cambiar de jugador observado, el círculo toma el valor de ese jugador sin arrastrar el del anterior.

## Funcionamiento durante un partido

### Modo automático

Se activa al abrir la aplicación y permanece conectado mientras está abierta.

- Los goles, el tiempo y la prórroga siguen los datos que envía Rocket League. No se hace avanzar un reloj independiente.
- Los goles, el tiempo y la prórroga no tienen controles manuales: se reciben exclusivamente de la API.
- Los paneles muestran los jugadores y el jugador en cámara cuando el juego facilita esos datos.
- Si faltan datos recientes, el estado deja de indicar «En directo». El reloj conserva el último dato recibido hasta que lleguen nuevas actualizaciones.
- Si se cierra el juego o se pierde la conexión, la aplicación vuelve a intentar conectarse.

Los nombres y escudos de los equipos son los que configures en Piruleta - Overlay. **Equipo 1 corresponde al lado azul del juego y Equipo 2 al naranja**. Ajusta la identidad de los equipos si cambian de lado.

### Resultado de la serie

Con **Sumar victorias automáticamente (API)** activado, el evento de final de partido suma una victoria al equipo ganador y actualiza el número de partido de la serie. El mismo identificador de partido solo cuenta una vez durante la sesión de la aplicación.

La serie termina al conseguir la mayoría de victorias o alcanzar el máximo de partidas del formato. BO2 admite 1–1 y BO4 admite 2–2; el marcador muestra **EMPATE**. Los formatos impares requieren 1, 2, 3 o 4 victorias para BO1, BO3, BO5 y BO7, respectivamente. Los indicadores se adaptan al objetivo de cada formato. Una serie terminada no sigue sumando partidos automáticamente; reiníciala para comenzar otra.

Los botones de serie permiten corregir las victorias incluso en modo automático. **Reiniciar serie** pone sus victorias a cero y el número de partido a uno; no reinicia el partido dentro del juego.

### Vista previa

**Abrir vista previa** permite comprobar todo el diseño con datos de ejemplo, incluidas la tarjeta de estadísticas, las barras de todos los jugadores y el indicador circular de turbo. La conexión automática sigue activa y OBS conserva los datos reales.

## Guardar y recuperar perfiles

- **Guardar perfil…** exporta el diseño y el resultado de serie a un archivo JSON. Los escudos importados se incluyen en ese archivo.
- **Cargar perfil…** recupera un perfil exportado.
- Al cerrar la aplicación, el perfil actual se guarda en `ultimo_perfil.json` y se recupera al abrir.

Los perfiles guardan el puerto de conexión, el diseño y el resultado de serie, pero no el estado completo del partido. `ultimo_perfil.json` se excluye de Git para mantener la configuración personal fuera del repositorio.

## Solución de problemas

| Problema | Qué comprobar |
| --- | --- |
| No se abre la ventana | Ejecuta `python app.py` desde una terminal para ver el error. Comprueba Python 3.11 o posterior y Tkinter con `python -m tkinter`. |
| Aparece «Esperando Rocket League» | Comprueba que la API esté activada, el puerto coincida y el juego se haya reiniciado tras cambiar la configuración. |
| Está conectado pero no recibe datos | Entra en un partido y comprueba que `PacketSendRate` sea mayor que cero. Los datos se emiten mientras hay un partido en curso. |
| No aparecen las barras de turbo | Comprueba el modo espectador y que los paneles estén activados en **Elementos**. Algunos datos solo se emiten como espectador. |
| No se puede guardar la configuración del juego | Comprueba los permisos de escritura del INI y conserva una copia antes de modificarlo. |
| OBS no muestra el marcador | Mantén la aplicación abierta, copia de nuevo su URL y revisa que la fuente esté visible por encima de la captura. |
| La fuente tiene un fondo ilustrativo | Quita `?preview=1` de la URL de OBS. |
| No puedo editar el tiempo o los goles | Es intencionado: desde la versión 0.2 proceden exclusivamente del juego. |

## Estado del proyecto

La sincronización del reloj, los goles, las estadísticas y el turbo se ha comprobado con un partido real y en la vista previa de OBS.

Esta versión no incluye instalador independiente, editor con arrastre, escenas de prepartido ni importación de temas de BARL. Tampoco modifica la apariencia del balón dentro del juego.

## Archivos del proyecto

| Archivo | Función |
| --- | --- |
| `app.py` | Panel de escritorio, recepción TCP, estado del partido y servidor local para OBS. |
| `api_config.py` | Activación de Stats API y copia de seguridad del INI. |
| `overlay.html` | Diseño del marcador que se muestra en OBS. |
| `boost-animation.js` | Interpolación de turbo independiente de la frecuencia de actualización. |
| `assets/` | Recursos visuales del torneo. |

Referencia de inspiración: [BARL](https://lndrlndr.github.io/BARL/).

## Visibilidad automática

La fuente de OBS solo se muestra en partidos privados online, de exhibición local o LAN (PlaylistId 6, 8 y 24). Se oculta al terminar o salir del partido, en modos públicos, entrenamiento, repeticiones guardadas y si se pierde la conexión. Los modos desconocidos se mantienen ocultos. Las repeticiones de gol dentro del partido conservan el marcador. La vista previa sigue mostrando los datos de ejemplo.

## Cortina de gol

En Elementos, Cortina de gol sustituye al aviso de victoria. Al recibir un gol de un partido privado se muestra durante 3 segundos un barrido diagonal con la paleta de Diseño y el logo de la cortina elegida. Durante la animación se ocultan los gráficos del overlay; después vuelven automáticamente. No cambia la escena de OBS, no incorpora una pelota ni mensajes de goleador. Probar cortina de gol abre una vista previa independiente del partido. El ajuste se conserva en perfiles mediante show_events para mantener compatibilidad.

En Elementos → Diseño de cortina puedes elegir Original o Bigness League. La segunda utiliza el logo de Bigness League incluido en assets y una paleta azul cian, negro, gris y dorado propia. Ambas duran tres segundos y se activan una sola vez por gol, sin repetirse al terminar la replay. La elección se guarda en el perfil.

## Estilo RCK y cortinas

Diseño → Estilo → RCK aplica un preset inspirado en la referencia: cabecera con torneo, fase y ronda; placas inclinadas; paleta lavanda, azul claro y azul marino; barras laterales compactas; estadísticas horizontales y turbo de doble aro. Al elegirlo se ajustan colores y posiciones, que puedes personalizar después. Los datos siguen sincronizados con el juego.

Las cortinas disponibles son Torneo Piruleta (antes Original), Bigness League y RCS. RCS utiliza el logo incluido y los colores #c80516 y #f9cd36. Los perfiles que guardaban Original se actualizan automáticamente al nombre Torneo Piruleta.

## Cámaras · versión 1.2.2

En Cámaras puedes activar Cámara estadísticas y Cámaras turbos. Los campos de configuración están dentro de la pestaña: escribe el nombre del jugador tal como aparece en Rocket League y su enlace de visualización OBS Ninja / VDO.Ninja con ?view=... Las mayúsculas y minúsculas no afectan. Pulsa Aplicar cambios para guardar en el estado del overlay y Guarda el perfil para conservar la configuración en otro archivo.

La opción automática muestra las cámaras de los turbos durante 6,5 segundos al terminar la repetición de un gol. Las cámaras activadas manualmente siguen mostrándose después de ese intervalo. Las cámaras se reciben sin audio. La vista previa usa los jugadores configurados y muestra marcos de ejemplo cuando falta un enlace.


### Comportamiento de las cámaras en 1.2.2

- Cámara estadísticas y Cámaras turbos son excluyentes: activar una desactiva la otra.
- Durante la repetición se ocultan el marcador, los turbos, las estadísticas y las cámaras. Solo permanece la barra de repetición si está activada y el estilo la admite.
- La opción automática muestra las cámaras de turbos durante 6,5 segundos después de la repetición. Durante ese intervalo oculta la cámara de estadísticas; al terminar recupera la opción manual elegida.
- Con la opción automática, las cámaras se precargan para reducir la espera al mostrarlas.
- Las imágenes de cámara llenan el marco en todos los estilos, recortando lo necesario para evitar bandas laterales.
- La zona de cámara tiene fondo transparente. El nombre y el turbo conservan su fondo. En RCK la franja mantiene su inclinación y la cámara es rectangular; en los otros estilos la cámara ocupa el mismo ancho que la caja del turbo.
- Abrir vista previa muestra los mismos ajustes y abre la revisión actual del diseño. Para actualizar una fuente de OBS que ya estaba abierta, utiliza Actualizar en sus propiedades.


### Pestaña Ajustes

Ajustes sustituye a Textos y reúne los textos superior e inferior, Equipo azul, Equipo naranja y Control del partido. El panel lateral desaparece y las demás pestañas aprovechan todo el ancho disponible. Borrar nombres y escudos vacía ambos nombres y elimina sus escudos. Guardar perfil y Cargar perfil permanecen accesibles en la barra inferior, junto a Aplicar cambios.


## Cambios de la versión 1.2.3

- **Angular:** la barra inferior comienza donde termina la parte principal y continúa su misma inclinación.
- **Turbo con cámaras:** en angular, classic y rounded, el turbo inferior se reduce únicamente al mostrar las seis cámaras de jugadores y recupera su tamaño al ocultarlas. La cámara de estadísticas mantiene el tamaño habitual del turbo. RCK conserva su comportamiento.
- **BO4:** aparecen cuatro huecos de serie. El objetivo para ganar y el empate 2–2 siguen funcionando como antes.
- **Ajustes:** sustituye a Textos. Arriba aparecen formato, texto de abajo y texto de arriba, sin marcos exteriores. Debajo están Reiniciar serie, Cambiar equipos de lado y Borrar nombres y escudos. Tras la separación aparecen los bloques ampliados de Equipo azul y Equipo naranja, con sus victorias de serie, nombre, escudo y goles recibidos de la API. Las indicaciones de serie y de comandos quedan debajo de los equipos.
- **Espacio de trabajo:** el control del partido queda dentro de Ajustes; las demás pestañas usan todo el ancho. La ventana abre más alta y reserva espacio para Guardar perfil, Cargar perfil y Aplicar cambios.

Reabre la aplicación desde el acceso directo o **Piruleta - Overlay.exe** tras actualizarla. Actualiza también la fuente de navegador de OBS para cargar los cambios visuales. La versión aparece en la ventana y en el pie de la aplicación.


### Iconos de acciones

En Elementos, Iconos de acciones activa los indicadores de gol, asistencia, parada, tiro y demolición junto al nombre en las barras de turbo de jugadores. Los iconos respetan los colores del panel y duran 4,5 segundos; las acciones diferentes del mismo jugador pueden aparecer juntas. Un tiro seguido de gol conserva los dos iconos durante la ventana del gol. Se activan mediante los eventos de la API durante partidos privados y se limpian en las repeticiones y al cambiar de partido. La vista previa muestra ejemplos periódicos sin modificar los datos del juego. La opción se conserva en los perfiles.


## Cambios de la versión 1.2.4

- Iconos de gol, asistencia, parada, tiro y demolición conectados a la API, con animación y duración de 4,5 segundos.
- Casilla Iconos de acciones en Elementos, conservada en perfiles, y ejemplos periódicos en la vista previa.
- PNG originales del juego descargados de Rocket League Wiki, incluidos localmente con su referencia de origen.
- Barras de jugadores de angular, classic y rounded: 20 px más arriba y 15 px menos altas respecto a 1.2.3. RCK se mantiene.
- Turbo inferior algo más grande con las seis cámaras visibles, conservando el ajuste para evitar superposiciones.

Los PNG se sirven desde la carpeta assets; no se necesita acceder a la wiki durante la emisión. Activa los iconos en Elementos → Iconos de acciones. Después de actualizar, reabre la app y actualiza la fuente de navegador en OBS.


Los iconos de acciones aparecen al final de la barra, en el extremo opuesto al nombre, sustituyendo temporalmente al número de turbo. Al caducar vuelven los datos habituales. En una demolición, el atacante muestra el icono y la barra de la víctima muestra el nombre del atacante, el icono y el de la víctima, con el color del equipo atacante. La vista previa incluye tiro y gol simultáneos y una demolición.


## Cambios de la versión 1.2.5

- Corregida la velocidad de la barra de replay: se usa GoalSpeed directamente en km/h, sin aplicar otra conversión.
- Iconos de acciones al final de la barra, en el extremo opuesto al nombre.
- Tiro y gol se muestran juntos; los eventos repetidos no duplican un mismo icono.
- Demoliciones: bomba en el atacante y aviso con atacante, bomba y víctima en la barra de quien recibe la demolición.
- El aviso de demolición cubre toda la barra y sus bordes con el color del atacante.
- Apertura de la vista previa corregida, con archivos integrados en el ejecutable y alternativa si Windows no abre el navegador.
- Launcher, documentación y ejecutable actualizados a 1.2.5.

La vista previa usa los mismos ajustes que OBS. Si no se puede abrir el navegador, la aplicación avisa y copia el enlace para pegarlo manualmente.

### Generar el ejecutable desde el código

Con Python y PyInstaller instalados, ejecuta desde la carpeta del proyecto:

```powershell
python -m PyInstaller --noconfirm Piruleta-Overlay.spec
```

El resultado queda en `dist/Piruleta - Overlay.exe`. El archivo de compilación incluye el diseño, las fuentes, los iconos y las cortinas de gol. Para usar el launcher, coloca el ejecutable a su lado.
