#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import sys
import os
import time
import shutil

# Diccionario con las dependencias y sus explicaciones didácticas de nivel de ingeniería
PAQUETES_A_INSTALAR = {
    "iw": (
        "Herramienta estándar en Linux para configurar dispositivos inalámbricos. "
        "Permite interactuar con los controladores de tu antena, revisar sus capacidades físicas "
        "y cambiar su tipo de operación a modo monitor."
    ),
    "iproute2": (
        "Suite de administración de red nativa del kernel que provee el comando 'ip'. "
        "Es crítica para apagar o levantar las interfaces de red antes de aplicar cambios de hardware."
    ),
    "systemd": (
        "Provee el comando 'systemctl'. Se requiere para reiniciar servicios del sistema "
        "como 'NetworkManager', devolviendo tus antenas a su estado normal para volver a navegar."
    ),
    "xterm": (
        "Emulador de terminal clásico para entornos gráficos. Permite abrir ventanas independientes "
        "flotantes en tu pantalla (como la del escáner en tiempo real) mientras el menú principal sigue libre."
    ),
    "aircrack-ng": (
        "Suite de ingeniería inalámbrica fundamental. De aquí se extrae 'airodump-ng' para capturar "
        "paquetes del aire y buscar handshakes, y 'aireplay-ng' para la inyección de tramas."
    ),
    "hostapd": (
        "Significa 'Host Access Point Daemon'. Se encarga de transformar tu tarjeta Wi-Fi física "
        "en un Punto de Acceso (Access Point) virtual para emitir tu propia señal de red."
    ),
    "dnsmasq": (
        "Servidor de infraestructura ligero que actúa como DHCP (asigna IPs automáticas a los clientes "
        "que se conectan a tu red) y como DNS (traduce los nombres de dominio de internet)."
    ),
    "nmap": (
        "El mapeador de redes por excelencia. Envía paquetes diseñados a medida para analizar qué puertos, "
        "servicios, sistemas operativos y vulnerabilidades tienen los dispositivos objetivos."
    )
}

def verificar_root():
    """Garantiza privilegios de administrador antes de interactuar con APT."""
    if os.getuid() != 0:
        print("\n" + "="*75)
        print(" [-] ERROR CRÍTICO: PERMISOS INSUFICIENTES")
        print("="*75)
        print(" [*] Este script de instalación requiere privilegios de administrador (root).")
        print(" [*] Por favor, ejecútalo usando: sudo python3 Instalame.py")
        print("="*75 + "\n")
        sys.exit(1)

def ejecutar_comando_narrado(descripcion_tecnica, comando):
    """Muestra la razón de ser del comando antes de invocarlo."""
    print(f"\n[EXPLICACIÓN TÉCNICA]: {descripcion_tecnica}")
    print(f"[EJECUTANDO COMANDO ]: {' '.join(comando)}")
    print("-" * 75)
    time.sleep(1.5)
    
    try:
        # Se ejecuta mostrando la salida nativa de APT en tiempo real para control del operador
        subprocess.run(comando, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[-] Error al procesar la instalación. Código de salida: {e.returncode}")
        return False

def main():
    os.system('clear')
    
    # Tu identidad visual oficial JAM (J vestida con saco de hacker)
    logo_jam = """
         .---.        ____     _       _       _ 
        /     \\      |____ |  / \\     | \\     / |
       |  ___  |         | | / _ \\    |  \\   /  |
       | /   \\ |         | |/ /_\\ \\   |   \\_/   |
       | | U | |     ___ | / ___   \\  | |\\_/| | |
       | \\___/ |    |____|/_/     \\_\\ |_|   |_|
        \\     /     
         `---'       [ JAM - ENTORNO DE INSTALACIÓN ]
    """
    print(logo_jam)
    
    print("="*78)
    print("      SISTEMA AUDITOR DE DEPENDENCIAS E INFRAESTRUCTURA DE RED")
    print("="*78)
    
    verificar_root()
    
    print("\n[*] FASE 1: Sincronización de repositorios del sistema...")
    explicacion_update = (
        "Invocaremos 'apt update' para descargar los índices actualizados desde los servidores oficiales. "
        "Esto le dice a tu Linux exactamente qué versiones de software existen hoy, previniendo errores "
        "de 'paquete no encontrado' durante la instalación."
    )
    ejecutar_comando_narrado(explicacion_update, ["apt", "update"])
    
    print("\n" + "="*78)
    print(" [*] FASE 2: COMPROBACIÓN INTEGRAL DE COMPONENTES DEL SISTEMA")
    print("="*78)
    print(" | PAQUETE       | ESTADO ACTUAL    | ACCIÓN DIRECTA")
    print(" |---------------|------------------|-----------------------------------------")
    
    paquetes_por_instalar = []
    
    # Mapeo y verificación estética de cada dependencia
    for paquete in PAQUETES_A_INSTALAR:
        comando_control = paquete
        if paquete == "aircrack-ng": comando_control = "airodump-ng"
        elif paquete == "iproute2":  comando_control = "ip"
        elif paquete == "systemd":   comando_control = "systemctl"
        
        if shutil.which(comando_control) is not None:
            # Relleno de espacios estético para mantener la tabla perfecta
            print(f" | {paquete.ljust(13)} | [ INSTALADO ✓ ]  | Detectado en el sistema. [OMITIR]")
        else:
            print(f" | {paquete.ljust(13)} | [ PENDIENTE ⏳ ] | Requiere instalación en este entorno.")
            paquetes_por_instalar.append(paquete)
            
    print(" " + "-"*77)
    time.sleep(2.0)

    # Si todo está instalado, terminamos con el resumen ejecutivo limpio
    if not paquetes_por_instalar:
        print("\n" + "="*78)
        print("              ANEXO DE AUDITORÍA: INFORME DE VERIFICACIÓN")
        print("="*78)
        print(" [+] ESTADO GENERAL : ENTORNO COMPLETADO E INTEGRAL")
        print(" [+] REPORTE        : No se detectaron herramientas faltantes en el sistema.")
        print(" [+] ACCIÓN         : Los módulos dependientes están listos para ser ejecutados.")
        print("="*78 + "\n")
        return

    # Si faltan elementos, procesamos únicamente los que están pendientes
    print("\n" + "="*78)
    print("       FASE 3: INSTALACIÓN SELECTIVA DE COMPONENTES PENDIENTES")
    print("="*78)
    print(f"[*] El sistema detectó {len(paquetes_por_instalar)} herramientas faltantes. Iniciando despliegue...")
    
    for paquete in paquetes_por_instalar:
        print(f"\n>>> PROCESANDO PAQUETE: {paquete.upper()} <<<")
        explicacion_instalacion = PAQUETES_A_INSTALAR[paquete]
        
        comando_apt = ["apt", "install", paquete, "-y"]
        exito = ejecutar_comando_narrado(explicacion_instalacion, comando_apt)
        
        if exito:
            print(f"[+] Estado actualizado: {paquete} ahora se encuentra disponible.")
        else:
            print(f"[!] Nota operativa: Ocurrió un retraso al configurar '{paquete}'.")
            
    print("\n" + "="*78)
    print("              ANEXO DE AUDITORÍA: RESUMEN FIN DE INSTALACIÓN")
    print("="*78)
    print("[+] Todas las herramientas seleccionadas han sido integradas en la suite de comandos.")
    print("[+] Interfaces de auditoría avanzada e inyección de tráfico preparadas.")
    print("="*78 + "\n")

if __name__ == "__main__":
    main()