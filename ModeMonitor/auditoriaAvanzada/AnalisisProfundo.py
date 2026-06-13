#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import sys
import os
import time
import re

def verificar_root():
    """Garantiza privilegios de root para escaneos SYN, lectura de interfaces e inyección inalámbrica."""
    if os.getuid() != 0:
        print("[-] Error: Este módulo de auditoría avanzada requiere privilegios de root.")
        sys.exit(1)

def preparar_directorios():
    """Crea la estructura de carpetas organizadas para los entregables del cliente."""
    dir_actual = os.path.dirname(os.path.abspath(__file__))
    dir_handshakes = os.path.join(dir_actual, "handshakes_visualizados")
    dir_reportes = os.path.join(dir_actual, "reportes_clientes")
    
    os.makedirs(dir_handshakes, exist_ok=True)
    os.makedirs(dir_reportes, exist_ok=True)
    
    return dir_handshakes, dir_reportes

def obtener_segmento_red(modo):
    """Interroga al sistema operativo usando 'ip route' para deducir los direccionamientos."""
    try:
        resultado = subprocess.run(["ip", "route"], stdout=subprocess.PIPE, text=True, check=True)
        lineas = resultado.stdout.splitlines()
        
        if modo == "ap":
            print("[*] Rastreando el direccionamiento de la Zona Wi-Fi instalada...")
            for linea in lineas:
                if "kernel scope link" in linea and "default" not in linea:
                    return linea.split()[0]
                    
        elif modo == "sistema":
            print("[*] Rastreando el direccionamiento de la red Wi-Fi predeterminada...")
            for linea in lineas:
                if "default via" in linea:
                    partes = linea.split()
                    if "dev" in partes:
                        idx_dev = partes.index("dev")
                        interfaz_default = partes[idx_dev + 1]
                        for l2 in lineas:
                            if interfaz_default in l2 and "kernel scope link" in l2:
                                return l2.split()[0]
    except Exception as e:
        print(f"[-] No se pudo autodetectar el segmento. Detalle: {e}")
    return None

def formatear_reporte_legible(archivo_nmap, archivo_salida, tipo_red, segmento):
    """
    Parsea la salida cruda de Nmap para construir un reporte ejecutivo
    altamente legible, limpio y estético para el cliente final.
    """
    if not os.path.exists(archivo_nmap):
        return

    with open(archivo_nmap, 'r', encoding='utf-8', errors='ignore') as f:
        contenido = f.read()

    # Extracción de bloques de hosts detectados
    hosts = contenido.split("Nmap scan report for ")
    
    reporte_formateado = []
    reporte_formateado.append("=" * 80)
    reporte_formateado.append("        INFORME EJECUTIVO DE AUDITORÍA DE SEGURIDAD DE RED")
    reporte_formateado.append("=" * 80)
    reporte_formateado.append(f"Fecha de Análisis : {time.strftime('%Y-%m-%d %H:%M:%S')}")
    reporte_formateado.append(f"Entorno Evaluado  : {tipo_red.upper()}")
    reporte_formateado.append(f"Segmento de Red   : {segmento}")
    reporte_formateado.append("Estado General    : Evaluación de Infraestructura Completada")
    reporte_formateado.append("-" * 80)
    reporte_formateado.append("\nRESUMEN DE DISPOSITIVOS DETECTADOS E INFRAESTRUCTURA CORRIENTE:\n")

    contador_hosts = 0
    for host_bloque in hosts[1:]:
        lineas = host_bloque.splitlines()
        if not lineas:
            continue
            
        contador_hosts += 1
        info_host = lineas[0]
        ip_actual = info_host.split()[-1].replace("(", "").replace(")", "")
        
        os_detectado = "No determinado (Filtrado o Protegido)"
        puertos = []
        vulnerabilidades = []

        # Recorrer las líneas internas del dispositivo para clasificar la información
        for linea in lineas:
            if "OS details:" in linea:
                os_detectado = linea.replace("OS details:", "").strip()
            elif "Running:" in linea and os_detectado == "No determinado (Filtrado o Protegido)":
                os_detectado = linea.replace("Running:", "").strip()
            elif "/tcp" in linea or "/udp" in linea:
                if "open" in linea:
                    puertos.append(linea.strip())
            elif "| " in linea and ("CVE-" in linea or "VULNERABLE" in linea or "SSLV2" in linea):
                vulnerabilidades.append(linea.strip())

        # Estructura visual limpia del dispositivo para el cliente
        reporte_formateado.append(f" [{contador_hosts}] DISPOSITIVO IDENTIFICADO: {ip_actual}")
        reporte_formateado.append(f"     • Sistema Operativo Estimado : {os_detectado}")
        
        # Tabla de puertos abiertos
        if puertos:
            reporte_formateado.append("     • Servicios y Puertos Abiertos Detectados:")
            reporte_formateado.append("       " + "-" * 55)
            reporte_formateado.append("       | PUERTO/PROTO | ESTADO | SERVICIO  | VERSIÓN")
            reporte_formateado.append("       " + "-" * 55)
            for p in puertos:
                reporte_formateado.append(f"       | {p}")
            reporte_formateado.append("       " + "-" * 55)
        else:
            reporte_formateado.append("     • Servicios y Puertos Abiertos : Ninguno detectado de forma pública.")

        # Resumen ejecutivo de debilidades encontradas
        if vulnerabilidades:
            reporte_formateado.append("     • ALERTA: Brechas o Vulnerabilidades Identificadas:")
            for v in vulnerabilidades[:8]: # Limitamos para no saturar al cliente, mostrando lo crítico
                reporte_formateado.append(f"       [!] {v}")
        else:
            reporte_formateado.append("     • Estado de Parcheo/Fallos     : No se evidenciaron brechas críticas inmediatas.")
        
        reporte_formateado.append("\n" + "." * 60 + "\n")

    reporte_formateado.append("=" * 80)
    reporte_formateado.append("        FIN DEL REPORTE - RECOMENDACIÓN: ACTUALIZAR SERVICIOS OBSOLETOS")
    reporte_formateado.append("=" * 80)

    # Escribir el informe legible final
    with open(archivo_output_limpio, 'w', encoding='utf-8') as out:
        out.write("\n".join(reporte_formateado))

