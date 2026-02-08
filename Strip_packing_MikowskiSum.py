""" 
    Aqui, adicionaremos a Diferença de Mikowski para calcular
    os NFP's correspondentes entre dois objetos
"""

from useful.verif_func import check_inside, Mikowski_Sum
from Class.class_polygon import polygon
from Class.class_point import Point
import matplotlib.pyplot as plt

polygons = []

limits_x = []
limits_y = []
limits_x.append(0)
limits_y.append(0)

# Configuração Inicial
height = int(input("What is the strip height?\n"))
numbers_p = int(input("How many TYPES of convex polygons?\n"))
num_p = numbers_p

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
    max_x, max_y = new_poly.limitsforBL()
    
# Definição da Matriz NFP (No-Fit Polygon)
# A matriz NFPs[i][j] guarda a geometria que define onde J não pode encostar em I.

NFPs = Mikowski_Sum(polygons)

allocated = [] # Guarda tuplas: (Indice_Tipo, Indice_Copia_Usada)
flag = 0
pos = Point(0, 0)

first_place = 1

while True:
    cont = input("\nAllocate another polygon? (y/n): ")
    if cont.lower() != 'y': break

    try:
        Index = int(input("\nWhich polygon type do you want do place?"))
        if Index >= len(polygons):
            print("Invalid index.")
            continue # Volta ao inicio do while

        idx_copy = 0
        if polygons[Index].copy > 1:
            # Pergunta qual das cópias pré-definidas usar
            idx_copy = int(input(f"Which copy index (0 to {len(polygons[Index].position)-1})?\n"))

        X_min, X_max, Y_min, Y_max = polygons[Index].height()

        collision = False

        for (aloc_type_idx, aloc_copy_idx) in allocated:
            first_place = 0
            # Pegamos o NFP correto da matriz: Fixo (aloc_type) vs Móvel (idx)
            nfp_obj = NFPs[aloc_type_idx][Index]
            vertices_NFP = nfp_obj.vertex_list
            
            # Posição da peça fixa já alocada
            pos_fixed = polygons[aloc_type_idx].position[aloc_copy_idx]

            # Adiciona TODOS os vértices do NFP transladados pela posição da peça fixa
            # Estes são as posições candidatas onde a peça móvel pode tocar sem colidir
            for v in vertices_NFP:
                candidate_x = v.x + pos_fixed.x
                candidate_y = v.y + pos_fixed.y
                limits_x.append(candidate_x)
                limits_y.append(candidate_y)
                print(f"Candidate position from NFP: ({candidate_x:.2f}, {candidate_y:.2f})")
        
            # Agora, nós temos os limites necessários para realizar o algoritmo Bottom-Left
        if first_place == 0:
            limits_x.sort()
            limits_y.sort()

            pos_encontrada = False
            for X in limits_x:
                for Y in limits_y:
                    # As posições candidatas já são absolutas
                    test_x = X
                    test_y = Y
                    
                    # Calcula os limites reais do polígono nesta posição
                    poly_x_min = test_x + X_min
                    poly_x_max = test_x + X_max
                    poly_y_min = test_y + Y_min
                    poly_y_max = test_y + Y_max
                    
                    # Verifica se a posição está dentro dos limites da faixa
                    if (poly_x_min < 0 or 
                        poly_y_max > height or 
                        poly_y_min < 0):
                        print(f"Position ({test_x:.2f}, {test_y:.2f}) is out of bounds.")
                        continue

                    # Colisão via NFP
                    collision = False

                    pos_esc = Point(test_x, test_y)
                    # Compara a nova peça contra TODAS as peças já alocadas
                    for (aloc_type_idx, aloc_copy_idx) in allocated:
                        # Pegamos o NFP correto da matriz: Fixo (aloc_type) vs Móvel (idx)
                        nfp_obj = NFPs[aloc_type_idx][Index]

                        # Pegamos a posição exata onde a peça fixa está
                        pos_ref_alocado = polygons[aloc_type_idx].position[aloc_copy_idx]

                        # Verificamos se a nova posição cai dentro desse NFP
                        # (Se cair dentro, significa que as formas físicas se sobrepõem)
                        
                        if check_inside(nfp_obj, pos_ref_alocado, pos_esc):
                            print(f"COLLISION detected with Polygon {aloc_type_idx} (Copy {aloc_copy_idx}) at position ({test_x:.2f}, {test_y:.2f})!")
                            collision = True
                            break # Para de testar, já bateu
                    
                    if not collision:
                        print(f"Allocation valid at position ({test_x:.2f}, {test_y:.2f})!")
                        polygons[Index].change_copy()
                        allocated.append((Index, idx_copy))
                        polygons[Index].position[idx_copy] = pos_esc
                        pos_encontrada = True

                        # Impressão da posição escolhida
                        print(f"Polygon Type {Index} (Copy {idx_copy}) placed at ({test_x:.2f}, {test_y:.2f})")
                        # Imagem no matplotlib da alocação dos polígonos até o momento

                        print("Current Allocations Visualized:")
                        plt.figure()
                        for (aloc_type_idx, aloc_copy_idx) in allocated:
                            poly_to_plot = polygons[aloc_type_idx]
                            pos_to_plot = poly_to_plot.position[aloc_copy_idx]
                            x_coords = [v.x + pos_to_plot.x for v in poly_to_plot.vertex_list] + [poly_to_plot.vertex_list[0].x + pos_to_plot.x]
                            y_coords = [v.y + pos_to_plot.y for v in poly_to_plot.vertex_list] + [poly_to_plot.vertex_list[0].y + pos_to_plot.y]
                            plt.plot(x_coords, y_coords, marker='o')
                            plt.fill(x_coords, y_coords, alpha=0.3)
                        plt.xlim(0, max(limits_x) + 10)
                        plt.ylim(0, height + 10)
                        plt.title("Current Polygon Allocations")
                        plt.xlabel("X-axis")
                        plt.ylabel("Y-axis")
                        plt.grid()
                        plt.show()
                        break  # Sai do loop Y quando encontrar posição válida
                    
                if pos_encontrada:
                    break  # Sai do loop X quando encontrar posição válida
            
            # Se nenhuma posição foi encontrada, notifica o usuário
            if not pos_encontrada:
                print(f"ERROR: Could not find a valid position for Polygon Type {Index}!")
                print("All attempted positions either went out of bounds or caused collisions.")
                continue  # Volta para o início do while, não aloca este polígono

        elif first_place == 1:
            # Primeira peça sempre vai para o canto inferior esquerdo (0, 0)
            pos = Point(-X_min, -Y_min)

            # Verifica se a peça cabe na altura da faixa
            if (Y_max - Y_min) > height:
                print(f"Error: Polygon Type {Index} is too tall for the strip (height: {Y_max - Y_min}, strip height: {height}).")
                continue
            else:
                print("First polygon allocated successfully!")
                polygons[Index].change_copy()
                allocated.append((Index, idx_copy))
                polygons[Index].position[idx_copy] = pos
                first_place = 0

                print(f"Polygon Type {Index} (Copy {idx_copy}) placed at ({pos.x:.2f}, {pos.y:.2f})")
                # Imagem no matplotlib da alocação do primeiro polígono
                print("Current Allocations Visualized:")
                plt.figure()
                for (aloc_type_idx, aloc_copy_idx) in allocated:
                    poly_to_plot = polygons[aloc_type_idx]
                    pos_to_plot = poly_to_plot.position[aloc_copy_idx]
                    x_coords = [v.x + pos_to_plot.x for v in poly_to_plot.vertex_list] + [poly_to_plot.vertex_list[0].x + pos_to_plot.x]
                    y_coords = [v.y + pos_to_plot.y for v in poly_to_plot.vertex_list] + [poly_to_plot.vertex_list[0].y + pos_to_plot.y]
                    plt.plot(x_coords, y_coords, marker='o')
                    plt.fill(x_coords, y_coords, alpha=0.3) 
                plt.xlim(0, max(limits_x) + 10 if limits_x else 10)
                plt.ylim(0, height + 10)
                plt.title("Current Polygon Allocations")
                plt.xlabel("X-axis")
                plt.ylabel("Y-axis")
                plt.grid()
                plt.show()

    except (ValueError, IndexError) as e:
        print("Invalid input error {e}")
