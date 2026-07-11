import time
import pandas as pd
import os
import sys
import csv

from usefull.verif_func import Minkowski_Sum, check_inside, Minkowski_Sum, segment_intersection, check_inside_cand
from Class.class_polygon import polygon
from Class.class_point import Point
import matplotlib.pyplot as plt
import matplotlib.animation as animation

"""
Nesse algoritmo, iremos desenvolver a heurística bottom-left, de modo a resolver o strip packing problem de maneira rápida e eficaz.
Ainda que não alcance a solução ótima. Ainda sim, de acordo com o artigo 
"""

# Para compilar:
# Get-Content Instances/instance02.txt | python Strip_packing__MKBL.py

def mostrar_animacao(historico, strip_height):
    if not historico:
        print("Nenhum polígono para animar.")
        return

    fig, ax = plt.subplots(figsize=(16, 5))
    
    # Define limites do gráfico baseados nas peças alocadas
    max_x = max([p.x for h in historico for p in h['vertices']]) + 10
    ax.set_xlim(0, max_x)
    ax.set_ylim(0, strip_height + 2)
    ax.set_aspect('equal')
    
    # Linha da altura da faixa
    ax.axhline(y=strip_height, color='r', linestyle='--', label='Strip Height')
    
    # Lista de objetos gráficos (patches)
    patches = []

    def update(frame):
        # Pega os dados da peça no frame atual
        peca = historico[frame]
        v_list = peca['vertices']
        
        # Fecha o polígono para desenhar
        coords = [[v.x, v.y] for v in v_list]
        coords.append(coords[0])
        
        xs, ys = zip(*coords)
        line, = ax.plot(xs, ys, label=f"Tipo {peca['tipo']}")
        patches.append(line)
        return patches

    ani = animation.FuncAnimation(
        fig, update, frames=len(historico), interval=1000, blit=True
    )

    plt.title("Sequência de Alocação - Bottom-Left")
    plt.legend(loc='upper right')
    plt.show()

historico_animacao = []  # Lista para armazenar o histórico de alocações para animação  

polygons = []

limits_x = []
limits_y = []
limits_x.append(0)
limits_y.append(0)

# Cronometra apenas a fase de alocação iterativa.
allocation_start_time = time.perf_counter()

# Configuração Inicial
height = int(input("What is the strip height?\n"))
numbers_p = int(input("How many TYPES of convex polygons?\n"))
num_p = numbers_p

# Tolerância numérica para comparações geométricas
EPSILON = 1e-9

# ================================================
# Definição do nome do arquivo de instância e diretório de resultados
# ================================================

instance_stem = "instance_output"
if len(sys.argv) > 2:
    instance_stem = sys.argv[2]
elif len(sys.argv) > 1:
    instance_stem = os.path.splitext(os.path.basename(sys.argv[1]))[0]

results_dir = "results"
os.makedirs(results_dir, exist_ok=True)

def is_out_of_bounds(candidate, x_min, y_min, y_max, strip_height, epsilon=EPSILON):
    """Valida limites da faixa com tolerância numérica."""
    if candidate.x < (x_min - epsilon):
        return True
    if candidate.y > (strip_height - y_max + epsilon):
        return True
    if candidate.y < (y_min - epsilon):
        return True
    return False

def candidate_better(candidate, current, epsilon=EPSILON):
    """Escolhe o candidato mais à esquerda e, em caso de empate, o mais baixo, com tolerância numérica."""
    if current is None:
        return True
    if candidate.x < (current.x - epsilon):
        return True
    if abs(candidate.y - current.y) <= epsilon and candidate.x >= (current.x - epsilon):
        return True
    return False

# Definição da Geometria dos Polígonos
for i in range(num_p):
    v = int(input(f"How many vertices does polygon Type {i} have?\n"))
    copies = int(input(f"How many copies does polygon Type {i} have?\n"))

    # Instancia a classe
    new_poly = polygon(v, copies)
    polygons.append(new_poly)

    # Preenche geometria (Forma)
    print(f"--- Geometry for Type {i} ---")
    for j in range(v):
        new_poly.vertex(j)
    
    # Preenche posições candidatas (Onde queremos colocar)

    print(f"Processing limits for Bottom-Left algorithm...") 
    new_poly.limitsforBL()
    

