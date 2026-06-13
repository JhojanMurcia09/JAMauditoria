#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import subprocess
import time

def verificar_root():
    """Garantiza privilegios elevados antes de arrancar la interfaz unificada."""
    if os.getuid() != 0:
        print("[-] Error: Esta suite unificada requiere privilegios de root.")
        print("[*] Ejecútala con: sudo python3 useAll.py")
        sys.exit(1)

def ejecutar_script_hijo(ruta_relativa):
    """
    Localiza el script secundario de forma dinámica basándose en la posición 
    de 'useAll.py' y lo ejecuta heredando el entorno de terminal actual.
    """
    directorio_raiz = os.path.dirname(os.path.abspath(__file__))
    ruta_absoluta = os.path.join(directorio_raiz, ruta_relativa)
    
    if not os.path.exists(ruta_absoluta):
        print(f"\n[-] Error de estructura: No se encontró el script en: {ruta_absoluta}")
        print("[*] Revisa que no hayas cambiado los nombres de las carpetas o archivos.")
        input("\nPresiona [Enter] para continuar...")
        return

    try:
        # Ejecutamos el script hijo compartiendo la misma consola interactiva
        subprocess.run(["python3", ruta_absoluta], check=True)
    except KeyboardInterrupt:
        print("\n[*] Volviendo al panel unificado principal (Interrupción por usuario).")
        time.sleep(1.0)
    except Exception as e:
        print(f"[-] Novedad al ejecutar el módulo secundario: {e}")
        input("\nPresiona [Enter] para continuar...")

def main():
    verificar_root()
    
    # Identidad visual oficial JAM (J vestida con saco de hacker)
    logo_jam = """
         .---.        ____     _       _       _ 
        /     \\      |____ |  / \\     | \\     / |
       |  ___  |         | | / _ \\    |  \\   /  |
       | /   \\ |         | |/ /_\\ \\   |   \\_/   |
       | | U | |     ___ | / ___   \\  | |\\_/| | |
       | \\___/ |    |____|/_/     \\_\\ |_|   |_|
        \\     /     
         `---'       [ JAM - PANEL CENTRAL OPERATIVO ]
    """
    
    while True:
        # Limpiamos pantalla para mantener la estética profesional en la terminal
        os.system('clear')
        
        # Despliegue del logo de la marca
        print(logo_jam)
        
        print("="*68)
        print("         SUITE UNIFICADA DE CONTROL INALÁMBRICO & ENTORNO")
        print("="*68)
        print(" [1] Lanzar Módulo: Instalador / Verificador de Dependencias")
        print(" [2] Lanzar Módulo: Activador / Desactivador de Modo Monitor")
        print(" [3] Lanzar Módulo: Zona Wi-Fi, Auditoría y Control de Clientes")
        print(" [4] Lanzar Módulo: Auditoría Avanzada (OS, Versiones y Fallos CVE)")
        print(" [5] Lanzar Módulo: Escáner de Redes en Tiempo Real (Modo Monitor)")
        print(" [6] Salir de la Suite Completa")
        print("="*68)

        opcion = input("Selecciona el entorno de trabajo (1-6): ").strip()

        if opcion == "1":
            ejecutar_script_hijo("Instalame.py")
        elif opcion == "2":
            ejecutar_script_hijo("ActivarModo/Jhscript.py")
        elif opcion == "3":
            ejecutar_script_hijo("ZonaWifi/CrearCobertura.py")
        elif opcion == "4":
            ejecutar_script_hijo("auditoriaAvanzada/AnalisisProfundo.py")
        elif opcion == "5":
            ejecutar_script_hijo("EscaneoEnVivo/MonitorEnTiempoReal.py")
        elif opcion == "6":
            print("\n[*] Desconectando suite JAM. ¡Buenas auditorías!")
            break
        else:
            print("[-] Selección inválida. Por favor, digita un número entre 1 y 6.")
            time.sleep(1.5)

if __name__ == "__main__":
    main()