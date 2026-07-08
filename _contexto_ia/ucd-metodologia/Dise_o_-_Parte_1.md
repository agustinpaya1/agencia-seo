Diseño
Desarrollo Centrado en el Usuario
Grado en Ingeniería Informática
Universitat Politècnica de València
Curso 2025-26

Diseño
1. Diseño de software
1.1. Diseño de software. Definición
1.2. Arquitectura software
1.3. Diseño detallado
2. Diseño de interfaces gráficas de usuario
Desarrollo Centrado en el Usuario

1.1  Diseño de software. Definición
| Análisis | Diseño | Implementación |
| -------- | ------ | -------------- |
Desarrollo Centrado en el Usuario

1.1 Diseño de software. Definición
● ¿Qué es?: Actividad que transforma requisitos en
soluciones.
● Objetivo: reducir complejidad y organizar el sistema.
● Dos niveles principales:
○ Diseño de alto nivel → arquitectura.
○ Diseño de bajo nivel → detalles técnicos e
interfaces.
Desarrollo Centrado en el Usuario

1.2 Arquitectura software
Definición
● ¿Qué es?: Fase del diseño de software en la que se define la estructura
global del sistema, identificando sus principales componentes, sus
responsabilidades y las formas en que se comunican. Proporciona una visión
de alto nivel que sirve de guía para las decisiones técnicas posteriores.
● ¿Para qué?: Establecer una base estructural sólida que cumpla los
requisitos. Actúa como un puente entre los requisitos y el diseño detallado.
● Relación con DCU: Debe permitir interacciones fluidas, tiempos de
respuesta adecuados, accesibilidad, personalización y seguridad.
Desarrollo Centrado en el Usuario

1.2 Arquitectura software
Tipos de arquitecturas software
● Monolítica: todo en una sola aplicación.
● Cliente-Servidor: clientes solicitan, servidor responde.
● En capas: presentación, lógica, datos.
● Microservicios / SOA: servicios independientes y
escalables.
● Orientada a eventos: comunicación mediante
sucesos.
● Cloud-native: contenedores, servicios en la nube.
Desarrollo Centrado en el Usuario

1.2 Arquitectura software
Tipos de arquitecturas software
● Monolítica: todo en una sola aplicación.
Desarrollo Centrado en el Usuario

1.2 Arquitectura software
Tipos de arquitecturas software
● En capas: presentación, lógica, datos.
Desarrollo Centrado en el Usuario

1.2 Arquitectura software
Tipos de arquitecturas software
● Cliente-Servidor: clientes solicitan, servidor responde.
Desarrollo Centrado en el Usuario

1.2 Arquitectura software
Tipos de arquitecturas software
● SOA: servicios independientes y escalables.
Desarrollo Centrado en el Usuario

1.2 Arquitectura software
Tipos de arquitecturas software
● Microservicios: servicios independientes y escalables.
Desarrollo Centrado en el Usuario

1.2 Arquitectura software
Tipos de arquitecturas software
● Orientada a eventos: comunicación mediante sucesos.
Desarrollo Centrado en el Usuario

1.2 Arquitectura software
Tipos de arquitecturas software
● Cloud-native: contenedores, servicios en la nube.
Desarrollo Centrado en el Usuario

1.2 Arquitectura software
Tipos de aplicaciones software
● Software empotrado: en coches, robots, IoT.
● Aplicaciones de escritorio: instaladas en PC.
● Aplicaciones web: accesibles desde navegador.
● Aplicaciones móviles.
● Aplicaciones distribuidas.
● Sistemas críticos y en tiempo real.
Desarrollo Centrado en el Usuario

