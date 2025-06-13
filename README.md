# **RAD-ALERT**
![Banner](static/banner.png) 

RAD-ALERT es un prototipo operativo que **detecta hallazgos críticos en informes radiológicos no estructurados y alerta en tiempo real al equipo de guardia**, sin exponer datos sensibles y sin interrumpir el flujo clínico existente. Este repositorio contiene la **lógica de negocio** (clasificación, API REST y notificaciones) junto con la documentación funcional y de pruebas.
Si en algún momento necesitas profundizar en un componente concreto (por ejemplo, los scripts de MIRTH, la API o la puesta en producción), encontrarás secciones específicas enlazadas al final de cada apartado.

---

## ¿Qué hace RAD-ALERT?

1. **Clasifica** cada informe HL7 con un modelo RoBERTa entrenado ad-hoc, alcanzando un recall superior al 92 %.
2. **Expone** un punto /hl7 que recibe el texto, genera la predicción y responde en menos de medio segundo.
3. **Notifica** por WhatsApp Business en cuestión de segundos cuando la probabilidad de criticidad supera el umbral clínico.
4. **Registra** cada evento en Supabase y mueve el archivo HL7 al repositorio histórico para auditoría.
5. **Se recupera** automáticamente si la API se reinicia, gracias al re-intento nativo de MIRTH.

---

## Resumen de la validación

* **Cobertura clínica**: recall > 0,92 y precisión equilibrada sobre un conjunto ciego representativo.
* **Rendimiento**: latencia media de 210 ms por solicitud; alertas de WhatsApp entregadas en < 10 s.
* **Robustez**: 13 pruebas unitarias e integración superadas, incluidos fallos simulados del backend.
* **Shadow mode**: miles de informes reales procesados durante 2 semanas sin interferir en el flujo normal y sin incidentes de privacidad.
* **Objetivos**: se cumplieron todos los hitos planteados (detección fiable, tiempo real, confidencialidad y resiliencia).

Para los detalles de métricas y las tablas completas de resultados, dirígete a la sección “Validación” del documento `docs/Resultados.md`.

---

## Estructura del repositorio (alto nivel)

* **api/** – Contiene la lógica principal (clasificador, API, notificaciones, configuración).
* **docs/** – Glosario, protocolos de prueba, bitácora de validación y diagramas.
* **mirth/** – Scripts JavaScript y plantillas de canal para el flujo HL7.
* **tests/** – Casos unitarios y de integración (pytest).

Cada carpeta incluye un README interno con instrucciones de uso y configuración específicas.

---

## Despliegue de referencia

El entorno de producción se levantó desde un repositorio hermano (por falta de permisos en este) y se ejecuta en un contenedor de Azure disponible en
`http://20.151.72.55:8080/`.
La configuración de variables de entorno y la estructura de carpetas replica la descrita aquí, de modo que las instrucciones de este repositorio siguen siendo válidas.

---

## Próximos pasos

* **Migración on-premise** al clúster de la Fundación Valle del Lili para producción controlada.
* **Ajuste fino** del umbral de alerta y panel de revisión de falsos positivos.