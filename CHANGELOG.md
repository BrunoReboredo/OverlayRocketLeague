# Cambios

## 1.2.2 · actualización de cámaras

- Cámaras manuales excluyentes y cámaras temporales durante 6,5 segundos tras la replay.
- Ocultación de gráficos durante las repeticiones y precarga de cámaras.
- Cámara a todo ancho, sin bandas laterales y con fondo transparente, conservando la franja del nombre y turbo.
- Cámaras RCK rectangulares y cabeceras inclinadas.
- Vista previa actualizada y launcher de la versión 1.2.2.

## 1.2.1 · actualización de Cámaras

- Nueva pestaña Cámaras para las opciones de cámara de estadísticas y cámaras de turbos.
- Configuración de los enlaces integrada en la misma pestaña.
- Activación opcional de cámaras de turbos durante 4,5 segundos al finalizar la replay del gol.
- Conservación de enlaces y opciones al guardar y cargar perfiles.


## 0.8.2

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
