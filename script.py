import psutil, datetime, time, pandas as pd, os, platform

num_cpus = psutil.cpu_count(logical=True)

while True:

    print(r"""  ____            _                         _      
 / ___|__ _ _ __ | |_ _   _ _ __ __ _    __| | ___ 
| |   / _` | '_ \| __| | | | '__/ _` |  / _` |/ _ \
| |__| (_| | |_) | |_| |_| | | | (_| | | (_| |  __/
 \____\__,_| .__/_\__|\__,_|_|  \__,_|  \__,_|\___|
  __| | __ |_|__| | ___  ___                       
 / _` |/ _` |/ _` |/ _ \/ __|                      
| (_| | (_| | (_| | (_) \__ \                      
 \__,_|\__,_|\__,_|\___/|___/                      """)


    rede_antiga = (psutil.net_io_counters())
    time.sleep(5)
    rede_nova = psutil.net_io_counters()

    bytes_enviados = ((rede_nova.bytes_sent - rede_antiga.bytes_sent) / 1024 / 1024 )
    bytes_recebidos = ((rede_nova.bytes_recv - rede_antiga.bytes_recv) / 1024 / 1024 )

    active_processes = 0
    for proc in psutil.process_iter(['name']):
        active_processes += 1

    mac_Ethernet = None
    for itens, detalhes in psutil.net_if_addrs().items():
        for especicacoes in detalhes:
            if platform.system() == 'Windows':
                if itens == 'Ethernet' and mac_Ethernet == None:
                    mac_Ethernet = especicacoes.address
            else:
                if itens.startswith(("eth", "enp", "ens")) and mac_Ethernet == None:
                    mac_Ethernet = especicacoes.address
    
    timestamp = time.time()
    data_formatada = datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")

    codigo_maquina="COD004"

    data_process_csv = {
        "timestamp": [],
        "pid": [],
        "process": [],
        "username": [],
        "cpu_percent": [],
        "ram_megabytes": []
    }

    for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_info']):
        data_process_csv['pid'].append(proc.info['pid'])
        # é necessario dividir o consumo em porcentagem pela quantidade de vcpus
        data_process_csv['cpu_percent'].append(proc.cpu_percent(interval=0.1) / num_cpus)
        data_process_csv['process'].append(proc.info['name'])
        data_process_csv['username'].append(proc.info['username'])
        # vms -> virtual memory size
        data_process_csv['ram_megabytes'].append(proc.info['memory_info'].vms / 1024 / 1024)
        data_process_csv['timestamp'].append(data_formatada)


    geral = {
        "datetime": [data_formatada],
        "codigo_maquina": [codigo_maquina],
        "mac_address": [mac_Ethernet],
        "cpu": [psutil.cpu_percent(interval=1)],
        "ram_usada": [psutil.virtual_memory().percent],
        "uso_disco": [(psutil.disk_usage('/').percent)],
        "mb_enviados": [round(bytes_enviados,3)],
        "mb_recebidos": [round(bytes_recebidos,3)],
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