def ejecutar_auditoria_completa(segmento, tipo_red, dir_reportes):
    """Lanza el escaneo nativo y posteriormente invoca al formateador estético."""
    if not segmento:
        print("[-] Error: No se pudo determinar el segmento de red objetivo.")
        input("\nPresione [Enter] para continuar...")
        return

    nombre_limpio = segmento.replace("/", "_")
    archivo_nmap_raw = os.path.join(dir_reportes, f"raw_nmap_{tipo_red}_{nombre_limpio}.log")
    global archivo_output_limpio
    archivo_output_limpio = os.path.join(dir_reportes, f"INFORME_CLIENTE_{tipo_red.upper()}_{nombre_limpio}.txt")

    print("\n" + "="*75)
    print(f" EJECUTANDO DIAGNÓSTICO MAESTRO SOBRE EL SEGMENTO: {segmento}")
    print("="*75)
    time.sleep(1.0)

    # Lanzamos el comando robusto de ingeniería de red
    comando = ["nmap", "-O", "-sV", "--script", "vuln,auth", "-v", "-oN", archivo_nmap_raw, segmento]
    
    try:
        subprocess.run(comando, check=True)
        print("\n[*] Procesando datos capturados para generar la vista del cliente...")
        formatear_reporte_legible(archivo_nmap_raw, archivo_output_limpio, tipo_red, segmento)
        
        # Eliminamos el archivo bruto de nmap para mantener la carpeta limpia solo con informes ejecutivos
        if os.path.exists(archivo_nmap_raw):
            os.remove(archivo_nmap_raw)
            
        print("\n" + "="*75)
        print("[+] ¡ANÁLISIS COMPLETADO E INDEXADO EXITOSAMENTE!")
        print(f"[+] El Reporte Estructurado para el Cliente se guardó en:")
        print(f"    {archivo_output_limpio}")
        print("="*75)
    except KeyboardInterrupt:
        print("\n[!] Escaneo cancelado. Generando reporte con los datos obtenidos hasta el momento...")
        formatear_reporte_legible(archivo_nmap_raw, archivo_output_limpio, tipo_red, segmento)
    except Exception as e:
        print(f"[-] Ocurrió una novedad durante el proceso: {e}")
        
    input("\nPresione [Enter] para continuar...")

