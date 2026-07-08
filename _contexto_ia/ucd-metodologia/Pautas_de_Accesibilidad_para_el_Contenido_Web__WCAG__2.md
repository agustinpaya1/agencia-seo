15/10/2015

Pautas de Accesibilidad para el Contenido Web (WCAG) 2.0

[Contenidos]

Web Content Accessibility Guidelines (WCAG) 2.0

Lead translating organization (LTO):

Fundación Sidar - Acceso Universal
Web site: http://www.sidar.org/
Coordinators of the translation: Emmanuelle Gutiérrez y Restrepo (e-mail:
coordina@sidar.org) and Carlos Benavidez (e-mail: carlos@sidar.org)
Translator: Sofía Benavidez (e-mail: sofia@sidar.org)

Traducción Candidata a ser la Oficial al Español

Publicada el 15 de diciembre de 2009

Esta versión:

http://www.sidar.org/traducciones/wcag20/es/

Versión original en inglés:

http://www.w3.org/TR/WCAG20/

Errata:

http://www.sidar.org/traducciones/wcag20/es/errata/

Organización coordinadora de la traducción:
Fundación Sidar - Acceso Universal
Sitio web: http://www.sidar.org/
Coordinadores de la traducción: Emmanuelle Gutiérrez y Restrepo (e-mail:
coordina@sidar.org) y Carlos Benavidez (e-mail: carlos@sidar.org)
Traductora: Sofía Benavidez (e-mail: sofia@sidar.org)

Miembros del Comité de Revisión:

El 16 de marzo de 2009 se envió la lista de miembros que conformarían el Comité de
Revisión, a la lista de traductores del W3C.

Resumen de los comentarios sobre el borrador de la traducción candidata a ser oficial
(CAT, por sus siglas en inglés que significan: Candidate Authorized Translation):

http://www.sidar.org/traducciones/wcag20/es/comentarios/

Esta es una Traducción Autorizada de un documento del W3C. La publicación de esta traducción
ha seguido los pasos descritos por las Normas para las Traducciones Autorizadas por el W3C.
En caso de controversia, la versión autorizada de la especificación es el documento original en
inglés.

Pautas de Accesibilidad para el Contenido Web (WCAG) 2.0

Recomendación del W3C del 11 de diciembre de 2008

Esta versión:

http://www.w3.org/TR/2008/REC-WCAG20-20081211/

Última versión:

http://www.w3.org/TR/WCAG20/

Versión anterior:

http://www.sidar.org/traducciones/wcag20/es/

1/37

15/10/2015

Pautas de Accesibilidad para el Contenido Web (WCAG) 2.0

http://www.w3.org/TR/2008/PR-WCAG20-20081103/

Editores:

Ben Caldwell, Trace R&D Center, Universidad de Wisconsin-Madison
Michael Cooper, W3C
Loretta Guarino Reid, Google, Inc.
Gregg Vanderheiden, Trace R&D Center, Universidad of Wisconsin-Madison

Editores anteriores:

Wendy Chisholm (hasta julio de 2006, cuando formaba parte del W3C)
John Slatin (hasta junio de 2006, cuando formaba parte del Instituto de Accesibilidad de la
Universidad de Austin, Texas)
Jason White (hasta junio de 2005, cuando formaba parte de la Universidad de Melbourne)

Por favor, véase la fe de erratas de este documento, que puede incluir correcciones normativas.

Véanse también las traducciones.

Este documento también está disponible en formatos no normativos en Versiones alternativas de las
Pautas de Accesibilidad para el Contenido Web 2.0.

Copyright © 2008 W3C® (MIT, ERCIM, Keio), todos los derechos reservados. Se aplican las reglas
del W3C sobre responsabilidad, marca registrada y uso del documento.

Resumen

Las Pautas de Accesibilidad para el Contenido Web (WCAG) 2.0 cubren un amplio rango de
recomendaciones para crear contenido Web más accesible. Seguir estas pautas permite crear un
contenido más accesible para un mayor número de personas con discapacidad, incluyendo ceguera y
baja visión, sordera y deficiencias auditivas, deficiencias del aprendizaje, limitaciones cognitivas,
limitaciones de la movilidad, deficiencias del habla, fotosensitividad y combinaciones de las anteriores.
Seguir estas pautas puede a menudo ayudar a que el contenido Web sea más usable para cualquier
tipo de usuario.

Los criterios de conformidad de las WCAG 2.0 están escritos como enunciados verificables no
específicos de ninguna tecnología. En documentos separados se proporcionan niveles de orientación
sobre cómo satisfacer los criterios de conformidad en tecnologías concretas, así como información
general acerca de cómo interpretar los criterios de conformidad. Para acceder a una introducción y a
enlaces a material técnico y educativo, diríjase a la Visión general de las Pautas de Accesibilidad para
el Contenido Web (WCAG).

Las WCAG 2.0 suceden a las Pautas de Accesibilidad para el Contenido Web (WCAG) 1.0 [WCAG10],
que fueron publicadas como Recomendación del W3C en mayo de 1999. Aunque es posible cumplir
con las WCAG 1.0 o con las WCAG 2.0 (o con ambas), el W3C recomienda que los contenidos
nuevos o actualizados sigan las WCAG 2.0. El W3C también recomienda que las políticas de
accesibilidad web hagan referencia a las WCAG 2.0.

Estado de este documento

En esta sección se describe el estado de este documento en el momento de su publicación. Otros
documentos pueden reemplazarlo. En el Índice de informes técnicos del W3C en
http://www.w3.org/TR/ se recoge una lista de las publicaciones actuales del W3C así como la última
revisión de este informe técnico.

Estas son las Pautas de Accesibilidad para el Contenido Web (WCAG) 2.0, una Recomendación del
W3C del Grupo de Trabajo sobre las Pautas de Accesibilidad para el Contenido Web.

Este documento ha sido revisado por Miembros del W3C, por desarrolladores de software y por otros
grupos del W3C y entidades interesadas, y fue aprobado por el Director como una Recomendación del

http://www.sidar.org/traducciones/wcag20/es/

2/37

15/10/2015

Pautas de Accesibilidad para el Contenido Web (WCAG) 2.0

W3C. Es un documento estable y puede ser utilizado como material de referencia o citado en otro
documento. El papel del W3C al crear la Recomendación es atraer la atención sobre la especificación
y promover su difusión, mejorando así la funcionalidad e interoperabilidad de la Web.

Las WCAG 2.0 se apoyan en documentos asociados que no son normativos: Comprender las WCAG
2.0 y Técnicas para las WCAG 2.0. Aunque estos documentos no tienen el estatus formal de las
WCAG 2.0, proporcionan información importante para poder entenderlas e implementarlas.

El Grupo de Trabajo solicita que cualquier comentario se haga por medio del formulario de
comentarios en línea. Si esto no es posible, los comentarios también pueden ser enviados a public-
comments-wcag20@w3.org. Los archivos de la lista de comentarios pública están disponibles
públicamente. Los comentarios recibidos acerca de la Recomendación WCAG 2.0 no pueden generar
cambios en esta versión de las pautas, pero pueden ser tenidos en cuenta para la fe de erratas o para
versiones futuras de las WCAG. El Grupo de Trabajo no planea responder formalmente a los
comentarios. Los archivos de las discusiones de la lista de correo de WCAG WG están disponibles
públicamente, y los trabajos que el Grupo de Trabajo realice en el futuro pueden hacer referencia a
comentarios recibidos sobre este documento.

Este documento fue producido como parte de la Iniciativa de Accesibilidad Web (WAI) del W3C. Los
objetivos del Grupo de Trabajo se discuten en el Estatuto del Grupo de Trabajo WCAG. El Grupo de
Trabajo WCAG es parte de la Actividad Técnica del WAI.

Este documento fue producido por un grupo que opera bajo la Política de Patentes del W3C del 5 de
febrero de 2004. El W3C mantiene una lista pública de las distribuciones de patentes, redactada en
conjunto con los entregables del grupo. Esa página también incluye instrucciones para distribuir una
patente. Cualquier individuo que tenga conocimiento real de una patente y crea que contiene
Reclamación(es) Esencial(es) debe remitir la información de acuerdo con lo enunciado en la sección 6
de la Política de Patentes del W3C.

Tabla de contenidos

Introducción

Niveles de orientación de las WCAG 2.0
Documentos de apoyo de las WCAG 2.0
Términos importantes en las WCAG 2.0

Pautas WCAG 2.0

1 Perceptible

1.1 Proporcionar alternativas textuales para todo contenido no textual de modo
que se pueda convertir a otros formatos que las personas necesiten, tales como
textos ampliados, braille, voz, símbolos o en un lenguaje más simple.
1.2 Medios tempodependientes: proporcionar alternativas para los medios
tempodependientes.
1.3 Crear contenido que pueda presentarse de diferentes formas (por ejemplo,
con una disposición más simple) sin perder información o estructura.
1.4 Facilitar a los usuarios ver y oír el contenido, incluyendo la separación entre el
primer plano y el fondo.

2 Operable

2.1 Proporcionar acceso a toda la funcionalidad mediante el teclado.
2.2 Proporcionar a los usuarios el tiempo suficiente para leer y usar el contenido.
2.3 No diseñar contenido de un modo que se sepa podría provocar ataques,
espasmos o convulsiones.
2.4 Proporcionar medios para ayudar a los usuarios a navegar, encontrar
contenido y determinar dónde se encuentran.

3 Comprensible

3.1 Hacer que los contenidos textuales resulten legibles y comprensibles.
3.2 Hacer que las páginas web aparezcan y operen de manera predecible.

http://www.sidar.org/traducciones/wcag20/es/

3/37

15/10/2015

Pautas de Accesibilidad para el Contenido Web (WCAG) 2.0

3.3 Ayudar a los usuarios a evitar y corregir los errores.

4 Robusto

4.1 Maximizar la compatibilidad con las aplicaciones de usuario actuales y futuras,
incluyendo las ayudas técnicas.

Conformidad

Requisitos de Conformidad
Declaraciones de conformidad (opcional)
Enunciado de conformidad parcial – Contenido de terceras partes
Enunciado de conformidad parcial – Lenguaje

Apéndices

Apéndice A: Glosario (Normativo)
Apéndice B: Reconocimientos
Apéndice C: Referencias

Introducción

Esta sección es informativa.

Las Pautas de Accesibilidad para el Contenido Web 2.0 definen cómo crear contenido web más
accesible para las personas con discapacidad. La accesibilidad considera un amplio rango de
discapacidades, tales como las visuales, auditivas, físicas, del habla, cognitivas, del lenguaje, de
aprendizaje y neurológicas. Aunque estas pautas cubren un amplio rango de discapacidades, no son
suficientes para satisfacer las necesidades de personas con todos los tipos, grados y combinaciones
de discapacidad posibles. Estas pautas también ayudan a que el contenido sea más usable para las
personas mayores, que ven sus habilidades reducidas a causa de la edad y, a menudo, mejoran la
usabilidad para los usuarios en general.

Las WCAG 2.0 se han desarrollado mediante el proceso del W3C en cooperación con individuos y
organizaciones en todo el mundo, con el fin de proporcionar un estándar compartido para la
accesibilidad del contenido web que satisfaga las necesidades de personas, organizaciones y
gobiernos a nivel internacional. Las WCAG 2.0 se basan en las WCAG 1.0 [WCAG10] y se han
diseñado para ser aplicadas a una amplia gama de tecnologías web ahora y en el futuro, y para ser
verificables con una combinación de pruebas automatizadas y evaluación humana. Para una
introducción a las WCAG, véase la Visión General de las Pautas de Accesibilidad para el Contenido
Web.

La accesibilidad web no sólo depende de un contenido accesible sino también de la accesibilidad de
los navegadores y otras aplicaciones de usuario. Las herramientas de autor también tienen un papel
importante en la accesibilidad web. Para una visión de conjunto de estos componentes del desarrollo
web y su interacción, véase:

Componentes Esenciales de Accesibilidad Web

Visión General de las Pautas de Accesibilidad para Aplicaciones de Usuario (UAAG)

Visión General de las Pautas de Accesibilidad para Herramientas de Autor (ATAG)

Niveles de orientación de las WCAG 2.0

Los individuos y organizaciones que emplean las WCAG son un grupo amplio y variado que incluye
diseñadores y desarrolladores web, reguladores, agentes de compra, profesores y estudiantes. Para
poder satisfacer las necesidades tan variadas de esta audiencia, se proporcionan varios niveles de
orientación: principios generales, pautas generales, criterios de conformidad verificables y una amplia
colección de técnicas suficientes, técnicas recomendables y fallos comunes documentados con
ejemplos, enlaces a recursos adicionales y código.

http://www.sidar.org/traducciones/wcag20/es/

4/37

15/10/2015

Pautas de Accesibilidad para el Contenido Web (WCAG) 2.0

Principios - En el nivel más alto se sitúan los cuatro principios que proporcionan los
fundamentos de la accesibilidad web: perceptible, operable, comprensible y robusto. Véase
también Comprender los Cuatro Principios de la Accesibilidad.

Pautas - Por debajo de los principios están las pautas. Las doce pautas proporcionan los
objetivos básicos que los autores deben lograr con el fin de crear un contenido más accesible
para los usuarios con distintas discapacidad. Estas pautas no son verificables, pero
proporcionan el marco y los objetivos generales que ayudan a los autores a comprender los
criterios de conformidad y a implementar mejor las técnicas.

Criterios de Conformidad - Para cada pauta se proporcionan los criterios de conformidad
verificables que permiten emplear las WCAG 2.0 en aquellas situaciones en las que existan
requisitos y necesidad de evaluación de conformidad como: especificaciones de diseño,
compras, regulación o acuerdos contractuales. Con el fin de cumplir con las necesidades de los
diferentes grupos y situaciones, se definen tres niveles de conformidad: A (el más bajo), AA y
AAA (el más alto). Se puede obtener más información sobre los niveles de las WCAG en
Comprender los Niveles de Conformidad.

Técnicas suficientes y recomendables - Para cada una de las pautas y criterios de
conformidad del propio documento de las WCAG 2.0, el grupo de trabajo ha documentado
también una amplia variedad de técnicas. Las técnicas son informativas y se agrupan en dos
categorías: aquellas que son suficientes para satisfacer los criterios de conformidad, y aquellas
que son recomendables. Las técnicas recomendables van más allá de los requisitos de cada
criterio de conformidad individual y permiten a los autores afrontar mejor las pautas. Algunas de
las técnicas recomendables tratan sobre barreras de accesibilidad que no han sido cubiertas
por los criterios de conformidad verificables. También se han documentado los errores
frecuentes que son conocidos. Véase también Técnicas Suficientes y Recomendables en
Comprender las WCAG 2.0.

