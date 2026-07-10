import time
import pandas as pd
import os

from usefull.verif_func import MKSum_Irregular, Minkowski_Sum, check_inside, Minkowski_Sum, segment_intersection, check_inside_cand_irregular
from Class.class_polygon import polygon
from Class.class_point import Point
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from Class.class_item import item
"""
Nesse algoritmo, iremos desenvolver a heurística bottom-left, de modo a resolver o strip packing problem de maneira rápida e eficaz.
Ainda que não alcance a solução ótima. Ainda sim, de acordo com o artigo 
"""

# Para compilar:
# Get-Content irreg_instances/instance_albano | python Strip_packing_MKBL_v05_test.py
EPSILON = 1e-9

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
    """Escolhe o candidato mais à esquerda; em empate, o mais abaixo."""
    if current is None:
        return True
    if candidate.x < (current.x - epsilon):
        return True
    if abs(candidate.x - current.x) <= epsilon and candidate.y < (current.y - epsilon):
        return True
    return False

def item_vertices_at_position(item_obj, position, ref_point=None):
    """Retorna os vértices de todos os polígonos do item transladados para a posição escolhida."""
    if ref_point is None:
        ref_point = Point(0, 0)

    translated_polygons = []
    for poly in item_obj.polygons:
        translated_polygons.append([
            Point(v.x + position.x - ref_point.x, v.y + position.y - ref_point.y)
            for v in poly.vertex_list
        ])
    return translated_polygons

def flatten_points(polygons_points):
    return [point for polygon_points in polygons_points for point in polygon_points]

def mostrar_resultado_final(allocated, itens, strip_height):
    if not allocated:
        print("Nenhum item alocado para plotar.")
        return

    fig, ax = plt.subplots(figsize=(16, 5))
    
    # Cria uma paleta de cores para garantir que cada item tenha uma única cor
    cmap = plt.get_cmap('tab20')
    
    all_points = []
    for i, (plot_type_idx, plot_copy_idx) in enumerate(allocated):
        plot_pos = itens[plot_type_idx].position[plot_copy_idx]
        ref_point = itens[plot_type_idx].polygons[0].vertex_list[0]
        translated_polygons = item_vertices_at_position(itens[plot_type_idx], plot_pos, ref_point)

        # Define a cor fixa para este item específico
        item_color = cmap(i % 20) 

        for polygon_vertices in translated_polygons:
            if not polygon_vertices:
                continue

            all_points.extend(polygon_vertices)
            coords = polygon_vertices + [polygon_vertices[0]]
            xs, ys = zip(*[(v.x, v.y) for v in coords])
            
            # Desenha a borda e preenche o interior com a MESMA cor
            ax.plot(xs, ys, color=item_color, linewidth=1.5)
            ax.fill(xs, ys, color=item_color, alpha=0.4) 

    if all_points:
        max_x = max(point.x for point in all_points) + 10
        ax.set_xlim(0, max_x)
    else:
        ax.set_xlim(0, 10)

    ax.set_ylim(0, strip_height + 2)
    ax.set_aspect('equal')
    ax.axhline(y=strip_height, color='r', linestyle='--', label='Strip Height')
    plt.title("Final Allocation Result")
    plt.legend(loc='upper right')
    plt.show()

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
    ax.axhline(y=strip_height, color='r', linestyle='--', label='Strip Height')

    def update(frame):
        peca = historico[frame]
        artists = []

        if 'polygons' in peca:
            for idx_poly, poly_vertices in enumerate(peca['polygons']):
                if not poly_vertices:
                    continue
                coords = [[v.x, v.y] for v in poly_vertices]
                coords.append(coords[0])
                xs, ys = zip(*coords)
                label = f"Tipo {peca['tipo']}" if idx_poly == 0 else None
                line, = ax.plot(xs, ys, label=label)
                artists.append(line)
        else:
            v_list = peca['vertices']
            coords = [[v.x, v.y] for v in v_list]
            coords.append(coords[0])
            xs, ys = zip(*coords)
            line, = ax.plot(xs, ys, label=f"Tipo {peca['tipo']}")
            artists.append(line)

        return artists

    ani = animation.FuncAnimation(
        fig, update, frames=len(historico), interval=1000, blit=False
    )

    plt.title("Sequência de Alocação - Bottom-Left")
    plt.legend(loc='upper right')
    plt.show()

historico_animacao = []  # Lista para armazenar o histórico de alocações para animação  

# Cronometra apenas a fase de alocação iterativa.
allocation_start_time = time.perf_counter()



#==============================================
# Configuração Inicial
#==============================================

polygons = []
itens = []

limits_x = []
limits_y = []
limits_x.append(0)
limits_y.append(0)
# Tolerância numérica para comparações geométricas
EPSILON = 1e-9

