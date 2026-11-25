# PIRULETA - Overlay 1.3

Aplicación de escritorio para Windows para personalizar un overlay de Rocket League y mostrarlo en OBS. Recibe tiempo, goles, jugadores, turbo, estadísticas y acciones desde la Stats API del juego. Se conecta y reconecta automáticamente.

## Abrir e instalar

- Abre **Piruleta - Overlay.exe**, el acceso directo del escritorio o **Abrir Piruleta.cmd**. El launcher abre el ejecutable de su misma carpeta.
- El ejecutable incluye el diseño, fuentes, logos e iconos necesarios. No requiere instalar Python.
- Mantén la aplicación abierta durante la retransmisión.
- Descargar o clonar el repositorio proporciona el código fuente; el ejecutable se genera aparte. Consulta Generar el ejecutable al final.

Si junto al ejecutable existen `overlay.html`, `boost-animation.js` o archivos de `assets`, la app utiliza esas versiones. Si faltan, utiliza las integradas. El último perfil se guarda en `ultimo_perfil.json`, junto a la aplicación.

## Conectar Rocket League

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
| **Ajustes** | Formato BO1, BO2, BO3, BO4, BO5 o BO7; textos; Equipo azul y Equipo naranja; nombres, escudos y victorias de serie. Reiniciar serie, cambiar lados y borrar nombres y escudos. |
| **Elementos** | Secciones General, Cámaras y Publicidad. Checks para escudos, jugadores, estadísticas, turbo, acciones, replay, cortina, cámaras y cada tipo de publicidad. |
| **Diseño** | Colores, estilos, tipografía y escala en la mitad izquierda; Fondos en la derecha. Colores en dos filas, importación de tipografías y fondos por equipo o degradado/plano. |
| **Cámaras** | Nombres de jugadores y enlaces de visualización OBS Ninja / VDO.Ninja. Las casillas de activación están en Elementos. |
| **Publicidad** | Intervalo, patrocinadores rotativos, patrocinadores de jugadas y botones para previsualizar repetición y prórroga. |

**Aplicar cambios** publica los campos editados. Las casillas, selectores y botones de color se aplican al usarlos. **Guardar perfil** y **Cargar perfil** permanecen en la barra inferior.

Las pestañas Posiciones y CSS libre se han eliminado. Los perfiles anteriores mantienen los ajustes guardados; las posiciones que coincidían con los valores antiguos por defecto se adaptan a la distribución actual.

## Equipos, textos y series

- **Texto de arriba** y **Texto de abajo** admiten `[GAME]` para el partido actual de la serie y `[SERIE]` para el número del formato: BO5 devuelve 5.
- Nombres y escudos se configuran manualmente. Las imágenes de equipos admiten PNG o JPEG de hasta 4 MB.
- **Cambiar equipos de lado** intercambia nombres, logos, colores y victorias; tiempo, goles y jugadores siguen los lados azul/naranja que envía el juego.
- **Borrar nombres y escudos** vacía esos datos de ambos equipos.
- Las victorias de serie pueden ajustarse con +/− o sumarse por la API si se activa la opción de Elementos.
- BO2 y BO4 admiten empate al agotar las partidas. BO4 muestra cuatro huecos; las series impares usan los huecos necesarios para alcanzar la victoria.

## Diseño y estadísticas

Hay cuatro estilos: angular, rounded, classic y RCK. El estilo inicial es rounded, con Verdana. Montserrat está incluida y puedes importar TTF, OTF, WOFF o WOFF2. Los colores admiten código hexadecimal.

Fondos permite elegir colores de estadísticas, turbo y tarjetas de jugadores por equipo, además de fondo plano o degradado del marcador. Los ajustes de RCK y de los otros estilos se conservan por separado.

En Elementos, las estadísticas pueden mostrarse como **Rectángulo** o **Barra compacta**. Rectángulo sustituye al nombre anterior Actual. Por defecto se anclan a los bordes izquierdo e inferior. El turbo inferior queda completo y con 12 px de margen. No cambia la posición de las estadísticas al activar las cámaras.

Las tarjetas de jugadores quedan pegadas a los bordes y sus franjas laterales tienen 5 px de grosor. El estilo angular continúa la inclinación del marcador en su barra inferior.

## Cámaras

Escribe el nombre tal como aparece en Rocket League y un enlace HTTPS de visualización con `?view=...`. No uses enlaces de emisión `push` ni de director. Las mayúsculas del nombre no afectan a la coincidencia.