Todos estos niveles de orientación (principios, pautas, criterios de conformidad y técnicas suficientes y
recomendables) actúan en conjunto para proporcionar una orientación sobre cómo crear un contenido
más accesible. Se anima a los autores a que revisen y apliquen todos los niveles que puedan, incluso
las técnicas recomendables, para satisfacer las necesidades del rango de usuarios más amplio
posible.

Nótese que incluso un contenido que sea conforme con el nivel más alto (AAA) no será accesible para
individuos con cualquier tipo, grado o combinación de discapacidades, en particular en el ámbito de
las discapacidades cognitivas, de las relativas al lenguaje y al aprendizaje. Se anima a los autores a
considerar todo el abanico de técnicas, incluidas las recomendables, así como a tratar de buscar
consejo acerca de las mejores prácticas actuales que aseguren un contenido web accesible, en la
medida de lo posible, para esos grupos de discapacidades. Los metadatos pueden ayudar a los
usuarios a localizar los contenidos más apropiados para sus necesidades.

Documentos de apoyo de las WCAG 2.0

El documento de las WCAG 2.0 se ha diseñado para cubrir las necesidades de quienes necesiten un
estándar técnico estable y referenciable. Otros documentos, denominados documentos de apoyo, se
basan en el documento de las WCAG 2.0 y cumplen otros propósitos adicionales importantes, como
permitir su actualización para describir cómo podrían ser aplicadas las WCAG a nuevas tecnologías.
Los documentos de apoyo incluyen:

1.  Cómo cumplir con las WCAG 2.0 - Un documento de referencia rápida personalizable que
incluye todas las pautas, criterios de conformidad y técnicas que los autores pueden emplear
para desarrollar y evaluar contenido web.

2.  Comprender las WCAG 2.0 - Una guía para comprender e implementar las WCAG 2.0. Para
cada pauta y criterio de conformidad, existe un breve documento llamado "Comprender" que
cubre temas clave.

http://www.sidar.org/traducciones/wcag20/es/

5/37

15/10/2015

Pautas de Accesibilidad para el Contenido Web (WCAG) 2.0

3.  Técnicas para las WCAG 2.0 - Una colección de técnicas y fallos frecuentes, cada una en un

documento independiente que incluye la descripción de los mismos, ejemplos, código y
pruebas.

4.  Los Documentos de las WCAG 2.0 - Un diagrama y una descripción de cómo se relacionan y

entrelazan entre sí los documentos técnicos.

Véase Visión General de las Pautas de Accesibilidad para el Contenido Web (WCAG) para una
descripción del material de apoyo de las WCAG 2.0, incluyendo recursos educativos relacionados con
ellas. En los Recursos del WAI se recogen documentos adicionales que cubren temas tales como
casos de negocio para la accesibilidad web, la planificación de la aplicación de mejoras a la
accesibilidad de los sitios web y las políticas de accesibilidad.

Términos importantes en las WCAG 2.0

Las WCAG 2.0 incluyen tres términos importantes con significado diferente al usado en las WCAG 1.0.
Cada uno de ellos se presenta brevemente a continuación y se definen de forma más completa en el
glosario.

Página web

Es importante señalar que, en este estándar, el término "página web" abarca mucho más que
páginas estáticas de HTML. Incluye además las páginas web cada vez más dinámicas que
están surgiendo, incluyendo "páginas" que pueden representar comunidades interactivas
virtuales completas. Por ejemplo, el término "página web" incluye una experiencia inmersiva
similar a la de una película interactiva que se localiza en una única URI. Para más
información, véase Comprender "Página Web".

Determinado por software

Varios criterios de conformidad exigen que el contenido (o ciertos aspectos del contenido)
pueda ser "determinado por software". Esto significa que el contenido se provee de manera
que las aplicaciones de usuario, incluidas las ayudas técnicas, pueden extraer y presentar
esa información a los usuarios en distintas modalidades. Para más información, véase
Comprender "Determinado por Software".

Compatible con la accesibilidad

Usar una tecnología de manera compatible con la accesibilidad significa que funciona con las
ayudas técnicas y con las características de accesibilidad de los sistemas operativos,
navegadores y otras aplicaciones de usuario. Sólo se puede depender de las características
de las tecnologías para cumplir con los criterios de conformidad de las WCAG 2.0 si se
utilizan de manera "compatible con la accesibilidad". Se pueden emplear características de
una tecnología en formas que no sea compatible con la accesibilidad (que no funcionen con
las ayudas técnicas, etc.) siempre que no se dependa de ellas para satisfacer algún criterio
de conformidad (es decir, la misma información o funcionalidad está disponible también de
otra forma que sí es compatible).
La definición de "compatible con la accesibilidad" se proporciona en el Apéndice A: Glosario
de estas pautas. Para más información, véase Comprender Compatible con la Accesibilidad.

Pautas WCAG 2.0

Esta sección es normativa.

Principio 1: Perceptible - La información y los componentes de la
interfaz de usuario deben ser presentados a los usuarios de modo que
ellos puedan percibirlos.

http://www.sidar.org/traducciones/wcag20/es/

6/37

15/10/2015

Pautas de Accesibilidad para el Contenido Web (WCAG) 2.0

Pauta 1.1 Alternativas textuales: Proporcionar
alternativas textuales para todo contenido no
textual de modo que se pueda convertir a otros
formatos que las personas necesiten, tales como
textos ampliados, braille, voz, símbolos o en un
lenguaje más simple.

Comprender la Pauta 1.1

1.1.1 Contenido no textual: Todo contenido no textual que se presenta
al usuario tiene una alternativa textual que cumple el mismo propósito,
excepto en las situaciones enumeradas a continuación. (Nivel A)

Cómo cumplir 1.1.1
Comprender 1.1.1

Controles, Entrada de datos: Si el contenido no textual es un
control o acepta datos introducidos por el usuario, entonces tiene
un nombre que describe su propósito. (Véase la Pauta 4.1 para
requisitos adicionales sobre los controles y el contenido que
aceptan entrada de datos).
Contenido multimedia tempodependiente: Si el contenido no
textual es una presentación multimedia con desarrollo temporal,
entonces las alternativas textuales proporcionan al menos una
identificación descriptiva del contenido no textual. (Véase la Pauta
1.2 para requisitos adicionales sobre contenido multimedia).
Pruebas: Si el contenido no textual es una prueba o un ejercicio
que no sería válido si se presentara en forma de texto, entonces
las alternativas textuales proporcionan al menos una identificación
descriptiva del contenido no textual.
Sensorial: Si el contenido no textual tiene como objetivo principal
el crear una experiencia sensorial específica, entonces las
alternativas textuales proporcionan al menos una identificación
descriptiva del contenido no textual.
CAPTCHA: Si el propósito del contenido no textual es confirmar
que quien está accediendo al contenido es una persona y no una
computadora, entonces se proporcionan alternativas textuales que
identifican y describen el propósito del contenido no textual y se
proporcionan formas alternativas de CAPTCHA con modos de
salida para distintos tipos de percepciones sensoriales, con el fin
de acomodarse a las diferentes discapacidades.
Decoración, Formato, Invisible: Si el contenido no textual es
simple decoración, se utiliza únicamente para definir el formato
visual o no se presenta a los usuarios, entonces se implementa de
forma que pueda ser ignorado por las ayudas técnicas.

Pauta 1.2 Medios tempodependientes:
Proporcionar alternativas para los medios
tempodependientes.

Comprender la Pauta 1.2

1.2.1 Sólo audio y sólo vídeo (grabado): Para contenido sólo audio
grabado y contenido sólo vídeo grabado, se cumple lo siguiente, excepto
cuando el audio o el vídeo es un contenido multimedia alternativo al
texto y está claramente identificado como tal: (Nivel A)

Sólo audio grabado: Se proporciona una alternativa para los

Cómo cumplir 1.2.1
Comprender 1.2.1

http://www.sidar.org/traducciones/wcag20/es/

7/37

15/10/2015

Pautas de Accesibilidad para el Contenido Web (WCAG) 2.0

medios tempodependientes que presenta información equivalente
para el contenido sólo audio grabado.
Sólo vídeo grabado: Se proporciona una alternativa para los
medios tempodependientes o se proporciona una pista sonora que
presenta información equivalente al contenido del medio de sólo
vídeo grabado.

1.2.2 Subtítulos (grabados): Se proporcionan subtítulos para el
contenido de audio grabado dentro de contenido multimedia
sincronizado, excepto cuando la presentación es un contenido
multimedia alternativo al texto y está claramente identificado como tal.
(Nivel A)

1.2.3 Audiodescripción o Medio Alternativo (grabado): Se
proporciona una alternativa para los medios tempodependientes o una
audiodescripción para el contenido de vídeo grabado en los multimedia
sincronizados, excepto cuando ese contenido es un contenido
multimedia alternativo al texto y está claramente identificado como tal.
(Nivel A)

Cómo cumplir 1.2.2
Comprender 1.2.2

Cómo cumplir 1.2.3
Comprender 1.2.3

1.2.4 Subtítulos (en directo): Se proporcionan subtítulos para todo el
contenido de audio en directo de los multimedia sincronizados. (Nivel
AA)

Cómo cumplir 1.2.4
Comprender 1.2.4

1.2.5 Audiodescripción (grabado): Se proporciona una
audiodescripción para todo el contenido de vídeo grabado dentro de
contenido multimedia sincronizado. (Nivel AA)

Cómo cumplir 1.2.5
Comprender 1.2.5

1.2.6 Lengua de señas (grabado): Se proporciona una interpretación
en lengua de señas para todo el contenido de audio grabado dentro de
contenido multimedia sincronizado. (Nivel AAA)

Cómo cumplir 1.2.6
Comprender 1.2.6

1.2.7 Audiodescripción ampliada (grabada): Cuando las pausas en el
audio de primer plano son insuficientes para permitir que la
audiodescripción comunique el significado del vídeo, se proporciona una
audiodescripción ampliada para todos los contenidos de vídeo grabado
dentro de contenido multimedia sincronizado. (Nivel AAA)

Cómo cumplir 1.2.7
Comprender 1.2.7

1.2.8 Medio alternativo (grabado): Se proporciona una alternativa para
los medios tempodependientes, tanto para todos los contenidos
multimedia sincronizados grabados como para todos los medios de sólo
vídeo grabado. (Nivel AAA)

Cómo cumplir 1.2.8
Comprender 1.2.8

1.2.9 Sólo audio (en directo): Se proporciona una alternativa para los
medios tempodependientes que presenta información equivalente para
el contenido de sólo audio en directo. (Nivel AAA)

Cómo cumplir 1.2.9
Comprender 1.2.9

Pauta 1.3 Adaptable: Crear contenido que pueda
presentarse de diferentes formas (por ejemplo, con

Comprender la Pauta 1.3

http://www.sidar.org/traducciones/wcag20/es/

8/37

15/10/2015

Pautas de Accesibilidad para el Contenido Web (WCAG) 2.0

una disposición más simple) sin perder información
o estructura.

1.3.1 Información y relaciones: La información, estructura y relaciones
comunicadas a través de la presentación pueden ser determinadas por
software o están disponibles como texto. (Nivel A)

Cómo cumplir 1.3.1
Comprender 1.3.1

1.3.2 Secuencia significativa: Cuando la secuencia en que se presenta
el contenido afecta a su significado, se puede determinar por software la
secuencia correcta de lectura. (Nivel A)

Cómo cumplir 1.3.2
Comprender 1.3.2

1.3.3 Características sensoriales: Las instrucciones proporcionadas
para entender y operar el contenido no dependen exclusivamente en las
características sensoriales de los componentes como su forma, tamaño,
ubicación visual, orientación o sonido. (Nivel A)

Nota: Para los requisitos relacionados con el color, véase la Pauta 1.4.

Cómo cumplir 1.3.3
Comprender 1.3.3

Pauta 1.4 Distinguible: Facilitar a los usuarios ver y
oír el contenido, incluyendo la separación entre el
primer plano y el fondo.

Comprender la Pauta 1.4

1.4.1 Uso del color: El color no se usa como único medio visual para
transmitir la información, indicar una acción, solicitar una respuesta o
distinguir un elemento visual. (Nivel A)

Cómo cumplir 1.4.1
Comprender 1.4.1

Nota: Este criterio de conformidad trata específicamente acerca de la
percepción del color. En la Pauta 1.3 se recogen otras formas de
percepción, incluyendo el acceso por software al color y a otros códigos
de presentación visual.

1.4.2 Control del audio: Si el audio de una página web suena
automáticamente durante más de 3 segundos, se proporciona ya sea un
mecanismo para pausar o detener el audio, o un mecanismo para
controlar el volumen del sonido que es independiente del nivel de
volumen global del sistema. (Nivel A)

Nota: En la medida en que cualquier contenido que no satisfaga este
criterio puede interferir con la capacidad del usuario de emplear la
página en su conjunto, todo contenido de la página web (tanto si
satisface o no otros criterios de conformidad) debe satisfacer este
criterio. Véase Requisito de Conformidad 5: Sin interferencia.

Cómo cumplir 1.4.2
Comprender 1.4.2

1.4.3 Contraste (mínimo): La presentación visual de texto e imágenes
de texto tiene una relación de contraste de, al menos, 4.5:1, excepto en
los siguientes casos: (Nivel AA)

Cómo cumplir 1.4.3
Comprender 1.4.3

Textos grandes: Los textos de gran tamaño y las imágenes de
texto de gran tamaño tienen una relación de contraste de, al
menos, 3:1.
Incidental: Los textos o imágenes de texto que forman parte de
un componente inactivo de la interfaz de usuario, que son simple

http://www.sidar.org/traducciones/wcag20/es/

9/37

15/10/2015

Pautas de Accesibilidad para el Contenido Web (WCAG) 2.0

decoración, que no resultan visibles para nadie o forman parte de
una imagen que contiene otros elementos visuales significativos,
no tienen requisitos de contraste.
Logotipos: El texto que forma parte de un logo o nombre de
marca no tiene requisitos de contraste mínimo.

1.4.4 Cambio de tamaño del texto: A excepción de los subtítulos y las
imágenes de texto, todo el texto puede ser ajustado sin ayudas técnicas
hasta un 200 por ciento sin que se pierdan el contenido o la
funcionalidad. (Nivel AA)

