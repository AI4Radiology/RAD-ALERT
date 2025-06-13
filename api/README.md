# RAD-ALERT API

**Descripción general**
RAD-ALERT es una aplicación que recibe informes de radiología en formato de texto (por ejemplo, contenido HL7 o texto plano con secciones de hallazgos), extrae y normaliza la sección relevante, clasifica si el informe es “crítico” usando un modelo de aprendizaje automático, registra el resultado en una base de datos Supabase y, en caso de criticidad, envía una alerta vía WhatsApp a través de Twilio. Además, proporciona una interfaz de monitorización basada en Streamlit donde se muestran los reportes procesados recientemente y se permite cambiar el número de destino para notificaciones.

---

## 1. Estructura del proyecto

* **Directorio raíz**: Contiene archivos de configuración (variables de entorno, Dockerfile, archivos de despliegue), el directorio del modelo y la carpeta de la aplicación.
* **Carpeta de la aplicación (`api/`)**:

  * Módulo de configuración de ajustes y lectura de variables de entorno mediante Pydantic Settings.
  * Módulo de conexión a la base de datos Supabase y función para registrar cada informe.
  * Módulo de carga y uso del modelo de Hugging Face para clasificación de texto.
  * Módulo de envío de notificaciones por WhatsApp empleando Twilio.
  * Módulo de procesamiento que coordina limpieza, extracción de sección, normalización, llamada al clasificador, decisión de enviar alerta y registro del resultado.
  * Módulo principal de FastAPI que expone el endpoint para recibir el informe y encola el procesamiento en segundo plano.
  * Módulo de la interfaz de Streamlit que, al iniciarse, arranca o se conecta a la API en desarrollo y muestra la tabla de reportes recientes, además de permitir cambiar el número de WhatsApp destino.
* **Directorio de modelo (`model/` o ruta configurada)**: Contiene los archivos exportados del modelo de clasificación (por ejemplo, archivos de pesos). Puede gestionarse con Git LFS o bien descargarse en tiempo de despliegue desde un almacenamiento externo.
* **Archivos de despliegue y configuración**:

  * Variables de entorno en un archivo de texto protegido (no versionar en claro).
  * Dockerfile (o configuración de buildpacks) que instala dependencias, copia código, prepara la imagen y arranca los servicios necesarios.
  * Opcionalmente, configuraciones de proxy inverso o gestor de procesos para combinar FastAPI y Streamlit en un solo contenedor.
  * Archivos de supervisión de procesos dentro del contenedor (si se usa supervisord, nginx, etc.) o bien enfoque más simple que arranque sólo los servicios principales.
  * Configuraciones específicas para la plataforma de despliegue (Railway, Heroku, AWS, etc.), como variables de entorno definidas en el panel de la plataforma, rutas de puertos y ajustes de red.
* **Dependencias listadas en un archivo de requerimientos** que incluye FastAPI, transformers, supabase client, Twilio, Streamlit, entre otras librerías necesarias.

---

## 2. Configuración previa

1. **Variables de entorno**

   * Definir la ruta local o remota donde se encuentra el modelo de clasificación.
   * Credenciales de Twilio para WhatsApp: identificador de la cuenta, token secreto y número de origen autorizado para enviar mensajes.
   * Número destino por defecto para WhatsApp (aunque la UI permite modificarlo en la sesión).
   * URL y clave de proyecto Supabase, para conectar con la base de datos y registrar los reportes.
   * Opcionales de desarrollo: modo depuración, host y puerto de la API, etc.
   * Estas variables deben cargarse desde un archivo de entorno o definirse en la plataforma de despliegue sin exponerlas públicamente.

2. **Modelo de clasificación**

   * Exportar el modelo de Hugging Face entrenado para clasificar texto en “crítico” vs “no crítico” o similares.
   * Ubicar los archivos del modelo en la ruta configurada y asegurar que el contenedor o entorno local pueda acceder a ellos.
   * Si el tamaño es muy grande, valorar usar Git LFS o bien un mecanismo de descarga externa durante el arranque.

