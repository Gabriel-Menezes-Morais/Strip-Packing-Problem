from typing import List
from Class.class_point import Point
from Class.class_polygon import polygon


class item:
    def __init__(self, id, copy):
        self.id = id
        self.polygons: List[polygon] = []
        self.num_polygons = 0
        self.copy = copy
        self.max_length_x = 0
        self.max_length_y = 0
        self.area = 0
        self.bounding_box_area_value = 0

        # Lista de posições onde cada item representa a coordenada (x,y) de uma cópia
        self.position: List[Point] = [None] * copy
    def change_copy(self):
        """Decrementa o contador de cópias disponíveis."""
        self.copy = self.copy - 1
    def get_position(self, i):
        """Solicita ao usuário as posições iniciais de todas as cópias."""
        for k in range(self.copy):
            try:
                raw_input = input(f"What is the coordinates for copy {k} of Type {i} (x y)?\n").split()
                x, y = float(raw_input[0]), float(raw_input[1])
                self.position[k] = Point(x, y)
            except (ValueError, IndexError):
                print("Invalid input. Please enter two numbers separated by space.")
                return False
        return True
    
    def get_polygons(self):
        return self.polygons
    def get_id(self):
        return self.id
    def get_polygon(self, i):
        return self.polygons[i]
    def calcular_area(self):
        
        self.area = sum(p.area() for p in self.polygons)
        return self.area
    def calcular_max_length(self):

        max_length = [p.max_length() for p in self.polygons]
        max_length_x = max(length[0] for length in max_length)
        max_length_y = max(length[1] for length in max_length)

        self.max_length_x = max_length_x
        self.max_length_y = max_length_y

        return max_length_x, max_length_y
    def calcular_bounding_box_area(self):
        self.bounding_box_area_value = self.max_length_x * self.max_length_y
        return self.bounding_box_area_value
    def ref_distance(self):
        if not self.polygons:
            return 0, 0, 0, 0

        ref = self.polygons[0].vertex_list[0]
        all_x = []
        all_y = []

        for pol in self.polygons:
            for vertex in pol.vertex_list:
                all_x.append(vertex.x)
                all_y.append(vertex.y)

        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)

        return (abs(ref.x - min_x), abs(ref.x - max_x),
                abs(ref.y - min_y), abs(ref.y - max_y))
    def normalize_to_reference(self):
        """
        Translada todos os polígonos do item para que o primeiro vértice 
        do primeiro polígono se torne a origem (0,0) local do item.
        Isso alinha o referencial do usuário com a matemática do NFP.
        """
        if not self.polygons or not self.polygons[0].vertex_list:
            return
            
        ref_ponto = self.polygons[0].vertex_list[0]
        ref_x, ref_y = ref_ponto.x, ref_ponto.y
        
        for poly in self.polygons:
            for vertex in poly.vertex_list:
                vertex.x -= ref_x
                vertex.y -= ref_y