Cómo cumplir 1.4.4
Comprender 1.4.4

Cómo cumplir 1.4.5
Comprender 1.4.5

1.4.5 Imágenes de texto: Si con las tecnologías que se están utilizando
se puede conseguir la presentación visual deseada, se utiliza texto para
transmitir la información en vez de imágenes de texto, excepto en los
siguientes casos. (Nivel AA)

Configurable: La imagen de texto es visualmente configurable
según los requisitos del usuario.
Esencial: Una forma particular de presentación del texto resulta
esencial para la información que se transmite.

Nota: Los logotipos (textos que son parte de un logo o de un nombre de
marca) se consideran esenciales.

1.4.6 Contraste (mejorado): La presentación visual de texto e
imágenes de texto tiene una relación de contraste de, al menos, 7:1,
excepto en los siguientes casos. (Nivel AAA)

Cómo cumplir 1.4.6
Comprender 1.4.6

Textos grandes: Los textos de gran tamaño y las imágenes de
texto de gran tamaño tienen una relación de contraste de, al
menos, 4.5:1.
Incidental: Los textos o imágenes de texto que forman parte de
un componente de la interfaz de usuario inactivo, que son simple
decoración, que no resultan visibles para nadie o forman parte de
una imagen que contiene otros elementos visuales significativos,
no tienen requisitos de contraste.
Logotipos: El texto que forma parte de un logo o nombre de
marca no tiene requisitos de contraste mínimo.

1.4.7 Sonido de fondo bajo o ausente: Para el contenido de sólo audio
grabado que (1) contiene habla en primer plano, (2) no es un CAPTCHA
sonoro o un audiologo, y (3) que no es una vocalización cuya intención
principal es servir como expresión musical (como el canto o el rap), se
cumple al menos uno de los siguientes casos: (Nivel AAA)

Cómo cumplir 1.4.7
Comprender 1.4.7

Ningún sonido de fondo: El audio no contiene sonidos de fondo.
Apagar: Los sonidos de fondo pueden ser apagados.
20 dB: Los sonidos de fondo son, al menos, 20 decibelios más
bajos que el discurso en primer plano, con la excepción de
sonidos ocasionales que duran solamente uno o dos segundos.
Nota: Por la definición de "decibelio", el sonido de fondo que
cumple con este requisito es aproximadamente cuatro veces
más silencioso que la locución principal.

1.4.8 Presentación visual: En la presentación visual de bloques de
texto, se proporciona algún mecanismo para lograr lo siguiente: (Nivel

Cómo cumplir 1.4.8
Comprender 1.4.8

http://www.sidar.org/traducciones/wcag20/es/

10/37

15/10/2015

Pautas de Accesibilidad para el Contenido Web (WCAG) 2.0

AAA)

1.  Los colores de fondo y primer plano pueden ser elegidos por el

usuario.

2.  El ancho no es mayor de 80 caracteres o signos (40 si es CJK).
3.  El texto no está justificado (alineado a los márgenes izquierdo y

derecho a la vez).

4.  El espacio entre líneas (interlineado) es de, al menos, un espacio
y medio dentro de los párrafos y el espacio entre párrafos es, al
menos, 1.5 veces mayor que el espacio entre líneas.

5.  El texto se ajusta sin ayudas técnicas hasta un 200 por ciento de
modo tal que no requiere un desplazamiento horizontal para leer
una línea de texto en una ventana a pantalla completa.

1.4.9 Imágenes de texto (sin excepciones): Las imágenes de texto
sólo se utilizan como simple decoración o cuando una forma de
presentación particular del texto resulta esencial para la información
transmitida. (Nivel AAA)

Nota: Los logotipos (textos que son parte de un logo o de un nombre de
marca) se consideran esenciales.

Cómo cumplir 1.4.9
Comprender 1.4.9

Principio 2: Operable - Los componentes de la interfaz de usuario y la
navegación deben ser operables.

Pauta 2.1 Accesible por teclado: Proporcionar
acceso a toda la funcionalidad mediante el teclado.

Comprender la Pauta 2.1

2.1.1 Teclado: Toda la funcionalidad del contenido es operable a través
de una interfaz de teclado sin que se requiera una determinada
velocidad para cada pulsación individual de las teclas, excepto cuando
la función interna requiere de una entrada que depende del trayecto de
los movimientos del usuario y no sólo de los puntos inicial y final. (Nivel
A)

Nota 1: Esta excepción se refiere a la función subyacente, no a la
técnica de entrada de datos. Por ejemplo, si la entrada de texto se hace
por medio de escritura a mano, la técnica de entrada (escritura a mano)
depende del trazo (ruta trazada) pero la función interna (introducir
texto) no.

Nota 2: Esto no prohíbe ni debería desanimar a los autores a
proporcionar entrada de ratón u otros métodos de entrada de datos
adicionales a la operabilidad a través del teclado.

2.1.2 Sin trampas para el foco del teclado: Si es posible mover el foco
a un componente de la página usando una interfaz de teclado, entonces
el foco se puede quitar de ese componente usando sólo la interfaz de
teclado y, si se requiere algo más que las teclas de dirección o de
tabulación, se informa al usuario el método apropiado para mover el
foco. (Nivel A)

Nota: En la medida en que cualquier contenido que no satisfaga este
criterio puede interferir con la capacidad del usuario para emplear la

Cómo cumplir 2.1.1
Comprender 2.1.1

Cómo cumplir 2.1.2
Comprender 2.1.2

http://www.sidar.org/traducciones/wcag20/es/

11/37

15/10/2015

Pautas de Accesibilidad para el Contenido Web (WCAG) 2.0

página por completo, todo contenido de la página web (tanto si
satisface o no otros criterios de conformidad) debe satisfacer este
criterio. Véase Requisito de Conformidad 5: Sin interferencia.

2.1.3 Teclado (sin excepciones): Toda la funcionalidad del contenido
se puede operar a través de una interfaz de teclado sin requerir una
determinada velocidad en la pulsación de las teclas. (Nivel AAA)

Cómo cumplir 2.1.3
Comprender 2.1.3

Pauta 2.2 Tiempo suficiente: Proporcionar a los
usuarios el tiempo suficiente para leer y usar el
contenido.

Comprender la Pauta 2.2

Cómo cumplir 2.2.1
Comprender 2.2.1

