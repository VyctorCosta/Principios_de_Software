import os
import time
import multiprocessing
import psutil
from tqdm import tqdm

# Forçando o programa a executar no CPU 0 para não precisar alterar manualmente via comando taskset.
os.sched_setaffinity(0, {0})

compute_value = int(100_000_000)
shared_value = multiprocessing.Value('i', 0) # Criação de um valor que será compartilhado entre a função de processo e a função de ajuste do nice.
start = time.time()


# Função de longa duração com um processo pesado
def process_value(shared_value):
  for i in tqdm(range(1, compute_value + 1)):
    shared_value.value = i
    _ = i ** 2

# Função que ajusta o valor do nice do processo computacional definindo se ele executa mais rápido ou lento para atingir os 60 segundos totais.
def print_value(shared_value, pid_process):
  sleep_time = 0.5
  seconds = 1

  compute_process = psutil.Process(pid_process) # Capturando o compute process para conseguir alterar o seu nice respectivo.
  compute_process_nice = compute_process.nice() # Pegando o nice inicial do processo

  while (shared_value.value < compute_value):
    try:
      time.sleep(sleep_time)

      if (shared_value.value < (compute_value * (seconds / 60))):
        compute_process_nice -= 1
        compute_process.nice(compute_process_nice) # Alterando o nice do processo para o novo valor (diminuindo o nice)
      elif (shared_value.value == compute_value * (seconds / 60)):
        continue
      else:
        compute_process_nice += 1
        compute_process.nice(compute_process_nice) # Alterando o nice do processo para o novo valor (aumentando o nice)

      seconds += sleep_time
    except:
      break


compute_process = multiprocessing.Process(target=process_value, args=(shared_value,)) # Criando o processo para computar os valores
compute_process.start()

control_process = multiprocessing.Process(target=print_value, args=(shared_value, compute_process.pid,)) # Criando o processo para controlar o valor do nice (passando o pid do processo de computar pelo parâmetro)
control_process.start()

compute_process.join()
control_process.join()


finish = time.time()

print(f"Tempo de execução: {((finish - start) * 1000):.6f} ms")
