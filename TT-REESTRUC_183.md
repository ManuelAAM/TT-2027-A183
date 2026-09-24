# **Sistema de Monitoreo, Diagnóstico y Recomendación de Acciones Iniciales para la Evaluación de Calidad de Redes de Área Local en Entornos Académicos** 

**_Trabajo Terminal No. 2027-A183_** 

_Alumnos: *Aragón Martínez Manuel Alejandro, Bejarano Balmori David Directores: Alcaraz Torres Juan Jesús_ 

_*e-mail: maragonm1900@alumno.ipn.mx_ 

**Resumen –** 

El presente Trabajo Terminal propone el desarrollo de un sistema de monitoreo y análisis de redes de área local orientado a entornos académicos. La plataforma permitirá medir métricas de calidad de servicio como latencia, pérdida de paquetes y disponibilidad de nodos mediante pruebas automatizadas. A partir del análisis de estas métricas, el sistema generará diagnósticos sobre posibles fallos de conectividad e intermitencias en las redes y sugerirá acciones iniciales para su resolución. Asimismo, almacenará registros históricos y reportes que facilitarán el seguimiento de problemas de red y apoyarán las tareas de diagnóstico por parte de usuarios y personal técnico. 

Palabras clave: Redes LAN, Monitoreo de Red, Calidad de Servicio, Diagnóstico de Red. 

## **1. Introducción** 

Las redes de computadoras constituyen un elemento fundamental en la infraestructura tecnológica de instituciones educativas, ya que permiten el acceso a recursos académicos, plataformas de aprendizaje y servicios en línea. Sin embargo, es común que en entornos universitarios se presenten problemas de conectividad tales como intermitencia en el acceso a Internet, alta latencia o pérdida de paquetes, lo que afecta el desempeño de las actividades académicas. 

En muchos casos, estos problemas no son diagnosticados de manera inmediata debido a la falta de herramientas accesibles que permitan identificar su origen o proporcionar información detallada sobre el estado de la red. Generalmente, los usuarios finales solo perciben la degradación del servicio sin contar con mecanismos que faciliten la identificación preliminar del problema o la generación de reportes útiles para el personal técnico. 

Actualmente existen herramientas profesionales de monitoreo de red como Nagios, Zabbix o PRTG que permiten supervisar el estado de los dispositivos y servicios de red. No obstante, estas soluciones suelen requerir configuraciones complejas y conocimientos especializados para su implementación y operación, lo que limita su uso en entornos académicos o por parte de usuarios no especializados. 

Debido a esta situación, surge la necesidad de desarrollar una herramienta orientada a entornos académicos que permita ejecutar pruebas de conectividad, monitorear métricas del desempeño de la red y generar recomendaciones iniciales para apoyar la identificación de problemas comunes de conectividad tanto para usuarios como para personal técnico. 

La solución propuesta consiste en un sistema de monitoreo y diagnóstico básico de redes de área local capaz de recopilar métricas como latencia, pérdida de paquetes y disponibilidad de la red mediante pruebas automatizadas. A partir del análisis de estas métricas, el sistema generará diagnósticos preliminares y sugerencias de acciones iniciales para apoyar la atención de incidencias comunes de conectividad dentro de entornos académicos. 

Tabla 1. Resumen de productos similares 

|**Software**|**Características**|**Precio**|
|---|---|---|
|Nagios|Monitoreo de red avanzado, alertas|Licencia<br>comercial|
|Zabbix|Plataforma profesional de monitoreo|Software libre|
|PRTG|Monitorización completa de infraestructura|Licencia<br>comercial|



|**Solución**|Monitoreo, diagnóstico y sugerencias de resolución orientado a|Desarrollo|
|---|---|---|
|**propuesta**|entornos académicos|académico|



## **2. Objetivo** 

Diseñar e implementar un sistema de monitoreo y diagnóstico básico de redes de área local orientado a entornos académicos, capaz de evaluar métricas de conectividad y desempeño mediante pruebas automatizadas, con el propósito de detectar incidencias comunes de red y generar recomendaciones iniciales de atención para usuarios y personal técnico. 

### **Objetivos específicos propuestos** 

1. Desarrollar un módulo de monitoreo capaz de ejecutar pruebas de conectividad y recopilar métricas de red como latencia, pérdida de paquetes y disponibilidad de nodos. 

2. Implementar mecanismos de almacenamiento para registrar históricamente los resultados obtenidos durante las pruebas de monitoreo. 

3. Diseñar un módulo de análisis que permita identificar condiciones anómalas o fallos básicos de conectividad a partir de las métricas recopiladas. 

4. Generar recomendaciones iniciales de solución orientadas a problemas comunes de red, tales como pérdida de conexión, alta latencia o fallos de acceso local. 

5. Desarrollar una interfaz web que permita visualizar métricas, diagnósticos y reportes generados por el sistema. 

6. Realizar pruebas funcionales en escenarios controlados de red para validar el funcionamiento de los módulos de monitoreo, análisis y generación de recomendaciones. 

