#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import sys
import os
import time
import shutil

def verificar_root():
    """Garantiza que el script se ejecute con los privilegios necesarios de superusuario."""
    if os.getuid() != 0:
        print("[-] Error: Este script requiere privilegios de root.")
        print("[*] Ejecútalo con: sudo python3 <nombre_del_archivo>.py")
        sys.exit(1)

def comprobar_herramientas():
    """Verifica que los binarios necesarios estén instalados en el sistema."""
    herramientas = ["iw", "ip", "hostapd", "dnsmasq", "xterm", "nmap", "iptables", "nmcli"]
    for cmd in herramientas:
        if shutil.which(cmd) is None:
            print(f"[-] Error crítico: No se encontró el comando '{cmd}'.")
            print(f"[*] Instálalo usando tu gestor de paquetes (ej. sudo apt install {cmd}).")
            sys.exit(1)

def escanear_tarjetas():
    """Mapea las interfaces inalámbricas conectadas al equipo analizando su modo operativo."""
    try:
        resultado = subprocess.run(["iw", "dev"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        salida = resultado.stdout
    except Exception:
        return []

    tarjetas = []
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
        if interfaz:
            tarjetas.append({"interfaz": interfaz, "tipo": tipo})
    return tarjetas

def autodeteccion_interfaz_ap(iface_internet):
    """Identifica automáticamente una tarjeta Wi-Fi disponible que no sea la que da Internet."""
    tarjetas = escanear_tarjetas()
    tarjetas_disponibles = [t["interfaz"] for t in tarjetas if t["interfaz"] != iface_internet]
    
    if not tarjetas_disponibles:
        return None
    
    if len(tarjetas_disponibles) == 1:
        print(f"[+] Interfaz de emisión seleccionada automáticamente: '{tarjetas_disponibles[0]}'")
        time.sleep(1)
        return tarjetas_disponibles[0]
    
    print(f"\n[*] Interfaces inalámbricas alternativas detectadas ({len(tarjetas_disponibles)}):")
    for i, iface in enumerate(tarjetas_disponibles, 1):
        print(f"  [{i}] {iface}")
    try:
        opc = int(input("\nSelecciona la interfaz para emitir el AP falso: ").strip())
        return tarjetas_disponibles[opc - 1]
    except Exception:
        return None

# Variables globales de control de procesos e interfaces
proceso_hostapd = None
proceso_dnsmasq = None
interfaz_ap_activa = None
interfaz_internet_activa = None

def levantar_infraestructura(ssid, interfaz_ap, interfaz_internet):
    """Configura el entorno de red, aplica el aislamiento, levanta NAT y arranca servicios."""
    global proceso_hostapd, proceso_dnsmasq, interfaz_ap_activa, interfaz_internet_activa
    interfaz_ap_activa = interfaz_ap
    interfaz_internet_activa = interfaz_internet
    
    print(f"\n[+] Pasando '{interfaz_ap}' a modo no-gestionado en NetworkManager para evitar caídas...")
    subprocess.run(["nmcli", "device", "set", interfaz_ap, "managed", "no"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    print("[*] Mitigando colisiones previas de wpa_supplicant...")
    subprocess.run(["killall", "wpa_supplicant"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.5)

    # 1. Archivo temporal hostapd optimizado para compatibilidad de hardware (Evita bucle connect/disconnect)
    ruta_hostapd_conf = "/tmp/hostapd_jam.conf"
    config_hostapd = f"""interface={interfaz_ap}
driver=nl80211
ssid={ssid}
hw_mode=g
channel=6
auth_algs=1
wmm_enabled=1
ieee80211n=1
country_code=CO
ieee80211d=1
ap_max_inactivity=300
"""
    with open(ruta_hostapd_conf, "w") as f:
        f.write(config_hostapd)

    # 2. Escritura del archivo temporal de dnsmasq (DHCP + Log de Consultas)
    ruta_dnsmasq_conf = "/tmp/dnsmasq_jam.conf"
    config_dnsmasq = f"""interface={interfaz_ap}
dhcp-range=192.168.10.10,192.168.10.50,255.255.255.0,12h
dhcp-option=3,192.168.10.1
dhcp-option=6,192.168.10.1
log-queries
log-dhcp
"""
    with open(ruta_dnsmasq_conf, "w") as f:
        f.write(config_dnsmasq)

    print("[*] Levantando direccionamiento IP estático en el segmento de auditoría...")
    subprocess.run(["ip", "link", "set", interfaz_ap, "down"])
    subprocess.run(["ip", "addr", "flush", "dev", interfaz_ap])
    subprocess.run(["ip", "addr", "add", "192.168.10.1/24", "dev", interfaz_ap])
    subprocess.run(["ip", "link", "set", interfaz_ap, "up"])
    time.sleep(1.5)

    # CONFIGURACIÓN DINÁMICA DE REGLAS DE REENVÍO (NAT)
    print(f"[*] Creando puente de red: [{interfaz_ap}] ---> Enrutando hacia Internet por: [{interfaz_internet}]...")
    with open("/proc/sys/net/ipv4/ip_forward", "w") as f:
        f.write("1")
    
    # Limpieza preventiva de iptables para evitar colisiones
    subprocess.run(["iptables", "-F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["iptables", "-t", "nat", "-F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Inyección de cadenas de enmascaramiento de paquetes (Masquerade)
    subprocess.run(["iptables", "-A", "FORWARD", "-i", interfaz_ap, "-o", interfaz_internet, "-j", "ACCEPT"])
    subprocess.run(["iptables", "-A", "FORWARD", "-i", interfaz_internet, "-o", interfaz_ap, "-m", "state", "--state", "ESTABLISHED,RELATED", "-j", "ACCEPT"])
    subprocess.run(["iptables", "-t", "nat", "-A", "POSTROUTING", "-o", interfaz_internet, "-j", "MASQUERADE"])

    # Despliegue de hostapd en ventana externa xterm para monitorear eventos físicos de conexión
    print("[*] Desplegando emisor inalámbrico (hostapd) en ventana flotante...")
    cmd_hostapd = ["xterm", "-geometry", "90x20", "-title", "JAM - EMISOR INALÁMBRICO (HOSTAPD)", "-e", "hostapd", ruta_hostapd_conf]
    proceso_hostapd = subprocess.Popen(cmd_hostapd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(3.0) # Pausa para inicialización del espectro regulado e inyección de Beacons

    # Lanzamiento controlado del backend DHCP/DNS con volcado de registros local
    print("[*] Iniciando servidor DHCP/DNS...")
    cmd_dnsmasq = ["dnsmasq", "-C", ruta_dnsmasq_conf, "-q", "-d"]
    ruta_log_dns = "/tmp/dns_queries.log"
    if os.path.exists(ruta_log_dns):
        os.remove(ruta_log_dns)
    f_log = open(ruta_log_dns, "w")
    
    proceso_dnsmasq = subprocess.Popen(cmd_dnsmasq, stdout=f_log, stderr=f_log)
    print("[+] Entorno operativo desplegado. Monitoreo listo.")
    time.sleep(1)

def apagar_infraestructura():
    """Apaga los procesos de red, limpia las reglas de iptables y devuelve el hardware al sistema."""
    global proceso_hostapd, proceso_dnsmasq, interfaz_ap_activa
    print("\n[*] Desactivando cobertura inalámbrica y limpiando el sistema...")
    
    if proceso_dnsmasq:
        proceso_dnsmasq.terminate()
    if proceso_hostapd:
        proceso_hostapd.terminate()
        
    subprocess.run(["killall", "dnsmasq"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["killall", "hostapd"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    print("[*] Removiendo reglas de enrutamiento y vaciando iptables...")
    subprocess.run(["iptables", "-F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["iptables", "-t", "nat", "-F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    if interfaz_ap_activa:
        subprocess.run(["ip", "link", "set", interfaz_ap_activa, "down"])
        subprocess.run(["ip", "addr", "flush", "dev", interfaz_ap_activa])
        # Re-vinculamos la interfaz a NetworkManager para restaurar el comportamiento normal de la PC
        subprocess.run(["nmcli", "device", "set", interfaz_ap_activa, "managed", "yes"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["systemctl", "restart", "NetworkManager"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        interfaz_ap_activa = None
        
    print("[+] Configuración original del sistema restaurada con éxito.")
    input("\nPresione [Enter] para continuar...")

def mostrar_ips_conectadas():
    """Lee de forma estructurada el archivo de asignaciones de dnsmasq para listar clientes."""
    print("\n" + "-"*75)
    print("         DISPOSITIVOS CONECTADOS ACTIVAMENTE (CONCESIONES DHCP)")
    print("-"*75)
    ruta_leases = "/var/lib/misc/dnsmasq.leases"
    
    if not os.path.exists(ruta_leases) or os.path.getsize(ruta_leases) == 0:
        print("[*] No se registran clientes asociados o solicitando IP en este momento.")
        return []
        
    clientes = []
    with open(ruta_leases, "r") as f:
        lineas = f.readlines()
        
    print(f"{'MAC ADDRESS':<20} {'IP ADDRESS':<18} {'NOMBRE DEL DISPOSITIVO':<25}")
    print("-" * 75)
    for linea in lineas:
        partes = linea.strip().split()
        if len(partes) >= 4:
            mac, ip, nombre = partes[1], partes[2], partes[3]
            print(f"{mac:<20} {ip:<18} {nombre:<25}")
            clientes.append((ip, nombre, mac))
    return clientes

def escanear_perfil_cliente():
    """Automatiza un análisis de servicios rápido y estructurado sobre una IP seleccionada."""
    clientes = mostrar_ips_conectadas()
    if not clientes:
        input("\nPresione [Enter] para continuar...")
        return
        
    target_ip = input("\nIntroduce la dirección IP del cliente a perfilar: ").strip()
    if not target_ip:
        return
        
    print(f"\n[*] Ejecutando reconocimiento de puertos y servicios sobre {target_ip}...")
    try:
        # Analiza los puertos más comunes de forma optimizada y legible
        res = subprocess.run(["nmap", "-sV", "-F", target_ip], stdout=subprocess.PIPE, text=True, timeout=45)
        print("\n" + "="*65)
        print(f" PERFIL TÉCNICO SIMPLIFICADO DE RECONOCIMIENTO: {target_ip}")
        print("="*65)
        print(res.stdout)
    except Exception as e:
        print(f"[-] No se pudo completar el análisis en el tiempo establecido: {e}")
    input("\nPresione [Enter] para continuar...")

def monitorear_consultas_dns():
    """Muestra en flujo continuo las peticiones de dominios que realizan los clientes."""
    print("\n" + "="*70)
    print("      MONITOR DE FLUJO DE TRÁFICO Y SOLICITUDES DNS EN TIEMPO REAL")
    print("      (Presione [Ctrl + C] en cualquier momento para regresar al menú)")
    print("="*70)
    ruta_log_dns = "/tmp/dns_queries.log"
    
    if not os.path.exists(ruta_log_dns):
        print("[-] El archivo de volcado de peticiones no se encuentra inicializado aún.")
        input("\nPresione [Enter] para continuar...")
        return

    try:
        with open(ruta_log_dns, "r") as f:
            f.seek(0, 2) # Ubica el puntero al final del archivo para leer en vivo
            while True:
                linea = f.readline()
                if not linea:
                    time.sleep(0.4)
                    continue
                if "query[" in linea:
                    print(f"[TRÁFICO EN VIVO] {linea.strip()}")
    except KeyboardInterrupt:
        print("\n[*] Monitoreo en vivo finalizado por el operador.")

def menu_gestion_cobertura():
    """Panel de administración una vez la red está en línea."""
    while True:
        os.system('clear')
        print("="*70)
        print("        PANEL MAESTRO DE CONTROL, ANÁLISIS Y MONITOREO DE COBERTURA")
        print("="*70)
        print(" [1] Mostrar IPs y Dispositivos Conectados (DHCP)")
        print(" [2] Analizar Perfil y Puertos Abiertos de un Cliente (Nmap)")
        print(" [3] Monitorear Tráfico y Consultas DNS de Clientes (Tiempo Real)")
        print(" [4] Desactivar Cobertura Inalámbrica y Salir al Menú Principal")
        print("="*70)
        
        opc = input("Selecciona una opción (1-4): ").strip()
        
        if opc == "1":
            mostrar_ips_conectadas()
            input("\nPresione [Enter] para continuar...")
        elif opc == "2":
            escanear_perfil_cliente()
        elif opc == "3":
            monitorear_consultas_dns()
        elif opc == "4":
            apagar_infraestructura()
            break

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
         `---'       [ JAM - COBERTURA UNIFICADA ]
    """
    
    while True:
        os.system('clear')
        print(logo_jam)
        print("="*70)
        print(" [1] Clonar Entorno Inalámbrico Visible con Tráfico de Datos Activo")
        print(" [2] Salir de la Suite")
        print("="*70)
        
        opcion = input("Selecciona una opción (1-2): ").strip()
        
        if opcion == "1":
            print("\n[*] Mapeo rápido de interfaces activas de la máquina:")
            subprocess.run(["ip", "-br", "addr", "show"])
            
            if_internet = input("\nIntroduce la interfaz que provee Internet a tu PC (ej. wlo1): ").strip()
            if not if_internet:
                continue
                
            ssid = input("Introduce el nombre del SSID que vas a clonar (ej. LUKA): ").strip()
            if not ssid:
                continue
                
            # Autodetección inteligente buscando una tarjeta de red inalámbrica libre (tu antena USB)
            if_ap = autodeteccion_interfaz_ap(if_internet)
            if not if_ap:
                print("\n[!] Error: No se encontraron tarjetas Wi-Fi secundarias libres.")
                print("[*] Asegúrate de contar con una antena adicional o estar por cable de red.")
                input("\nPresione [Enter] para continuar...")
                continue
                
            print(f"\n[+] Configuración aprobada: Emisión por [{if_ap}] | Enrutamiento vía [{if_internet}]")
            time.sleep(1.5)
            
            levantar_infraestructura(ssid, if_ap, if_internet)
            menu_gestion_cobertura()
        elif opcion == "2":
            print("\n[*] Saliendo de la Suite JAM. ¡Buen laboratorio!")
            break

if __name__ == "__main__":
    main()