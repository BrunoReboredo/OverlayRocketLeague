# Cambios

## 1.3.2

- Barras de victorias distribuidas como en Piruleta Studio; margen propio de angular para evitar recortes en todos los BO.
- Campo Siglas del equipo de hasta cuatro caracteres: sustituye al nombre cuando no cabe, se conserva en perfiles y cambia de lado junto al equipo.
- Etiquetas y campos de nombre y siglas alineados en Ajustes.
- Compacto: escudos de 36 px, con sus colores originales, y nombres centrados sin aumentar las dimensiones del marcador.
- Barra de repetición de Compacto unificada con los demás estilos; patrocinador recolocado para evitar solapamientos.
- README actualizado con las siglas de equipos.

## 1.3.1

- La barra de repetición muestra al goleador y al asistente con sus iconos. El goleador queda centrado cuando no hay asistencia.

## 1.3

- Nueva pestaña Publicidad con patrocinadores rotativos, de repetición y de prórroga, logos de hasta 4 MB y vistas previas.
- Tres anuncios rotativos por defecto; botones para añadir hasta ocho y quitar siempre el último, con mínimo de dos.
- Patrocinador rotativo del mismo ancho que las tarjetas de jugadores y posición adaptable a las cámaras.
- Patrocinio de prórroga solo durante el countdown del kickoff, ocultando temporalmente el turbo inferior y las estadísticas.
- Carteles ampliados: PATROCINADO POR en repetición; PRORROGA y patrocinada por en prórroga. Ambos conservan su fondo.
- Barra de repetición con el color del equipo goleador y barra de prórroga con el fondo principal.
- Estadísticas ancladas a la esquina inferior izquierda; turbo inferior completamente visible y con 12 px de margen al borde.
- Turbos laterales pegados a los bordes y franjas de 5 px, iguales a la del rotativo.
- Elementos pasa a la segunda pestaña, con General, Cámaras y Publicidad en columna y títulos en negrita.
- Fondos integrado en Diseño, distribuido en dos mitades iguales con separador blanco. Colores en dos filas y apartado Estilos, tipografía y escala.
- Eliminadas las pestañas CSS libre y Posiciones, y los controles de opacidad y posición del marcador.
- Estilo de estadísticas Actual renombrado a Rectángulo; compatibilidad con perfiles anteriores.
- Imagen PATROCÍNATE AQUÍ incluida en assets para usar como logo de ejemplo.


## 1.2.8

- Corregida la velocidad de la barra de replay: se usa GoalSpeed directamente en km/h, sin aplicar otra conversión.
- Iconos de acciones al final de la barra, en el extremo opuesto al nombre.
- Tiro y gol se muestran juntos; los eventos repetidos no duplican un mismo icono.
- Demoliciones: bomba en el atacante y aviso con atacante, bomba y víctima en la barra de quien recibe la demolición.
- El aviso de demolición cubre toda la barra y sus bordes con el color del atacante.
- Apertura de la vista previa corregida, con archivos integrados en el ejecutable y alternativa si Windows no abre el navegador.
- Launcher, documentación y ejecutable actualizados a 1.2.5.


## 1.2.7

- Iconos de gol, asistencia, parada, tiro y demolición conectados a la API, con animación y duración de 4,5 segundos.
- Casilla Iconos de acciones en Elementos, conservada en perfiles, y ejemplos periódicos en la vista previa.
- PNG originales del juego descargados de Rocket League Wiki, incluidos localmente con su referencia de origen.
- Barras de jugadores de angular, classic y rounded: 20 px más arriba y 15 px menos altas respecto a 1.2.3. RCK se mantiene.
- Turbo inferior algo más grande con las seis cámaras visibles, conservando el ajuste para evitar superposiciones.


## 1.2.6

- Barra inferior angular alineada con la inclinación de la parte principal.
- Turbo inferior reducido solo con las seis cámaras visibles en angular, classic y rounded. La cámara de estadísticas mantiene su tamaño habitual; RCK no cambia.
- Cuatro huecos de serie en BO4.
- Nueva pestaña Ajustes con formato y textos arriba, tres acciones y dos bloques ampliados para Equipo azul y Equipo naranja.
- Botón para borrar los nombres y escudos de ambos equipos.
- Mayor separación entre acciones y equipos; indicaciones al pie de los equipos.
- Pestañas a todo ancho, ventana inicial más alta y espacio reservado para los botones inferiores.
- README y ejecutable actualizados.