- **Cámara estadísticas** y **Cámaras turbos** son excluyentes.
- La opción automática muestra las cámaras de turbos durante **6,5 segundos al terminar la replay**.
- Si está activa la cámara de estadísticas, se oculta durante esos 6,5 segundos y después vuelve.
- Las cámaras se precargan con la opción automática y se reciben sin audio.
- La imagen llena su marco, recortando si hace falta para evitar bandas laterales.
- El nombre y turbo conservan su fondo; la zona que rodea la cámara es transparente.
- Con las seis cámaras visibles, el turbo inferior de angular, classic y rounded adapta su tamaño para evitar superposiciones.

Durante la repetición se ocultan el marcador, los turbos, las estadísticas y las cámaras. La vista previa muestra cámaras configuradas o marcos de ejemplo.

## Goles, repeticiones y acciones

La **Cortina de gol** dura tres segundos, se activa una vez por gol y oculta temporalmente los gráficos. Están disponibles Torneo Piruleta, Bigness League, RCS y RCK.

La **Barra de repetición** muestra REPETICIÓN, goleador y velocidad en km/h durante la replay, después de la cortina. Esta barra no se muestra en RCK. La velocidad utiliza el dato del gol sin una conversión adicional.

**Iconos de acciones** muestra gol, asistencia, parada, tiro y demolición durante 4,5 segundos. Los iconos aparecen en el extremo opuesto al nombre y sustituyen temporalmente al número de turbo. Tiro y gol pueden mostrarse juntos. En una demolición, el atacante muestra la bomba y la víctima muestra el aviso con ambos nombres. Los PNG originales están incluidos localmente; su procedencia se recoge en `assets/action-icons-source.txt`.

## Publicidad

En Elementos puedes activar por separado **Publicidad rotativa**, **Publicidad en repetición** y **Publicidad en prórroga**. Desactivar una no borra sus nombres ni logos.

### Patrocinadores rotativos

Por defecto hay **3 anuncios**. El intervalo, situado debajo del título, admite de 3 a 60 segundos.

- **Añadir patrocinador rotativo** añade una fila, hasta un máximo de **8**.
- **Quitar último patrocinador** elimina siempre la última fila, hasta un mínimo de **2**.
- Los botones se desactivan al alcanzar el límite correspondiente.
- Cada fila admite nombre, logo o ambos. Dejarla vacía la excluye de la rotación.
- El panel tiene el mismo ancho y escala que las tarjetas de jugadores. Su posición se adapta al aparecer las cámaras.

### Patrocinadores de jugadas

- **Repetición:** cartel con fondo, PATROCINADO POR y el logo, cerca de la barra inferior. Su franja usa el color del equipo goleador.
- **Prórroga:** cartel con fondo, PRORROGA, subtítulo patrocinada por y logo. Su franja usa el color de Fondo principal. Solo aparece durante el countdown del kickoff de overtime; en ese momento se ocultan el turbo inferior, las estadísticas y su cámara, que vuelven después.

Los logos admiten PNG o JPEG de hasta 4 MB. Usa los botones de vista previa para comprobar ambos casos sin alterar el partido. En `assets/patrocinate-aqui.png` tienes un banner transparente de ejemplo para seleccionar como logo.

## Perfiles y actualización

Los perfiles guardan nombres, logos, diseño, colores, cámaras, patrocinadores y opciones de visibilidad. Las filas adicionales de publicidad se conservan al guardar y cargar. Los perfiles anteriores se adaptan al formato actual.

Para actualizar, cierra la app, sustituye el ejecutable y los archivos externos si los usas, y vuelve a abrir desde el launcher o acceso directo. Actualiza la fuente de OBS y vuelve a abrir las vistas previas que estuvieran abiertas.

## Generar el ejecutable

Para trabajar con el código se necesita Python 3.11 o posterior con Tkinter. Para compilar, instala PyInstaller y ejecuta desde la carpeta del proyecto:

```powershell
python -m pip install pyinstaller
python -m PyInstaller --noconfirm Piruleta-Overlay.spec
```

El resultado queda en `dist/Piruleta - Overlay.exe`, con diseño, fuentes, iconos y cortinas integrados. Para usar Abrir Piruleta.cmd, coloca ese ejecutable a su lado. También puedes ejecutar el código con `python app.py`.

## Historial

Consulta [CHANGELOG.md](CHANGELOG.md). La versión 1.3 reúne la publicidad y sus controles, la reorganización de la app y los últimos ajustes visuales del overlay.

## Contribuidores
[<img src="https://avatars.githubusercontent.com/u/113421203?v=4" width=115><br><sub>Bruno Reboredo Álvarez</sub>](https://github.com/Brunoo652) 
