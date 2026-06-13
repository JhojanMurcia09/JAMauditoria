# JAMauditoria
JAM es una herramienta de auditoría inalámbrica para investigación de seguridad. Automatiza el despliegue de puntos de acceso con monitoreo en tiempo real y perfilado de clientes. Diseñado exclusivamente con fines educativos y de investigación personal en entornos controlados El autor no asume responsabilidad alguna por el uso indebido del software

# JAM - Cobertura Unificada de Auditoría Inalámbrica

JAM es una herramienta de automatización para el despliegue de entornos de red inalámbrica con fines de auditoría, investigación de seguridad y desarrollo de proyectos personales. Este script facilita la clonación de entornos Wi-Fi, permitiendo el análisis de tráfico y la gestión de dispositivos conectados en entornos controlados.

## ⚠️ Aviso Legal y Descargo de Responsabilidad (Disclaimer)

**Este software se proporciona exclusivamente con fines educativos e investigativos.**

El autor no se hace responsable del uso indebido de esta herramienta. Es responsabilidad total del usuario utilizar este script dentro de un entorno ético, sobre redes de su propiedad o para las cuales tenga autorización expresa y por escrito para realizar pruebas de penetración o auditorías de seguridad.

El uso de este software para interceptar comunicaciones o acceder a redes sin consentimiento explícito es ilegal y constituye una violación de la privacidad y las leyes de ciberseguridad vigentes. Al utilizar este código, usted acepta cumplir con todas las leyes locales, estatales y federales aplicables.

## Características Principales

* **Compatibilidad Universal:** Optimizado para la conexión estable de dispositivos Android, iOS, Windows y macOS.
* **Automatización de Procesos:** Despliegue automático de servicios (`hostapd`, `dnsmasq`, `iptables`) con aislamiento de interfaz.
* **Monitoreo en Tiempo Real:** Interfaz multiventana (`xterm`) que permite visualizar el estado del hardware y el tráfico de datos/consultas DNS simultáneamente.
* **Perfilado de Clientes:** Integración nativa con `nmap` para el reconocimiento rápido de servicios y puertos abiertos en los dispositivos conectados.
* **Restauración Segura:** Limpieza automática de reglas y configuración original del sistema al finalizar la sesión.

## Requisitos

* Sistema operativo basado en Linux (Kali, Debian, Ubuntu, etc.).
* Tarjeta inalámbrica compatible con modo AP (Access Point).
* Privilegios de superusuario (`root`).
* Dependencias: `iw`, `ip`, `hostapd`, `dnsmasq`, `xterm`, `nmap`, `iptables`, `nmcli`.

## Instalación

```bash
git clone https://github.com/JhojanMurcia09/JAMauditoria.git
cd JAMauditoria
cd ModeMonitor
sudo python3 instalame.py