2.2.1 Tiempo ajustable: Para cada límite de tiempo impuesto por el
contenido, se cumple al menos uno de los siguientes casos: (Nivel A)
Apagar: El usuario puede detener el límite de tiempo antes de
alcanzar el límite de tiempo; o
Ajustar: El usuario puede ajustar el límite de tiempo antes de
alcanzar dicho límite en un rango amplio que es, al menos, diez
veces mayor al tiempo fijado originalmente; o
Extender: Se advierte al usuario antes de que el tiempo expire y
se le conceden al menos 20 segundos para extender el límite
temporal con una acción simple (por ejemplo, "presione la barra de
espacio") y el usuario puede extender ese límite de tiempo al
menos diez veces; o
Excepción de tiempo real: El límite de tiempo es un requisito que
forma parte de un evento en tiempo real (por ejemplo, una
subasta) y no resulta posible ofrecer una alternativa al límite de
tiempo; o
Excepción por ser esencial: El límite de tiempo es esencial y, si
se extendiera, invalidaría la actividad; o
Excepción de 20 horas: El límite de tiempo es mayor a 20 horas.

Nota: Este criterio de conformidad ayuda a asegurarse de que los
usuarios puedan completar una tarea sin cambios inesperados en el
contenido o contexto que sean el resultado de un límite de tiempo. Este
criterio de conformidad debe considerarse en combinación con el
Criterio de Conformidad 3.2.1, que impone límites a los cambios de
contenido o contexto como resultado de una acción del usuario.

2.2.2 Poner en pausa, detener, ocultar: Para la información que tiene
movimiento, parpadeo, se desplaza o se actualiza automáticamente, se
cumplen todos los casos siguientes: (Nivel A)

Cómo cumplir 2.2.2
Comprender 2.2.2

Movimiento, parpadeo, desplazamiento: Para toda información
que se mueve, parpadea o se desplaza, que (1) comienza
automáticamente, (2) dura más de cinco segundos y (3) se
presenta en paralelo con otro contenido, existe un mecanismo
para que el usuario la pueda poner en pausa, detener u ocultar, a
menos que el movimiento, parpadeo o desplazamiento sea parte
esencial de una actividad; y
Actualización automática: Para toda información que se
actualiza automáticamente, que (1) se inicia automáticamente y (2)

http://www.sidar.org/traducciones/wcag20/es/

12/37

15/10/2015

Pautas de Accesibilidad para el Contenido Web (WCAG) 2.0

se presenta en paralelo con otro contenido, existe un mecanismo
para que el usuario la pueda poner en pausa, detener u ocultar, o
controlar la frecuencia de actualización a menos que la
actualización automática sea parte esencial de una actividad.

Nota 1: Para los requisitos relacionados con el parpadeo o el destello
de contenido, véase la Pauta 2.3.

Nota 2: En la medida en que cualquier contenido que no satisfaga este
criterio puede interferir con la capacidad del usuario para emplear la
página como un todo, todo contenido de la página web (tanto si
satisface o no otros criterios de conformidad) debe satisfacer este
criterio. Véase Requisito de Conformidad 5: Sin interferencia.

Nota 3: Para el contenido que es actualizado periódicamente por medio
de un software, o que se sirve a la aplicación de usuario por medio de
streaming, no hay obligación de preservar o presentar la información
que ha sido generada o recibida entre el inicio de la pausa y el reinicio
de la presentación; no sólo podría no ser técnicamente posible, sino
que además en muchas ocasiones podría ser erróneo o engañoso
hacerlo.

Nota 4: Una animación que ocurre como parte de una fase de precarga
de un contenido o una situación similar puede ser considerada esencial
si no se permite interacción a ningún usuario durante esa fase, y si el
hecho de no indicar el progreso pudiera confundir a los usuarios y
hacerles creer que ha habido un fallo en el contenido.

2.2.3 Sin tiempo: El tiempo no es parte esencial del evento o actividad
presentada por el contenido, exceptuando los multimedia sincronizados
no interactivos y los eventos en tiempo real. (Nivel AAA)

Cómo cumplir 2.2.3
Comprender 2.2.3

2.2.4 Interrupciones: El usuario puede postergar o suprimir las
interrupciones, excepto cuando las interrupciones implican una
emergencia. (Nivel AAA)

Cómo cumplir 2.2.4
Comprender 2.2.4

2.2.5 Re-autentificación: Cuando expira una sesión autentificada, el
usuario puede continuar la actividad sin pérdida de datos tras volver a
identificarse. (Nivel AAA)

Cómo cumplir 2.2.5
Comprender 2.2.5

Pauta 2.3 Convulsiones: No diseñar contenido de
un modo que se sepa podría provocar ataques,
espasmos o convulsiones.

Comprender la Pauta 2.3

2.3.1 Umbral de tres destellos o menos: Las páginas web no
contienen nada que destelle más de tres veces en un segundo, o el
destello está por debajo del umbral de destello general y de destello
rojo. (Nivel A)

Nota: En la medida en que cualquier contenido que no satisfaga este
criterio puede interferir con la capacidad del usuario para emplear la
página como un todo, todo contenido de la página web (tanto si
satisface o no otros criterios de conformidad) debe satisfacer este
criterio. Véase Requisito de Conformidad 5: Sin interferencia.

Cómo cumplir 2.3.1
Comprender 2.3.1

http://www.sidar.org/traducciones/wcag20/es/

13/37

15/10/2015

Pautas de Accesibilidad para el Contenido Web (WCAG) 2.0

2.3.2 Tres destellos: Las páginas web no contienen nada que destelle
más de tres veces por segundo. (Nivel AAA)

Cómo cumplir 2.3.2
Comprender 2.3.2

Pauta 2.4 Navegable: Proporcionar medios para
ayudar a los usuarios a navegar, encontrar
contenido y determinar dónde se encuentran.

Comprender la Pauta 2.4

2.4.1 Evitar bloques: Existe un mecanismo para evitar los bloques de
contenido que se repiten en múltiples páginas web. (Nivel A)

Cómo cumplir 2.4.1
Comprender 2.4.1

2.4.2 Titulado de páginas: Las páginas web tienen títulos que
describen su temática o propósito. (Nivel A)

2.4.3 Orden del foco: Si se puede navegar secuencialmente por una
página web y la secuencia de navegación afecta su significado o su
operación, los componentes que pueden recibir el foco lo hacen en un
orden que preserva su significado y operabilidad. (Nivel A)

2.4.4 Propósito de los enlaces (en contexto): El propósito de cada
enlace puede ser determinado con sólo el texto del enlace o a través del
texto del enlace sumado al contexto del enlace determinado por
software, excepto cuando el propósito del enlace resultara ambiguo para
los usuarios en general. (Nivel A)

Cómo cumplir 2.4.2
Comprender 2.4.2

Cómo cumplir 2.4.3
Comprender 2.4.3

Cómo cumplir 2.4.4
Comprender 2.4.4

2.4.5 Múltiples vías: Se proporciona más de un camino para localizar
una página web dentro de un conjunto de páginas web, excepto cuando
la página es el resultado, o un paso intermedio, de un proceso. (Nivel
AA)

Cómo cumplir 2.4.5
Comprender 2.4.5

2.4.6 Encabezados y etiquetas: Los encabezados y etiquetas
describen el tema o propósito. (Nivel AA)

2.4.7 Foco visible: Cualquier interfaz de usuario operable por teclado
tiene una forma de operar en la cuál el indicador del foco del teclado
resulta visible. (Nivel AA)

Cómo cumplir 2.4.6
Comprender 2.4.6

Cómo cumplir 2.4.7
Comprender 2.4.7

2.4.8 Ubicación: Se proporciona información acerca de la ubicación del
usuario dentro de un conjunto de páginas web. (Nivel AAA)

Cómo cumplir 2.4.8
Comprender 2.4.8

2.4.9 Propósito de los enlaces (sólo enlaces): Se proporciona un
mecanismo que permite identificar el propósito de cada enlace con sólo
el texto del enlace, excepto cuando el propósito del enlace resultara
ambiguo para los usuarios en general. (Nivel AAA)

Cómo cumplir 2.4.9
Comprender 2.4.9

2.4.10 Encabezados de sección: Se usan encabezados de sección
para organizar el contenido. (Nivel AAA)

Cómo cumplir 2.4.10
Comprender 2.4.10

http://www.sidar.org/traducciones/wcag20/es/

14/37

15/10/2015

Pautas de Accesibilidad para el Contenido Web (WCAG) 2.0

Nota 1: "Encabezados" se usa en sentido general e incluye los títulos y
otras formas de agregar encabezados a las distintos tipos de
contenido.

Nota 2: Este criterio de conformidad se refiere al contenido
propiamente dicho, no a los componentes de la interfaz de usuario. Los
componentes de la interfaz de usuario se tratan en el Criterio de
Conformidad 4.1.2.

Principio 3: Comprensible - La información y el manejo de la interfaz de
usuario deben ser comprensibles.

Pauta 3.1 Legible: Hacer que los contenidos
textuales resulten legibles y comprensibles.

Comprender la Pauta 3.1

3.1.1 Idioma de la página: El idioma predeterminado de cada página
web puede ser determinado por software. (Nivel A)

Cómo cumplir 3.1.1
Comprender 3.1.1

3.1.2 Idioma de las partes: El idioma de cada pasaje o frase en el
contenido puede ser determinado por software, excepto los nombres
propios, términos técnicos, palabras en un idioma indeterminado y
palabras o frases que se hayan convertido en parte natural del texto que
las rodea. (Nivel AA)

Cómo cumplir 3.1.2
Comprender 3.1.2

3.1.3 Palabras inusuales: Se proporciona un mecanismo para
identificar las definiciones específicas de palabras o frases usadas de
modo inusual o restringido, incluyendo expresiones idiomáticas y jerga.
(Nivel AAA)

Cómo cumplir 3.1.3
Comprender 3.1.3

3.1.4 Abreviaturas: Se proporciona un mecanismo para identificar la
forma expandida o el significado de las abreviaturas. (Nivel AAA)

Cómo cumplir 3.1.4
Comprender 3.1.4

3.1.5 Nivel de lectura: Cuando un texto requiere un nivel de lectura más
avanzado que el nivel mínimo de educación secundaria una vez que se
han eliminado nombres propios y títulos, se proporciona un contenido
suplementario o una versión que no requiere un nivel de lectura mayor a
ese nivel educativo. (Nivel AAA)

Cómo cumplir 3.1.5
Comprender 3.1.5

3.1.6 Pronunciación: Se proporciona un mecanismo para identificar la
pronunciación específica de las palabras cuando el significado de esas
palabras, dentro del contexto, resulta ambiguo si no se conoce su
pronunciación. (Nivel AAA)

Cómo cumplir 3.1.6
Comprender 3.1.6

Pauta 3.2 Predecible: Hacer que las páginas web
aparezcan y operen de manera predecible.

Comprender la Pauta 3.2

http://www.sidar.org/traducciones/wcag20/es/

15/37

15/10/2015

Pautas de Accesibilidad para el Contenido Web (WCAG) 2.0

3.2.1 Al recibir el foco: Cuando cualquier componente recibe el foco,
no inicia ningún cambio en el contexto. (Nivel A)

Cómo cumplir 3.2.1
Comprender 3.2.1

3.2.2 Al recibir entradas: El cambio de estado en cualquier
componente de la interfaz de usuario no provoca automáticamente un
cambio en el contexto a menos que el usuario haya sido advertido de
ese comportamiento antes de usar el componente. (Nivel A)

Cómo cumplir 3.2.2
Comprender 3.2.2

3.2.3 Navegación coherente: Los mecanismos de navegación que se
repiten en múltiples páginas web dentro de un conjunto de páginas web
aparecen siempre en el mismo orden relativo cada vez que se repiten, a
menos que el cambio sea provocado por el propio usuario. (Nivel AA)

Cómo cumplir 3.2.3
Comprender 3.2.3

3.2.4 Identificación coherente: Los componentes que tienen la misma
funcionalidad dentro de un conjunto de páginas web son identificados de
manera coherente. (Nivel AA)

Cómo cumplir 3.2.4
Comprender 3.2.4

3.2.5 Cambios a petición: Los cambios en el contexto son iniciados
únicamente a solicitud del usuario o se proporciona un mecanismo para
detener tales cambios. (Nivel AAA)

Cómo cumplir 3.2.5
Comprender 3.2.5

Pauta 3.3 Entrada de datos asistida: Ayudar a los
usuarios a evitar y corregir los errores.

Comprender la Pauta 3.3

3.3.1 Identificación de errores: Si se detecta automáticamente un error
en la entrada de datos, el elemento erróneo es identificado y el error se
describe al usuario mediante un texto. (Nivel A)

Cómo cumplir 3.3.1
Comprender 3.3.1

3.3.2 Etiquetas o instrucciones: Se proporcionan etiquetas o
instrucciones cuando el contenido requiere la introducción de datos por
parte del usuario. (Nivel A)

Cómo cumplir 3.3.2
Comprender 3.3.2

3.3.3 Sugerencias ante errores: Si se detecta automáticamente un
error en la entrada de datos y se dispone de sugerencias para hacer la
corrección, entonces se presentan las sugerencias al usuario, a menos
que esto ponga en riesgo la seguridad o el propósito del contenido.
(Nivel AA)

3.3.4 Prevención de errores (legales, financieros, datos): Para las
páginas web que representan para el usuario compromisos legales o
transacciones financieras; que modifican o eliminan datos controlables
por el usuario en sistemas de almacenamiento de datos; o que envían
las respuestas del usuario a una prueba, se cumple al menos uno de los
siguientes casos. (Nivel AA)

1.  Reversible: El envío es reversible.
2.  Revisado: Se verifica la información para detectar errores en la
entrada de datos y se proporciona al usuario una oportunidad de

Cómo cumplir 3.3.3
Comprender 3.3.3

Cómo cumplir 3.3.4
Comprender 3.3.4

http://www.sidar.org/traducciones/wcag20/es/

16/37

15/10/2015

Pautas de Accesibilidad para el Contenido Web (WCAG) 2.0

corregirlos.

3.  Confirmado: Se proporciona un mecanismo para revisar,

confirmar y corregir la información antes de finalizar el envío de los
datos.

3.3.5 Ayuda: Se proporciona ayuda dependiente del contexto . (Nivel
AAA)

Cómo cumplir 3.3.5
Comprender 3.3.5

3.3.6 Prevención de errores (todos): Para las páginas web que
requieren al usuario el envío de información, se cumple al menos uno de
los siguientes casos. (Nivel AAA)

Cómo cumplir 3.3.6
Comprender 3.3.6

1.  Reversible: El envío es reversible.
2.  Revisado: Se verifica la información para detectar errores en la
entrada de datos y se proporciona al usuario una oportunidad de
corregirlos.

3.  Confirmado: Se proporciona un mecanismo para revisar,

confirmar y corregir la información antes de finalizar el envío de los
datos.

Principio 4: Robusto - El contenido debe ser suficientemente robusto
como para ser interpretado de forma fiable por una amplia variedad de
aplicaciones de usuario, incluyendo las ayudas técnicas.

Pauta 4.1 Compatible: Maximizar la compatibilidad
con las aplicaciones de usuario actuales y futuras,
incluyendo las ayudas técnicas.

Comprender la Pauta 4.1

4.1.1 Procesamiento: En los contenidos implementados mediante el
uso de lenguajes de marcas, los elementos tienen las etiquetas de
apertura y cierre completas; los elementos están anidados de acuerdo a
sus especificaciones; los elementos no contienen atributos duplicados y
los ID son únicos, excepto cuando las especificaciones permitan estas
características. (Nivel A)

Nota: Las etiquetas de apertura y cierre a las que les falte un carácter
crítico para su formación, como un signo de "mayor qué", o en las que
falten las comillas de apertura o cierre en el valor de un atributo, no se
consideran completas.

4.1.2 Nombre, función, valor: Para todos los componentes de la
interfaz de usuario (incluyendo pero no limitado a: elementos de
formulario, enlaces y componentes generados por scripts), el nombre y
la función pueden ser determinados por software; los estados,
propiedades y valores que pueden ser asignados por el usuario pueden
ser especificados por software; y los cambios en estos elementos se
encuentran disponibles para su consulta por las aplicaciones de usuario,
incluyendo las ayudas técnicas. (Nivel A)

Nota: Este criterio de conformidad se dirige principalmente a los
autores web que desarrollan o programan sus propios componentes de

Cómo cumplir 4.1.1
Comprender 4.1.1

Cómo cumplir 4.1.2
Comprender 4.1.2

http://www.sidar.org/traducciones/wcag20/es/

17/37

15/10/2015

Pautas de Accesibilidad para el Contenido Web (WCAG) 2.0

interfaz de usuario. Por ejemplo, los controles estándar de HTML
satisfacen automáticamente este criterio cuando se emplean de
acuerdo con su especificación.

Conformidad

Esta sección es normativa.

En esta sección se presentan los requisitos de conformidad con las WCAG 2.0. También se
proporciona información acerca de cómo realizar declaraciones de conformidad, las cuales son
opcionales. Finalmente, se describe el significado de compatible con la accesibilidad, ya que sólo se
puede depender de las tecnologías que se usan de un modo compatible con la accesibilidad para
satisfacer la conformidad. En Comprender la Conformidad se incluye más información acerca del
concepto de compatible con la accesibilidad.

Requisitos de conformidad

Para que una página web sea conforme con las WCAG 2.0, deben satisfacerse todos los requisitos de
conformidad siguientes:

1. Nivel de conformidad: Uno de los siguientes niveles de conformidad se satisface por completo.

Nivel A: Para lograr conformidad con el Nivel A (el mínimo), la página web satisface todos los
Criterios de Conformidad del Nivel A, o proporciona una versión alternativa conforme.

Nivel AA: Para lograr conformidad con el Nivel AA, la página web satisface todos los Criterios
de Conformidad de los Niveles A y AA, o se proporciona una versión alternativa conforme al
Nivel AA.

Nivel AAA: Para lograr conformidad con el Nivel AAA, la página web satisface todos los
Criterios de Conformidad de los Niveles A, AA y AAA, o proporciona una versión alternativa
conforme al Nivel AAA.

Nota 1: Aunque la conformidad sólo puede alcanzarse en los niveles mencionados, se alienta a los
autores a notificar en sus declaraciones cualquier avance que hayan realizado para satisfacer los
criterios de conformidad de un nivel de conformidad mayor al que hayan alcanzado.

Nota 2: No se recomienda que el Nivel de Conformidad AAA sea requerido como política general
para la totalidad de un sitio web, ya que en algunos contenidos no es posible satisfacer todos los
Criterios de Conformidad de Nivel AAA.

2. Páginas completas: La conformidad (y el nivel de conformidad) se aplica a páginas web
completas, y no se puede alcanzar si se excluye una parte de la página.

Nota 1: Con el fin de determinar el nivel de conformidad, se considera que las alternativas a parte del
contenido de una página son parte de esa página si se puede acceder a ellas directamente desde la
página, por ejemplo, en el caso de una descripción extensa o la presentación alternativa de un vídeo.

Nota 2: Los autores de las páginas web que no cumplen con los requisitos debido a que parte del
contenido está fuera de su control, pueden considerar la opción de una Declaración de Conformidad
Parcial.

3. Procesos completos: Cuando una página web es parte de una serie de páginas web que
presentan un proceso (es decir, una secuencia de pasos que es necesario completar para realizar una
actividad), todas las páginas en ese proceso deben ser conformes con el nivel especificado o uno
superior. (No es posible lograr conformidad con un nivel en particular si una de las páginas del
proceso no cumple con ese nivel o uno superior).

Ejemplo: Una tienda en línea tiene una serie de páginas en las que se pueden seleccionar y comprar
productos. Todas y cada una de las páginas de la serie de páginas de principio a fin (el pago) deben
cumplir con los requisitos de conformidad para que se considere que cada una de ellas es también

http://www.sidar.org/traducciones/wcag20/es/

18/37

15/10/2015

Pautas de Accesibilidad para el Contenido Web (WCAG) 2.0

conforme.

4. Uso de tecnologías exclusivamente según métodos que sean compatibles con la
accesibilidad: Para satisfacer los criterios de conformidad sólo se depende de aquellos usos de las
tecnologías que sean compatibles con la accesibilidad. Toda información o funcionalidad que se
proporcione de una forma que no sea compatible con la accesibilidad debe estar disponible de una
forma que sí sea compatible con la accesibilidad. (Véase Comprender Compatible con la
Accesibilidad.)

5. Sin interferencia: Si las tecnologías se usan de una forma que no es compatible con la
accesibilidad, o está usada de una forma que no cumple los requisitos de conformidad, no debe
impedir a los usuarios acceder al contenido del resto de la página. Además, es necesario que la
página web como un todo siga cumpliendo con los requisitos de conformidad en las siguientes
circunstancias:

1.  cuando cualquier tecnología de la que no se depende está activada en una aplicación de

usuario,

2.  cuando cualquier tecnología de la que no se depende está desactivada en una aplicación de

usuario, y

3.  cuando cualquier tecnología de la que no se depende no es soportada por una aplicación de

usuario

Además, los siguientes criterios de conformidad se aplican a todo el contenido de la página,
incluyendo el contenido del que, de todos modos, no se depende para alcanzar la conformidad, ya que
su incumplimiento puede interferir con el uso de la página:

1.4.2 - Control del audio,

2.1.2 - Sin trampas para el foco del teclado,

2.3.1 - Umbral de tres destellos o menos, y

2.2.2 - Poner en pausa, detener, ocultar.

Nota: Si una página no puede cumplir con los requisitos (por ejemplo, una página de prueba de
conformidad o una página de ejemplo), no puede ser incluida en el ámbito de la conformidad ni en la
declaración de conformidad.

Para más información, ejemplos incluidos, véase Comprender los Requisitos de Conformidad.

Declaraciones de conformidad (opcional)

La conformidad se aplica sólo a las páginas web. Sin embargo, la declaración de conformidad puede
cubrir una sola página, una serie de páginas o múltiples páginas web relacionadas.

Componentes exigidos en la declaración de conformidad

Las declaraciones de conformidad no son obligatorias. Los autores pueden cumplir con los
requisitos de las WCAG 2.0 sin realizar la declaración. Sin embargo, si se realiza la declaración, ésta
debe contener la siguiente información:

1.  Fecha de la declaración

2.  Título de las pautas, versión y URI "Web Content Accessibility Guidelines 2.0 en

http://www.w3.org/TR/2008/REC-WCAG20-20081211/"

3.  Nivel de conformidad satisfecho: (Nivel A, AA o AAA)

4.  Una breve descripción de las páginas web, como por ejemplo una lista de sus URI para las
que se hace la declaración, incluyendo si los subdominios están incluidos en la declaración.

Nota 1: Las páginas web pueden ser descritas por medio de una lista o de una expresión que
describa todas las URI incluidas en la declaración.

Nota 2: El autor puede declarar que, para los productos basados en web que no tienen un URI
antes de su instalación en el sitio web del cliente, el producto será conforme cuando se
instale.

http://www.sidar.org/traducciones/wcag20/es/

19/37

15/10/2015

Pautas de Accesibilidad para el Contenido Web (WCAG) 2.0

5.  Una lista de las tecnologías de contenido web de las que se depende.

Nota: Si se emplea un logo de conformidad, éste constituye una declaración y debe estar
acompañado de todos los componentes requeridos para una declaración de conformidad declarados
anteriormente.

Componentes opcionales de la declaración de conformidad

Además de los componentes exigidos arriba para una declaración de conformidad, considere incluir
información adicional para ayudar a los usuarios. La información adicional recomendada incluye:

Una lista de los criterios de conformidad satisfechos más allá del nivel de conformidad
declarado. Esta información debería proporcionarse de forma tal que el usuario pueda
emplearla, preferiblemente en forma de metadatos legibles por máquinas.

Una lista de las tecnologías específicas que "se emplean pero de las que no se depende."

Una lista de las aplicaciones de usuario, incluyendo las ayudas técnicas que se han empleado
para probar los contenidos.

Información sobre cualquier paso adicional que se haya dado para mejorar la accesibilidad más
allá de los criterios de conformidad.

Una versión de metadatos legible por máquinas de la lista de tecnologías específicas de las
que se depende.

Una versión de metadatos legibles por máquinas de la declaración de conformidad.

Nota 1: Véase Comprender las Declaraciones de Conformidad para más información y ejemplos de
declaraciones de conformidad.

Nota 2: Véase Comprender los Metadatos para más información sobre el uso de metadatos en las
declaraciones de conformidad.

Enunciado de conformidad parcial - Contenido de terceras partes

En ocasiones se crean páginas web que recibirán luego contenido adicional. Es el caso, por ejemplo,
de un programa de correo electrónico, un blog, un artículo que permita a los usuarios agregar
comentarios o las aplicaciones que permiten a los usuarios aportar contenido. Otro ejemplo sería una
página, como un portal o un sitio de noticias, que esté compuesto por contenido generado por
múltiples usuarios, o los sitios que, a lo largo del tiempo, insertan contenido automáticamente desde
otras fuentes, como cuando se inserta publicidad dinámicamente.

En estos casos, no es posible saber en el momento de la creación de la página cómo será este
contenido sobre el cual el autor no tiene control. Es importante destacar que el contenido sobre el cual
no se tiene control también puede afectar a la accesibilidad del contenido controlado. Ante esta
situación hay dos opciones posibles:

1.  Se puede redactar una resolución de conformidad basada en un conocimiento óptimo. Si una

página es constantemente revisada y reparada (el contenido no conforme se elimina o se hace
conforme) en el periodo de dos días laborales, puede hacerse una resolución o declaración de
conformidad, ya que a excepción de los errores en el contenido aportado externamente, que
son corregidos o eliminados cuando son detectados, la página cumple con los requisitos de
conformidad. No se puede hacer una declaración de conformidad si no es posible controlar o
corregir el contenido no conforme.
O

2.  Se puede redactar un "enunciado de conformidad parcial" que indique que la página no es

conforme, pero que lo sería si ciertas partes fueran eliminadas. La forma de este enunciado
podría ser "Esta página no cumple con los requisitos de conformidad de las WCAG 2.0, pero
sería conforme al nivel X si las siguientes partes provenientes de fuentes no controladas fueran
eliminadas". Además, las siguientes condiciones deberían ser verdaderas para el contenido no
controlado descrito en el enunciado de conformidad parcial:
a.  No es un contenido que esté bajo el control del autor.

http://www.sidar.org/traducciones/wcag20/es/

20/37

15/10/2015

Pautas de Accesibilidad para el Contenido Web (WCAG) 2.0

b.  El contenido se describe de manera tal que los usuarios puedan identificarlo (por

ejemplo, no puede ser descrito como "todas las partes sobre las cuales no tenemos
control", a menos que estén claramente etiquetadas como tales).

Enunciado de conformidad parcial - Lenguaje

Se puede hacer un "enunciado de conformidad parcial debido al lenguaje" en caso de que la página
no sea conforme pero que podría serlo de existir compatibilidad con la accesibilidad para el lenguaje
(o todos los lenguajes) empleado en la página. La forma de este enunciado podría ser: "Esta página
no es conforme, pero podría ser conforme con el nivel X si existiera soporte accesible para el/los
siguiente/s lenguaje/s:"

Apéndice A: Glosario

Esta sección es normativa.

abreviaturas

Forma reducida de una palabra, frase o nombre cuando la abreviatura no se ha convertido en
parte del idioma.

Nota 1: esto incluye siglas y acrónimos:

1.  Siglas: son formas cortas de un nombre o frase hechas a partir de las iniciales o sílabas

contenidas en el nombre o la frase.

Nota 1: No se definen en todos los idiomas.

Ejemplo1: SNCF es la sigla en francés que contiene las iniciales de Société Nationale
des Chemins de Fer, la red de ferrocarriles nacional de Francia.

Ejemplo 2: PES es la sigla de percepción extrasensorial

2.  Acrónimos: son formas cortas hechas a partir de las iniciales o partes de las palabras
(de un nombre o una frase) que se pueden pronunciar como una palabra distinta.

Ejemplo: NOAA es un acrónimo formado a partir de las iniciales de National Oceanic
and Atmospheric Administration de los Estados Unidos

Nota 2: algunas empresas adoptan lo que solía ser la abreviatura de su nombre. En estos
casos, el nuevo nombre de la empresa son las letras (por ejemplo, Ecma) y la palabra no se
considera más una abreviatura.

alternativa para los medios tempodependientes

Documento que incluye una secuencia correcta de descripciones textuales de la información
visual y auditiva tempodependiente, y que proporciona los medios para lograr los resultados de
cualquier interacción basada en el tiempo.

Nota: El guión empleado para crear el contenido multimedia sincronizado podría satisfacer esta
definición sólo si ha sido corregido para representar con precisión el contenido multimedia
sincronizado resultante tras la edición.

alternativa textual

Texto determinado por software que se usa en lugar de un contenido no textual o el texto que se
usa conjunto a un contenido no textual y es referenciado por el texto determinado por software.
El texto “asociado por software” es texto cuya localización puede ser determinada a partir de un
contenido no textual.

Ejemplo: La imagen de un gráfico estadístico se describe en un texto ubicado en un párrafo a
continuación del gráfico. La alternativa textual corta indica que la descripción completa se
encuentra a continuación.

Nota: Véase Comprender las Alternativas Textuales para más información.

ambiguo para los usuarios en general

http://www.sidar.org/traducciones/wcag20/es/

21/37

15/10/2015

Pautas de Accesibilidad para el Contenido Web (WCAG) 2.0

El propósito del enlace no puede ser determinado a partir del propio texto del enlace y la
información que se presenta simultáneamente al usuario desde la página web (por ejemplo, los
usuarios sin discapacidad que lo leen podrían no saber qué hará el enlace hasta haberlo
activado)

Ejemplo: La palabra guayaba en la frase "Una de las exportaciones notables es la guayaba" es
un enlace. El enlace podría dirigir a una definición de "guayaba", una gráfica de la cantidad de
guayaba exportada o a una fotografía de gente recolectando guayabas. Hasta que no se activa
el enlace, todo lector está inseguro y, en ese caso, la persona con una discapacidad no está en
desventaja alguna.

aplicaciones de usuario

Cualquier software que recupera y presenta el contenido web a los usuarios.

Ejemplos: Navegadores web, reproductores multimedia, plug-ins y otros programas -incluyendo
las ayudas técnicas- que ayudan en la recuperación, procesamiento e interacción con el
contenido de la web.

arte ASCII

Una figura creada por la ubicación espacial de caracteres o glifos (típicamente de los 95
caracteres imprimibles definidos en ASCII).

audio

La técnica de reproducción de sonidos.

Nota: El audio puede ser creado sintéticamente (incluyendo sintetizadores de habla), grabando
los sonidos del mundo real, o de ambas maneras.

audiodescripción

La narración agregada a la pista de sonido para describir los detalles visuales importantes que
no se pueden entender sólo con la banda de sonido principal.

Nota 1: La audiodescripción del vídeo proporciona información sobre las acciones, personajes,
cambios de escena, textos que aparecen en pantalla y otros contenidos visuales.

Nota 2: En las audiodescripciones estándares, la narración se añade durante las pausas
existentes en el diálogo. (Véase también audiodescripción ampliada.)

Nota 3: Cuando toda la información sobre el vídeo ya se proporciona en el audio de la
presentación, no es necesaria ninguna audiodescripción adicional.

Nota 4: En inglés también se la denomina "video description" (descripción de vídeo) o
"descriptive narration" (narración descriptiva).

audiodescripción ampliada

Audiodescripción que se agrega a una presentación audiovisual poniendo en pausa el vídeo, de
manera que haya tiempo suficiente para agregar una descripción adicional.

Nota: Esta técnica se emplea sólo cuando el sentido del vídeo se perdería sin el añadido de
una audiodescripción y las pausas entre el diálogo o la narración son demasiado cortas.

ayuda dependiente del contexto

El texto de ayuda que proporciona información relacionada con la función que actualmente se
lleva a cabo.

Nota: Una rotulación clara puede servir como ayuda dependiente del contexto.

ayudas técnicas (como se usa en este documento)

Hardware y/o software que actúa como una aplicación de usuario, o en combinación con una
aplicación de usuario principal, para proporcionar la funcionalidad necesaria para cubrir las
necesidades de los usuarios con discapacidad que van más allá de las que proporcionan las
aplicaciones de usuario principales.

Nota 1: La funcionalidad proporcionada por las ayudas técnicas incluye presentaciones
alternativas (por ejemplo, voz sintetizada o contenido ampliado), métodos de entrada de datos
alternativos (por ejemplo, voz), navegación adicional o mecanismos de orientación, y

http://www.sidar.org/traducciones/wcag20/es/

22/37

15/10/2015

Pautas de Accesibilidad para el Contenido Web (WCAG) 2.0

transformaciones de contenido (por ejemplo, hacer las tablas más accesibles).

Nota 2: La ayudas técnicas a menudo comunican datos y mensajes a las aplicaciones de
usuario de uso generalizado empleando y monitorizando una API.

Nota 3: La distinción entre aplicaciones de usuario comunes y ayudas técnicas no es absoluta.
Muchas aplicaciones de usuario de uso generalizado proporcionan algunas características para
asistir a individuos con discapacidad. La diferencia básica es que las aplicaciones de usuario
comunes apuntan a una audiencia más amplia y diversa, que normalmente incluye a personas
con discapacidad o sin ellas. Las ayudas técnicas se dirigen a un rango más reducido de
usuarios con discapacidades específicas. La asistencia proporcionada por una ayuda técnica
es más específica y apropiada para satisfacer las necesidades de sus usuarios objetivo. Las
aplicaciones de usuarios comunes pueden proporcionar una funcionalidad importante para las
ayudas técnicas como extraer contenido web de objetos programados o procesar las marcas
para agruparlas en grupos identificables.

Ejemplo: Entre las ayudas técnicas que son importantes en el contexto de este documento se
incluyen las siguientes:

magnificadores de pantalla, y otros asistentes para la lectura visual, que son usados por
personas con limitaciones para la lectura visual, de percepción y física para cambiar la
fuente de texto, tamaño, el espacio, el color, la sincronización con el habla, etc, a fin de
mejorar la legibilidad visual del texto y las imágenes;

lectores de pantalla, que son utilizados por personas ciegas para leer la información
textual a través de un sintetizador de voz o en sistema braille;

sintetizadores de voz, que son utilizados por algunas personas con dificultades
cognitivas, de lenguaje o de aprendizaje para convertir el texto en una voz artificial;

programas de reconocimiento de voz, que pueden ser utilizados por personas con
algunas discapacidades físicas;

teclados alternativos, que son utilizados por personas con ciertas discapacidades físicas
para simular el teclado (incluyendo los teclados especiales que se usan a través de
punteros de cabeza, pulsadores de un solo botón, soplido y aspirado, y otros
dispositivos especiales de entrada),

dispositivos apuntadores alternativos, utilizados por personas con ciertas
discapacidades físicas para simular el apuntamiento mediante el ratón y las activaciones
mediante botones.

bloques de texto

Más de una oración de texto.

cambios en el contexto

Los cambios importantes en el contenido de una página web que, cuando se hacen sin el
conocimiento del usuario, pueden desorientar a quienes no pueden ver toda la página al mismo
tiempo.
Los cambios en el contexto incluyen los cambios de:

1.  aplicación de usuario;

2.  vista;

3.  foco;

4.  contenido que cambia el significado de la página web.

Nota: Un cambio en el contenido no siempre es un cambio de contexto. Los cambios en el
contenido tales como un esquema desplegable, un menú dinámico o un control de pestañas,
no cambian necesariamente el contexto, a menos que produzcan también algún otro cambio de
entre los anteriores (por ejemplo, el foco).

Ejemplo: Abrir una nueva ventana, mover el foco a otro componente, ir a otra página
(incluyendo cualquier acción que pueda hacer creer al usuario que se ha movido a otra página)

http://www.sidar.org/traducciones/wcag20/es/

23/37

15/10/2015

Pautas de Accesibilidad para el Contenido Web (WCAG) 2.0

o reorganizar el contenido de una página de forma significativa son ejemplos de cambios en el
contexto.

CAPTCHA

Acrónimo de "Completely Automated Public Turing test to tell Computers and Humans Apart"
(Prueba de Turing pública y automática para diferenciar a máquinas y humanos).

Nota 1: las pruebas de CAPTCHA a menudo consisten en pedirle al usuario que escriba en
forma de texto aquello que aparece en una imagen o en un archivo de audio distorsionados.

Nota 2: una prueba de Turing es cualquier sistema de pruebas diseñado para diferenciar a un
humano de una computadora. Su nombre se debe al famoso científico Alan Turing. El término
fue acuñado por investigadores de la Carnegie Mellon University. [CAPTCHA]

compatible con la accesibilidad

Soportado por las ayudas técnicas de los usuarios, así como por las características de
accesibilidad en los navegadores y otras aplicaciones de usuario.
Para ser considerada una tecnología de contenido web (o característica de una tecnología)
compatible con la accesibilidad, debe cumplir los dos siguientes requisitos:

1.  El modo en que se usa la tecnología de contenido Web es soportado por las

ayudas técnicas de los usuarios. Esto significa que la manera en que la tecnología es
usada, ha sido probada en cuanto a la interoperabilidad con las ayudas técnicas de los
usuarios, en el idioma o idiomas del contenido,
y

2.  Para esta tecnología de contenido web existen aplicaciones de usuario

compatibles con la accesibilidad disponibles para los usuarios. Esto significa que al
menos una de las siguientes premisas es verdadera:

a.  La tecnología tiene soporte de forma nativa en agentes de usuario ampliamente
distribuidos y que a su vez son compatibles con la accesibilidad (como HTML y
CSS);
O

b.  La tecnología tiene soporte en un complemento (plugin) ampliamente disponible y

que a su vez es compatible con la accesibilidad;
O

c.  El contenido está disponible en un medio cerrado, como una universidad o una

red corporativa, donde la aplicación de usuario exigido por la tecnología y
empleado por la organización también es compatible con la accesibilidad;
O

d.  La/s aplicación/es de usuario que soporta la tecnología es compatible con la
accesibilidad y está disponible para descarga o compra de manera que:

no cuesta a una persona con una discapacidad más de lo que cuesta a una
persona sin discapacidad y

es tan fácil de encontrar y obtener para una persona con discapacidad
como para una persona sin discapacidad.

Nota 1: Ni el Grupo de trabajo de las WCAG ni el W3C especificarán qué ayudas técnicas
deben soportar una tecnología web, o en qué medida deben hacerlo para que sea clasificada
como compatible con la accesibilidad (véase Nivel de Soporte Necesario para que una Ayuda
Técnica sea "Compatible con la Accesibilidad").

Nota 2: Las tecnologías web pueden emplearse de maneras que no sean compatibles con la
accesibilidad siempre y cuando no se dependa de ellas y la página como un todo cumpla con
los requisitos de conformidad, incluyendo el Requisito de Conformidad 4: Uso de tecnologías
exclusivamente según métodos que sean compatibles con la accesibilidad y Requisito de
Conformidad 5: Sin Interferencia.

Nota 3: Cuando una tecnología web se emplea de forma "compatible con la accesibilidad" no
implica que la tecnología entera (o todos sus usos) sea compatible. La mayoría de las

http://www.sidar.org/traducciones/wcag20/es/

24/37

15/10/2015

Pautas de Accesibilidad para el Contenido Web (WCAG) 2.0

tecnologías, incluyendo HTML, carecen de soporte en al menos una de sus características o
usos. Las páginas son conformes a las WCAG sólo si se depende del uso de tecnología que es
compatible con la accesibilidad para cumplir con los requisitos de las WCAG.

Nota 4: Cuando se citen tecnologías de contenido web que tengan múltiples versiones, la
versión o versiones soportadas deben especificarse.

Nota 5: Una forma de localizar usos de tecnologías que sean compatibles con la accesibilidad a
disposición de los autores sería consultar recopilaciones de usos documentados como
compatibles. (Véase Comprender Usos de Tecnologías Compatibles con la Accesibilidad). Los
autores, compañías, fabricantes de tecnologías u otros podrían documentar los usos de
tecnologías de contenido web compatibles con la accesibilidad. Sin embargo, todos los usos de
las tecnologías documentados necesitan cumplir con la definición de "compatible con la
accesibilidad" dada.

componente de la interfaz de usuario

Una parte del contenido que es percibida por los usuarios como un control único para una
función en particular.

Nota 1: Múltiples componentes de la interfaz de usuario pueden ser implementados como un
único elemento de programación. Aquí, componentes no está vinculado a las técnicas de
programación sino a lo que el usuario percibe como controles separados.

Nota 2: Los componentes de la interfaz de usuario incluyen los elementos de formulario y los
enlaces, así como los componentes generados por scripts.

Ejemplo: Un applet posee un "control" que permite moverse a través del contenido por línea,
por página o por acceso aleatorio. Como cada uno de ellos necesitaría tener un nombre y ser
configurado de forma independiente, cada uno sería un "componente de la interfaz de usuario".

compromisos legales

Las operaciones en las cuales la persona incurre en una obligación o beneficio jurídicamente
vinculante.

Ejemplo: Un contrato matrimonial, una transacción de acciones, un testamento, un préstamo,
adopción, alistamiento en el ejército, un contrato de cualquier tipo, etcétera.

conformidad

La satisfacción de todos los requisitos de un estándar, pauta o especificación determinados.

conjunto de páginas web

Un grupo de páginas web que comparte un propósito común y que han sido creadas por el
mismo autor, grupo u organización.

Nota: Versiones en diferentes idiomas podrían considerarse conjuntos de páginas web
diferentes.

contenido (contenido Web)

Información y experiencia sensorial transmitida a un usuario por medio de una aplicación de
usuario, que incluye el código o marcado que define su estructura, su presentación y las
interacciones.

contenido multimedia alternativo al texto

El contenido multimedia que no presenta más información que la que ya se ofrece textualmente
(directamente o a través de alternativas textuales).

Nota: Un contenido multimedia alternativo al texto se proporcionan para quienes se benefician
de las representaciones alternativas del texto. Pueden ser sólo audio, sólo vídeo (incluyendo
los vídeos en lengua de señas) o de audio y vídeo simultáneos.

contenido no textual

Cualquier contenido que no está formado por una secuencia de caracteres que puede ser
determinado por software o donde la secuencia no expresa nada en ningún idioma.

Nota: Esto incluye el arte ASCII (que es un patrón de caracteres), los emoticonos, la escritura

http://www.sidar.org/traducciones/wcag20/es/

25/37

15/10/2015

Pautas de Accesibilidad para el Contenido Web (WCAG) 2.0

leet (que utiliza sustitución de caracteres) e imágenes que representan texto.

contenido suplementario

El contenido adicional que ilustra o aclara el contenido principal.

Ejemplo 1: Una versión de audio de una página web.

Ejemplo 2: La ilustración de un proceso complejo.

Ejemplo 3: Un párrafo que resume los principales resultados y recomendaciones formuladas en
un estudio de investigación.

contexto del enlace determinado por software

La información adicional que puede ser determinada por software a partir de las relaciones con
un enlace, combinada con el texto del enlace y presentada al usuario en diferentes modos.

Ejemplo: En HTML, la información determinable por software sobre un enlace en castellano
incluye el texto que está en el mismo párrafo, lista o o celda de una tabla que el enlace, o el
texto en la cabecera de la tabla que está asociada con la celda de datos que contiene al
enlace.

Nota: Como los lectores de pantalla interpretan la puntuación, también pueden proporcionar el
contexto a partir de la oración en la que se encuentran, cuando el foco está en un enlace en
dicha oración.

controlables por el usuario

Datos cuya finalidad es que los usuarios accedan a ellos.

Nota: No se refiere a cosas tales como los registros de Internet y los datos de seguimiento de
los motores de búsqueda.

Ejemplo: Los campos de nombre y dirección para la cuenta de un usuario.

de la que se depende (tecnología)

El contenido no puede ser conforme si dicha tecnología se desconecta o no es soportada.

destello

Un par de cambios opuestos en la luminosidad relativa que pueden causar convulsiones en
algunas personas si son lo suficientemente pronunciados y en un rango de frecuencia
determinado.

Nota 1: Véase umbral de destello general y de destello rojo para obtener información sobre los
tipos de destellos no permitidos.

Nota 2: Véase también parpadeo.

determinado por software (determinable por software)

Determinado por software a partir de la información suministrada por el autor de modo tal que
las aplicaciones de usuario, incluyendo las ayudas técnicas, pueden extraer y presentar esta
información a los usuarios de distintas maneras.

Ejemplo 1: Determinado en el lenguaje de marcas a partir de elementos y atributos a los que
acceden directamente las ayudas técnicas comúnmente disponibles.

Ejemplo 2: Determinado a partir de la estructura de datos de una tecnología específica que no
es un lenguaje de marcas y expuesta a las ayudas técnicas a través de una API de
accesibilidad que es soportada por las ayudas técnicas comúnmente disponibles.

emergencia

Situación o suceso repentino que requiere una acción inmediata para preservar la salud, la
seguridad o la propiedad.

en directo

La información capturada de un evento de la vida real y transmitida al receptor sin más demora
que el retardo intencional de la emisión.

Nota 1: El retardo intencional es una demora corta (generalmente automatizada) que se usa,
por ejemplo, para dar tiempo al órgano de difusión de censurar el audio (o vídeo) transmitido,

http://www.sidar.org/traducciones/wcag20/es/

26/37

15/10/2015

Pautas de Accesibilidad para el Contenido Web (WCAG) 2.0

pero no suficiente para permitir trabajos de edición significativos.

Nota 2: Si la información es generada completamente por una computadora, no es en directo.

en una ventana a pantalla completa

En los ordenadores de sobremesa y portátiles más comunes, pantalla con la ventana
maximizada.

Nota: En la medida en que la gente suele mantener sus computadoras durante años, es mejor
no confiar en las resoluciones de los últimos modelos de monitores de sobremesa o de
pantallas de portátiles, sino considerar las resoluciones más comunes en los últimos años a la
hora de realizar esta evaluación.

error en la entrada de datos

La información proporcionada por el usuario que no es aceptada.

Nota: Esto incluye:

1.  La información requerida por la página web, pero omitida por el usuario.

2.  La información que es proporcionada por el usuario pero que no cumple con el formato

o valores requeridos para los datos.

esencial

Si se quitara, cambiaría la información o la funcionalidad del contenido y éstas no se pueden
alcanzar de ninguna otra manera que sea conforme a los requisitos.

especificado por software

Establecido por software, utilizando métodos que son soportados por las aplicaciones de
usuario, incluyendo las ayudas técnicas.

estructura

1.  La forma en que las partes de una página web están organizadas entre sí; y

2.  La forma en que una colección de páginas web está organizada.

etiqueta

El texto u otro componente con una alternativa textual que se presenta al usuario para identificar
un componente dentro del contenido web.

Nota 1: Una etiqueta se presenta a todos los usuarios mientras que el nombre puede estar
oculto y sólo ser expuesto por las ayudas técnicas. En muchos casos (pero no siempre) el
nombre y la etiqueta son iguales.

Nota 2: El término etiqueta no se limita al elemento label en HTML.

evento en tiempo real

El evento que a) ocurre en el momento en que se lo está viendo y b) no es generado
completamente por el contenido.

