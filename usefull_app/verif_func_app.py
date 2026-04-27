# FUNÇÃO MATEMÁTICA CENTRAL (D-FUNCTION)
import math

from class_app.class_polygon_app import polygon
from class_app.class_point_app import Point


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
    if n == 0:
        return False

    for i in range(n):
        p1 = vertices[i]
        p2 = vertices[(i + 1) % n]

        xA_real = p1.x + ref_Point.x
        yA_real = p1.y + ref_Point.y
        xB_real = p2.x + ref_Point.x
        yB_real = p2.y + ref_Point.y

        d = D_function(xA_real, yA_real, xB_real, yB_real, Point_teste.x, Point_teste.y)

        print(f"d = {d}")
        if d <= 0:
            print("Point is outside or on the edge.")
            return False

    return True


def get_angle(vector):
    rad = math.atan2(vector.y, vector.x)
    if rad < 0:
        rad += 2 * math.pi
    return rad


def reorder_edges_by_angle(edges):
    if not edges:
        return []

    angles = [(get_angle(e), i) for i, e in enumerate(edges)]
    angles.sort()
    start_idx = angles[0][1]
    return [edges[(start_idx + i) % len(edges)] for i in range(len(edges))]


def get_edges(pol):
    points = pol.vertex_list
    edges = []
    for i in range(len(points)):
        p1 = points[i]
        p2 = points[(i + 1) % len(points)]
        edges.append(p2 - p1)
    return edges


def get_negative_B(polB):
    neg_points = [Point(-p.x, -p.y) for p in polB.vertex_list]
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

            edgesA = reorder_edges_by_angle(edgesA)
            edgesB = reorder_edges_by_angle(edgesB)

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
                polA.vertex_list[start_idxA].y + polB_neg.vertex_list[start_idxB].y,
            )

            nfp_points = [start_point]
            current = start_point

            for edge in merged_edges[:-1]:
                current = current + edge
                nfp_points.append(current)

            if len(merged_edges) > 0:
                final_check = current + merged_edges[-1]
                dist = math.sqrt((final_check.x - start_point.x) ** 2 + (final_check.y - start_point.y) ** 2)
                if dist > 1e-6:
                    print(f"WARNING: NFP polygon doesn't close properly. Distance: {dist}")

            nfp_poly = polygon(len(nfp_points), 0)
            nfp_poly.vertex_list = nfp_points
            NFPs[i].append(nfp_poly)

    return NFPs


def segment_intersection(p1, p2, p3, p4):
    """
    Calcula a intersecção entre dois segmentos de reta: (p1, p2) e (p3, p4).
    Retorna o Ponto de intersecção se houver, ou None caso não se cruzem.
    """
    x1, y1 = p1.x, p1.y
    x2, y2 = p2.x, p2.y
    x3, y3 = p3.x, p3.y
    x4, y4 = p4.x, p4.y

    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if den == 0:
        return None

    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
    u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / den

    if 0 <= t <= 1 and 0 <= u <= 1:
        intersec_x = x1 + t * (x2 - x1)
        intersec_y = y1 + t * (y2 - y1)
        return Point(intersec_x, intersec_y)

    return None


def check_inside_cand(allocated, NFPs, polygons, point, Index):
    collision = False

    for (aloc_type_idx, aloc_copy_idx) in allocated:
        nfp_obj = NFPs[aloc_type_idx][Index]
        pos_ref_alocado = polygons[aloc_type_idx].position[aloc_copy_idx]

        pos_esc = Point(point.x, point.y)
        print(
            f"Checking collision against Polygon {aloc_type_idx} (Copy {aloc_copy_idx}) at position "
            f"({pos_ref_alocado.x}, {pos_ref_alocado.y}) with test position ({pos_esc.x}, {pos_esc.y})"
        )
        if check_inside(nfp_obj, pos_ref_alocado, pos_esc):
            print(
                f"COLLISION detected with Polygon {aloc_type_idx} (Copy {aloc_copy_idx}) at position "
                f"({pos_ref_alocado.x}, {pos_ref_alocado.y})!"
            )
            collision = True
            break

    if not collision:
        print("No collision detected for this candidate position.")
        return True

    print("Candidate position is invalid due to collision.")
    return False