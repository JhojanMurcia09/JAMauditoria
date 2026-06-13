#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import sys
import os
import shutil
import time

def verificar_root():
    """Garantiza que el script se ejecute con los privilegios necesarios."""
    if os.getuid() != 0:
        print("[-] Error: Este script requiere privilegios de root.")
        print("[*] Ejecútalo con: sudo python3 MonitorEnTiempoReal.py")
        sys.exit(1)

def comprobar_herramientas():
    """Verifica que los binarios necesarios estén instalados."""
    herramientas = ["airodump-ng", "xterm", "iw"]
    for cmd in herramientas:
        if shutil.which(cmd) is None:
            print(f"[-] Error crítico: No se encontró el comando '{cmd}'.")
            print(f"[*] Por favor, ejecuta el Instalador (Módulo 1) para corregir esto.")
            sys.exit(1)

def escanear_interfaces_monitor():
    """Busca interfaces que ya estén en modo monitor."""
    try:
        resultado = subprocess.run(["iw", "dev"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        salida = resultado.stdout
    except Exception:
        return []

    interfaces = []
    bloques = salida.split("phy#")
    for bloque in bloques[1:]:
        lineas = bloque.split("\n")
        interfaz = None
        tipo = None
        for linea in lineas:
            if "Interface" in linea:
                interfaz = linea.split()[1]
            if "type" in linea:
                tipo = linea.split()[1]
        if interfaz and tipo == "monitor":
            interfaces.append(interfaz)
    return interfaces

def main():
    verificar_root()
    comprobar_herramientas()

    logo_jam = """
         .---.        ____     _       _       _
        /     \\      |____ |  / \\     | \\     / |
       |  ___  |         | | / _ \\    |  \\   /  |
       | /   \\ |         | |/ /_\\ \\   |   \\_/   |
       | | U | |     ___ | / ___   \\  | |\\_/| | |
       | \\___/ |    |____|/_/     \\_\\ |_|   |_|
        \\     /
         `---'       [ JAM - MONITOR EN TIEMPO REAL ]
    """

    while True:
        os.system('clear')
        print(logo_jam)
        print("="*65)
        print("       SISTEMA DE VISUALIZACIÓN DE REDES EN TIEMPO REAL")
        print("="*65)

        interfaces_monitor = escanear_interfaces_monitor()

        if not interfaces_monitor:
            print("\n[!] No se detectaron interfaces en modo monitor.")
            print("[*] Por favor, ve al Módulo 2 (Activar Modo Monitor) primero.")
            print("\n [1] Volver al Panel Maestro")
            print(" [2] Salir")
        else:
            print(f"\n[+] Interfaces en modo monitor detectadas: {len(interfaces_monitor)}")
            for i, iface in enumerate(interfaces_monitor, 1):
                print(f"  [{i}] {iface}")

            print("\n" + "="*65)
            print(" [1] Lanzar Escáner en Tiempo Real (airodump-ng)")
            print(" [2] Volver al Panel Maestro")
            print("="*65)

        opcion = input("\nSelecciona una opción: ").strip()

        if not interfaces_monitor:
            if opcion == "1":
                # En este caso, el 1 es volver al panel maestro según la lista arriba
                break
            elif opcion == "2":
                sys.exit(0)
            continue

        if opcion == "1":
            try:
                idx = int(input("\nSelecciona el número de la interfaz a monitorear: ").strip()) - 1
                if 0 <= idx < len(interfaces_monitor):
                    iface = interfaces_monitor[idx]
                    print(f"\n[*] Desplegando ventana de monitorización para {iface}...")

                    # Ejecutamos airodump-ng en una xterm independiente
                    # -hold mantiene la ventana abierta si el proceso falla
                    comando_xterm = ["xterm", "-geometry", "100x25", "-title", f"JAM - MONITOREO REAL-TIME ({iface})", "-e", "airodump-ng", iface]

                    subprocess.Popen(comando_xterm, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    print("[+] Ventana de escaneo lanzada con éxito.")
                    time.sleep(2)
                else:
                    print("[-] Índice fuera de rango.")
            except ValueError:
                print("[-] Por favor, introduce un número válido.")
            input("\nPresione [Enter] para continuar...")
        elif opcion == "2":
            break
        else:
            print("[-] Opción inválida.")
            time.sleep(1)

if __name__ == "__main__":
    main()