# Definição da Matriz NFP (No-Fit Polygon)
# A matriz NFPs[i][j] guarda a geometria que define onde J não pode encostar em I.
# Para o algoritmo Bottom-Left simples, aproximamos NFP como bounding boxes

allocated = [] # Guarda tuplas: (Indice_Tipo, Indice_Copia_Usada)
flag = 0
pos = Point(0, 0)
pos_encontrada = None
first_place = 1 # Variável para controlar se é a primeira peça a ser alocada

order = input("\nWhich order do you want to allocate? (0 to allocate by your choice, 1 to allocate by area)\n")

print("\n--- Generating NFP Approximations ---")
NFPs = Minkowski_Sum(polygons)


if order == '1':
    """ ORDENAÇÃO POR ÁREA """
    # para cada polígono, calcular a área e ordenar por área decrescente
    for pol in polygons:
        pol.area()
    sorted_polygons = sorted(enumerate(polygons), key=lambda x: x[1].area_value, reverse=True)
    flag = 0
    idx_copy = -1
elif order == '2':
    """ ORDENAÇÃO POR COMPRIMENTO MÁXIMO """
    for pol in polygons:
        pol.max_length()
    sorted_polygons = sorted(enumerate(polygons), key=lambda x: x[1].max_length_x, reverse=True)
    flag = 0
    idx_copy = -1
elif order == '3':
    # Razão entre área envolvente (bounding box) e área do polígono
    for pol in polygons:
        pol.area()
        pol.bounding_box_area()
    sorted_polygons = sorted(enumerate(polygons), key=lambda x: (x[1].bounding_box_area_value / x[1].area_value), reverse=False)
    print(f"Sorted by bounding box to area ratio: {[f'Type {idx} Ratio {pol.bounding_box_area_value / pol.area_value:.4f}' for idx, pol in sorted_polygons]}")
    flag = 0
    idx_copy = -1