def capturar_handshake(dir_handshakes):
    """Captura el saludo WPA guardándolo con la nomenclatura y estructura ordenada solicitada."""
    print("\n" + "="*75)
    print("         MÓDULO DE CAPTURA DE HANDSHAKE (PROCESO EN DOS ETAPAS)")
    print("="*75)
    
    interfaz = input("Introduce tu interfaz en modo monitor (ej. wlan1): ").strip()
    if not interfaz: return

    ssid_red = input("Introduce el Nombre de la Red (SSID, ej. Wi-Fi_Hogar): ").strip().replace(" ", "_")
    bssid_ap = input("Introduce el BSSID (Dirección MAC del Router objetivo): ").strip()
    canal_ap = input("Introduce el Canal de la red (ej. 1, 6, 11): ").strip()
    mac_cliente = input("Introduce la MAC del dispositivo cliente (ej. Celular conectado): ").strip()
    
    if not ssid_red or not bssid_ap or not canal_ap or not mac_cliente:
        print("[-] Error: Todos los campos (incluyendo el dispositivo cliente) son requeridos para la nomenclatura.")
        input("\nPresione [Enter] para continuar...")
        return

    # Construimos el nombre exacto solicitado: handshake-[SSID]-[MAC_DISPOSITIVO]
    nombre_archivo = f"handshake-{ssid_red}-{mac_cliente.replace(':', '')}"
    ruta_captura_completa = os.path.join(dir_handshakes, nombre_archivo)

    print("\n[EXPLICACIÓN PASO 1 - Escucha Inalámbrica Dirigida]:")
    print(f"Abriremos una consola flotante para capturar los paquetes en el canal {canal_ap}.")
    print(f"El archivo base se guardará en la carpeta ordenada como: {nombre_archivo}-01.cap")
    
    comando_sniffer = ["airodump-ng", "--bssid", bssid_ap, "-c", canal_ap, "-w", ruta_captura_completa, interfaz]
    comando_xterm = ["xterm", "-geometry", "90x20", "-hold", "-e"] + comando_sniffer
    
    try:
        subprocess.Popen(comando_xterm, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("[+] Ventana flotante de monitorización desplegada.")
    except Exception as e:
        print(f"[-] No se pudo inicializar xterm: {e}")
        return

    print("\n[EXPLICACIÓN PASO 2 - Inyección Activa]:")
    print(f"Enviaremos tramas de desautenticación selectivas al cliente '{mac_cliente}' para forzar")
    print("su reconexión inmediata y capturar las llaves criptográficas de forma segura.")
    input("\nPresiona [Enter] para inyectar los paquetes de desautenticación...")
    
    comando_ataque = ["aireplay-ng", "-0", "15", "-a", bssid_ap, "-c", mac_cliente, interfaz]
    
    try:
        subprocess.run(comando_ataque, check=True)
        print("\n[+] Ráfaga completada.")
        print("[*] Cuando visualices el Handshake en la parte superior de la ventana flotante,")
        print(f"[+] El archivo limpio estará listo para análisis en: {dir_handshakes}/")
    except Exception as e:
        print(f"[-] Error en el proceso de inyección inalámbrica: {e}")

    input("\nPresione [Enter] para volver al menú...")

def main():
    verificar_root()
    dir_handshakes, dir_reportes = preparar_directorios()
    
    # Firma visual oficial JAM (La J vestida con saco de hacker)
    logo_jam = """
         .---.        ____     _       _       _ 
        /     \\      |____ |  / \\     | \\     / |
       |  ___  |         | | / _ \\    |  \\   /  |
       | /   \\ |         | |/ /_\\ \\   |   \\_/   |
       | | U | |     ___ | / ___   \\  | |\\_/| | |
       | \\___/ |    |____|/_/     \\_\\ |_|   |_|
        \\     /     
         `---'       [ JAM - AUDITORÍA AVANZADA ]
    """
    
    while True:
        os.system('clear')
        print(logo_jam)
        
        print("="*75)
        print("        AUDITORÍA AVANZADA: ENTORNO ACADÉMICO Y EXPORTACIÓN ENTREGABLE")
        print("="*75)
        print(" [1] Auditar entorno de la ZONA WI-FI GRATIS desplegada")
        print("     (Genera Informe Ejecutivo Limpio para los clientes del AP virtual)")
        print("\n [2] Auditar entorno de la RED WI-FI PREDETERMINADA del sistema")
        print("     (Genera Informe Estructurado de los equipos de la red local)")
        print("\n [3] Capturar Handshake de Red Externa y Guardar en Historial")
        print("     (Almacena en /handshakes_visualizados/ con la nomenclatura limpia)")
        print("\n [4] Volver al Panel Unificado Principal (JAM)")
        print("="*75)
        
        opcion = input("Selecciona una opción de trabajo (1-4): ").strip()
        
        if opcion == "1":
            segmento = obtener_segmento_red("ap")
            if segmento:
                ejecutar_auditoria_completa(segmento, "zona_wifi_gratis", dir_reportes)
            else:
                print("[-] Interfaz virtual no detectada. Active el AP en el Módulo 3 primero.")
                time.sleep(3)
        elif opcion == "2":
            segmento = obtener_segmento_red("sistema")
            if segmento:
                ejecutar_auditoria_completa(segmento, "wifi_predeterminado", dir_reportes)
            else:
                print("[-] Interfaz predeterminada no encontrada. Revise su conexión de red.")
                time.sleep(3)
        elif opcion == "3":
            capturar_handshake(dir_handshakes)
        elif opcion == "4":
            break
        else:
            print("[-] Opción inválida.")
            time.sleep(1.2)

if __name__ == "__main__":
    main()