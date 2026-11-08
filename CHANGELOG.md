# Cambios

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