while True:
    cont = input("\nAllocate polygon? (y/n): ")
    if cont.lower() != 'y': break

    try:
        if order == '0':
            Index = int(input("\nWhich polygon type do you want to place?"))

            idx_copy = 0
            if polygons[Index].copy >= 1:
                # Pergunta qual das cópias pré-definidas usar
                idx_copy = int(input(f"Which copy index (0 to {len(polygons[Index].position)-1})?\n"))
                if idx_copy < 0 or idx_copy >= len(polygons[Index].position):
                    print("Invalid copy index.")
                    continue
        elif order == '1' or order == '2' or order == '3':
            # Avança para o próximo tipo com cópias disponíveis.
            while flag < len(sorted_polygons) and polygons[sorted_polygons[flag][0]].copy <= 0:
                flag += 1
                idx_copy = -1

            if flag >= len(sorted_polygons):
                print("All polygons allocated.")
                break

            Index = sorted_polygons[flag][0]

            # Seleciona a próxima cópia livre (posição ainda não utilizada).
            idx_copy = next(
                (i for i, posicao in enumerate(polygons[Index].position) if posicao is None),
                -1
            )

            if idx_copy == -1:
                # Estado inconsistente: não há slot livre apesar de haver cópias.
                polygons[Index].copy = 0
                flag += 1
                continue
        else:
            print("Invalid order.")
            continue

        if Index >= len(polygons) or Index < 0 or polygons[Index].copy <= 0:
            print(f"{Index >= len(polygons)} | {Index < 0} | {polygons[Index].copy <= 0}")
            print("Invalid index.")
            continue # Volta ao inicio do while
        
        X_min, X_max, Y_min, Y_max = polygons[Index].height()

        # Aqui, vem a lógica principal do bottom-left. Os vértices candidatos serão as intersecções dos NFPs das peças já alocadas.
        # Para cada NFP, pegamos suas laterais e testamos intersecção com as laterais dos outros NFPs e com o eixo X, Y e o eixo de altura da faixa.
        if first_place == 0:
            MAX_X = 999999
            # Lista para armazenar posições candidatas encontradas durante a verificação dos NFPs
            pos_encontrada = None
            for (aloc_type_idx, aloc_copy_idx) in allocated:
                
                # Pegamos o NFP correto da matriz: Fixo (aloc_type) vs Móvel (idx)
                nfp_obj = NFPs[aloc_type_idx][Index]
                pos_ref_alocado = polygons[aloc_type_idx].position[aloc_copy_idx]
                print(f"vertex list do NFP entre Polygon {aloc_type_idx} e Polygon {Index}: {[f'({v.x}, {v.y})' for v in nfp_obj.vertex_list]}")
                for vert in nfp_obj.vertex_list:
                    
                    # Gerar borda do NFP e testar intersecção com as bordas dos outros NFPs e com os limites da faixa
                    test_x = vert.x + pos_ref_alocado.x
                    test_y = vert.y + pos_ref_alocado.y
                    print(f"Testing candidate position from NFP vertex: ({test_x}, {test_y})")
                    if len(nfp_obj.vertex_list) == 0:
                        print(f"NFP between Polygon {aloc_type_idx} and Polygon {Index} has no vertices. Skipping.")
                        continue
                    len_vert = len(nfp_obj.vertex_list)
                    if vert == nfp_obj.vertex_list[len_vert - 1]: # Último vértice, conecta com o primeiro
                        next_vert = nfp_obj.vertex_list[0]
                    else:
                        next_vert = nfp_obj.vertex_list[nfp_obj.vertex_list.index(vert) + 1]
                    
                    p1 = Point(test_x, test_y)
                    p2 = Point(next_vert.x + pos_ref_alocado.x, next_vert.y + pos_ref_alocado.y)
                    segmento = (p1, p2)

                    # Testar intersecção do segmento com os limites da faixa
                    #if test_x < 0 or test_y < 0 or test_y > height:
                    if not ((p1.x < -EPSILON or p1.y < -EPSILON or p1.y > height + EPSILON) and (p2.x < -EPSILON or p2.y < -EPSILON or p2.y > height + EPSILON)):
                        # Posição candidata é o ponto de intersecção do segmento com o limite da faixa
                        limit_faixa = [
                            (Point(X_min, Y_min), Point(X_min, height - Y_max)), # Limite esquerdo viável
                            (Point(X_min, Y_min), Point(MAX_X, Y_min)), # Limite inferior viável
                            (Point(X_min, height - Y_max), Point(MAX_X, height - Y_max)) # Limite superior viável
                        ]

                        for p3, p4 in limit_faixa:
                            # p3 e p4 definem um segmento do limite viável da peça
                            # p3 = Point(X_min, Y_min), p4 = Point(X_min, height - Y_max) para o limite esquerdo
                            # p3 = Point(X_min, Y_min), p4 = Point(MAX_X, Y_min) para o limite inferior
                            # p3 = Point(X_min, height - Y_max), p4 = Point(MAX_X, height - Y_max) para o limite superior
                            intersec = segment_intersection(p1, p2, p3, p4)
                            print(f"Testing segment ({p1.x}, {p1.y}) to ({p2.x}, {p2.y}) against limit from ({p3.x}, {p3.y}) to ({p4.x}, {p4.y})")
                            print(f"Intersection result: {('None' if intersec is None else f'({intersec.x}, {intersec.y})')}")
                            if intersec:
                                
                                # Testar se o ponto está dentro da faixa
                                if is_out_of_bounds(intersec, X_min, Y_min, Y_max, height):
                                    print(f"Candidate position ({intersec.x}, {intersec.y}) is out of bounds. Skipping.")
                                    continue

                                # Testar se um ponto é melhor para o algoritmo bottom-left do que o outro anteriormente encontrado
                                if check_inside_cand(allocated, NFPs, polygons, intersec, Index):
                                    if candidate_better(intersec, pos_encontrada):
                                        if pos_encontrada is None:
                                            print(f"First candidate position found: ({intersec.x}, {intersec.y})")
                                        pos_encontrada = intersec
                            continue
                    # Testar intersecção do segmento com os segmentos dos NFPs das peças já alocadas
                    for (aloc_type_idx2, aloc_copy_idx2) in allocated:
                        if (aloc_type_idx2, aloc_copy_idx2) == (aloc_type_idx, aloc_copy_idx):
                            continue # Não testa contra si mesmo

                        nfp_obj2 = NFPs[aloc_type_idx2][Index]
                        pos_ref_alocado2 = polygons[aloc_type_idx2].position[aloc_copy_idx2]

                        for vert2 in nfp_obj2.vertex_list:
                            if len(nfp_obj2.vertex_list) == 0:
                                print(f"NFP between Polygon {aloc_type_idx2} and Polygon {Index} has no vertices. Skipping.")
                                continue
                            len_vert2 = len(nfp_obj2.vertex_list)
                            if vert2 == nfp_obj2.vertex_list[len_vert2 - 1]: # Último vértice, conecta com o primeiro
                                next_vert2 = nfp_obj2.vertex_list[0]
                            else:
                                next_vert2 = nfp_obj2.vertex_list[nfp_obj2.vertex_list.index(vert2) + 1]
                            
                            p3 = Point(vert2.x + pos_ref_alocado2.x, vert2.y + pos_ref_alocado2.y)
                            p4 = Point(next_vert2.x + pos_ref_alocado2.x, next_vert2.y + pos_ref_alocado2.y)
                            segmento2 = (p3, p4)
                            
                            intersec = segment_intersection(p1, p2, p3, p4)

                            # Testar se o ponto está dentro da faixa
                            
                            if intersec:
                                    # Testar se o ponto está dentro da faixa
                                    if is_out_of_bounds(intersec, X_min, Y_min, Y_max, height):
                                        print(f"Candidate position ({intersec.x}, {intersec.y}) is out of bounds. Skipping.")
                                        continue

                                    # Testar se um ponto é melhor para o algoritmo bottom-left do que o outro anteriormente encontrado
                                    if check_inside_cand(allocated, NFPs, polygons, intersec, Index):
                                        if candidate_better(intersec, pos_encontrada):
                                            pos_encontrada = intersec
                        
            print(pos_encontrada)
            
            print(f"Allocated at position ({pos_encontrada.x}, {pos_encontrada.y})") # Posição alocada
            polygons[Index].change_copy()
            allocated.append((Index, idx_copy))

            # Garantir que a lista de posições tem espaço suficiente
            if len(polygons[Index].position) <= idx_copy:
                polygons[Index].position.extend([Point(0, 0)] * (idx_copy + 1 - len(polygons[Index].position)))
            polygons[Index].position[idx_copy] = Point(pos_encontrada.x, pos_encontrada.y)

            # Plotar todas as peças alocadas para visualização usando matplotlib
            for (plot_type_idx, plot_copy_idx) in allocated:
                plot_pos = polygons[plot_type_idx].position[plot_copy_idx]
                vertices = [(v.x + plot_pos.x, v.y + plot_pos.y) for v in polygons[plot_type_idx].vertex_list]
                vertices.append(vertices[0])  # Fechar o polígono
                xs, ys = zip(*vertices)
            #     plt.plot(xs, ys, label=f'Polygon Type {plot_type_idx} Copy {plot_copy_idx}')
            # Defining strip height for visualization
            # plt.axhline(y=height, color='r', linestyle='--', label='Strip Height')
            # plt.legend()
            # plt.show()
                

            historico_animacao.append({
                'vertices': [Point(v.x + pos_encontrada.x, v.y + pos_encontrada.y) for v in polygons[Index].vertex_list],
                'tipo': Index,
                'copia': idx_copy
            })
        

        elif first_place == 1:
            #i.e. a posição é (0,0)
            pos = Point(X_min, Y_min)

            print(f"Testing first placement at ({pos.x}, {pos.y})")
            if is_out_of_bounds(pos, X_min, Y_min, Y_max, height):
                print("Error: Out of bounds.")
                continue
            else:
                print("First polygon allocated successfully!")
                polygons[Index].change_copy()
                allocated.append((Index, idx_copy))

                # Garantir que a lista de posições tem espaço suficiente
                if len(polygons[Index].position) <= idx_copy:
                    polygons[Index].position.extend([Point(0, 0)] * (idx_copy + 1 - len(polygons[Index].position)))
                polygons[Index].position[idx_copy] = Point(pos.x, pos.y)

                # Plotar a peça alocada para visualização usando matplotlib
                vertices = [(v.x + pos.x, v.y + pos.y) for v in polygons[Index].vertex_list]
                vertices.append(vertices[0])  # Fechar o polígono
                xs, ys = zip(*vertices)
                # plt.plot(xs, ys, label=f'Polygon Type {Index} Copy {idx_copy}')
                # Defining strip height for visualization
                # plt.axhline(y=height, color='r', linestyle='--', label='Strip Height')
                # plt.legend()
                # plt.show()

                print(f"Polygon Type {Index} Copy {idx_copy} allocated at ({polygons[Index].position[idx_copy].x}, {polygons[Index].position[idx_copy].y})")
                
                first_place = 0

                historico_animacao.append({
                            'vertices': [Point(v.x + pos.x, v.y + pos.y) for v in polygons[Index].vertex_list],
                            'tipo': Index,
                            'copia': idx_copy
                        })
                continue
        print("Finished animation.")
        
    except (ValueError, IndexError) as e:
        print(f"Invalid input error: {e}")