Ejemplo 1: La transmisión vía web de una actuación en directo (ocurre en el momento que se la
ve y no está previamente grabada).

Ejemplo 2: Una subasta en línea con gente ofertando (ocurre en el mismo momento).

Ejemplo 3: Personas interactuando en un mundo virtual usando avatares (no es completamente
generado por el contenido y ocurre en el mismo momento en que se lo observa).

experiencia sensorial específica

Experiencia sensorial que no es puramente decorativa y que principalmente no proporciona
información importante o cumple una función.

Ejemplo: Los ejemplos incluyen la interpretación de un solo de flauta, una obra de arte visual,
etc.

expresión idiomática

La frase cuyo significado no se puede deducir a partir del significado de las palabras individuales
y cuyas palabras específicas no se pueden cambiar sin pérdida de significado.

Nota: Las expresiones idiomáticas no se pueden traducir directamente, palabra por palabra, sin

http://www.sidar.org/traducciones/wcag20/es/

27/37

15/10/2015

Pautas de Accesibilidad para el Contenido Web (WCAG) 2.0

perder su significado (cultural o dependiente del idioma).

Ejemplo 1: En inglés, "spilling the beans" ("derramar los frijoles") significa "revelar un secreto".
Sin embargo, "Knocking over the beans" o "spilling the vegetables" no significan lo mismo.

