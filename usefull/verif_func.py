# FUNÇÃO MATEMÁTICA CENTRAL (D-FUNCTION)
from Class.class_polygon import polygon
import math
from Class.class_point import Point
from Class.class_nfp import NFP
from Class.class_item import item

EPSILON_GEOM = 1e-4

def D_function(xA, yA, xB, yB, xP, yP):
    """
    Calcula o Produto Vetorial (Cross Product) entre os vetores da aresta (AB) e o ponto P.
    
    Matematicamente: Determinante da matriz formada pelos vetores.
    
    Retorno:
      > 0: Ponto P está à esquerda da reta orientada AB.
      < 0: Ponto P está à direita da reta orientada AB.
      = 0: Ponto P está colinear (em cima da linha).
      
    Nota: O sinal depende se os vértices estão em sentido Horário ou Anti-Horário.
    """
    return (xA - xB) * (yA - yP) - (yA - yB) * (xA - xP)

def check_inside(nfp_poly, ref_Point, Point_teste):
    """
    Verifica se 'Point_teste' está ESTRITAMENTE DENTRO do Polígono de Não-Ajuste (NFP).
    
    Pontos na borda (D == 0) são considerados FORA (sem colisão), permitindo toque.
    Apenas pontos estritamente internos (D > 0 em todas arestas) causam colisão.
    """

    
    vertices = nfp_poly.vertex_list
    n = len(vertices)
    if n == 0: return False
    
    # Tolerância para considerar como "na borda"

    # Percorre todas as arestas do NFP
    for i in range(n):
        p1 = vertices[i]
        p2 = vertices[(i + 1) % n]
        
        # Transladamos os vértices do NFP pela posição da peça fixa
        xA_real = p1.x + ref_Point.x
        yA_real = p1.y + ref_Point.y
        xB_real = p2.x + ref_Point.x
        yB_real = p2.y + ref_Point.y
        
        # Cross product
        d = D_function(xA_real, yA_real, xB_real, yB_real, Point_teste.x, Point_teste.y)
        
        print(f"d = {d}")
        # Se o ponto estiver à direita (D < 0) ou na borda (D ≈ 0), NÃO há colisão
        if d <= EPSILON_GEOM:
            print("Point is outside or on the edge.")
            return False
    
    # Se o ponto está estritamente à esquerda de TODAS as arestas (D > 0), há COLISÃO
    return True 
def get_angle(vector):

    #Coletamos os ângulos para ordenar as arestas com base neles e realizar o Slope Diagram
    rad = math.atan2(vector.y, vector.x)

    if rad < 0:
        rad += 2*math.pi

    return rad

def reorder_edges_by_angle(edges):
    # Ordena arestas (vetores) por ângulo para o Slope Diagram.
    if not edges:
        return []
    
    # Encontrar a aresta com menor ângulo
    angles = [(get_angle(e), i) for i, e in enumerate(edges)]
    angles.sort()
    
    start_idx = angles[0][1]

    # Reordenar as arestas começando pela de menor ângulo
    return [edges[(start_idx + i) % len(edges)] for i in range(len(edges))]

def get_edges(pol):
    # Aqui, iremos coletar as arestas de cada polígono
    points = pol.vertex_list
    edges = []
    for i in range(len(points)):
        p1 = points[i]
        p2 = points[(i + 1) % len(points)]
        edges.append(p2 - p1)
    return edges
def get_negative_B(polB):
    # Pegamos o espaço vetorial -B para realizar a diferença de Mikowski e criar o NFP
    neg_points = [Point(-p.x, -p.y) for p in polB.vertex_list]
    # Reverter para manter sentido CCW ao negar
    neg_poly = polygon(len(neg_points), 0)
    neg_poly.vertex_list = neg_points
    return neg_poly

def bottom_left_vertex(points):
    idx_min = 0

    for i in range(1, len(points)):
        current = points[i]
        lowest = points[idx_min]

        if (current.y < lowest.y) or (current.y == lowest.y and current.x < lowest.x):
            idx_min = i
    
    return idx_min

