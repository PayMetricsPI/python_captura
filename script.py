import psutil, datetime, time, pandas as pd, os, platform
from random import randint

CODIGO_MAQUINA="<insira o codigo da máquina>"
QTD_MAX_LINHAS=100 # -1 para infinito
SIMULAR_REGRA_NEGOCIO=True

num_cpus = psutil.cpu_count(logical=True)
qtd_linha_atual = 0

while True:
    if qtd_linha_atual >= QTD_MAX_LINHAS and QTD_MAX_LINHAS != -1:
        break

    print(r"""
              ____            _                         _      
             / ___|__ _ _ __ | |_ _   _ _ __ __ _    __| | ___ 
            | |   / _` | '_ \| __| | | | '__/ _` |  / _` |/ _ \
            | |__| (_| | |_) | |_| |_| | | | (_| | | (_| |  __/
            \____\__,_| .__/_\__|\__,_|_|  \__,_|  \__,_|\___|
             __| | __ |_|__| | ___  ___                       
            / _` |/ _` |/ _` |/ _ \/ __|                      
            | (_| | (_| | (_| | (_) \__ \                      
            \__,_|\__,_|\__,_|\___/|___/""")


    rede_antiga = (psutil.net_io_counters())
    time.sleep(5)
    rede_nova = psutil.net_io_counters()

    bytes_enviados = ((rede_nova.bytes_sent - rede_antiga.bytes_sent) / 1024 / 1024 )
    bytes_recebidos = ((rede_nova.bytes_recv - rede_antiga.bytes_recv) / 1024 / 1024 )

    active_processes = 0
    for proc in psutil.process_iter(['name']):
        active_processes += 1

    mac_address = None
    for itens, detalhes in psutil.net_if_addrs().items():
        for especicacoes in detalhes:
            if platform.system() == 'Windows':
                if itens == 'Ethernet' and mac_address == None:
                    mac_address = especicacoes.address
            else:
                if itens.startswith(("eth", "enp", "ens")) and mac_address == None:
                    mac_address = especicacoes.address
    
    timestamp = time.time()
    data_formatada = datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")

    data_process_csv = {
        "datetime": [],
        "pid": [],
        "process": [],
        "username": [],
        "ram": []
    }

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
        cpu_percent += randint(qtd_linha_atual-3, qtd_linha_atual+3)
        if(cpu_percent < 0): cpu_percent = 0
        if(cpu_percent > 100): cpu_percent = 100

        ram_percent += randint(qtd_linha_atual-3, qtd_linha_atual+3)/2
        if(ram_percent < 0): ram_percent = 0
        if(ram_percent > 100): ram_percent = 100

        disk_percent += randint(qtd_linha_atual-10, qtd_linha_atual+10)
        if(disk_percent < 0): disk_percent = 0
        if(disk_percent > 100): disk_percent = 100

        bytes_enviados += bytes_enviados + qtd_linha_atual/10
        bytes_recebidos += bytes_recebidos + qtd_linha_atual/10

        bytes_enviados = round(bytes_enviados, 3)
        bytes_recebidos = round(bytes_recebidos, 3)

        active_processes += qtd_linha_atual

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
    df_processes = pd.DataFrame(data_process_csv)

    if os.path.exists("DadosHardware.csv"):
        df.to_csv("DadosHardware.csv", sep= ';', mode= 'a', index=False, header=False)
    else:
        df.to_csv("DadosHardware.csv", index=False, sep= ';')

    if os.path.exists("Processos.csv"):
        df_processes.to_csv("Processos.csv", sep=";", mode="a", index=False, header=False)
    else:
        df_processes.to_csv("Processos.csv", index=False, sep=';')

    time.sleep(5)
    qtd_linha_atual+=1

print("Encerrou o monitoramento programado!!!")