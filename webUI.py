from usefull_app.verif_func_app import Minkowski_Sum, check_inside
from class_app.class_polygon_app import polygon
from class_app.class_point_app import Point
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import streamlit as st


st.title("Strip Packing Verification Tool")

# clear buffers

if st.session_state.get('Generate NFPs', True):
    if st.button("Clear Buffers"):
        del st.session_state['Generate NFPs']
        del st.session_state['strip_height']
        del st.session_state['num_types']
        del st.session_state['generate_polygons']
polygons = []

limits_x = []
limits_y = []
limits_x.append(0)
limits_y.append(0)

# Configuração Inicial
height = int(st.number_input("What is the strip height?", min_value=1, step=1, key='strip_height'))
numbers_p = int(st.number_input("How many TYPES of convex polygons?", min_value=1, step=1, key='num_types'))
num_p = numbers_p

if (height and num_p and "generate_polygons" not in st.session_state and st.button("Generate Polygons", key='generate_polygons')) or (st.session_state['generate_polygons']):
    for i in range(num_p):
        v = int(st.number_input(f"How many vertices does polygon Type {i} have?", min_value=1, step=1, key=f'vertices_type_{i}'))
        copies = int(st.number_input(f"How many copies does polygon Type {i} have?", min_value=1, step=1, key=f'copies_type_{i}'))

        new_poly = polygon(v, copies)
        polygons.append(new_poly)

        if st.button(f"Enter vertices for polygon Type {i}"):
            for j in range(v):
                new_poly.vertex(j)
    if "Generate NFPs" not in st.session_state:
        st.session_state['Generate NFPs'] = True

if st.session_state.get('Generate NFPs', True):
    if st.button("Generate NFPs"):
        st.write("--- Generating NFP Approximations ---")
        NFPs = Minkowski_Sum(polygons)

        allocated = [] # Guarda tuplas: (Indice_Tipo, Indice_Copia_Usada)
        flag = 0
        pos = Point(0, 0)

        while True:
            cont = st.text_input("\nAllocate polygon? (y/n): ")
            if cont.lower() != 'y': break

            try:
                Index = int(st.number_input("\nWhich polygon type do you want to place?"))
                if Index >= len(polygons) or Index < 0 or polygons[Index].copy <= 0:
                    st.error("Invalid index.")
                    continue 

                idx_copy = 0
                if polygons[Index].copy >= 1:
                    idx_copy = int(st.number_input(f"Which copy index (0 to {len(polygons[Index].position)-1})?\n"))

                X_min, X_max, Y_min, Y_max = polygons[Index].height()

                first_place = 1
                collision = False

                for (aloc_type_idx, aloc_copy_idx) in allocated:
                    first_place = 0

                    nfp_obj = NFPs[aloc_type_idx][Index]
                    pos_ref_alocado = polygons[aloc_type_idx].position[aloc_copy_idx]
                        
                    for v in nfp_obj.vertex_list:
                        limits_x.append(pos_ref_alocado.x + v.x)
                        limits_y.append(pos_ref_alocado.y + v.y)

                    limits_x = sorted(list(set([max(0, x) for x in limits_x])))
                    limits_y = sorted(list(set([max(0, y) for y in limits_y])))

                if first_place == 0:
                    limits_x.sort()
                    limits_y.sort()

                    pos_encontrada = False
                    for X in limits_x:

                        for Y in limits_y:

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

                            collision = False

                            for (aloc_type_idx, aloc_copy_idx) in allocated:
                                nfp_obj = NFPs[aloc_type_idx][Index]

                                pos_ref_alocado = polygons[aloc_type_idx].position[aloc_copy_idx]

                                pos_esc = Point(test_x, test_y)
                                
                                if check_inside(nfp_obj, pos_ref_alocado, pos_esc):
                                    print(f"COLLISION detected with Polygon {aloc_type_idx} (Copy {aloc_copy_idx}) at position ({pos_ref_alocado.x}, {pos_ref_alocado.y})!")
                                    collision = True
                                    break
                                
                            if not collision:
                                polygons[Index].change_copy()
                                allocated.append((Index, idx_copy))

                                if len(polygons[Index].position) <= idx_copy:
                                    polygons[Index].position.extend([Point(0, 0)] * (idx_copy + 1 - len(polygons[Index].position)))
                                polygons[Index].position[idx_copy] = Point(test_x, test_y)
                                
                                pos_encontrada = True
                                break 
                            else:
                                print("Allocation failed due to overlap.")
                        if pos_encontrada:
                            break

                elif first_place == 1:

                    pos = Point(X_min, Y_min)

                    print(f"Testing first placement at ({pos.x}, {pos.y})")
                    if ((pos.x - X_min) < 0 or 
                        (pos.y + Y_max) > height or 
                        (pos.y - Y_min) < 0):
                        print("Error: Out of bounds.")
                        continue
                    else:
                        polygons[Index].change_copy()
                        allocated.append((Index, idx_copy))

                        if len(polygons[Index].position) <= idx_copy:
                            polygons[Index].position.extend([Point(0, 0)] * (idx_copy + 1 - len(polygons[Index].position)))
                        polygons[Index].position[idx_copy] = Point(pos.x, pos.y)

                        continue
                print("Finished animation.")
                
            except (ValueError, IndexError) as e:
                print("Invalid input error {e}")