3. **Base de datos Supabase**

   * Crear en el proyecto Supabase una tabla para registrar los informes procesados, con columnas al menos para: identificador de informe, puntaje de confianza, bandera de criticidad, bandera de envío de WhatsApp y sello de tiempo de creación.
   * Ajustar permisos de la clave usada para permitir inserciones o actualizaciones (upsert) en esa tabla.

4. **Cuenta Twilio WhatsApp**

   * Registrar y verificar el número sandbox o de producción para WhatsApp.
   * Asegurarse de que el número destino haya aceptado el sandbox (en desarrollo) o esté habilitado para recibir mensajes.

---

## 3. Ejecución en entorno de desarrollo

* **Entorno virtual**: Crear y activar un entorno aislado, instalar dependencias listadas.
* **Variables de entorno locales**: Colocar un archivo de entorno (no versionado o en gitignore) con las credenciales y rutas necesarias.
* **Arranque de la API**: Levantar el servidor FastAPI para exponer el endpoint que recibe los informes. El servicio debe estar escuchando en el host y puerto configurados.
* **Arranque de la UI**: Iniciar la aplicación de monitorización basada en Streamlit. En desarrollo, esta interfaz puede iniciar la API internamente si detecta que no está corriendo, o puede funcionar conectándose a una API ya activa. Mostrará la tabla de reportes recientes consultando Supabase y un campo para cambiar temporalmente el número de WhatsApp destino para futuros envíos.
* **Pruebas manuales**:

  * Enviar un informe de ejemplo al endpoint de la API: la respuesta debe confirmar recepción y devolver un identificador.
  * Revisar que en segundo plano se procese el informe: se extrae la sección de hallazgos, se normaliza el texto, se clasifica. Si resultado es crítico, se envía el mensaje de WhatsApp. Finalmente, se registra el resultado en Supabase.
  * Verificar en la UI de Streamlit que el nuevo registro aparece en la tabla, con los valores esperados de puntaje, criticidad y envío.
* **Mocks en pruebas unitarias**: Para las pruebas automáticas, reemplazar el clasificador con uno simulado y la función de envío de WhatsApp para no efectuar llamadas reales. Verificar distintos escenarios: informe sin sección hallazgos, sin opinión, clasificación no crítica, fallo en envío de WhatsApp, informe muy largo, identificador duplicado, etc.

---

## 4. Interfaz de monitorización (Streamlit)

* **Objetivo**: Ofrecer una vista rápida de los reportes procesados recientemente y permitir cambiar el número destino de alertas.
* **Funcionamiento en desarrollo**:

  * Se arranca la UI de Streamlit; detecta si la API está activa o inicia un proceso de la API en segundo plano.
  * Se conecta a Supabase para consultar la tabla de registros recientes, muestra las columnas principales (identificador, puntaje, criticidad, envío de WhatsApp, sello de tiempo u otras columnas adicionales).
  * Permite al usuario introducir un nuevo número de WhatsApp destino; este cambio se guarda en la sesión de la UI.
  * En producción, este arranque conjunto puede desactivarse y la UI simplemente conecta a la API desplegada externamente.
* **Consideraciones de despliegue**:

  * La UI de Streamlit se expone en otro puerto o ruta. Si se desea combinar con FastAPI detrás de un proxy inverso, hay que configurar correctamente el proxy para solicitudes HTTP y WebSocket de Streamlit.
  * Si no se expone públicamente, se puede restringir acceso a la UI (autenticación o red interna).

---

## 5. Despliegue con contenedor

1. **Enfoque “único contenedor”**

   * Incluir solo la API o bien API y UI juntas. Si ambas conviven, puede usarse un gestor de procesos o un script que lance ambos servicios y los mantenga activos.
   * Alternativa simplificada: desplegar solo la API en el contenedor que escuche en el puerto expuesto (generalmente un único puerto expuesto por la plataforma). La UI de monitor se ejecuta por separado o se omite en producción.
   * Si se desea exponer ambos en un único puerto, puede usarse un proxy interno para enrutar rutas específicas (por ejemplo, ruta raíz a Streamlit y ruta /hl7 a FastAPI). Esto requiere configurar un servidor web ligero o proxy inverso dentro del contenedor y manejar WebSocket para Streamlit.
   * Asegurarse de que las rutas de los archivos dentro de la imagen coincidan con lo que la configuración de arranque espera (por ejemplo, dónde está el script de Streamlit y el módulo de FastAPI).

