# Pipeline de Mirth Connect

Este README describe cómo configurar en Mirth Connect un canal que procesa archivos o mensajes, los transforma, los envía a un backend HTTP y gestiona la respuesta, con archivado de archivos entrantes. Abarca todas las secciones principales de configuración en la UI de Mirth.

---

## 1. Requisitos previos

* Tener instalado Mirth Connect Server y Mirth Connect Administrator.
* Acceso al sistema de archivos del servidor si se usa lector de archivos.
* Endpoint HTTP o API externo preparado (p. ej., la ruta /hl7 de tu servicio FastAPI).
* Directorios en filesystem para entrada, procesados y errores (si se procesa por archivos).
* Credenciales o parámetros de conexión necesarios para el backend (URLs, tokens, etc.).

---

## 2. Definición de variables globales o de canal

1. **Variables globales**

   * En Mirth, ir a “Settings > Global Variables” (o “Parameters/Channels > Channel Variables” en versiones más nuevas) para definir constantes reutilizables: p. ej. URL base del servicio HTTP, credenciales, rutas de carpetas, etc.
   * Ejemplos de variables:

     * BACKEND\_URL: la URL completa a la API (p. ej. [https://mi-backend/hl7](https://mi-backend/hl7))
     * AUTH\_TOKEN o API\_KEY si se requiere autorización en el header.
     * RUTA\_ENTRADA, RUTA\_PROCESADOS, RUTA\_ERRORES si se usan archivos.
   * Marcar sensibles como “Encrypted” si la versión de Mirth lo permite.

2. **Channel-specific variables**

   * Dentro de la configuración del canal, en “Edit Channel > Channel Settings > Source/Global Scripts” se pueden definir parámetros en el contexto del canal (channelMap) para rutas o credenciales particulares a este canal.

---

## 3. Creación del canal

1. **Nombre y descripción**

   * Dar un nombre claro, p. ej. “RAD\_ALERT\_Processor”.
   * Escribir descripción del propósito: “Lee informes de radiología, extrae hallazgos, envía a API y procesa respuesta.”

2. **Tipo de Source Connector**

   * Puede ser File Reader o HTTP Listener, según la fuente:

     * **File Reader**: si la entrada son ficheros depositados en una carpeta.

       * Configurar directorio de entrada (usando la variable RUTA\_ENTRADA).
       * Filtros de nombre (extensión \*.txt, \*.hl7, etc.).
       * Intervalo de polling y acciones tras lectura: mantener archivo o mover tras procesar.
     * **HTTP Listener**: si Mirth expone un endpoint y recibe el mensaje vía HTTP.

       * Configurar puerto y path (p. ej. /inbound).
       * Ajustar método (POST) y tipo de contenido esperado (JSON o texto HL7).
   * En ambos casos, se registra en el contexto el contenido bruto (por ejemplo, como variable message.getRawData()).

3. **Source Transformer**

   * En “Edit Channel > Transformers > Source Transformer”:

     * Añadir un paso tipo JavaScript o groovy que:

       * Valide la estructura entrante (XML HL7, JSON, texto plano).
       * Extraiga campos necesarios (por ejemplo, reportId, reportText).
       * Normalice caracteres (quitar BOM, unificar saltos de línea).
       * Construya el payload que se enviará al destino HTTP: p. ej., un objeto JSON con campos “reportId” y “report”.
     * Guardar datos útiles en channelMap para usar en el destino o en logging.
   * Configurar en cada paso mensajes de error: si el mensaje de origen es inválido, asignar canalMap.flagError para mover a carpeta de errores.

4. **Destination Connector**

   * Añadir un conector de tipo HTTP Sender (o Web Service Sender si SOAP).
   * En “Destination Settings”:

     * URL: referenciar la variable global BACKEND\_URL o hardcodear la ruta completa.
     * Método: POST.
     * Encabezados: Content-Type (application/json), Authorization si aplica.
     * Timeout apropiado.
     * Configurar autenticación básica o tokens si el backend lo requiere, usando las variables definidas.
   * En “Destination Transformer” (Request Transformer): opcionalmente ajustar format: serializar JSON preparado en Source Transformer, o empaquetar en estructura concreta que espera el servicio.

5. **Response Transformer**

   * En “Edit Connector > Response Transformer”:

     * Añadir un paso JavaScript para procesar la respuesta HTTP.
     * Obtener el cuerpo de la respuesta: si se espera JSON, parsear con JSON.parse.
     * Validar campos esperados: p. ej., que ack == "bien recibido" o que status == “OK”.
     * Si la respuesta es HTML o error (código 4xx/5xx), marcar error en contexto: channelMap.responseError = true.
     * Extraer cualquier identificador o dato devuelto para logging. Guardar en channelMap para posteriores pasos de logging o notificación.
   * Definir lógica de reintento: en caso de fallo temporal, usar la configuración de reintentos de Mirth o reenviar manualmente según channelMap flags.

6. **File Movement (post-processor)**

   * Si se usa File Reader: en “Edit Connector > Destination Response > Post-processor” o “Source Connector > Postprocessor”:

     * Basado en channelMap flags (por ejemplo, responseError), mover el archivo de origen a carpeta de procesados o a carpeta de errores.
     * Se usa File Writer o JavaScript que invoque funciones para mover el archivo en el filesystem.
   * Asegurar que RUTA\_PROCESADOS y RUTA\_ERRORES existan y tengan permisos.
   * Registrar en logs el destino de cada archivo.

7. **Logging y Alertas internas**

   * En “Edit Channel > Summary” o “Alerts”: configurar notificaciones de canal en caso de errores frecuentes, p. ej. enviar email o mensaje de alerta si se produce un número elevado de fallos al día.
   * Usar “Dashboard” de Mirth para monitorizar tasas de éxito/fallo.
   * En los scripts JavaScript, usar logger.info / logger.error para registrar detalles útiles: reportId, tiempo de respuesta, código HTTP, contenido de error.

---

## 4. Manejo de errores y reintentos

* **Configuración de retry**

  * En HTTP Sender: definir reintentos automáticos ante fallos transitorios (timeout, 5xx). Ajustar número de reintentos y backoff.
  * En Response Transformer: si detecta error irreversible (payload mal formado), no reintentar y mover a carpeta de error.
* **Registro de errores**

  * Mantener un registro (tabla o log) con reportId, timestamp, tipo de error (HTTP 4xx/5xx o parseo).
  * Permitir re-procesar manualmente desde UI de Mirth los mensajes en carpeta de errores tras corregir origen.
* **Alertas operativas**

  * Configurar alertas si se supera un umbral de errores (p. ej. más de X fallos en 1 hora).
  * En “Settings > Alerts” de Mirth, apuntar a un email o webhook interno.

---

## 5. Ejecución y despliegue

1. **Importar canal**

   * Guardar canal configurado en un archivo XML de Mirth Connect.
   * Versionar ese XML en tu repositorio, sin incluir credenciales directas (usar variables).

2. **Entorno de pruebas**

   * Crear un canal análogo en entorno de desarrollo con endpoints de prueba.
   * Probar con mensajes de ejemplo (incluyendo casos normales, sin hallazgos, hallazgos críticos, payloads inválidos).

3. **Despliegue en producción**

   * Importar canal en el servidor de Mirth de producción.
   * Ajustar variables globales para apuntar a URL de producción del backend y rutas de archivos en producción.
   * Verificar permisos en filesystem y conectividad HTTP (puede requerir reglas de firewall).

4. **Supervisión**

   * Revisar Dashboard y logs de Mirth para asegurar que los mensajes fluyen correctamente.
   * Monitorizar métricas clave: número de mensajes procesados, tiempo de respuesta del backend, tasa de errores.

5. **Actualizaciones**

   * Cuando cambie la API o la lógica de transformación, ajustar los scripts y reimportar canal.
   * Mantener un proceso de CI/CD para versionar los scripts de transformación y los XML de canal.

---

## 6. Flujo resumido de ejecución

1. **Source Connector** recibe mensaje o fichero.
2. **Source Transformer** valida y extrae reportId/report; normaliza texto; genera payload JSON.
3. **Destination HTTP Sender** envía POST al backend con payload.
4. **Response Transformer** parsea respuesta: si ack correcto, marca éxito; si falla, marca error.
5. **Post-processor/File Movement** mueve archivo de origen a carpeta procesados o errores según resultado.
6. **Logging** en base de datos o sistema de auditoría (usando los datos en channelMap).
7. **Alertas** si patrones de error se exceden.

---

## 7. Consideraciones de seguridad

* Nunca almacenar credenciales en texto plano en los scripts: usar variables de canal o globales cifradas en Mirth.
* Asegurar HTTPS para llamadas HTTP Sender; validar certificados.
* Controlar acceso al servidor Mirth: roles de usuario, acceso restringido.
* Registrar sólo la información necesaria, sin exponer datos sensibles en los logs.

---

## 8. Mantenimiento de scripts

* Mantener en tu repositorio los scripts JavaScript de transformación y moverlos a la carpeta de recursos de Mirth.
* Documentar dentro del script (comentarios) la lógica de extracción, formatos esperados y errores manejados.
* Versionar cada cambio y probar en entorno de desarrollo antes de aplicar en producción.

---

## 9. Ejemplo de elevación de versión

* Cuando actualices la versión de tu API (cambio de ruta o payload), actualizar:

  * Variable BACKEND\_URL si cambia endpoint.
  * Lógica de Source Transformer si cambia el campo reportId o estructura de entrada.
  * Lógica de Response Transformer si cambia formato de acuse.
* Reimportar el canal modificado y comprobar end-to-end en QA antes de producción.