def Minkowski_Sum(polygons):
    NFPs = []
    for i in range(len(polygons)):
        NFPs.append([])
        for j in range(len(polygons)):
            print(f"\nBuilding through Mikowski Sum the NFP between {j} sliding around fixed type {i}.")

            polA = polygons[i]
            polB = polygons[j]
            polB_neg = get_negative_B(polB)

            edgesA = get_edges(polA)
            edgesB = get_edges(polB_neg)

            # Reordenar arestas por ângulo
            edgesA = reorder_edges_by_angle(edgesA)
            edgesB = reorder_edges_by_angle(edgesB)

            merged_edges = []
            ia, ib = 0, 0
            na, nb = len(edgesA), len(edgesB)

            # Loop até ter processado todas as arestas de ambos os polígonos
            # O Slope Diagram é construído comparando os ângulos das arestas de A e B e mesclando-as em ordem crescente de ângulo
            while ia < na and ib < nb:
                vecA = edgesA[ia]
                vecB = edgesB[ib]

                angleA = get_angle(vecA)
                angleB = get_angle(vecB)

                # Tolerância para comparação de ângulos (para lidar com erros de ponto flutuante)
                epsilon = 1e-10

                if angleA < angleB - epsilon:
                    merged_edges.append(vecA)
                    ia += 1
                elif angleB < angleA - epsilon:
                    merged_edges.append(vecB)
                    ib += 1
                else:
                    # Ângulos são aproximadamente iguais, soma os vetores
                    merged_edges.append(vecA + vecB)
                    ia += 1
                    ib += 1
            
            # Adiciona as arestas restantes
            while ia < na:
                merged_edges.append(edgesA[ia])
                ia += 1
            
            while ib < nb:
                merged_edges.append(edgesB[ib])
                ib += 1
            
            # Pegar índices dos vértices mais baixos à esquerda
            start_idxA = bottom_left_vertex(polA.vertex_list)
            start_idxB = bottom_left_vertex(polB_neg.vertex_list)
            
            # Somar as coordenadas dos pontos de partida
            start_point = Point(
                polA.vertex_list[start_idxA].x + polB_neg.vertex_list[start_idxB].x,
                polA.vertex_list[start_idxA].y + polB_neg.vertex_list[start_idxB].y
            )

            # Construir os vértices do NFP percorrendo as arestas mescladas
            nfp_points = [start_point]
            current = start_point

            for edge in merged_edges[:-1]:  # Não incluir a última aresta para evitar duplicação
                current = current + edge
                nfp_points.append(current)

            # Verificar se o polígono fecha corretamente
            # O último ponto deve ser igual ao primeiro
            if len(merged_edges) > 0:
                final_check = current + merged_edges[-1]
                dist = math.sqrt((final_check.x - start_point.x)**2 + (final_check.y - start_point.y)**2)
                if dist > 1e-6:
                    print(f"WARNING: NFP polygon doesn't close properly. Distance: {dist}")

            # Criar polígono para o NFP
            nfp_poly = polygon(len(nfp_points), 0)
            nfp_poly.vertex_list = nfp_points
            NFPs[i].append(nfp_poly)

    return NFPs

def MKSum_Irregular(itens):
    """
    Gera NFPs para dois cenários:
    - lista de itens irregulares (cada item com atributo ``polygons``): retorna uma matriz
    em que cada célula ``NFPs[i][j]`` contém um objeto ``NFP`` com uma lista plana de
    NFPs, um para cada combinação entre os polígonos internos do item fixo ``i`` e do item
    móvel ``j``.
    Exemplo: se o item A tem 2 polígonos e o item B tem 3, então ``NFPs[A][B]`` terá 6
    polígonos NFP armazenados dentro de um único objeto ``NFP``.
    """

    if not itens:
        return []  # Retorna uma matriz vazia se não houver itens

    
    # itens irregulares compostos por múltiplos polígonos.
    NFPs = []
    for i, item_fixed in enumerate(itens):
        NFPs.append([])
        for j, item_mobile in enumerate(itens):
            print(f"\nBuilding irregular NFP for item {j} sliding around fixed item {i}.")

            pair_nfp = NFP(i, j)
            for idx_fixed, polA in enumerate(item_fixed.polygons):
                for idx_mobile, polB in enumerate(item_mobile.polygons):
                    print(f"  - Polygon pair fixed {idx_fixed} vs mobile {idx_mobile}")

                    polB_neg = get_negative_B(polB)
                    edgesA = reorder_edges_by_angle(get_edges(polA))
                    edgesB = reorder_edges_by_angle(get_edges(polB_neg))

                    merged_edges = []
                    ia, ib = 0, 0
                    na, nb = len(edgesA), len(edgesB)

                    while ia < na and ib < nb:
                        vecA = edgesA[ia]
                        vecB = edgesB[ib]
                        angleA = get_angle(vecA)
                        angleB = get_angle(vecB)
                        epsilon = 1e-10

                        if angleA < angleB - epsilon:
                            merged_edges.append(vecA)
                            ia += 1
                        elif angleB < angleA - epsilon:
                            merged_edges.append(vecB)
                            ib += 1
                        else:
                            merged_edges.append(vecA + vecB)
                            ia += 1
                            ib += 1

                    while ia < na:
                        merged_edges.append(edgesA[ia])
                        ia += 1

                    while ib < nb:
                        merged_edges.append(edgesB[ib])
                        ib += 1

                    start_idxA = bottom_left_vertex(polA.vertex_list)
                    start_idxB = bottom_left_vertex(polB_neg.vertex_list)
                    start_point = Point(
                        polA.vertex_list[start_idxA].x + polB_neg.vertex_list[start_idxB].x,
                        polA.vertex_list[start_idxA].y + polB_neg.vertex_list[start_idxB].y
                    )

                    nfp_points = [start_point]
                    current = start_point

                    for edge in merged_edges[:-1]:
                        current = current + edge
                        nfp_points.append(current)

                    if len(merged_edges) > 0:
                        final_check = current + merged_edges[-1]
                        dist = math.sqrt((final_check.x - start_point.x)**2 + (final_check.y - start_point.y)**2)
                        if dist > 1e-6:
                            print(f"WARNING: NFP polygon doesn't close properly. Distance: {dist}")

                    nfp_poly = polygon(len(nfp_points), 0)
                    nfp_poly.vertex_list = nfp_points
                    pair_nfp.add_polygon(nfp_poly)

            NFPs[i].append(pair_nfp)
    return NFPs