height = int(input("What is the strip height?\n"))
numbers_i = int(input("How many types of itens?\n"))
num_i = numbers_i

#==============================================
# Definição dos Itens
#==============================================

for i in range(num_i):
    numbers_p = int(input(f"How many polygons have item {i}?\n"))
    num_p = numbers_p
    print(f"--- Defining Item Type {i} with {num_p} polygons ---")
    copies = int(input(f"How many copies of item {i}?\n"))
    print(f"--- Defining Item Type {i} with {num_p} polygons and {copies} copies ---")
    new_item = item(i, copies)
    new_item.num_polygons = num_p
    itens.append(new_item)

# Definição da Geometria dos Polígonos
for item_idx in range(num_i):
    print(f"--- Defining geometry for Item Type {item_idx} ---")
    for polygon_idx in range(itens[item_idx].num_polygons):
        v = int(input(f"How many vertices does polygon piece {polygon_idx} have?\n"))
        copies = 1

        # Instancia a classe
        new_poly = polygon(v, copies)
        polygons.append(new_poly)

        # Preenche geometria (Forma)
        print(f"--- Geometry for piece {polygon_idx} ---")
        for vertex_idx in range(v):
            new_poly.vertex(vertex_idx)
        
        # Preenche posições candidatas (Onde queremos colocar)

        print(f"Processing limits for Bottom-Left algorithm...") 
        new_poly.limitsforBL()

        itens[item_idx].polygons.append(new_poly)

    #itens[item_idx].normalize_to_reference()

#=====================================================
# Definição da Matriz NFP (No-Fit Polygon)
#=====================================================

# A matriz NFPs[i][j] guarda a geometria que define onde J não pode encostar em I.

print("\n--- Generating NFP Approximations ---")

NFPs = MKSum_Irregular(itens)
# NFPs é uma matriz onde NFPs[i][j] é o NFP do item i (fixo) contra o item j (orbital).
# e em cada NFPs[i][j], temos uma classe NFP que contém uma lista de polígonos (no caso, apenas um polígono que é a bounding box).

# Agora, para verificar sobreposição, basta verificar se o vértice candidato de alocação está dentro do NFP correspondente a cada peça já alocada.
# Isto é, dentro de algum dos NFPs dentro da classe NFP em NFPs[i][j], onde i é o tipo da peça já alocada e j é o tipo da peça que queremos alocar.



#====================================================
# Ordenação dos itens para alocação iterativa
#====================================================

allocated = [] # Guarda tuplas: (Indice_Tipo, Indice_Copia_Usada)
flag = 0
pos = Point(0, 0)
pos_encontrada = None
first_place = 1 # Variável para controlar se é a primeira peça a ser alocada

order = input("\nWhich order do you want to allocate?\n")

if order == '1':
    """ ORDENAÇÃO POR ÁREA """
    for it in itens:
        it.calcular_area() # Invoca o método corrigido
    sorted_polygons = sorted(enumerate(itens), key=lambda x: x[1].area, reverse=True)
    flag = 0
    idx_copy = -1
elif order == '2':
    """ ORDENAÇÃO POR COMPRIMENTO MÁXIMO """
    for it in itens:
        it.calcular_max_length()
    sorted_polygons = sorted(enumerate(itens), key=lambda x: x[1].max_length_x, reverse=True)
    flag = 0
    idx_copy = -1
elif order == '3':
    """ ORDENAÇÃO PELA RAZÃO (BOUNDING BOX / AREA) """
    for it in itens:
        it.calcular_area()
        it.calcular_max_length() # max_length precisa rodar para alimentar os limites da Bounding Box
        it.calcular_bounding_box_area()
    sorted_polygons = sorted(enumerate(itens), key=lambda x: (x[1].bounding_box_area_value / x[1].area), reverse=False)
    flag = 0
    idx_copy = -1
