# Piruleta Studio

Aplicación de escritorio para Windows, con un marcador transparente para OBS.
Basada en las funciones públicas de BARL y las referencias del torneo; es una aplicación independiente.

## Abrir

Haz doble clic en **Abrir Piruleta.cmd**. Usa el Python ya instalado en este equipo, sin dependencias adicionales.
También puedes ejecutar `python app.py` desde esta carpeta. Mantén la aplicación abierta durante la emisión.

## Personalizar

- **Textos:** edición manual de nombres, escudos PNG/JPG, torneo, fase y número de partido.
- **Diseño:** cinco colores, tres estilos, tipografía, escala, opacidad y posición del marcador superior en un lienzo de 1920 × 1080.
- **Elementos:** checks para activar o desactivar escudos, jugadores, estadísticas, turbo, marca y avisos. Check marcado significa función activa.
- **Posiciones:** coordenadas y escala independiente de los paneles de jugadores, estadísticas, turbo, marca y avisos.
- **CSS libre:** ajustar cualquier detalle del diseño con estilos propios opcionales.
- **Control del partido:** formato BO1, BO2, BO3, BO4, BO5 o BO7, goles y victorias de serie. Los indicadores se adaptan al formato. BO2 y BO4 admiten empate al agotar las partidas. Tiempo y prórroga proceden exclusivamente de la API.
- **Perfiles:** guardar/cargar JSON. Los escudos importados se incluyen en el perfil. El último diseño se recupera al abrir.

Pulsa **Aplicar diseño** para publicar cambios de campos de texto y números. Los botones de color y las casillas se aplican al instante.
El esquema integrado resume el marcador; **Abrir vista previa** muestra el diseño completo en el navegador.
**Ver estadísticas y turbo** abre una vista ampliada con datos ficticios sin desconectar la API ni alterar el partido real. La vista previa general también utiliza datos de ejemplo aislados.
Los colores iniciales están aproximados de las imágenes aportadas: rosa `#FA54B7`, coral `#FF8875`, amarillo `#FFD14C`, fondo `#181426`, blanco.

## OBS

1. Pulsa **Copiar URL para OBS**.
2. Añade una **Fuente de navegador** en OBS y pega la dirección.
3. Establece ancho **1920** y alto **1080**. El fondo de la fuente es transparente.
4. Ponla encima de la captura de Rocket League.

La URL habitual es `http://127.0.0.1:18765/overlay`. Si ese puerto está ocupado, la aplicación muestra el puerto alternativo utilizado: vuelve a copiar la URL.
La vista previa agrega un fondo ilustrativo; para OBS usa la URL sin `?preview=1`.

## Datos automáticos del juego

La aplicación intenta conectarse al abrir y reconecta automáticamente. En este modo, tiempo, goles y prórroga los decide exclusivamente el juego. No hay controles manuales de tiempo o prórroga. Para editar goles, pulsa **Desconectar / modo manual**. Las vistas de ejemplo son independientes del partido real.

**Activar API en el juego…** permite seleccionar `TAStatsAPI.ini` o `DefaultStatsAPI.ini` con Rocket League cerrado. Guarda una copia `.bak`, activa 10 actualizaciones por segundo y conserva un puerto TCP válido ya configurado. Tras iniciar o reiniciar el juego, la aplicación busca ese puerto. Si no se reciben datos recientes, el estado deja de indicar «En directo»; no se simula el paso del tiempo.

Se ha implementado un cliente de la **Stats API oficial**, sin modificar el juego ni depender de BARL.

1. Cierra Rocket League.
2. Haz una copia de seguridad de su archivo de configuración.
3. En `<carpeta de instalación>/TAGame/Config/TAStatsAPI.ini` (o `DefaultStatsAPI.ini` si no existe), configura la sección:

```ini
[TAGame.MatchStatsExporter_TA]
PacketSendRate=10
Port=49123
WebPort=49124
```

4. Inicia Rocket League, entra a un partido y pulsa **Conectar** en Piruleta Studio.

El cliente escucha el flujo TCP local del puerto indicado y vuelve a conectar si el juego se cierra. El estado de conexión aparece abajo.
Recibe goles, reloj, prórroga, jugadores, jugador en cámara y estadísticas. El turbo solo está disponible cuando el juego lo proporciona, normalmente como espectador; un dato ausente se muestra con un guion.
Las victorias de serie se suman al recibir `MatchEnded`, una vez por identificador de partido durante la sesión de la aplicación. Puedes corregirlas con los botones de serie. El total de serie se guarda al cerrar o guardar perfil.
Los equipos de la aplicación corresponden a los índices de juego 0 (azul) y 1 (naranja): ajusta los nombres cuando cambien de lado.
Los controles manuales de goles se bloquean mientras la conexión automática está activa. Los controles de serie siguen disponibles para que el realizador pueda corregir el total del torneo. La serie deja de sumar automáticamente al completarse el formato; pulsa **Reiniciar serie** para comenzar otra.

## Alcance de esta primera versión

Incluye personalización del marcador superior, posiciones, escalas y visibilidad de paneles, además de estilos CSS propios. Aún no hay editor con arrastre, escenas de prepartido, instalador independiente o importación de temas de BARL.
La conexión se ha comprobado con mensajes de prueba de la API; falta validarla con un partido real en este equipo y con OBS.
No modifica el balón del juego. Un balón personalizado requiere un trabajo separado sobre sus recursos.

## Referencias

- BARL: https://lndrlndr.github.io/BARL/
- Stats API oficial y disponibilidad de campos: https://www.rocketleague.com/developer/stats-api?lang=en

## Comprobación

Ejecuta `python -m unittest -v` desde esta carpeta para comprobar el flujo de datos, el conteo de serie y la fuente de OBS.