2. **Variables de entorno en producción**

   * Configurar en la plataforma de despliegue las variables de entorno necesarias (credenciales, rutas, modo de depuración desactivado).
   * Validar que, al iniciar el contenedor, la aplicación encuentre dichas variables para no fallar en la inicialización de ajustes. Si faltan, la aplicación debe registrarlo en logs y detenerse o fallar de forma clara.

3. **Modelo grande**

   * Si el modelo ocupa espacio considerable, considerar descargarlo al iniciar el contenedor desde un almacenamiento externo (S3, bucket, supabase storage) en lugar de incorporarlo en la imagen final. Esto reduce tamaño de imagen y facilita actualizaciones de modelo sin reconstruir la imagen completa.
   * Si se incluye en la imagen, usar Git LFS o un volumen adicional.
   * Ajustar cualquier configuración de entorno necesaria para lectura de safetensors o mecanismos equivalentes (por ejemplo, variables de entorno que permitan cabeceras grandes).

4. **Proxy inverso y WebSocket**

   * Cuando se expone Streamlit detrás de un proxy (por ejemplo, nginx), es necesario habilitar el paso de cabeceras Upgrade y Connection para WebSocket en la configuración del proxy, de modo que la parte interactiva de Streamlit funcione.
   * Si no se requiere UI interactiva en producción, se puede omitir Streamlit o exponerlo directamente en un puerto distinto.

5. **Supervisión de procesos**

   * Si se usa un gestor de procesos dentro del contenedor (supervisord, s6, etc.), configurar cada programa (API, UI, proxy) con arranque automático y reinicio ante fallo.
   * Alternativamente, usar un enfoque más simple que lance un único proceso (por ejemplo, solo FastAPI) y relegar la UI a otra unidad de despliegue.

6. **Plataforma PaaS (por ejemplo Railway, Heroku, AWS App Runner)**

   * Configurar la plataforma para que detecte el contenedor o use buildpacks/Nixpacks.
   * Definir la orden de inicio que arranque el proceso principal y escuche en el puerto que la plataforma exponga. Si el contenedor pretende escuchar en múltiples puertos, normalmente la plataforma solo enruta uno, por lo que es más sencillo exponer solo la API o solo la UI.
   * Definir variables de entorno en el panel de la plataforma, incluidas las credenciales sensibles.
   * Monitorear logs de la plataforma para detectar errores en arranque y faltas de variables.

---

## 6. Flujo de procesamiento (pipeline)

1. **Recepción del informe**

   * La aplicación expone un endpoint HTTP que recibe una carga JSON con identificador de informe y texto completo del informe.
   * Al recibir la petición, se valida que el contenido sea JSON válido y se extrae el campo correspondiente al texto. Si no se proporciona identificador, se genera uno nuevo.
   * Se retorna inmediatamente una respuesta de confirmación al emisor (“bien recibido” y el identificador asignado), mientras que el procesamiento posterior se realiza en segundo plano.

2. **Limpieza y extracción de sección**

   * Se elimina cualquier carácter de orden de bytes al inicio, se unifican saltos de línea y espacios innecesarios.
   * Se busca con una expresión regular la sección que comienza con una palabra clave (p. ej., “Hallazgos”) y se extrae desde allí hasta el final.
   * Se normaliza el texto extraído: convertir a minúsculas, eliminar tildes y acentos, colapsar múltiples espacios.

3. **Clasificación**

   * Se invoca el pipeline de Hugging Face configurado con el modelo cargado: se le pasa el texto normalizado y se obtiene una etiqueta y puntaje de confianza.
   * Se determina si la etiqueta corresponde a “crítico” según la configuración de etiquetas del modelo.