Ejemplo 2: En japonés, la frase "さじを投げる" se traduce literalmente como "tiró una cuchara"
pero significa que no había nada que hacer y al final se dio por vencido.

Ejemplo 3: En holandés, "Hij ging met de kippen op stok" literalmente se traduce como "se fue
a dormir con las gallinas", pero significa "se fue a la cama temprano".

función

El texto o número por medio del cual el software puede identificar el rol de un componente en el
contenido web.

Ejemplo: Un número que indica si una imagen funciona como un enlace, un botón de comando
o una casilla de verificación.

funcionalidad

Los procesos y resultados que se pueden alcanzar a través de las acciones del usuario.

grabado

Información que no es en directo.

gran tamaño (texto)

El texto de al menos 18 puntos o 14 puntos en negritas, o un tamaño que alcanzaría un trazo
equivalente para las fuentes en Chino, Japonés y Coreano (CJK).

Nota 1: Las fuentes con trazos muy finos o con características especiales -que reducen la
familiaridad de las formas de las letras- son más difíciles de leer, especialmente con bajos
niveles de contraste.

Nota 2: El tamaño de fuente es la medida con que se presenta el contenido. No incluye la
ampliación o reducción que pueda hacer el usuario.

Nota 3: El tamaño de fuente real que ve el usuario depende del tamaño definido por el autor y
la pantalla del usuario o la configuración de las aplicaciones de usuario. Para la mayoría de las
fuentes comunes, 14 y 18 puntos es aproximadamente el equivalente a 1.2 y 1.5 ems o 120% o
150% del tamaño del texto en el cuerpo del documento (asumiendo que el tamaño de la fuente
del cuerpo del documento sea 100%), pero los autores necesitan comprobarlo para las fuentes
particulares que empleen. Cuando los tamaños se definen en unidades relativas, el tamaño real
en puntos lo calcula la aplicación de usuario para su representación. A la hora de evaluar este
criterio, el tamaño en puntos debería obtenerse de la propia aplicación de usuario o calcularse
sobre la base de las mediciones que haga la aplicación de usuario para calcular el tamaño de
la fuente. Los usuarios que tengan una visión reducida serían responsables de elegir las
configuraciones apropiadas a sus necesidades.

Nota 4: Cuando se usa texto sin especificar el tamaño de fuente, será razonable asumir el
menor tamaño -utilizado por la mayoría de los navegadores- para tamaños no especificados. Si
un título de nivel 1 se muestra en negritas de un tamaño de 14pt o más, entonces será
razonable asumir que es texto de gran tamaño. Las escalas relativas se pueden calcular de la
misma manera a partir de los tamaños predeterminados.

