"""
Nesse algoritmo, iremos desenvolver a heurística bottom-left, de modo a resolver o strip packing problem de maneira rápida e eficaz.
Ainda que não alcance a solução ótima. Ainda sim, de acordo com o artigo 
"""

from usefull.verif_func import check_inside
from Class.class_polygon import polygon

polygons = []

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

    print(f"--- Positions for Type {i} ---") 
    new_poly.position_get(i)
    
# Definição da Matriz NFP (No-Fit Polygon)
# A matriz NFPs[i][j] guarda a geometria que define onde J não pode encostar em I.
NFPs = [] 

print("\n--- NFP Configuration ---")
for i in range(len(polygons)):
    NFPs.append([]) # Cria uma nova linha na matriz
    for j in range(len(polygons)):
        print(f"\nDefining NFP: Mobile Type {j} sliding around Fixed Type {i}")
        v_nfp = int(input(f"How many vertices does this NFP have?\n"))
        
        
        nfp_poly = polygon(v_nfp, 0)
        
        for k in range(v_nfp):
            nfp_poly.vertex(k)
        
        NFPs[i].append(nfp_poly)          

allocated = [] # Guarda tuplas: (Indice_Tipo, Indice_Copia_Usada)
flag = 0

# Alocação da Primeira Peça
# Esta peça só precisa respeitar as bordas da faixa (altura e largura), pois não há outras peças.
while(flag == 0):
    try:
        Index = int(input("\nWhich polygon Type do you want to place first?\n"))
        if Index >= len(polygons): 
            print("Invalid index.")
            continue # Volta ao inicio do while
        
        idx_copy = 0
        if polygons[Index].copy > 1:
            # Pergunta qual das posições pré-definidas usar
            idx_copy = int(input(f"Which copy index (0 to {len(polygons[Index].position)-1})?\n"))
        
        # Pega as dimensões da Bounding Box
        X_min, X_max, Y_min, Y_max = polygons[Index].height()
        
        pos_escolhida = polygons[Index].position[idx_copy]

        # Verificação de Fronteira (Boundaries)
        # Garante que a peça inteira (ref + distancias máximas) esteja dentro da faixa
        if ((pos_escolhida.x - X_min) < 0 or
            (pos_escolhida.y + Y_max) > height or
            (pos_escolhida.y - Y_min) < 0):
            
            print("Error: Polygon is out of strip boundaries.")
            flag = 0 # Mantém no loop para tentar de novo
        else:
            flag = 1 # Sai do loop
            polygons[Index].change_copy()
            allocated.append((Index, idx_copy))
            print("First polygon placed successfully.")

    except (ValueError, IndexError):
        print("Invalid input error.")

# Alocação das Peças Seguintes
# Agora precisamos checar Fronteiras e Colisões com peças anteriores.
while True:
    cont = input("\nAllocate another polygon? (y/n): ")
    if cont.lower() != 'y': break

    try:
        idx = int(input("Which polygon TYPE do you want to place?\n"))
        
        if idx >= len(polygons):
            print("Invalid type.")
            continue
            
        if polygons[idx].copy <= 0:
            print("No copies left for this polygon type.")
            continue

        idx_copy = int(input(f"Which copy index (0 to {len(polygons[idx].position)-1})?\n"))
        cand_pos = polygons[idx].position[idx_copy] # Posição que queremos testar

        # Check A: Fronteira (Igual à fase 1)
        X_min, X_max, Y_min, Y_max = polygons[idx].height()
        if ((cand_pos.x - X_min) < 0 or 
            (cand_pos.y + Y_max) > height or 
            (cand_pos.y - Y_min) < 0):
            print("Error: Out of bounds.")
            continue

        # Check B: Colisão via NFP
        collision = False

        # Compara a nova peça contra TODAS as peças já alocadas
        for (aloc_type_idx, aloc_copy_idx) in allocated:
            # Pegamos o NFP correto da matriz: Fixo (aloc_type) vs Móvel (idx)
            nfp_obj = NFPs[aloc_type_idx][idx]

            # Pegamos a posição exata onde a peça fixa está
            pos_ref_alocado = polygons[aloc_type_idx].position[aloc_copy_idx]

            # Verificamos se a nova posição cai dentro desse NFP
            # (Se cair dentro, significa que as formas físicas se sobrepõem)
            if check_inside(nfp_obj, pos_ref_alocado, cand_pos):
                print(f"COLLISION detected with Polygon {aloc_type_idx} (Copy {aloc_copy_idx})!")
                collision = True
                break # Para de testar, já bateu
        
        if not collision:
            print("Allocation valid!")
            polygons[idx].change_copy()
            allocated.append((idx, idx_copy))
        else:
            print("Allocation failed due to overlap.")

    except ValueError:
        print("Invalid input.")