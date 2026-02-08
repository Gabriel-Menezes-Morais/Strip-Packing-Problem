# FUNÇÃO MATEMÁTICA CENTRAL (D-FUNCTION)
from Class.class_polygon import polygon
import math
from Class.class_point import Point
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
        if d <= 0:
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
    """Ordena arestas (vetores) por ângulo para o Slope Diagram."""
    if not edges:
        return []
    
    # Encontrar a aresta com menor ângulo
    angles = [(get_angle(e), i) for i, e in enumerate(edges)]
    angles.sort()
    
    start_idx = angles[0][1]
    return [edges[(start_idx + i) % len(edges)] for i in range(len(edges))]

def get_edges(pol):
    #Aqui, iremos coletar as arestas de cada polígono
    points = pol.vertex_list
    edges = []
    for i in range(len(points)):
        p1 = points[i]
        p2 = points[(i + 1) % len(points)]
        edges.append(p2 - p1)
    return edges
def get_negative_B(polB):
    # Pegamos o espaço vetorial -B para realizar a diferença de Mikowski
    # e criar o NFP
    neg_points = [Point(-p.x, -p.y) for p in polB.vertex_list]
    # Reverter para manter sentido CCW ao negar
    neg_points = neg_points[::-1]
    neg_poly = polygon(len(neg_points), 0)
    neg_poly.vertex_list = neg_points
    return neg_poly

def lowest_left_vertex(points):
    idx_min = 0

    for i in range(1, len(points)):
        current = points[i]
        lowest = points[idx_min]

        if(current.y < lowest.y) or (current.y == lowest.y and current.x < lowest.x):
            idx_min = i
    
    return idx_min

def reorder_by_angle(points):

    start_idx = lowest_left_vertex(points)

    return points[start_idx:] + points[:start_idx]

def normalize_polygon(pol):
    """
    Normaliza o polígono movendo o vértice inferior esquerdo para a origem (0, 0).
    Isso é essencial para o cálculo correto do NFP via Soma de Minkowski.
    """
    if not pol.vertex_list:
        return pol
    
    # Encontra o vértice inferior esquerdo
    idx = lowest_left_vertex(pol.vertex_list)
    ref_vertex = pol.vertex_list[idx]
    
    # Cria uma cópia normalizada do polígono
    normalized_poly = polygon(len(pol.vertex_list), 0)
    normalized_poly.vertex_list = [
        Point(v.x - ref_vertex.x, v.y - ref_vertex.y) 
        for v in pol.vertex_list
    ]
    
    return normalized_poly

def Mikowski_Sum(polygons):
    NFPs = []
    for i in range(len(polygons)):
        NFPs.append([])
        for j in range(len(polygons)):
            print(f"\nBuilding through Mikowski Sum the NFP between {j} sliding around fixed type {i}.")

            # Normaliza os polígonos antes de calcular o NFP
            polA = normalize_polygon(polygons[i])
            polB = normalize_polygon(polygons[j])
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
            start_idxA = lowest_left_vertex(polA.vertex_list)
            start_idxB = lowest_left_vertex(polB_neg.vertex_list)
            
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
            # O último ponto deve ser igual ao primeiro (ou muito próximo)
            if len(merged_edges) > 0:
                final_check = current + merged_edges[-1]
                dist = math.sqrt((final_check.x - start_point.x)**2 + (final_check.y - start_point.y)**2)
                if dist > 1e-6:
                    print(f"WARNING: NFP polygon doesn't close properly. Distance: {dist}")

            # Criar polígono para o NFP (sem duplicar o primeiro vértice)
            nfp_poly = polygon(len(nfp_points), 0)
            nfp_poly.vertex_list = nfp_points
            NFPs[i].append(nfp_poly)

    return NFPs