while True:
    cont = input("\nAllocate item? (y/n): ")
    if cont.lower() != 'y': break

    try:
        if order == '0':
            Index = int(input("\nWhich item do you want to place?"))

            idx_copy = 0
            if itens[Index].copy >= 1:
                # Pergunta qual das cópias pré-definidas usar
                idx_copy = int(input(f"Which copy index (0 to {len(itens[Index].position)-1})?\n"))
                if idx_copy < 0 or idx_copy >= len(itens[Index].position):
                    print("Invalid copy index.")
                    continue
        elif order == '1' or order == '2' or order == '3':
            # Avança para o próximo tipo com cópias disponíveis.
            while flag < len(sorted_polygons) and itens[sorted_polygons[flag][0]].copy <= 0:
                flag += 1
                idx_copy = -1

            if flag >= len(sorted_polygons):
                print("All polygons allocated.")
                break

            Index = sorted_polygons[flag][0]

            # Seleciona a próxima cópia livre (posição ainda não utilizada).
            idx_copy = next(
                (i for i, posicao in enumerate(itens[Index].position) if posicao is None),
                -1
            )

            if idx_copy == -1:
                # Estado inconsistente: não há slot livre apesar de haver cópias.
                itens[Index].copy = 0
                flag += 1
                continue
        else:
            print("Invalid order.")
            continue

        if Index >= len(itens) or Index < 0 or itens[Index].copy <= 0:
            print(f"{Index >= len(itens)} | {Index < 0} | {itens[Index].copy <= 0}")
            print("Invalid index.")
            continue # Volta ao inicio do while
        
        


        #=============================================================
        # Verificar posição candidata de alocação usando o algoritmo bottom-left
        # ============================================================
        
        if not itens[Index].polygons or not itens[Index].polygons[0].vertex_list:
            print("Invalid item geometry.")
            continue

        X_min, X_max, Y_min, Y_max = itens[Index].ref_distance()
        item_ref_point = itens[Index].polygons[0].vertex_list[0]

        if first_place == 0:
            MAX_X = 999999
            pos_encontrada = None
            
            for (aloc_type_idx, aloc_copy_idx) in allocated:
                nfp_obj = NFPs[aloc_type_idx][Index]
                pos_ref_alocado = itens[aloc_type_idx].position[aloc_copy_idx]
                
                #=============================================
                # Configuração para NFP
                #=============================================
                for nfp_poly in nfp_obj.polygons:
                    if not nfp_poly.vertex_list:
                        print(f"NFP between item {aloc_type_idx} and item {Index} has no vertices. Skipping.")
                        continue

                    print(f"vertex list do NFP entre item {aloc_type_idx} e item {Index}: {[f'({v.x}, {v.y})' for v in nfp_poly.vertex_list]}")
                    len_vert = len(nfp_poly.vertex_list)

                    for idx_vert, vert in enumerate(nfp_poly.vertex_list):
                        test_x = vert.x + pos_ref_alocado.x
                        test_y = vert.y + pos_ref_alocado.y

                        next_vert = nfp_poly.vertex_list[(idx_vert + 1) % len_vert]
                        p1 = Point(test_x, test_y)
                        p2 = Point(next_vert.x + pos_ref_alocado.x, next_vert.y + pos_ref_alocado.y)

                        if not ((p1.x < -EPSILON or p1.y < -EPSILON or p1.y > height + EPSILON) and (p2.x < -EPSILON or p2.y < -EPSILON or p2.y > height + EPSILON)):
                            limit_faixa = [
                                (Point(X_min, Y_min), Point(X_min, height - Y_max)),
                                (Point(X_min, Y_min), Point(MAX_X, Y_min)),
                                (Point(X_min, height - Y_max), Point(MAX_X, height - Y_max))
                            ]

                            for p3, p4 in limit_faixa:
                                intersec = segment_intersection(p1, p2, p3, p4)
                                print(f"Testing segment ({p1.x}, {p1.y}) to ({p2.x}, {p2.y}) against limit from ({p3.x}, {p3.y}) to ({p4.x}, {p4.y})")
                                print(f"Intersection result: {('None' if intersec is None else f'({intersec.x}, {intersec.y})')}")
                                if intersec:
                                    
                                    # Testar se o ponto está dentro da faixa
                                    if is_out_of_bounds(intersec, X_min, Y_min, Y_max, height):
                                        print(f"Candidate position ({intersec.x}, {intersec.y}) is out of bounds. Skipping.")
                                        continue

                                    # Testar se um ponto é melhor para o algoritmo bottom-left do que o outro anteriormente encontrado
                                    if check_inside_cand_irregular(allocated, NFPs, itens, intersec, Index):
                                        if candidate_better(intersec, pos_encontrada):
                                            if pos_encontrada is None:
                                                print(f"First candidate position found: ({intersec.x}, {intersec.y})")
                                            pos_encontrada = intersec

                        for (aloc_type_idx2, aloc_copy_idx2) in allocated:
                            if (aloc_type_idx2, aloc_copy_idx2) == (aloc_type_idx, aloc_copy_idx):
                                continue

                            nfp_obj2 = NFPs[aloc_type_idx2][Index]
                            pos_ref_alocado2 = itens[aloc_type_idx2].position[aloc_copy_idx2]

                            for nfp_poly2 in nfp_obj2.polygons:
                                if not nfp_poly2.vertex_list:
                                    print(f"NFP between item {aloc_type_idx2} and item {Index} has no vertices. Skipping.")
                                    continue

                                len_vert2 = len(nfp_poly2.vertex_list)
                                for idx_vert2, vert2 in enumerate(nfp_poly2.vertex_list):
                                    next_vert2 = nfp_poly2.vertex_list[(idx_vert2 + 1) % len_vert2]

                                    p3 = Point(vert2.x + pos_ref_alocado2.x, vert2.y + pos_ref_alocado2.y)
                                    p4 = Point(next_vert2.x + pos_ref_alocado2.x, next_vert2.y + pos_ref_alocado2.y)

                                    intersec = segment_intersection(p1, p2, p3, p4)
                                    if intersec:
                                        if is_out_of_bounds(intersec, X_min, Y_min, Y_max, height):
                                            print(f"Candidate position ({intersec.x}, {intersec.y}) is out of bounds. Skipping.")
                                            continue

                                        if check_inside_cand_irregular(allocated, NFPs, itens, intersec, Index):
                                            if candidate_better(intersec, pos_encontrada):
                                                pos_encontrada = intersec

            print(pos_encontrada)
            print(f"Allocated at position ({pos_encontrada.x}, {pos_encontrada.y})")

            itens[Index].change_copy()
            allocated.append((Index, idx_copy))

            if len(itens[Index].position) <= idx_copy:
                itens[Index].position.extend([Point(0, 0)] * (idx_copy + 1 - len(itens[Index].position)))
            itens[Index].position[idx_copy] = Point(pos_encontrada.x, pos_encontrada.y)

            for (plot_type_idx, plot_copy_idx) in allocated:
                plot_pos = itens[plot_type_idx].position[plot_copy_idx]
                plot_vertices = item_vertices_at_position(itens[plot_type_idx], plot_pos, itens[plot_type_idx].polygons[0].vertex_list[0])
                for polygon_vertices in plot_vertices:
                    if not polygon_vertices:
                        continue
                    vertices = polygon_vertices + [polygon_vertices[0]]
                    xs, ys = zip(*[(v.x, v.y) for v in vertices])

            historico_animacao.append({
                'vertices': flatten_points(item_vertices_at_position(itens[Index], pos_encontrada, item_ref_point)),
                'polygons': item_vertices_at_position(itens[Index], pos_encontrada, item_ref_point),
                'tipo': Index,
                'copia': idx_copy
            })

            #==========================================

        elif first_place == 1:
            
            #i.e. a posição é (0,0)
            pos = Point(X_min, Y_min)

            print(f"Testing first placement at ({pos.x}, {pos.y})")
            if is_out_of_bounds(pos, X_min, Y_min, Y_max, height):
                print("Error: Out of bounds.")
                continue
            else:
                print("First item allocated successfully!")
                itens[Index].change_copy()
                allocated.append((Index, idx_copy))

                # Garantir que a lista de posições tem espaço suficiente
                if len(itens[Index].position) <= idx_copy:
                    itens[Index].position.extend([Point(0, 0)] * (idx_copy + 1 - len(itens[Index].position)))
                itens[Index].position[idx_copy] = Point(pos.x, pos.y)


                #===========================================

                # Plotar a peça alocada para visualização usando matplotlib dos itens
                item_plot_vertices = item_vertices_at_position(itens[Index], pos)
                for polygon_vertices in item_plot_vertices:
                    if not polygon_vertices:
                        continue
                    vertices = polygon_vertices + [polygon_vertices[0]]
                    xs, ys = zip(*[(v.x, v.y) for v in vertices])
                #plt.plot(xs, ys, label=f'Polygon Type {Index} Copy {idx_copy}')
                #Defining strip height for visualization
                #plt.axhline(y=height, color='r', linestyle='--', label='Strip Height')
                #plt.legend()

                #==========================================

                print(f"item Type {Index} Copy {idx_copy} allocated at ({itens[Index].position[idx_copy].x}, {itens[Index].position[idx_copy].y})")
                
                first_place = 0

                #==========================================

                historico_animacao.append({
                            'vertices': flatten_points(item_vertices_at_position(itens[Index], pos)),
                            'polygons': item_vertices_at_position(itens[Index], pos),
                            'tipo': Index,
                            'copia': idx_copy
                        })
                continue
                
                #==========================================
        print("Finished animation.")
        
    except (ValueError, IndexError) as e:
        print(f"Invalid input error: {e}")


# =========================================================

allocation_total_time = time.perf_counter() - allocation_start_time

mostrar_animacao(historico_animacao, height)
mostrar_resultado_final(allocated, itens, height)
# Resumo final em formato de tabela.

if historico_animacao:
    max_length = max(v.x for h in historico_animacao for v in h['vertices'])
else:
    max_length = 0.0

summary_rows = [
    ("Pecas alocadas", str(len(allocated))),
    ("Comprimento maximo na faixa", f"{max_length:.4f}"),
    ("Tempo total de alocacao (s)", f"{allocation_total_time:.6f}"),
]

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

# Linha vermelha na vertical
# Acabar na altura máxima