4. **Construcción de alerta**

   * Si el resultado es “crítico”, se busca la sección de “Opinión” dentro del texto ya extraído o en el informe, para incluirla en el mensaje de alerta.
   * Se prepara el cuerpo del mensaje de WhatsApp incluyendo identificador de informe, fragmento de texto relevante (opinión o parte de hallazgos) y puntaje de confianza.
   * Se intenta enviar el mensaje mediante la API de Twilio. Se captura cualquier excepción para no detener el procesamiento si el envío falla.
   * Se marca en la base de datos si el envío fue exitoso o no.

5. **Registro en la base de datos**

   * Independientemente de si es crítico o no, se registra en la tabla: identificador, puntaje, bandera de criticidad, bandera de envío de WhatsApp. (En la versión actual puede registrar solo si es crítico; se puede ampliar para todos los informes.)
   * Si el mismo identificador llega de nuevo, se actualiza o duplica el registro según la lógica de upsert configurada.

6. **Monitorización y consulta**

   * La interfaz Streamlit ofrece una vista de los registros guardados, ordenados por fecha o identificador. Permite al usuario ver rápidamente qué informes han sido procesados, con qué puntaje y si se envió alerta.
   * Permite modificar dinámicamente el número destino para alertas futuras, guardándolo en la sesión de la UI. Para persistir este cambio más allá de la sesión, sería necesario extender la lógica para guardar en configuración o base de datos.

---

## 7. Integración con Mirth Connect (u otros sistemas de origen)

* Si los informes llegan desde Mirth Connect u otro sistema de integración de HL7, se configura en Mirth un conector HTTP que envíe el BODY JSON al endpoint de la API.
* En Mirth se puede definir un transformer de salida que convierta el mensaje HL7 a JSON con los campos “reportId” y “report”.
* Se recomienda manejar la respuesta de la API: confirmar que la respuesta tenga el formato esperado, detectar posibles errores HTTP o contenido inesperado.
* En la integración, si se obtiene código de error o contenido HTML (por ejemplo, página de error 403), revisar la URL, autenticación y permisos de red.
* Documentar en Mirth: indicar la URL del endpoint, método HTTP, formato de JSON esperado, mapeo de campos desde el mensaje HL7 original, y lógica de manejo de la respuesta (por ejemplo, solo continuar si la API confirma recepción).

---

## 8. Pruebas y casos de uso

* **Pruebas unitarias**: Simular distintos contenidos de informe y verificar que la función de limpieza y extracción retorna lo esperado. Mockear la llamada al clasificador para simular etiquetas y puntajes concretos. Mockear envío de WhatsApp para verificar que, cuando se clasifica como crítico, se invoca la función correspondiente y se registra en Supabase la bandera adecuada. Verificar manejo de excepción en envío de WhatsApp: la bandera queda en falso y no detiene el flujo.
* **Pruebas de integración**: Con un entorno local de Supabase de prueba y credenciales de Twilio sandbox, enviar peticiones reales al endpoint y observar el comportamiento completo. Confirmar que la tabla en Supabase se va llenando con registros según los envíos.
* **Casos de esquina**: Informe sin sección “Hallazgos”; informe muy extenso; informe con sección “Opinión” ausente o con formato irregular; informe con caracteres especiales; informe duplicado de identificador; fallo de red al enviar a Supabase o Twilio; credenciales inválidas.
* **Pruebas de la UI**: Arrancar Streamlit y confirmar que muestra registros; cambiar número destino y simular un informe nuevo para verificar que el mensaje va al número actualizado en la sesión.

---

## 9. Despliegue en producción

* Para la puesta en marcha en un entorno de producción, el despliegue se realizó desde un repositorio distinto al actual, dado que no se contaba con los permisos necesarios sobre este proyecto. La versión en producción está disponible en la siguiente dirección:
http://20.151.72.55:8080/

* Allí corre la aplicación dentro de un contenedor en Azure. No se exponen en esta documentación los detalles internos de configuración o scripts específicos de ese repositorio de despliegue, pero se confirma que la estructura general y las variables de entorno necesarias (credenciales de Twilio, Supabase, ruta del modelo, etc.) se configuraron de forma análoga a lo explicado en este README.