def segment_intersectionn(p1, p2, p3, p4):
    # Calcula a interseção entre os segmentos p1p2 e p3p4
    denom = (p2.x - p1.x) * (p4.y - p3.y) - (p2.y - p1.y) * (p4.x - p3.x)
    
    if abs(denom) < 1e-10:
        print("Segments are parallel or coincident.")
        return None  # Segmentos são paralelos ou coincidentes
        
    ua = ((p3.x - p4.x) * (p1.y - p3.y) - (p3.y - p4.y) * (p1.x - p3.x)) / denom
    ub = -((p1.x - p2.x) * (p1.y - p3.y) - (p1.y - p2.y) * (p1.x - p3.x)) / denom
    
    print(f"Calculated ua: {ua}, ub: {ub}")
    if 0 <= ua <= 1 and 0 <= ub <= 1:
        # Os segmentos se intersectam dentro dos limites
        print("intersect true")
        return Point(p1.x + ua * (p2.x - p1.x), p1.y + ua * (p2.y - p1.y))
    
    return None  # Os segmentos não se intersectam dentro dos limites 

def segment_intersection(p1, p2, p3, p4):
    x1, y1 = p1.x, p1.y
    x2, y2 = p2.x, p2.y
    x3, y3 = p3.x, p3.y
    x4, y4 = p4.x, p4.y

    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if den == 0:
        return None # Linhas são paralelas ou colineares
    
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
    u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / den

    # CORREÇÃO: Adicionando tolerância nas pontas dos vetores
    eps = 1e-5
    if -eps <= t <= 1 + eps and -eps <= u <= 1 + eps:
        intersec_x = x1 + t * (x2 - x1)
        intersec_y = y1 + t * (y2 - y1)
        return Point(intersec_x, intersec_y)
    
    return None

def check_inside_cand(allocated, NFPs, polygons, point, Index):

    collision = False

    for (aloc_type_idx, aloc_copy_idx) in allocated:
        # Pegamos o NFP correto da matriz: Fixo (aloc_type) vs Móvel (idx)
        nfp_obj = NFPs[aloc_type_idx][Index]

        # Pegamos a posição exata onde a peça fixa está
        pos_ref_alocado = polygons[aloc_type_idx].position[aloc_copy_idx]

        # Verificamos se a nova posição cai dentro desse NFP
        # (Se cair dentro, significa que as formas físicas se sobrepõem)
        pos_esc = Point(point.x, point.y)
        print(f"Checking collision against Polygon {aloc_type_idx} (Copy {aloc_copy_idx}) at position ({pos_ref_alocado.x}, {pos_ref_alocado.y}) with test position ({pos_esc.x}, {pos_esc.y})")
        if check_inside(nfp_obj, pos_ref_alocado, pos_esc):
            print(f"COLLISION detected with Polygon {aloc_type_idx} (Copy {aloc_copy_idx}) at position ({pos_ref_alocado.x}, {pos_ref_alocado.y})!")
            collision = True
            break # Para de testar, já bateu


    if not collision:
        print("No collision detected for this candidate position.")
        return True
    else:     
        print("Candidate position is invalid due to collision.")
        return False
        
def check_inside_cand_irregular(allocated, NFPs, itens, point, Index):
        
    collision = False

    for (aloc_type_idx, aloc_copy_idx) in allocated:
    # Pegamos o NFP correto da matriz: Fixo (aloc_type) vs Móvel (idx)
        nfp_obj = NFPs[aloc_type_idx][Index]

        # Pegamos a posição exata onde a peça fixa está
        pos_ref_alocado = itens[aloc_type_idx].position[aloc_copy_idx]

        # Verificamos se a nova posição cai dentro desse NFP
        # (Se cair dentro, significa que as formas físicas se sobrepõem)
        pos_esc = Point(point.x, point.y)
        print(f"Checking collision against Polygon {aloc_type_idx} (Copy {aloc_copy_idx}) at position ({pos_ref_alocado.x}, {pos_ref_alocado.y}) with test position ({pos_esc.x}, {pos_esc.y})")
        for nfp_poly in getattr(nfp_obj, "polygons", [nfp_obj]):
            if check_inside(nfp_poly, pos_ref_alocado, pos_esc):
                print(f"COLLISION detected with Polygon {aloc_type_idx} (Copy {aloc_copy_idx}) at position ({pos_ref_alocado.x}, {pos_ref_alocado.y})!")
                collision = True
                break

        if collision:
            break # Para de testar, já bateu
    if not collision:
        print("No collision detected for this candidate position.")
        return True
    else:     
        print("Candidate position is invalid due to collision.")
        return False