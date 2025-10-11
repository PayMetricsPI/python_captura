import psutil, datetime, time, pandas as pd, os, platform
from random import randint, gauss, uniform

CODIGO_MAQUINA = "<insira o codigo da máquina>"
QTD_MAX_LINHAS = 100  # -1 para infinito
SIMULAR_REGRA_NEGOCIO = True
CAPTURAR_PROCESSOS = False

num_cpus = psutil.cpu_count(logical=True)
qtd_linha_atual = 0

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
    data_formatada = datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
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
        if randint(0, QTD_MAX_LINHAS // 10) == 0:  # pico surpresa (mander uma aleatoriedade)
            fator_pico *= uniform(1.5, 3.0)

        # aumentando cpu, ram e disco atraves do "frac" e "fator_pico" gerando uma correlação
        cpu_percent = cpu_percent * fator_pico + gauss(0, 5)
        ram_percent = ram_percent * (1 + 0.5 * (frac ** 1.5)) + cpu_percent * 0.1 + gauss(0, 3)
        disk_percent = disk_percent * (1 + 0.3 * (frac ** 1.2)) + gauss(0, 2)

        # rede cresce proporcionalmente ao pico
        bytes_enviados *= fator_pico * uniform(1.1, 1.5)
        bytes_recebidos *= fator_pico * uniform(1.1, 1.5)

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

    try:
        if os.path.exists(f"{CODIGO_MAQUINA}-hardware.csv"):
            df.to_csv(f"{CODIGO_MAQUINA}-hardware.csv", sep=';', mode='a', index=False, header=False)
        else:
            df.to_csv(f"{CODIGO_MAQUINA}-hardware.csv", index=False, sep=';')

        if CAPTURAR_PROCESSOS:
            if os.path.exists(f"{CODIGO_MAQUINA}-processes.csv"):
                df_processes.to_csv(f"{CODIGO_MAQUINA}-processes.csv", sep=";", mode="a", index=False, header=False)
            else:
                df_processes.to_csv(f"{CODIGO_MAQUINA}-processes.csv", index=False, sep=';')
    except(OSError):
        print("INSIRA O CÓDIGO DA MÁQUINA CORRETAMENTE!!!")
        break

    qtd_linha_atual += 1
    time.sleep(5)