1.2 Arquitectura software
Relación tipos de aplicaciones software - arquitectura
Software empotrado Monolítica, en capas ligeras Limitaciones de recursos y
necesidad de simplicidad.
● Ejemplo: Sistema de control de lavadora
● La lavadora tiene un microcontrolador con memoria y procesamiento limitados. Se
programa un conjunto de rutinas que controlan sensores y actuadores. Simplicidad y
fiabilidad son esenciales.
● El usuario no ve el software, pero su interacción se da mediante el panel físico
(botones, indicadores). La arquitectura debe garantizar respuesta inmediata y
feedback claro (luces, pitidos) para una buena experiencia de uso.
Desarrollo Centrado en el Usuario

1.2 Arquitectura software
Relación tipos de aplicaciones software - arquitectura
Aplicaciones de escritorio Monolítica, en capas ligeras Normalmente un ejecutable,
modularidad facilita mantenimiento.
● Ejemplo: Gestor de recursos tecnológicos de una empresa
● Utilizar el patrón arquitectónico: Modelo-Vista-Controlador (MVC).
● La arquitectura MVC permite iterar sobre la interfaz sin reescribir la lógica, facilitando
pruebas de usabilidad y prototipado rápido.
Desarrollo Centrado en el Usuario

1.2 Arquitectura software
Relación tipos de aplicaciones software - arquitectura
Aplicaciones web Cliente-servidor, en capas, Escalabilidad, separación
microservicios presentación-lógica-datos.
● Ejemplo: Aplicación de gestión de biblioteca universitaria
● Utiliza una arquitectura cliente-servidor “tradicional”
● Cliente: Navegador web con interfaz HTML/CSS/JavaScript
● Servidor: Una aplicación central (por ejemplo, en PHP o Java EE) que maneja toda la
lógica de negocio y accede a una única base de datos
● El cliente envía peticiones HTTP y el servidor responde con páginas completas (por
ejemplo, en JSP, Django, Laravel…)
Desarrollo Centrado en el Usuario

1.2 Arquitectura software
Relación tipos de aplicaciones software - arquitectura
Aplicaciones web Cliente-servidor, en capas, Escalabilidad, separación
microservicios presentación-lógica-datos.
● Ejemplo: Netflix
● Utiliza una arquitectura basada en microservicios
● Cada funcionalidad se implementa como un microservicio independiente:
○ Servicio de usuarios
○ Servicio de recomendaciones
○ Servicio de streaming
○ Servicio de facturación
● Cada microservicio tiene su propia base de datos y se comunica con otros mediante
API REST o mensajería (Kafka, RabbitMQ)
● Se despliegan de forma independiente (normalmente en contenedores Docker
orquestados con Kubernetes)
Desarrollo Centrado en el Usuario

1.2 Arquitectura software
Relación tipos de aplicaciones software - arquitectura
Aplicaciones web Cliente-servidor, en capas, Escalabilidad, separación
microservicios presentación-lógica-datos.
● Ejemplo: Sistema de banca en línea corporativo (multicanal)
● Utiliza una arquitectura SOA
● Conjunto de servicios reutilizables expuestos mediante SOAP o REST, definidos en un
bus de servicios (ESB):
○ Servicio de autenticación
○ Servicio de gestión de cuentas
○ Servicio de transferencias
○ Servicio de notificaciones
● Los servicios pueden ser consumidos por distintas aplicaciones (web, móvil, cajeros,
API de terceros)
Desarrollo Centrado en el Usuario

1.2 Arquitectura software
Relación tipos de aplicaciones software - arquitectura
Aplicaciones móviles Cliente-servidor, en capas, Dependencia de backend, uso de
orientada a eventos sensores y contexto
● Ejemplo: Whatsapp
● Arquitectura cliente-servidor más tradicional
● El cliente móvil envía y recibe mensajes al servidor central que gestiona usuarios,
chats y notificaciones
● Toda la lógica de negocio (entrega de mensajes, sincronización de chats) reside en el
backend
Desarrollo Centrado en el Usuario

