import psutil
from datetime import datetime
import time
import pandas as pd
import platform
import os
from random import randint, gauss, uniform
from bucket import upload_file

CODIGO_MAQUINA = "<insira o código da máquina>"

QTD_MAX_LINHAS = 100  # -1 para infinito
SIMULAR_REGRA_NEGOCIO = True
CAPTURAR_PROCESSOS = False

ENVIAR_PARA_BUCKET = True
ENVIAR_PARA_BUCKET_A_CADA_QTD_LINHAS = 20
NOME_BUCKET = "raw-paymetrics"

qtd_linha_atual = 0

nome_arquivo_hardware = f"{datetime.now().strftime("%Y-%m-%d %H-%M-%S")}-{CODIGO_MAQUINA}-hardware.csv"
nome_arquivo_processos = f"{datetime.now().strftime("%Y-%m-%d %H-%M-%S")}-{CODIGO_MAQUINA}-processes.csv"

if not os.path.exists("hardware-csvs"): os.mkdir("hardware-csvs")
if not os.path.exists("processes-csvs") and CAPTURAR_PROCESSOS: os.mkdir("processes-csvs")

while True:
    if qtd_linha_atual >= QTD_MAX_LINHAS and QTD_MAX_LINHAS != -1:
        break

    print(r"""

 ██████╗ █████╗ ██████╗ ████████╗██╗   ██╗██████╗  █████╗    
██╔════╝██╔══██╗██╔══██╗╚══██╔══╝██║   ██║██╔══██╗██╔══██╗   
██║     ███████║██████╔╝   ██║   ██║   ██║██████╔╝███████║   
██║     ██╔══██║██╔═══╝    ██║   ██║   ██║██╔══██╗██╔══██║   
╚██████╗██║  ██║██║        ██║   ╚██████╔╝██║  ██║██║  ██║   
 ╚═════╝╚═╝  ╚═╝╚═╝        ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝   
                                                             
██████╗ ███████╗    ██████╗  █████╗ ██████╗  ██████╗ ███████╗
██╔══██╗██╔════╝    ██╔══██╗██╔══██╗██╔══██╗██╔═══██╗██╔════╝
██║  ██║█████╗      ██║  ██║███████║██║  ██║██║   ██║███████╗
██║  ██║██╔══╝      ██║  ██║██╔══██║██║  ██║██║   ██║╚════██║
██████╔╝███████╗    ██████╔╝██║  ██║██████╔╝╚██████╔╝███████║
╚═════╝ ╚══════╝    ╚═════╝ ╚═╝  ╚═╝╚═════╝  ╚═════╝ ╚══════╝

    """)

    rede_antiga = psutil.net_io_counters()

    time.sleep(5)
    rede_nova = psutil.net_io_counters()

    bytes_enviados = (rede_nova.bytes_sent - rede_antiga.bytes_sent) / 1024 / 1024
    bytes_recebidos = (rede_nova.bytes_recv - rede_antiga.bytes_recv) / 1024 / 1024

    active_processes = len(list(psutil.process_iter(['name'])))

    mac_address = None
    for iface, detalhes in psutil.net_if_addrs().items():
        for espec in detalhes:
            if platform.system() == 'Windows':
                if iface == 'Ethernet' and mac_address is None:
                    mac_address = espec.address
            else:
                if iface.startswith(("eth", "enp", "ens")) and mac_address is None:
                    mac_address = espec.address

    timestamp = time.time()
    data_formatada = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
    data_process_csv = {"datetime": [], "pid": [], "process": [], "username": [], "ram": []}

    if CAPTURAR_PROCESSOS:
        for proc in psutil.process_iter(['pid', 'name', 'username', 'memory_info']):
            data_process_csv['pid'].append(proc.info['pid'])
            data_process_csv['process'].append(proc.info['name'])
            data_process_csv['username'].append(proc.info['username'])
            data_process_csv['ram'].append(proc.info['memory_info'].vms / 1024 / 1024)
            data_process_csv['datetime'].append(data_formatada)

    cpu_percent = psutil.cpu_percent(interval=1)
    ram_percent = psutil.virtual_memory().percent
    disk_percent = psutil.disk_usage('/').percent
    bytes_enviados = round(bytes_enviados, 3)
    bytes_recebidos = round(bytes_recebidos, 3)

    if SIMULAR_REGRA_NEGOCIO:
        frac = qtd_linha_atual / QTD_MAX_LINHAS
        fator_pico = 1 + 4 * (frac ** 2)  # cresce exponencialmente ate 5x
        if randint(0, QTD_MAX_LINHAS // 10) == 0:  # pico surpresa (mander uma certa aleatoriedade)
            fator_pico *= uniform(1.5, 4)

        # aumentando cpu, ram e disco atraves do "frac" e "fator_pico" gerando uma correlação
        cpu_percent = cpu_percent * fator_pico + gauss(0, 5)
        ram_percent = ram_percent * (1 + 0.5 * (frac ** 1.4)) + cpu_percent * 0.1 + gauss(0, 3)
        disk_percent = disk_percent * (1 + 0.3 * (frac ** 1.2)) + gauss(0, 2)

        # rede cresce proporcionalmente ao pico
        bytes_enviados = ((bytes_enviados + 0.1) + fator_pico * (ram_percent*0.1) + (cpu_percent*0.1)) / uniform(1, 3)
        bytes_recebidos = (bytes_recebidos + 0.1) + fator_pico * (ram_percent*0.1) + (cpu_percent*0.1)

        # para que nao passe dos limites (0 - 100)
        cpu_percent = min(100, max(0, cpu_percent))
        ram_percent = min(100, max(0, ram_percent))
        disk_percent = min(100, max(0, disk_percent))
        bytes_enviados = round(bytes_enviados, 3)
        bytes_recebidos = round(bytes_recebidos, 3)
        active_processes += int(qtd_linha_atual * uniform(0.5, 1.2))

    geral = {
        "datetime": [data_formatada],
        "codigo_maquina": [CODIGO_MAQUINA],
        "mac_address": [mac_address],
        "cpu": [cpu_percent],
        "ram": [ram_percent],
        "disco": [disk_percent],
        "mb_enviados": [bytes_enviados],
        "mb_recebidos": [bytes_recebidos],
        "processos_ativos": [active_processes]
    }

    df = pd.DataFrame(geral)
    if CAPTURAR_PROCESSOS:
        df_processes = pd.DataFrame(data_process_csv)

    enviado_para_bucket=False
    try:
        if os.path.exists("hardware-csvs/"+nome_arquivo_hardware):
            df.to_csv("hardware-csvs/"+nome_arquivo_hardware, sep=';', mode='a', index=False, header=False)

            if ENVIAR_PARA_BUCKET and ((qtd_linha_atual+1) % ENVIAR_PARA_BUCKET_A_CADA_QTD_LINHAS == 0):
                print("Enviando para o Bucket...")
                upload_file(file_name="hardware-csvs/"+nome_arquivo_hardware, bucket=NOME_BUCKET, object_name="hardware/"+nome_arquivo_hardware)
                nome_arquivo_hardware = f"{datetime.now().strftime("%Y-%m-%d %H-%M-%S")}-{CODIGO_MAQUINA}-hardware.csv"
                enviado_para_bucket = True
        else:
            df.to_csv("hardware-csvs/"+nome_arquivo_hardware, index=False, sep=';')

        if CAPTURAR_PROCESSOS:
            if os.path.exists("processes-csvs/"+nome_arquivo_processos):
                df_processes.to_csv("processes-csvs/"+nome_arquivo_processos, sep=";", mode="a", index=False, header=False)

                if enviado_para_bucket:
                    enviado_para_bucket = False
                    upload_file(file_name="processes-csvs/"+nome_arquivo_processos, bucket=NOME_BUCKET, object_name="processes/"+nome_arquivo_processos)
                    nome_arquivo_processos = f"{datetime.now().strftime("%Y-%m-%d %H-%M-%S")}-{CODIGO_MAQUINA}-processes.csv"
            else:
                df_processes.to_csv("processes-csvs/"+nome_arquivo_processos, index=False, sep=';')
    except OSError as e:
        print(e)
        print("INSIRA O CÓDIGO DA MÁQUINA CORRETAMENTE!!!")
        break

    qtd_linha_atual += 1
    time.sleep(5)