allocation_total_time = time.perf_counter() - allocation_start_time

# ==================================================
# Espaço para mostrar animação
# ==================================================

#mostrar_animacao(historico_animacao, height)

if historico_animacao:
    max_length = max(v.x for h in historico_animacao for v in h['vertices'])
else:
    max_length = 0.0

summary_rows = [
    ("Allocated Pieces", str(len(allocated))),
    ("Maximum Length on Strip", f"{max_length:.4f}"),
    ("Total Allocation Time (s)", f"{allocation_total_time:.6f}"),
]


# ====================================================
# Espaço para criação do csv
# ====================================================

csv_output_path = os.path.join(results_dir, f"{instance_stem}.csv")

order_name = {
    '0': "Bottom-Left (User Choice)",
    '1': "Bottom-Left (Area Order)",
    '2': "Bottom-Left (Max Length Order)",
    '3': "Bottom-Left (Bounding Box to Area Ratio Order)"
}.get(order, "Bottom-Left (Unknown Order)")
df_summary = pd.DataFrame([
    {
        "Algoritmo": order_name,
        "Allocated Pieces": len(allocated),
        "Maximum Length on Strip": f"{max_length:.4f}",
        "Total Allocation Time (s)": f"{allocation_total_time:.6f}",
    }
])

# =====================================================
# Impressão do resumo final em formato de tabela
# =====================================================