Nota 5: Los tamaños de 14 y 18 puntos para textos compuestos por caracteres latinos se han
tomado de los tamaños más pequeño (14pt) y mayor (18pt) considerados estándares a la hora
de hablar de ellos como "a gran escala". Para las fuentes de otros idiomas como CJK el
"equivalente" deberían ser los tamaños mínimo y máximo correspondientes.

idioma

La lengua que se habla, escribe o expresa con gestos (por medios visuales o tactiles) para
comunicarse con humanos.

Nota: Véase también lengua de señas.

imágenes de texto

http://www.sidar.org/traducciones/wcag20/es/

28/37

15/10/2015

Pautas de Accesibilidad para el Contenido Web (WCAG) 2.0

El texto que ha sido presentado en forma no textual (por ejemplo, una imagen) para conseguir
un efecto visual determinado.

Nota: Esto no incluye el texto que forma parte de una imagen que contiene otros elementos
visuales significativos.

Por ejemplo, la etiqueta con el nombre de la persona que aparece en una fotografía.

informativo

Con propósito de información y que no es un requisito para lograr conformidad.

Nota: El contenido que se considera requisito de conformidad se identifica como "normativo".

interfaz de teclado

La interfaz usada por un programa para obtener pulsaciones de teclas.

Nota 1: Una interfaz de teclado permite al usuario transmitir pulsaciones de teclas a los
programas incluso cuando la tecnología nativa no contiene un teclado.

Ejemplo: Un PDA con pantalla táctil tiene una interfaz de teclado incorporada en su sistema
operativo, así como un conector para teclados externos. Las aplicaciones en el PDA pueden
usar la interfaz para obtener entradas por teclado, ya sea desde un teclado externo o de otras
aplicaciones que proporcionen una entrada de teclado simulada, tales como los intérpretes de
escritura manual o aplicaciones de reconocimiento de voz con funcionalidad de "emulación de
teclado".

Nota 2: El funcionamiento de la aplicación (o partes de la aplicación) usando una emulación del
ratón a través del teclado (por ejemplo, MouseKeys) no se puede considerar una operación a
través de una interfaz de teclado porque el funcionamiento del programa se realiza usando su
interfaz de dispositivo apuntador, no su interfaz de teclado.

interpretación en lengua de señas

La traducción de un idioma, generalmente un idioma hablado, a lengua de señas.

Nota: Las lenguas de señas auténticas son idiomas independientes que no están relacionados
con las lenguas habladas del mismo país o región.

jerga

Las palabras usadas de manera particular por personas en un campo determinado.

Ejemplo: La palabra StickyKeys pertenece a la jerga del campo de las ayudas
técnicas/accesibilidad.

lengua de señas

Idioma que emplea combinaciones de los movimientos de manos y brazos, expresiones faciales
o posiciones del cuerpo para transmitir un significado.

luminosidad relativa

Brillo relativo de cualquier punto situado en un espacio de color, normalizado a 0 para el negro
más oscuro y a 1 para el blanco más claro.

Nota 1: Para el espacio de color sRGB, la luminosidad relativa de un color se define como L =
0.2126 * R + 0.7152 * G + 0.0722 * B donde R, G y B se definen como:

si RsRGB <= 0.03928 entonces R = RsRGB/12.92 si no R = ((RsRGB+0.055)/1.055) ^ 2.4

si GsRGB <= 0.03928 entonces G = GsRGB/12.92 si no G = ((GsRGB+0.055)/1.055) ^ 2.4

si BsRGB <= 0.03928 entonces B = BsRGB/12.92 si no B = ((BsRGB+0.055)/1.055) ^ 2.4

and RsRGB, GsRGB, y BsRGB se definen como:

RsRGB = R8bit/255

GsRGB = G8bit/255

BsRGB = B8bit/255

http://www.sidar.org/traducciones/wcag20/es/

29/37

15/10/2015

Pautas de Accesibilidad para el Contenido Web (WCAG) 2.0

El caracter "^" es el operador de potencia (formula extraída de [sRGB] y [IEC-4WD]).

Nota 2: Casi todos los sistemas empleados hoy para ver contenido web asumen la codificación
sRGB. A menos que se sepa que otro espacio de color va a ser empleado para procesar y
mostrar el contenido, los autores deben realizar sus evaluaciones sobre el espacio de color
sRGB. Si se emplean otros espacios de color, véase Comprender el Criterio de Conformidad
1.4.3.

Nota 3: Si se aplica un difuminado después de la distribución de un contenido, entonces se usa
el valor del color de la fuente original. Para colores que se difuminan en el original, se deben
emplear los valores promedio de los colores que se han difuminado (R promedio, G promedio y
B promedio).

Nota 4: Hay herramientas disponibles que pueden realizar los cálculos de forma automática
mientras comprueban los contrastes y destellos.

Note 5: Hay disponible una versión en MathML de la definición de luminosidad relativa.

mecanismo

El proceso o técnica para alcanzar un resultado.

Nota 1: El mecanismo puede proveerse explícitamente en el contenido, o se puede depender
de que sea proporcionado por la plataforma o por las aplicaciones de usuario, incluyendo las
ayudas técnicas.

Nota 2: El mecanismo debe satisfacer todos los Criterios de Conformidad para el nivel de
conformidad declarado.

misma funcionalidad

Se obtienen los mismos resultados cuando se usan.

Ejemplo: Un botón "buscar" en una página y un botón "encontrar" en otra página pueden tener
ambos un campo para introducir un término y listar los temas del sitio web relacionados con el
término introducido. En este caso, los botones tendrían la misma funcionalidad pero no estarían
etiquetados de modo coherente.

mismo orden relativo

Una misma posición en relación con otros elementos.

Nota: Se considera que los elementos están en el mismo orden relativo incluso si otros se
insertan o se quitan del orden original. Por ejemplo, un menú de navegación expansible puede
insertar niveles adicionales de detalle o una sección secundaria de navegación puede ser
insertada en el orden de lectura.

multimedia sincronizado

El audio o vídeo sincronizado con otro formato para presentar información y/o con componentes
interactivos basados en el tiempo, excepto cuando se trata de un contenido multimedia
alternativo al texto y está claramente identificado como tal.

navegada secuencialmente

Navegada en el orden definido para el avance del foco (de un elemento al próximo elemento)
usando una interfaz de teclado.

nivel de educación primario

Periodo de seis años que empieza a las edades de entre cinco y siete, posiblemente sin ninguna
educación previa.

Nota: Esta definición está basada en la Clasificación Internacional Normalizada de la
Educación [UNESCO].

nivel mínimo de educación secundaria

Los dos o tres años de educación que se inician al término de seis años de escuela y finalizan
nueve años después del comienzo de la enseñanza primaria.

Nota: Esta definición se basa en la Clasificación Internacional Normalizada de la Educación
[UNESCO].

http://www.sidar.org/traducciones/wcag20/es/

30/37

15/10/2015

Pautas de Accesibilidad para el Contenido Web (WCAG) 2.0

nombre

Texto a través del cual un programa puede identificar un componente dentro del contenido web.

Nota 1: El nombre puede estar oculto y ser expuesto solamente por una ayuda técnica,
mientras que una etiqueta se presenta a todos los usuarios. En muchos casos (pero no en
todos), la etiqueta y el nombre son iguales.

Nota 2: Esto no tiene relación con el atributo name en HTML.

normativo

Necesario para lograr conformidad.

Nota 1: Se puede lograr la conformidad con este documento en una amplia variedad de formas
bien definidas.

Nota 2: El contenido identificado como "informativo" o "no normativo" no se considera
obligatorio para la conformidad.

página web

El recurso no incrustado obtenido a partir de una URI única usando HTTP, junto con cualquier
otro recurso que se use en la presentación o que pretenda ser presentado por una aplicación de
usuario junto con él.

Nota 1: Aunque cualquier "otro recurso" sería procesado junto con el recurso principal, no
necesariamente debe ser procesado simultáneamente.

Nota 2: A los efectos de la conformidad con estas pautas, un recurso debe ser "no incrustado",
en el ámbito de la conformidad, para ser considerado una página web.

Ejemplo 1: Un recurso web incluyendo todas las imágenes y los elementos multimedia
incrustados.

Ejemplo 2: Un programa de correo web desarrollado con AJAX (Asynchronous JavaScript and
XML). Todo el programa reside en http://ejemplo.com/mail pero incluye una bandeja de
entrada, un área de contactos y un calendario. Se proporcionan enlaces o botones que hacen
aparecer estas secciones pero no cambian la URL de la página en su conjunto.

Ejemplo 3: Un portal personalizable, donde los usuarios pueden elegir el contenido a mostrar
de entre un conjunto de diferentes módulos.

Ejemplo 4: Al entrar en "http://shopping.ejemplo.com", se ingresa a un ambiente interactivo de
una tienda donde el usuario se puede mover visualmente, tomar productos de las estanterías y
ponerlos en su carrito de compras. Al hacer clic sobre un producto se muestra al lado una hoja
de especificaciones. Esto podría ser un sitio web de una sola página o una única página dentro
de un sitio web.

parpadeo

Alternar entre dos estados visuales de una manera que tiene por objeto llamar la atención.

Nota: Véase también destellos. Es posible que algo que sea lo suficientemente grande y
parpadee con el brillo y a la frecuencia necesaria pueda ser también clasificado como un
destello.

pausar

Detener a petición del usuario y no reanudar hasta que el usuario lo solicite.

presentación

El procesamiento del contenido de manera que pueda ser percibido por los usuarios.

proceso

Una serie de acciones del usuario donde cada acción es necesaria para completar una
actividad.

Ejemplo 1: El uso exitoso de una serie de páginas web de un sitio de compras requiere que los
usuarios vean productos alternativos, precios y ofertas; seleccionen los productos; realicen el
pedido y proporcionen información de envío y de la forma de pago.

Ejemplo 2: Una página de registro de una cuenta necesita que se realice una prueba de Turing

http://www.sidar.org/traducciones/wcag20/es/

31/37

15/10/2015

Pautas de Accesibilidad para el Contenido Web (WCAG) 2.0

antes de acceder al formulario de inscripción.

propósito del enlace

La naturaleza del resultado obtenido al activar un enlace.

relaciones

Las asociaciones significativas entre distintas partes del contenido.

relación de contraste

(L1 + 0.05) / (L2 + 0.05), donde

L1 es la luminosidad relativa del más claro de los colores, y

L2 es la luminosidad relativa del más oscuro de los colores.

Nota 1: Las relaciones de contraste abarcan desde 1 a 21 (normalmente escrito de 1:1 a 21:1).

Nota 2: Dado que los autores no tienen control sobre cómo se verá afectada la presentación
del texto a través de las preferencias de usuario (por ejemplo suavizado de fuentes o
antialiasing), la relación de contraste para el texto puede evaluarse con el antialiasing
desactivado.

Nota 3: A propósito de los criterios de conformidad 1.4.3 y 1.4.6, el contraste se mide con
respecto al fondo sobre el cual el texto se representa normalmente. Si no se especifica color de
fondo, se asume el blanco.

Nota 4: El color de fondo es el color especificado sobre el cual el texto se representa
normalmente. Se considera un fallo si no se especifica color de fondo cuando sí se especifica
el del texto, porque el color de fondo por defecto del usuario se desconoce y no se puede
evaluar si su contraste es suficiente. Por la misma razón, se considera un fallo no especificar el
color de un texto cuando sí se especifica el del fondo.

Nota 5: Cuando existe un borde alrededor de una letra, el borde puede añadir contraste y
puede emplearse en el cálculo del contraste entre la letra y el fondo. Un borde estrecho
alrededor de la letra puede considerarse como la letra en sí. Un borde ancho alrededor de la
letra que rellene la zona interior de la misma actúa como un halo y podría considerarse fondo.

Nota 6: La conformidad con las WCAG debe evaluarse para pares de colores especificados en
el contenido que el autor espera que aparezcan adyacentes en la presentación típica. Los
autores no necesitan considerar presentaciones inusuales, como cambios de colores
realizados por la aplicación de usuario, excepto cuando sean causadas por el código del autor.

satisface un criterio de conformidad

El criterio de conformidad no se evalúa como "falso" al aplicarse a una página.

sección

Un segmento auto-contenido de texto que se refiere a uno o más temas o contenidos
relacionados.

Nota: Una sección puede constar de uno o más párrafos e incluir gráficos, tablas, listas y sub-
secciones.

secuencia correcta de lectura

Cualquier secuencia donde las palabras y párrafos se presentan en un orden que no cambia el
significado del contenido.

simple decoración

Que sólo persigue un propósito estético, no proporciona información y no tiene ninguna
funcionalidad.

Nota: Un texto es simplemente decorativo si las palabras pueden ser reorganizadas o
sustituidas sin alterar su propósito.

Ejemplo: La portada de un diccionario contiene palabras al azar de colores muy suaves como
fondo.

subtítulos (para sordos)

http://www.sidar.org/traducciones/wcag20/es/

32/37

15/10/2015

Pautas de Accesibilidad para el Contenido Web (WCAG) 2.0

Alternativa visual y/o alternativa textual, sincronizada, para la información sonora necesaria para
comprender el contenido multimedia, que puede ser tanto hablada como no hablada.

Nota 1: Los subtítulos para sordos son similares a los subtítulos que presentan sólo los
diálogos, excepto por que los subtítulos para sordos transmiten no sólo el contenido de los
diálogos sino también equivalentes para la información sonora que no es diálogo y que es
necesaria para comprender el contenido del programa, incluyendo efectos sonoros, música,
risas, identificación del hablante y localización.

Nota 2: Los subtítulos ocultos o codificados (en inglés llamados "closed captions") son
equivalentes que pueden activarse o desactivarse en algunos reproductores.

Nota 3: Los subtítulos abiertos son cualquier subtítulo que no se puede desactivar u ocultar.
Por ejemplo, cuando los subtítulos son imágenes de texto incrustadas en la pista de vídeo.

Nota 4: Los subtítulos no deberían ocultar u obstaculizar la percepción de la información
relevante de la pista de vídeo.

Nota 5: En algunos países de lengua inglesa, se le llama "subtitles" también a lo que en otros
se llama "caption". Nota de la traducción: En el Reino Unido se le llama subtítulos tanto a los
subtítulos en una lengua distinta a la original de la pista de diálogos, como a los subtítulos para
sordos. En Estados Unidos, Canadá, Nueva Zelanda y Australia se hace la diferenciación
utilizando el término "captions" para referirse a los subtítulos para sordos.

