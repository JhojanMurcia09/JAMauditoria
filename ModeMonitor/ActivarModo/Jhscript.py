#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import sys
import os
import time
import shutil

def verificar_root():
    """Garantiza que el script se ejecute con los privilegios necesarios."""
    if os.getuid() != 0:
        print("[-] Error: Este script requiere privilegios de root.")
        print("[*] Ejecútalo con: sudo python3 <nombre_del_archivo>.py")
        sys.exit(1)

def comprobar_herramientas():
    """Verifica de forma rápida que los comandos esenciales estén en el sistema."""
    for cmd in ["iw", "ip", "systemctl"]:
        if shutil.which(cmd) is None:
            print(f"[-] Error: No se encontró el comando '{cmd}'. Ejecuta primero el instalador.")
            sys.exit(1)

def explicar_y_ejecutar(descripcion, comando):
    """Muestra una explicación didáctica antes de ejecutar el comando en el sistema."""
    print(f"\n[EXPLICACIÓN]: {descripcion}")
    print(f"[EJECUTANDO]: {' '.join(comando)}")
    time.sleep(1.2) # Pausa para lectura en tiempo real
    
    try:
        resultado = subprocess.run(comando, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return resultado.stdout
    except subprocess.CalledProcessError as e:
        print(f"[-] Error al ejecutar el comando. Detalles: {e.stderr.strip()}")
        return None

def escanear_tarjetas():
    """Mapea las interfaces inalámbricas conectadas al equipo en tiempo real."""
    salida = explicar_y_ejecutar(
        "Consultamos el estado de las interfaces usando 'iw dev' para identificar nombres y modos operativos.",
        ["iw", "dev"]
    )
    
    if not salida:
        return []

    tarjetas = []
    bloques = salida.split("phy#")
    
    for bloque in bloques[1:]:
        lineas = bloque.split("\n")
        phy_id = lineas[0].split()[0]
        interfaz = None
        ssid = None
        tipo = None
        
        for linea in lineas:
            if "Interface" in linea:
                interfaz = linea.split()[1]
            if "ssid" in linea:
                ssid = " ".join(linea.split()[1:])
            if "type" in linea:
                tipo = linea.split()[1]
                
        if interfaz:
            tarjetas.append({
                "phy": f"phy{phy_id}",
                "interfaz": interfaz,
                "ssid": ssid,
                "tipo": tipo
            })
    return tarjetas

def verificar_soporte_monitor(phy_device):
    """Revisa si el chip de la antena admite modo monitor."""
    salida = explicar_y_ejecutar(
        f"Interrogamos las capacidades físicas de '{phy_device}' mediante 'iw phy info' para validar el soporte de fábrica.",
        ["iw", phy_device, "info"]
    )
    if salida and "monitor" in salida.lower():
        print(f"[+] ¡Hardware '{phy_device}' compatible con modo monitor!")
        return True
    print(f"[-] Alerta: El hardware '{phy_device}' NO reporta soporte para monitor.")
    return False

def cambiar_a_modo_monitor(interfaz):
    """Aplica los cambios de red para activar el modo monitor."""
    print("\n" + "-"*50)
    print(f"  ACTIVANDO MODO MONITOR EN: {interfaz}")
    print("-"*50)

    explicar_y_ejecutar(f"Desactivamos temporalmente la interfaz '{interfaz}' para poder modificar sus parámetros de bajo nivel.", ["ip", "link", "set", interfaz, "down"])
    explicar_y_ejecutar(f"Cambiamos el tipo operativo de '{interfaz}' de modo estación (Managed) a modo escucha (Monitor).", ["iw", interfaz, "set", "monitor", "control"])
    explicar_y_ejecutar(f"Volvemos a levantar la interfaz '{interfaz}' para empezar a capturar paquetes del aire.", ["ip", "link", "set", interfaz, "up"])

def restaurar_modo_managed(interfaz):
    """Devuelve la interfaz a modo normal de navegación."""
    print("\n" + "-"*50)
    print(f"  RESTAURANDO MODO NORMAL (MANAGED) EN: {interfaz}")
    print("-"*50)

    explicar_y_ejecutar(f"Apagamos la interfaz '{interfaz}' para retirar de forma segura el modo monitor.", ["ip", "link", "set", interfaz, "down"])
    explicar_y_ejecutar(f"Reconfiguramos '{interfaz}' de vuelta a su modo de conexión estándar (Managed).", ["iw", interfaz, "set", "type", "managed"])
    explicar_y_ejecutar(f"Levantamos la interfaz '{interfaz}' para dejarla disponible para el gestor de redes.", ["ip", "link", "set", interfaz, "up"])

def restaurar_todo_el_sistema():
    """Busca tarjetas en modo monitor, las normaliza y levanta el internet."""
    print("\n" + "="*60)
    print(" FASE DE RESTAURACIÓN COMPLETA Y RECONEXIÓN A INTERNET")
    print("="*60)
    
    tarjetas = escanear_tarjetas()
    modificadas = 0
    
    for t in tarjetas:
        if t['tipo'] == 'monitor':
            restaurar_modo_managed(t['interfaz'])
            modificadas += 1
            
    if modificadas == 0:
        print("\n[*] No se encontraron tarjetas operando en modo monitor.")
    else:
        print(f"\n[+] Se restauraron {modificadas} interfaz(ces) al modo normal (Managed).")

    explicar_y_ejecutar(
        "Reiniciamos el servicio 'NetworkManager' para forzar al sistema a escanear los canales de Wi-Fi y reconectarse a internet.",
        ["systemctl", "restart", "NetworkManager"]
    )
    print("\n[+] Antenas en estado normal y servicio de internet restablecido.")

def flujo_activacion_monitor():
    """Lógica inteligente de asignación de roles para las tarjetas de red."""
    print("\n" + "="*60)
    print(" DETECCIÓN Y ASIGNACIÓN DE HARDWARE")
    print("="*60)
    tarjetas = escanear_tarjetas()
    
    if not tarjetas:
        print("[-] Error crítico: No se detectó ninguna tarjeta inalámbrica.")
        return
        
    print(f"\n[+] Análisis: Se detectaron {len(tarjetas)} tarjeta(s):")
    for t in tarjetas:
        conexion = f"Conectada a la red Wi-Fi: [{t['ssid']}]" if t['ssid'] else "Desconectada / Libre"
        print(f"  • {t['interfaz']} ({t['phy']}) -> Modo: {t['tipo']} | {conexion}")

    tarjeta_objetivo = None
    modo_monousuario = False

    # Si hay 2 o más, dejamos quieta la que tiene internet
    if len(tarjetas) >= 2:
        tarjeta_sistema = None
        for t in tarjetas:
            if t['ssid'] is not None:
                tarjeta_sistema = t
                break
        for t in tarjetas:
            if t != tarjeta_sistema:
                tarjeta_objetivo = t
                break
        if tarjeta_sistema and tarjeta_objetivo:
            print(f"\n[+] Escenario Doble Tarjeta: Mantendremos internet en '{tarjeta_sistema['interfaz']}' y usaremos '{tarjeta_objetivo['interfaz']}' para monitor.")
        else:
            tarjeta_objetivo = tarjetas[1]
            print(f"\n[*] Múltiples libres. Seleccionando secundaria: {tarjeta_objetivo['interfaz']}")
    else:
        tarjeta_objetivo = tarjetas[0]
        modo_monousuario = True
        print(f"\n[!] ADVERTENCIA: Solo hay una tarjeta disponible ({tarjeta_objetivo['interfaz']}). Perderás internet temporalmente.")

    if not verificar_soporte_monitor(tarjeta_objetivo['phy']):
        print("[-] La tarjeta seleccionada no admite este modo.")
        return

    if modo_monousuario:
        if input(f" ¿Deseas poner tu ÚNICA tarjeta ({tarjeta_objetivo['interfaz']}) en modo monitor? (s/n): ").strip().lower() != 's':
            print("[-] Cancelado.")
            return

    cambiar_a_modo_monitor(tarjeta_objetivo['interfaz'])
    
    print("\n" + "="*60)
    print(" COMPROBACIÓN FINAL")
    print("="*60)
    escanear_tarjetas()
    print("\n[+] Modo monitor activo con éxito.")

def main():
    verificar_root()
    comprobar_herramientas()
    
    # Firma visual oficial JAM (La J vestida con saco de hacker)
    logo_jam = """
         .---.        ____     _       _       _ 
        /     \\      |____ |  / \\     | \\     / |
       |  ___  |         | | / _ \\    |  \\   /  |
       | /   \\ |         | |/ /_\\ \\   |   \\_/   |
       | | U | |     ___ | / ___   \\  | |\\_/| | |
       | \\___/ |    |____|/_/     \\_\\ |_|   |_|
        \\     /     
         `---'       [ JAM - CONTROL DE INTERFACES ]
    """
    
    while True:
        os.system('clear')
        print(logo_jam)
        
        print("="*60)
        print("           MENU PRINCIPAL DE CONTROL DE RED Wi-Fi")
        print("="*60)
        print(" [1] Activar Modo Monitor (Detección automática inteligente)")
        print(" [2] Desactivar Modo Monitor y Volver a Internet Normal")
        print(" [3] Salir al Panel Maestro")
        print("="*60)
        
        opcion = input("Selecciona una opción (1-3): ").strip()
        
        if opcion == "1":
            flujo_activacion_monitor()
            input("\nPresione [Enter] para continuar...")
        elif opcion == "2":
            restaurar_todo_el_sistema()
            input("\nPresione [Enter] para continuar...")
        elif opcion == "3":
            print("\n[*] Retornando al panel central. ¡Buenas auditorías!")
            break
        else:
            print("[-] Opción inválida. Digita 1, 2 o 3.")
            time.sleep(1.2)

if __name__ == "__main__":
    main()