import os
import sys
import glob
import subprocess
import time
import csv
from pathlib import Path

# Diretório de instâncias
instances_dir = "Instances"

# Encontrar todos os arquivos de instância (sem extensão .txt)
instance_files = sorted(glob.glob(os.path.join(instances_dir, "instance_*")))

if not instance_files:
    print(f"Nenhuma instância encontrada em '{instances_dir}'")
    sys.exit(1)

print(f"Encontradas {len(instance_files)} instâncias:")
for f in instance_files:
    print(f"  - {os.path.basename(f)}")


# Tempo alvo acumulado (segundos) por instância
target_seconds = 1.0
# Proteção contra loops infinitos
max_runs = 100000

results_dir = "results"
os.makedirs(results_dir, exist_ok=True)

python_exe = os.path.join(".venv", "Scripts", "python.exe")
script_name = "Strip_packing_MKBL_v04.py"

# Arquivo resumo onde salvaremos quantas rodadas foram necessárias
summary_csv = "runs_to_1s_summary.csv"
if not os.path.exists(summary_csv):
    with open(summary_csv, 'w', newline='') as sc:
        writer = csv.writer(sc)
        writer.writerow(["instance", "runs_needed", "total_time_s", "average_time_s"]) 

for instance_path in instance_files:
    instance_name = os.path.basename(instance_path)
    print(f"\n{'='*60}")
    print(f"Rodando: {instance_name} (até {target_seconds} segundo cumulativo)")
    print(f"{'='*60}")

    cumulative = 0.0
    run_num = 0

    while cumulative < target_seconds and run_num < max_runs:
        run_num += 1

        # Ler o conteúdo do arquivo de instância
        try:
            with open(instance_path, 'r') as f:
                instance_content = f.read()
        except Exception as e:
            print(f"ERRO ao ler {instance_path}: {e}")
            break

        # Executar o script com o conteúdo como stdin e o caminho como argumento
        start = time.perf_counter()
        try:
            print(f"  Rodada {run_num}... ", end="", flush=True)

            result = subprocess.run(
                [python_exe, script_name, instance_path, instance_name],
                input=instance_content,
                capture_output=True,
                text=True,
                timeout=60
            )
            elapsed = time.perf_counter() - start

            # Tentar ler o tempo reportado pelo próprio script no CSV gerado
            csv_time = None
            try:
                # Nome esperado: <instance_name>.csv (p.ex. instance_three_area.csv)
                expected_csv = os.path.join(results_dir, f"{instance_name}.csv")
                candidates = []
                if os.path.exists(expected_csv):
                    candidates = [expected_csv]
                else:
                    candidates = sorted(glob.glob(os.path.join(results_dir, f"{instance_name}*.csv")), key=os.path.getmtime, reverse=True)

                if candidates:
                    csv_file = candidates[0]
                    with open(csv_file, 'r', newline='') as cf:
                        reader = csv.DictReader(cf)
                        rows = list(reader)
                        if rows:
                            last = rows[-1]
                            # Campo no CSV: 'Total Allocation Time (s)'
                            time_field = 'Total Allocation Time (s)'
                            if time_field in last and last[time_field].strip() != '':
                                try:
                                    csv_time = float(last[time_field])
                                except ValueError:
                                    csv_time = None

            except Exception:
                csv_time = None

            # Se conseguimos ler do CSV, acumulamos esse valor; senão acumulamos o wall-clock
            if csv_time is not None:
                cumulative += csv_time
                used_time = csv_time
                source = 'csv'
            else:
                cumulative += elapsed
                used_time = elapsed
                source = 'wall'

            if result.returncode == 0:
                print(f"✓ ({used_time:.6f}s via {source}; wall {elapsed:.4f}s)")
            else:
                print(f"⚠ ({used_time:.6f}s via {source}; wall {elapsed:.4f}s) código: {result.returncode}")
                if result.stderr:
                    print(f"    Erro: {result.stderr[:200]}")

        except subprocess.TimeoutExpired:
            elapsed = time.perf_counter() - start
            cumulative += elapsed
            print(f"✗ TIMEOUT ({elapsed:.4f}s)")
        except Exception as e:
            elapsed = time.perf_counter() - start
            cumulative += elapsed
            print(f"✗ ERRO: {e} ({elapsed:.4f}s)")

    average = cumulative / run_num if run_num else 0.0
    print(f"-> Finalizado: {instance_name} | rodadas: {run_num} | tempo total: {cumulative:.4f}s | média: {average:.6f}s")

    # Salvar resumo para esta instância
    try:
        with open(summary_csv, 'a', newline='') as sc:
            writer = csv.writer(sc)
            writer.writerow([instance_name, run_num, f"{cumulative:.6f}", f"{average:.6f}"])
    except Exception as e:
        print(f"Falha ao gravar resumo: {e}")

print(f"\n{'='*60}")
print(f"✓ Concluído!")
print(f"CSVs gerados:")

# Listar os CSVs criados
csvs = sorted(glob.glob(os.path.join(results_dir, "instance_*.csv")))
for csv in csvs:
    rows = len(open(csv).readlines()) - 1  # Subtrair header
    print(f"  - {csv} ({rows} linhas)")