7. Elaborar la documentación técnica y manuales de usuario correspondientes al sistema desarrollado. 

## **3. Justificación** 

Las redes de comunicación son esenciales para el funcionamiento de las actividades académicas en instituciones educativas, ya que permiten el acceso a servicios digitales, recursos en línea y plataformas de aprendizaje. Sin embargo, es frecuente que se presenten problemas de conectividad tales como degradación del servicio, intermitencia en la conexión o dificultades en el acceso a Internet. 

Uno de los principales retos en la atención de estos problemas es la falta de información clara sobre el estado de la red y las posibles causas del fallo. Los usuarios finales suelen reportar únicamente síntomas generales como “internet lento” o “falta de conexión”, lo cual dificulta el diagnóstico inicial y retrasa la resolución del problema. 

El desarrollo de un sistema de monitoreo y diagnóstico de red permitirá obtener métricas objetivas sobre el desempeño de la infraestructura de red, tales como latencia, pérdida de paquetes y disponibilidad de nodos. A partir del análisis de estos datos, será posible identificar patrones de comportamiento que indiquen fallos potenciales o degradación del servicio. 

La originalidad del proyecto radica en integrar, dentro de una misma plataforma, no solo mecanismos de monitoreo y registro de métricas de red, sino también un módulo de diagnóstico que genere recomendaciones de acciones iniciales para intentar resolver problemas comunes de conectividad. Estas recomendaciones estarán orientadas a usuarios con conocimientos básicos, permitiendo realizar verificaciones sencillas como comprobar la conectividad con el gateway, reiniciar interfaces de red o validar configuraciones básicas. 

Los principales beneficiarios de esta herramienta serían estudiantes, profesores y personal técnico, quienes podrán contar con información estructurada sobre el estado de la red y registros históricos de su comportamiento. Esto facilitará el análisis de incidentes y permitirá que el personal especializado disponga de más información para realizar un diagnóstico más preciso cuando el problema no pueda resolverse mediante las acciones sugeridas. 

Además, el proyecto representa una aplicación práctica de los conocimientos adquiridos durante la carrera en áreas como redes de computadoras, programación y análisis de sistemas, permitiendo desarrollar una herramienta funcional y potencialmente útil para entornos académicos. 

## **4. Productos o resultados esperados** 



