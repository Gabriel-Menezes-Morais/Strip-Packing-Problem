from usefull.verif_func import Minkowski_Sum, check_inside, Minkowski_Sum
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
    new_poly.limitsforBL()
    

# Definição da Matriz NFP (No-Fit Polygon)
# A matriz NFPs[i][j] guarda a geometria que define onde J não pode encostar em I.
# Para o algoritmo Bottom-Left simples, aproximamos NFP como bounding boxes
print("\n--- Generating NFP Approximations ---")
NFPs = Minkowski_Sum(polygons)

allocated = [] # Guarda tuplas: (Indice_Tipo, Indice_Copia_Usada)
flag = 0
pos = Point(0, 0)

while True:
    cont = input("\nAllocate polygon? (y/n): ")
    if cont.lower() != 'y': break

    try:
        Index = int(input("\nWhich polygon type do you want to place?"))
        if Index >= len(polygons) or Index < 0 or polygons[Index].copy <= 0:
            print("Invalid index.")
            continue # Volta ao inicio do while

        idx_copy = 0
        if polygons[Index].copy >= 1:
            # Pergunta qual das cópias pré-definidas usar
            idx_copy = int(input(f"Which copy index (0 to {len(polygons[Index].position)-1})?\n"))

        X_min, X_max, Y_min, Y_max = polygons[Index].height()

        first_place = 1
        collision = False

        for (aloc_type_idx, aloc_copy_idx) in allocated:
            first_place = 0
            # Pegamos o NFP correto da matriz: Fixo (aloc_type) vs Móvel (idx)
            nfp_obj = NFPs[aloc_type_idx][Index]
            pos_ref_alocado = polygons[aloc_type_idx].position[aloc_copy_idx]
                
            # Adicione os vértices REAIS do NFP transladados como candidatos
            for v in nfp_obj.vertex_list:
                limits_x.append(pos_ref_alocado.x + v.x)
                limits_y.append(pos_ref_alocado.y + v.y)

            limits_x = sorted(list(set([max(0, x) for x in limits_x])))
            limits_y = sorted(list(set([max(0, y) for y in limits_y])))
            # Agora, nós temos os limites necessários para realizar o algoritmo Bottom-Left
        if first_place == 0:

            pos_encontrada = False
            for X in limits_x:
                print(f"Testing X = {X} for placement...")
                for Y in limits_y:
                    print(f"Testing Y = {Y} for placement...")
                     # Criar nova posição para cada teste
                    if X == 0:
                        test_x = X + X_min
                    else:
                        test_x = X
                    if Y == 0:
                        test_y = Y + Y_min
                    else:
                        test_y = Y
                    
                    if ((test_x - X_min) < 0 or 
                        (test_y + Y_max) > height or 
                        (test_y - Y_min) < 0):
                        print("Error: Out of bounds.")
                        continue

                    # Colisão via NFP
                    collision = False

                    # Compara a nova peça contra TODAS as peças já alocadas
                    for (aloc_type_idx, aloc_copy_idx) in allocated:
                        # Pegamos o NFP correto da matriz: Fixo (aloc_type) vs Móvel (idx)
                        nfp_obj = NFPs[aloc_type_idx][Index]

                        # Pegamos a posição exata onde a peça fixa está
                        pos_ref_alocado = polygons[aloc_type_idx].position[aloc_copy_idx]

                        # Verificamos se a nova posição cai dentro desse NFP
                        # (Se cair dentro, significa que as formas físicas se sobrepõem)
                        pos_esc = Point(test_x, test_y)
                        print(f"Checking collision against Polygon {aloc_type_idx} (Copy {aloc_copy_idx}) at position ({pos_ref_alocado.x}, {pos_ref_alocado.y}) with test position ({pos_esc.x}, {pos_esc.y})")
                        if check_inside(nfp_obj, pos_ref_alocado, pos_esc):
                            print(f"COLLISION detected with Polygon {aloc_type_idx} (Copy {aloc_copy_idx}) at position ({pos_ref_alocado.x}, {pos_ref_alocado.y})!")
                            collision = True
                            break # Para de testar, já bateu
                        
                    if not collision:
                        print("Allocation valid!")
                        print(f"Allocated at position ({test_x}, {test_y})") # Posição alocada
                        polygons[Index].change_copy()
                        allocated.append((Index, idx_copy))

                        # Garantir que a lista de posições tem espaço suficiente
                        if len(polygons[Index].position) <= idx_copy:
                            polygons[Index].position.extend([Point(0, 0)] * (idx_copy + 1 - len(polygons[Index].position)))
                        polygons[Index].position[idx_copy] = Point(test_x, test_y)

                        # Plotar todas as peças alocadas para visualização usando matplotlib
                        for (plot_type_idx, plot_copy_idx) in allocated:
                            plot_pos = polygons[plot_type_idx].position[plot_copy_idx]
                            vertices = [(v.x + plot_pos.x, v.y + plot_pos.y) for v in polygons[plot_type_idx].vertex_list]
                            vertices.append(vertices[0])  # Fechar o polígono
                            xs, ys = zip(*vertices)
                            #plt.plot(xs, ys, label=f'Polygon Type {plot_type_idx} Copy {plot_copy_idx}')
                        # Defining strip height for visualization
                        # plt.axhline(y=height, color='r', linestyle='--', label='Strip Height')
                        # plt.legend()
                        # plt.show()
                        
                        pos_encontrada = True

                        historico_animacao.append({
                            'vertices': [Point(v.x + test_x, v.y + test_y) for v in polygons[Index].vertex_list],
                            'tipo': Index,
                            'copia': idx_copy
                        })
                        break # Para de testar, já alocou
                    else:
                        print("Allocation failed due to overlap.")
                if pos_encontrada:
                    break

        elif first_place == 1:
            #i.e. a posição é (0,0)
            pos = Point(X_min, Y_min)

            print(f"Testing first placement at ({pos.x}, {pos.y})")
            if ((pos.x - X_min) < 0 or 
                (pos.y + Y_max) > height or 
                (pos.y - Y_min) < 0):
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

                historico_animacao.append({
                            'vertices': [Point(v.x + pos.x, v.y + pos.y) for v in polygons[Index].vertex_list],
                            'tipo': Index,
                            'copia': idx_copy
                        })
                continue
        print("Finished animation.")
        
    except (ValueError, IndexError) as e:
        print("Invalid input error {e}")

mostrar_animacao(historico_animacao, height)