from typing import List
from class_app.class_point_app import Point

class polygon:
    def __init__(self, vertices, copy):
        self.vertex_list: List[Point] = []
        self.vertices = vertices
        # Lista de Pontos onde cada item representa a coordenada (x,y) de uma cópia
        self.position: List[Point] = [None] * copy
        self.copy = copy
        
    
    def change_copy(self):
        """Decrementa o contador de cópias disponíveis."""
        self.copy = self.copy - 1

    def length(self):
        return len(self.vertex_list)

    def height(self): 
        """
        Calcula a 'Bounding Box' do polígono.
        Retorna as distâncias relativas do ponto de referência (vértice 0) 
        até os extremos (Mínimo e Máximo) em X e Y.
        Isso é crucial para verificar se a peça sai das bordas da faixa.
        """
        if not self.vertex_list:
            return 0,0,0,0
        
        all_x = [p.x for p in self.vertex_list]
        all_y = [p.y for p in self.vertex_list]

        # Encontra os limites absolutos
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)

        ref = self.vertex_list[0] # Ponto de referência (normalmente (0,0) local)

        # Calcula distâncias relativas à referência
        return (abs(ref.x - min_x), abs(ref.x - max_x), 
                abs(ref.y - min_y), abs(ref.y - max_y))
    
    def limitsforBL(self):
        """
        Retorna os limites x e y máximos do polígono para o algoritmo Bottom-Left.
        """
        if not self.vertex_list:
            return 0, 0
        all_x = [p.x for p in self.vertex_list]
        all_y = [p.y for p in self.vertex_list]

        print(max(all_x), max(all_y))
        
        return max(all_x), max(all_y)

    def position_get(self, i):
        """Solicita ao usuário as posições iniciais de todas as cópias."""
        for k in range(self.copy):
            try:
                raw_input = input(f"What is the coordinates for copy {k} of Type {i} (x y)?\n").split()
                pos = list(map(float, raw_input))
                
                # Armazena diretamente o Ponto na lista de posições
                novo_Point = Point(x=pos[0], y=pos[1])
                self.position.append(novo_Point)
            except ValueError:
                print("Invalid input.")
                self.position.append(Point(0,0))

    def vertex(self, j): 
        """Solicita e armazena um vértice."""
        try:
            raw = input(f"Vertex {j} coordinates (x y)?\n").split()
            xy = list(map(float, raw))
            novo_Point = Point(x=xy[0], y=xy[1])

            print(f"Vertex added: ({novo_Point.x}, {novo_Point.y})")

            self.vertex_list.append(novo_Point)
        except ValueError as e:
            print(f"Invalid input. {e}")
            pass

if __name__ == "__main__":
    # Exemplo de uso
    pol = polygon(3, 2)  # Polígono com 3 vértices e 2 cópias
    for i in range(pol.vertices):
        pol.vertex(i)
    
    pol.position_get(0)  # Solicita posições para as cópias do tipo 0