<!-- Start of picture text -->
[sistema de Monitoreo[Argitactura General y Diagnostica  de Sistema de Monitoreo y Diagnésico de Red<br>eaeNeoreode<br>smae|<br>{iavedasConeswocerxtese er)<br>mrs<br>L Co tntraestrvcturade Red (—CiapesttivesGente [|<br>Semsooum|{Wostgresau UT sf” [sence] [Rea caeeey<br>cont<br>mamIndia Se Metco atoGe Acco WF<br>xcse<br>Diese Bases<br>scene mt<br>GeneratorRecerensconesde<br>i Servisor Backend i<br>visio Vesa](reer 1 Fteico<br>anata aa ne mar<br>Sates leeraDo s  Wedtana<br>y Reports<br><!-- End of picture text -->

### **Productos esperados** 

1. Código fuente del sistema desarrollado. 

2. Base de datos con registros de monitoreo. 

3. Manual técnico del sistema. 

4. Manual de usuario. 

5. Reporte técnico del Trabajo Terminal. 

6. Resultados de pruebas de funcionamiento del sistema. 

## **5. Metodología** 

El desarrollo del presente Trabajo Terminal se realizará siguiendo un enfoque incremental que permita dividir el proyecto en etapas progresivas de análisis, diseño, implementación y evaluación. Este enfoque facilitará el desarrollo gradual del sistema y permitirá validar cada uno de los módulos que conforman la plataforma. 

En una primera etapa se llevará a cabo el análisis de requerimientos, identificando las métricas de red que serán monitoreadas y las funcionalidades principales del sistema. Posteriormente se realizará el diseño de la arquitectura del sistema bajo un modelo cliente-servidor que permita separar los componentes de monitoreo, procesamiento de datos y visualización de información. 

La implementación del sistema se realizará utilizando el lenguaje de programación Python debido a su amplia disponibilidad de librerías orientadas al análisis de redes y automatización de tareas. Para la ejecución de pruebas de conectividad se utilizarán herramientas y protocolos de diagnóstico como ICMP, traceroute y pruebas de transferencia de datos mediante distintas tecnologías y utilidades como iPerf. Asimismo, se podrán emplear librerías especializadas para el análisis de tráfico de red. 

Los datos obtenidos a partir de las pruebas de monitoreo serán almacenados en una base de datos relacional como PostgreSQL, lo que permitirá mantener registros históricos y realizar análisis posteriores sobre el comportamiento de la red. 

Para la visualización de resultados se desarrollará una interfaz web que permitirá consultar el estado de la red, revisar métricas obtenidas y visualizar reportes generados por el sistema. Además, se implementará un módulo de diagnóstico que, a partir del análisis de las métricas registradas, generará recomendaciones de acciones iniciales que los usuarios podrán realizar para intentar resolver problemas comunes de conectividad. 

Finalmente, se llevarán a cabo pruebas funcionales del sistema utilizando escenarios controlados de red, con el objetivo de validar el correcto funcionamiento de los módulos de monitoreo, análisis y generación de recomendaciones. 

## **6. Cronograma** 

CRONOGRAMA Nombre del alumno(a): Aragón Martínez Manuel Alejandro                                           TT No.:_ 

Título del TT: Sistema de Monitoreo, Diagnóstico y Recomendación de Acciones Iniciales para la Evaluación de Calidad de Redes de Área Local en Entornos Académicos 

|Actividad|AGO|SEP|OCT|NOV|DIC|ENE|FEB|MAR|ABR|MAY|JUN|
|---|---|---|---|---|---|---|---|---|---|---|---|
|Análisis de requisitos y diseño<br>arquitectónico||||||||||||
|Desarrollo del módulo de<br>pruebas de conectividad||||||||||||
|Integración del sistema con<br>almacenamiento de datos||||||||||||
|Implementación del motor de<br>análisisydetección de anomalías||||||||||||
|Desarrollo de la interfaz de<br>visualización||||||||||||
|Elaboración de manual técnico||||||||||||
|Pruebas de integración y<br>optimización del sistema||||||||||||
|Documentación del software||||||||||||
|Generación el Reporte Técnico.||||||||||||
|Presentación de resultados||||||||||||
|Evaluación de TT II.||||||||||||



CRONOGRAMA Nombre del alumno(a): Bejarano Balmori David                                         TT No.:_ 

Título del TT: Sistema de Monitoreo, Diagnóstico y Recomendación de Acciones Iniciales para la Evaluación de Calidad de Redes de Área Local en Entornos Académicos 

|Actividad|AGO|SEP|OCT|NOV|DIC|ENE|FEB|MAR|ABR|MAY|JUN|
|---|---|---|---|---|---|---|---|---|---|---|---|
|Análisis de requisitos y diseño<br>arquitectónico||||||||||||
|Desarrollo del módulo de pruebas<br>de rendimiento||||||||||||
|Diseño e implementación del<br>almacenamiento de datos||||||||||||
|Implementación del motor de<br>diagnósticoyrecomendaciones||||||||||||
|Desarrollo de consultas y<br>generación de reportes||||||||||||



|Pruebas funcionales en entorno<br>controlado|
|---|
|Elaboración de manual de usuario|
|Validación de resultados y<br>generación de métricas finales|
|Soporte a presentación de<br>resultados|
|Documentación del software|
|Generación el Reporte Técnico.|
|Presentación de resultados|
|Evaluación de TT II.|





## **7. Referencias** 

[1] R. Ríos y J. R. Fermín, “Análisis de tráfico de una red local universitaria,” Telématique, vol. 8, no. 2, pp. 15–27, 2009. Disponible en: 

https://www.redalyc.org/pdf/784/78411787002.pdf 

[2] J. A. Gómez Martínez y O. Gualdrón González, “Caracterización de tráfico en una red de área local,” Revista UIS Ingenierías, vol. 8, no. 2, pp. 167–176, 2009. Disponible en: 

https://revistas.uis.edu.co/index.php/revistauisingenierias/article/view/507 

[3] P. Jurkiewicz, G. Rzym y P. Boryło, “Flow length and size distributions in campus Internet traffic,” arXiv preprint arXiv:1809.03486, 2018. Disponible en: 

https://arxiv.org/abs/1809.03486 

[4] A. S. Tanenbaum y D. J. Wetherall, Computer Networks, 5th ed. Boston, MA, USA: Pearson, 2011. 

[5] J. F. Kurose y K. W. Ross, Computer Networking: A Top-Down Approach, 8th ed. Boston, MA, USA: Pearson, 2021. 

[6] W. Stallings, Data and Computer Communications, 10th ed. Upper Saddle River, NJ, USA: Pearson, 2013. 

[7] L. Peterson y B. Davie, Computer Networks: A Systems Approach, 5th ed. San Francisco, CA, USA: Morgan Kaufmann, 2012. Disponible en: 

https://book.systemsapproach.org/ 

[8] L. Chappell y G. Combs, Wireshark Network Analysis: The Official Wireshark Certified Network Analyst Study Guide, 2nd ed. Houston, TX, USA: Chappell University, 2012. 

[9] ESnet, “iPerf – The ultimate tool for network performance measurement,” 2024. Disponible en: 

https://iperf.fr/ 

[10] B. Claise, “Cisco Systems NetFlow Services Export Version 9,” IETF RFC 3954, 2004. Disponible en: 

https://www.rfc-editor.org/rfc/rfc3954 

uae Martine Manuel Alejandro. Alumno de la carrera de Ing. en Sistemas Computacionales en ESCOM, pecialidad Sistemas, Boleta: 2023630411, Tel. 5587422612, email maragonm1900@alumno.ipn.mx 