1.2 Arquitectura software
Relación tipos de aplicaciones software - arquitectura
Aplicaciones móviles Cliente-servidor, en capas, Dependencia de backend, uso de
orientada a eventos sensores y contexto
● Ejemplo: Strava
● Arquitectura: Orientada a eventos
● Los sensores del móvil (GPS, acelerómetro, frecuencia cardíaca) generan eventos que
la app procesa en tiempo real
● La app reacciona a eventos de usuario (empezar/pausar entrenamiento) y del entorno
(cambios de ubicación o ritmo)
Desarrollo Centrado en el Usuario

1.2 Arquitectura software
Relación tipos de aplicaciones software - arquitectura
Tipo de aplicación Arquitecturas más comunes Justificación
Software empotrado Monolítica, en capas ligeras Limitaciones de recursos y
necesidad de simplicidad.
Aplicaciones de escritorio Monolítica en algunos casos, en Podría servir con un ejecutable,
capas modularidad facilita mantenimiento.
Aplicaciones web Cliente-servidor, en capas, Escalabilidad, separación
microservicios presentación-lógica-datos.
Aplicaciones móviles Cliente-servidor, en capas, Dependencia de backend, uso de
orientada a eventos sensores y contexto.
Aplicaciones distribuidas Microservicios, orientada a eventos, Escalabilidad, resiliencia y
cloud-native despliegue en múltiples nodos.
Sistemas críticos en tiempo real Monolítica optimizada, en capas, Fiabilidad, predictibilidad y
SOA controlada seguridad estricta.
Desarrollo Centrado en el Usuario

1.3 Diseño detallado
Definición
● ¿Qué es?: Fase del diseño de software en la que se especifican los
componentes internos del sistema, sus relaciones y su comportamiento.
Define cómo se implementa cada módulo internamente.
● ¿Para qué?: Traducir la arquitectura (componentes y relaciones de alto nivel)
en un diseño implementable (clases, estructuras de datos, algoritmos, APIs,
etc.).
● Relación con DCU: Las decisiones del diseño detallado deben reflejar los
requisitos de usuario, usabilidad y experiencia definidos durante el proceso
de diseño centrado en el usuario.
Desarrollo Centrado en el Usuario

1.3 Diseño detallado
¿Qué puede incluir?
● Estructura interna de los módulos: Clases, objetos, funciones, métodos.
Relaciones: herencia, agregación, composición, dependencias.
● Diseño de datos: Estructuras de datos. Modelos de datos persistentes (por
ejemplo, entidades y relaciones). Correspondencia entre modelo conceptual
y modelo lógico.
● Diseño de algoritmos: Lógica de negocio. Flujo de control. Pseudocódigo
o diagramas de flujo.
● Interfaces internas: APIs entre módulos. Contratos (entradas, salidas,
excepciones).
Desarrollo Centrado en el Usuario

1.3 Diseño detallado
Artefactos a construir
● Diagramas UML:
○ Diagrama de clases (estructura).
○ Diagrama de secuencia o comunicación (interacciones).
○ Diagrama de estados (comportamientos reactivos).
● Diagramas de componentes o despliegue → para ver cómo se concreta
la arquitectura.
● Wireframes o prototipos UI → cómo el diseño detallado da soporte
técnico a los elementos de interfaz.
Desarrollo Centrado en el Usuario

1.3 Diseño detallado
Ejemplo. Diagrama de clases para componente gestión de carrito
Desarrollo Centrado en el Usuario

1.3 Diseño detallado
Del diseño técnico al diseño de interacción
● No solo importa cómo se organiza el sistema, sino cómo
lo usan los usuarios.
● La arquitectura influye en la interfaz:
○ Apps móviles → sensores, notificaciones.
○ Web → conectividad, navegadores.
○ Empotrado → pantallas reducidas o interacción
mínima.
Desarrollo Centrado en el Usuario

1.3 Diseño detallado
Del diseño técnico al diseño de interacción
● El usuario es el centro del proceso de diseño.
● El diseño de interfaces debe:
○ Ser intuitivo.
○ Adaptarse al contexto de uso.
○ Asegurar usabilidad y experiencia positiva.
Desarrollo Centrado en el Usuario