Nota 6: Las audiodescripciones pueden, pero no necesariamente, ser subtituladas puesto que
son descripciones de información que ya se presenta visualmente.

sólo audio

Una presentación basada en el tiempo que contiene únicamente audio (sin vídeo y sin
interacción).

sólo vídeo

Una presentación basada en el tiempo que contiene únicamente imágenes (vídeo), sin sonidos
(audio) ni interacción.

tecnología (contenido web)

Mecanismo para codificar instrucciones sobre cómo debe representarse, reproducirse o
ejecutarse en una aplicación de usuario.

Nota 1: Tal como se emplea en estas pautas, tanto "tecnología web" como "tecnología"
(empleada sola) se refieren a tecnologías de contenido web.

Nota 2: Las tecnologías de contenido web pueden incluir lenguajes de marcado, formatos de
datos o lenguajes de programación que los autores pueden emplear independientemente o en
combinación para crear experiencias de usuario final, las cuales abarcan desde páginas web
estáticas a presentaciones multimedia sincronizadas, pasando por aplicaciones web dinámicas.

Ejemplo: Algunos ejemplos comunes de tecnologías de contenido web son HTML, CSS, SVG,
PNG, PDF, Flash y JavaScript.

texto

La secuencia de caracteres que puede ser determinada por software, cuando la secuencia está
expresando algo en un idioma.

umbral de destello general y de destello rojo

El destello o la secuencia de imágenes que cambian rápidamente está por debajo del umbral
permitido (es decir, el contenido es adecuado) si se cumple alguna de las siguientes
condiciones:

1.  No hay más de tres destellos generales y/o no hay más de tres destellos rojos dentro

del período de un segundo; o

2.  el área combinada de destellos que se producen de forma concurrente, ocupa no más de

un total de .006 estereorradianes dentro de un campo visual de 10 grados sobre la
pantalla (25% de los 10 grados de campo visual en la pantalla) a una distancia de visión
típica,

http://www.sidar.org/traducciones/wcag20/es/

33/37

15/10/2015

Pautas de Accesibilidad para el Contenido Web (WCAG) 2.0

donde:

Un destello general se define como un par de cambios opuestos en la luminosidad
relativa del 10% o más de la luminosidad relativa máxima, donde la luminosidad relativa
de la imagen más oscura es inferior a 0.80; y donde "un par de cambios opuestos" es un
incremento seguido por un decremento o viceversa, y

Un destello rojo se define como un par de transiciones opuestas que involucran un rojo
saturado.

Excepción: El destello de un patrón sutil y equilibrado como un ruido blanco o un patrón de
damero con "escaques" menores de 0.1° (del campo visual a una distancia tipica de visión) a un
lado no viola los umbrales.

Nota 1: Para software en general o contenido web, emplear como medida un rectángulo de 341
x 256 píxeles situado en cualquier parte del área de una pantalla cuyo contenido está a una
resolución de 1024 x 768 píxeles es una buena aproximación de lo que son 10° del campo
visual para tamaños de pantalla y distancias de visión estándares (pantallas de 15 a 17
pulgadas vistas a distancias entre 56 y 66 centímetros). Dispositivos a mayores resoluciones
que presenten el mismo contenido producirían imágenes más pequeñas y por tanto más
seguras; por eso se emplean resoluciones bajas para definir los umbrales.

Nota 2: Una transición es un cambio en la luminosidad relativa (o de luminosidad relativa/color
en el caso del destello rojo) entre picos y valles adyacentes de puntos de luminosidad relativa
(o de luminosidad relativa/color en el caso del destello rojo) representados gráficamente a lo
largo de una línea temporal. Un destello consiste en dos transiciones opuestas.

Nota 3: La definición válida actual en la materia de "par de transiciones opuestas que
implican un rojo saturado" indica que ésta se produce cuando, para cualquiera de los dos
estados implicados en cada transición, R/(R+G+B) >= 0.8, y el cambio en el valor de (R-G-
B)x320 > 20 (los valores negativos de (R-G-B)x320 se igualan a cero) para ambas transiciones.
Los valores de R, G, B oscilan entre 0 y 1 tal y como se especifica en la definición de
luminosidad relativa. [HARDING-BINNIE]

Nota 4: Existen herramientas disponibles para llevar a cabo el análisis a partir de una captura
de pantalla. De todas maneras, no es necesaria una herramienta para evaluar esta condición si
los destellos son menos de o igual a 3 por segundo. En este caso, el contenido cumple el
Criterio automáticamente (véanse los puntos 1 y 2 anteriores).

usadas de modo inusual o restringido

Las palabras usadas de tal forma que requieren que los usuarios sepan exactamente la
definición a aplicar para entender el contenido correctamente.

Ejemplo: El término "avatar" significa algo diferente si aparece en una discusión sobre
religiones que si lo hace en un artículo sobre informática, pero la definición apropiada puede
determinarse por el contexto. Por el contrario, la palabra "texto" se usa de modo muy específico
en las WCAG 2.0, de modo que se proporciona su definición en el glosario.

versión alternativa conforme
Una versión que:

1.  es conforme según un nivel designado, y

2.  proporciona la misma información y funcionalidad en el mismo idioma, y

3.  se mantiene actualizada con la misma frecuencia que el contenido no conforme, y

4.  para la cual al menos una de las siguientes condiciones es verdadera:

a.  se puede acceder a la versión conforme desde la página no conforme a través de

un mecanismo compatible con la accesibilidad, o

b.  sólo se puede acceder a la versión no conforme desde la versión conforme, o

c.  sólo se puede acceder a la versión no conforme desde una página conforme que

además proporciona un mecanismo para llegar a la versión conforme.

http://www.sidar.org/traducciones/wcag20/es/

34/37

15/10/2015

Pautas de Accesibilidad para el Contenido Web (WCAG) 2.0

Nota 1: En esta definición, "sólo se puede acceder" significa que hay algún mecanismo, como
una redirección condicional, que previene que el usuario "acceda" (cargue) la página no
conforme a menos que el usuario haya llegado desde la versión conforme.

Nota 2: La versión alternativa no necesita ser un equivalente página a página del original (por
ejemplo, la versión alternativa conforme podría consistir en varias páginas).

Nota 3: Si están disponibles versiones en diversos idiomas, las versiones alternativas
conformes son necesarias para cada idioma ofrecido.

Nota 4: Se pueden proporcionar versiones alternativas diferentes adaptadas a diferentes
tecnologías o grupos de usuarios. Cada versión debería ser tan conforme como fuera posible.
Una versión necesitaría ser totalmente conforme para cumplir el requisito de conformidad 1.

Nota 5: La versión conforme alternativa no necesita pertenecer al mismo alcance de
conformidad, ni siquiera al mismo sitio web, que la versión no conforme en la medida en que
esté disponible tan libremente como la versión no conforme.

Note 6: Las versiones alternativas no deben confundirse con contenidos complementarios, que
sirven de material de apoyo a la página original y mejoran su comprensión.

Nota 7: Permitir que el usuario establezca sus preferencias sobre el contenido para acceder a
una versión conforme es un mecanismo aceptable para acceder a otra versión siempre que el
método empleado para establecer las preferencias sea compatible con la accesibilidad.

Véase Comprender las Versiones Alternativas Conformes

vista

El objeto en el cual la aplicación de usuario presenta un contenido.

Nota 1: La aplicación de usuario puede presentar el contenido a través de una o más vistas.
Las vistas incluyen ventanas, marcos, altavoces y lupas virtuales. Una vista puede contener a
su vez otras vistas (por ejemplo en el caso de marcos anidados). Los componentes de interfaz
creados por la aplicación de usuario tales como cuadros de diálogo, menús o ventanas de
alerta no se consideran vistas.

Nota 2: Esta definición se basa en el Glosario de las Pautas de Accesibilidad para las
Aplicaciones de Usuario 1.0.

visualmente configurable

Cuando se puede establecer el tipo de letra, el tamaño, el color y el fondo.

vídeo

La tecnología de fotografías o imágenes secuenciales o en movimiento.

Nota: Un vídeo puede estar formado por imágenes animadas, imágenes fotográficas o ambas.

Apéndice B: Reconocimientos

Esta sección es informativa.

Esta publicación ha sido financiada en parte con fondos federales del Departamento de Educación de
los Estados Unidos, el Instituto Nacional de Investigación en Discapacidad y Rehabilitación (NIDRR,
por sus siglas en inglés) bajo el contrato número ED05CO0039. El contenido de esta publicación no
refleja necesariamente el punto de vista o las políticas del Departamento de Educación de los Estados
Unidos; y la mención de nombres comerciales, productos comerciales u organizaciones no implica que
el gobierno de los Estados Unidos las haya avalado.

Se puede encontrar información adicional acerca de la participación en el Grupo de Trabajo sobre las
Pautas de Accesibilidad para el Contenido Web en el sitio del Grupo de Trabajo.

Participantes activos en el Grupo de Trabajo de las WCAG en el momento de su
publicación

Bruce Bailey (U.S. Access Board)

http://www.sidar.org/traducciones/wcag20/es/

35/37

15/10/2015

Pautas de Accesibilidad para el Contenido Web (WCAG) 2.0

Frederick Boland (NIST)

Ben Caldwell (Trace R&D Center, Universidad de Wisconsin)

Sofia Celic (W3C Invited Expert)

Michael Cooper (W3C)

Roberto Ellero (International Webmasters Association / HTML Writers Guild)

Bengt Farre (Rigab)

Loretta Guarino Reid (Google)

Katie Haritos-Shea

Andrew Kirkpatrick (Adobe)

Drew LaHart (IBM)

Alex Li (SAP AG)

David MacDonald (E-Ramp Inc.)

Roberto Scano (International Webmasters Association / HTML Writers Guild)

Cynthia Shelly (Microsoft)

Andi Snow-Weaver (IBM)

Christophe Strobbe (DocArch, K.U.Leuven)

Gregg Vanderheiden (Trace R&D Center, University of Wisconsin)

Otros participantes anteriormente activos en el Grupo de Trabajo de las WCAG y otros
colaboradores de las WCAG 2.0

Shadi Abou-Zahra, Jim Allan, Jenae Andershonis, Avi Arditti, Aries Arditi, Mike Barta, Sandy Bartell,
Kynn Bartlett, Marco Bertoni, Harvey Bingham, Chris Blouch, Paul Bohman, Patrice Bourlon, Judy
Brewer, Andy Brown, Dick Brown, Doyle Burnett, Raven Calais, Tomas Caspers, Roberto Castaldo,
Sambhavi Chandrashekar, Mike Cherim, Jonathan Chetwynd, Wendy Chisholm, Alan Chuter, David M
Clark, Joe Clark, James Coltham, James Craig, Tom Croucher, Nir Dagan, Daniel Dardailler, Geoff
Deering, Pete DeVasto, Don Evans, Neal Ewers, Steve Faulkner, Lainey Feingold, Alan J. Flavell,
Nikolaos Floratos, Kentarou Fukuda, Miguel Garcia, P.J. Gardner, Greg Gay, Becky Gibson, Al
Gilman, Kerstin Goldsmith, Michael Grade, Jon Gunderson, Emmanuelle Gutiérrez y Restrepo, Brian
Hardy, Eric Hansen, Sean Hayes, Shawn Henry, Hans Hillen, Donovan Hipke, Bjoern Hoehrmann,
Chris Hofstader, Yvette Hoitink, Carlos Iglesias, Ian Jacobs, Phill Jenkins, Jyotsna Kaki, Leonard R.
Kasday, Kazuhito Kidachi, Ken Kipness, Marja-Riitta Koivunen, Preety Kumar, Gez Lemon, Chuck
Letourneau, Scott Luebking, Tim Lacy, Jim Ley, William Loughborough, Greg Lowney, Luca Mascaro,
Liam McGee, Jens Meiert, Niqui Merret, Alessandro Miele, Mathew J Mirabella, Charles
McCathieNevile, Matt May, Marti McCuller, Sorcha Moore, Charles F. Munat, Robert Neff, Bruno von
Niman, Tim Noonan, Sebastiano Nutarelli, Graham Oliver, Sean B. Palmer, Sailesh Panchang, Nigel
Peck, Anne Pemberton, David Poehlman, Adam Victor Reed, Chris Ridpath, Lee Roberts, Gregory J.
Rosmaita, Matthew Ross, Sharron Rush, Gian Sampson-Wild, Joel Sanda, Gordon Schantz, Lisa
Seeman, John Slatin, Becky Smith, Jared Smith, Neil Soiffer, Jeanne Spellman, Mike Squillace,
Michael Stenitzer, Jim Thatcher, Terry Thompson, Justin Thorp, Makoto Ueki, Eric Velleman, Dena
Wainwright, Paul Walsch, Takayuki Watanabe, Jason White.

Apéndice C: Referencias

Esta sección es informativa.

CAPTCHA

The CAPTCHA Project, Universidad Carnegie Mellon. El proyecto se encuentra en línea en
http://www.captcha.net.

HARDING-BINNIE

Harding G.F.A. and Binnie, C.D., Independent Analysis of the ITC Photosensitive Epilepsy
Calibration Test Tape. 2002.

http://www.sidar.org/traducciones/wcag20/es/

36/37

15/10/2015

Pautas de Accesibilidad para el Contenido Web (WCAG) 2.0

IEC-4WD

IEC/4WD 61966-2-1: Colour Measurement and Management in Multimedia Systems and
Equipment - Part 2.1: Default Colour Space - sRGB. 5 de mayo de 1998.

sRGB

"A Standard Default Color Space for the Internet - sRGB," M. Stokes, M. Anderson, S.
Chandrasekar, R. Motta, eds., Version 1.10, 5 de noviembre de 1996. Una copia de este artículo
se encuentra en http://www.w3.org/Graphics/Color/sRGB.html.

UNESCO

International Standard Classification of Education, 1997. Una copia del estándar se encuentra en
http://www.unesco.org/education/information/nfsunesco/doc/isced_1997.htm.

WCAG10

Web Content Accessibility Guidelines 1.0, G. Vanderheiden, W. Chisholm, I. Jacobs, Editors,
W3C Recommendation, 5 de mayo de 1999, http://www.w3.org/TR/1999/WAI-WEBCONTENT-
19990505/. La última versión de las WCAG 1.0 está disponible en http://www.w3.org/TR/WAI-
WEBCONTENT/.

http://www.sidar.org/traducciones/wcag20/es/

37/37