## 1.2.5 · actualización de cámaras

- Cámaras manuales excluyentes y cámaras temporales durante 6,5 segundos tras la replay.
- Ocultación de gráficos durante las repeticiones y precarga de cámaras.
- Cámara a todo ancho, sin bandas laterales y con fondo transparente, conservando la franja del nombre y turbo.
- Cámaras RCK rectangulares y cabeceras inclinadas.
- Vista previa actualizada y launcher de la versión 1.2.2.

## 1.2.4 · actualización de Cámaras

- Nueva pestaña Cámaras para las opciones de cámara de estadísticas y cámaras de turbos.
- Configuración de los enlaces integrada en la misma pestaña.
- Activación opcional de cámaras de turbos durante 4,5 segundos al finalizar la replay del gol.
- Conservación de enlaces y opciones al guardar y cargar perfiles.


## 1.2.3

- Estadísticas e indicador de turbo desplazados 15 px hacia abajo.
- Cámara de estadísticas pegada al panel y alineada con el inicio del borde superior de RCK.

## 1.2.2

- Cámaras de estadísticas y turbos con enlaces de visualización OBS Ninja / VDO.Ninja asociados a cada jugador.
- Opciones independientes en Elementos y configuración de hasta ocho cámaras, guardada en perfiles.
- Vista previa con cámaras configuradas o marcos de ejemplo.
- Cámaras reducidas 5 px de ancho y alto.
- Barra de repetición rectangular.
- Estadísticas compactas en los tres estilos por defecto y ajustes de la barra de estadísticas de RCK.
- Cajas de turbo 10 px más estrechas en angular, redondeado y clásico.

## 1.2.1

- Barra inferior durante la repetición de gol, tras la cortina. Muestra el color del equipo, el goleador y la velocidad del balón.
- Casilla de la barra de repetición en Elementos para los estilos angular, redondeado y clásico.
- Aplicar cambios actualiza la vista previa. La aplicación evita abrir dos instancias en Windows.

## 1.2.0

- Barra superior RCK rediseñada, con paleta original, barras laterales al borde y ajustes de posición en turbo y estadísticas.
- Textos superior e inferior personalizables con `[GAME]` y `[SERIE]`. El número de partido se calcula a partir de la serie.
- Nueva cortina de gol RCK.
- Montserrat incluida e importación de fuentes TTF, OTF, WOFF y WOFF2.
- Entrada de colores hexadecimales y controles ampliados tras retirar el esquema integrado.

## 1.1.0

- Nuevo estilo RCK con placas inclinadas, barras compactas, estadísticas horizontales y turbo de doble aro.
- Cortinas de gol de tres segundos: Torneo Piruleta, Bigness League y RCS.
- Una sola cortina por gol, sin repetirse durante o al finalizar la replay.
- Selector de cortina, previsualización y compatibilidad de perfiles anteriores.
- Versión y crédito a Bruno Reboredo Álvarez en la esquina inferior derecha de la aplicación.
- Launcher actualizado.


## 1.0.0

- Estilo rounded y tipografía Verdana por defecto.
- Fondos independientes de turbo y estadísticas para cada equipo, vinculados a la paleta de Diseño y al jugador en cámara.
- Marcador con fondo degradado o plano.
- PNG personalizable para la marca del torneo (hasta 4 MB), incluido en los perfiles. El nombre se toma de Textos.
- Compatibilidad con perfiles anteriores y con el intercambio de equipos.

## 0.2.0

- Eliminado el texto rosa «PIRULETA» del esquema integrado debajo del marcador.
- Nuevo botón **Cambiar equipos de lado** en **Textos**: intercambia nombres, logos, victorias de serie y colores. Conserva la sincronización de datos con los lados de la API.
- Turbo animado durante 200 ms entre actualizaciones, tanto en números como en barras laterales y círculo. Las tarjetas se conservan entre actualizaciones para evitar saltos y reinicios de animación.
- Eliminado el apartado **Datos de Rocket League** y los controles de goles manuales. La conexión y reconexión siguen siendo automáticas.
- Los perfiles guardan el puerto de la API mediante `api_port` (49123 por defecto).
- Se conservan los perfiles anteriores, el diseño, los fondos, los formatos BO y la fuente transparente para OBS.