header_metric = "Metrica"
header_value = "Valor"
metric_width = max(len(header_metric), *(len(metric) for metric, _ in summary_rows))
value_width = max(len(header_value), *(len(value) for _, value in summary_rows))
separator = f"+-{'-' * metric_width}-+-{'-' * value_width}-+"

print("\nResumo final da alocacao")
print(separator)
print(f"| {header_metric.ljust(metric_width)} | {header_value.ljust(value_width)} |")
print(separator)
for metric, value in summary_rows:
    print(f"| {metric.ljust(metric_width)} | {value.ljust(value_width)} |")
print(separator)


# ====================================================
# Espaço para salvar o csv
# ====================================================

try:
    csv_row = df_summary.iloc[0].to_dict()
    file_exists = os.path.exists(csv_output_path) and os.path.getsize(csv_output_path) > 0
    with open(csv_output_path, 'a', newline='', encoding='utf-8') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(csv_row.keys()))
        if not file_exists:
            writer.writeheader()
        writer.writerow(csv_row)
    print(f"CSV salvo em: {csv_output_path} (append)")
except Exception as e:
    print(f"Falha ao salvar CSV: {e}")

# ====================================================
# Espaço para salvar o txt para utilizar em TikZ ou LaTeX
# ====================================================

# print("\nResumo final da alocacao (DataFrame do pandas)")
# print(df_summary)

# # Imprimir os vértices de cada peça alocada para armazenar em um arquivo de texto ou para análise posterior
# print("\nVertices de cada peça alocada:")
# for (plot_type_idx, plot_copy_idx) in allocated:
#     plot_pos = polygons[plot_type_idx].position[plot_copy_idx]
#     vertices = [(v.x + plot_pos.x, v.y + plot_pos.y) for v in polygons[plot_type_idx].vertex_list]
#     print(f"Polygon Type {plot_type_idx} Copy {plot_copy_idx} at position ({plot_pos.x}, {plot_pos.y}) with vertices: {vertices}")

# # Armazenar em txt
# with open("allocated_pieces_vertices.txt", "w") as f:
#     for (plot_type_idx, plot_copy_idx) in allocated:
#         plot_pos = polygons[plot_type_idx].position[plot_copy_idx]
#         vertices = [(v.x + plot_pos.x, v.y + plot_pos.y) for v in polygons[plot_type_idx].vertex_list]
#         f.write(f"Polygon Type {plot_type_idx} Copy {plot_copy_idx} at position ({plot_pos.x}, {plot_pos.y}) with vertices: {vertices}\n")

# Testar em ordenações diferentes(crescente, decrescente).
