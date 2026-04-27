from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Optional

import matplotlib.pyplot as plt
import streamlit as st

from usefull_app.verif_func_app import Minkowski_Sum, segment_intersection, check_inside_cand
from class_app.class_polygon_app import polygon
from class_app.class_point_app import Point


EPSILON = 1e-9
MAX_X = 999999


@dataclass
class AllocationResult:
    step: int
    type_idx: int
    copy_idx: int
    status: str
    message: str
    position: Optional[Point]


def is_out_of_bounds(candidate: Point, x_min: float, y_min: float, y_max: float, strip_height: float) -> bool:
    if candidate.x < (x_min - EPSILON):
        return True
    if candidate.y > (strip_height - y_max + EPSILON):
        return True
    if candidate.y < (y_min - EPSILON):
        return True
    return False


def candidate_better(candidate: Point, current: Optional[Point]) -> bool:
    if current is None:
        return True
    if candidate.x < current.x:
        return True
    if candidate.x == current.x and candidate.y < current.y:
        return True
    return False


def parse_instance_text(raw_text: str):
    lines = [ln.strip() for ln in raw_text.splitlines() if ln.strip() != ""]
    idx = 0

    height = int(lines[idx])
    idx += 1

    num_types = int(lines[idx])
    idx += 1

    poly_specs = []
    for type_idx in range(num_types):
        vertices_count = int(lines[idx])
        idx += 1
        copies = int(lines[idx])
        idx += 1

        vertices = []
        for _ in range(vertices_count):
            x_str, y_str = lines[idx].split()
            idx += 1
            vertices.append((float(x_str), float(y_str)))

        poly_specs.append(
            {
                "type_idx": type_idx,
                "vertices_count": vertices_count,
                "copies": copies,
                "vertices": vertices,
            }
        )

    requests = []
    while idx < len(lines):
        cmd = lines[idx].lower()
        idx += 1
        if cmd != "y":
            break

        type_idx = int(lines[idx])
        idx += 1
        copy_idx = int(lines[idx])
        idx += 1
        requests.append((type_idx, copy_idx))

    return height, poly_specs, requests


def build_polygons(poly_specs) -> List[polygon]:
    polys: List[polygon] = []
    for spec in poly_specs:
        p = polygon(spec["vertices_count"], spec["copies"])
        p.vertex_list = [Point(x, y) for x, y in spec["vertices"]]
        polys.append(p)
    return polys


def find_position_for_piece(type_idx: int, idx_copy: int, strip_height: float, polygons: List[polygon], allocated: List[Tuple[int, int]], nfp_matrix):
    x_min, _, y_min, y_max = polygons[type_idx].height()

    if not allocated:
        first = Point(x_min, y_min)
        if is_out_of_bounds(first, x_min, y_min, y_max, strip_height):
            return None, "Primeira peça fora dos limites"
        if not check_inside_cand(allocated, nfp_matrix, polygons, first, type_idx):
            return None, "Primeira peça em colisão"
        return first, "Primeira peça alocada"

    best: Optional[Point] = None
    limit_segments = [
        (Point(0, 0), Point(0, strip_height - y_max)),
        (Point(0, 0), Point(MAX_X, 0)),
        (Point(0, strip_height - y_max), Point(MAX_X, strip_height - y_max)),
    ]

    for fixed_type_idx, fixed_copy_idx in allocated:
        nfp_obj = nfp_matrix[fixed_type_idx][type_idx]
        fixed_pos = polygons[fixed_type_idx].position[fixed_copy_idx]

        if not nfp_obj.vertex_list:
            continue

        for i, vert in enumerate(nfp_obj.vertex_list):
            next_vert = nfp_obj.vertex_list[(i + 1) % len(nfp_obj.vertex_list)]

            p1 = Point(vert.x + fixed_pos.x, vert.y + fixed_pos.y)
            p2 = Point(next_vert.x + fixed_pos.x, next_vert.y + fixed_pos.y)

            if not ((p1.x < -EPSILON or p1.y < -EPSILON or p1.y > strip_height + EPSILON) and (p2.x < -EPSILON or p2.y < -EPSILON or p2.y > strip_height + EPSILON)):
                for p3, p4 in limit_segments:
                    intersec = segment_intersection(p1, p2, p3, p4)
                    if intersec is None:
                        continue
                    if is_out_of_bounds(intersec, x_min, y_min, y_max, strip_height):
                        continue
                    if not check_inside_cand(allocated, nfp_matrix, polygons, intersec, type_idx):
                        continue
                    if candidate_better(intersec, best):
                        best = intersec

            for other_type_idx, other_copy_idx in allocated:
                if (other_type_idx, other_copy_idx) == (fixed_type_idx, fixed_copy_idx):
                    continue

                nfp_other = nfp_matrix[other_type_idx][type_idx]
                other_pos = polygons[other_type_idx].position[other_copy_idx]
                if not nfp_other.vertex_list:
                    continue

                for j, vert2 in enumerate(nfp_other.vertex_list):
                    next_vert2 = nfp_other.vertex_list[(j + 1) % len(nfp_other.vertex_list)]
                    p3 = Point(vert2.x + other_pos.x, vert2.y + other_pos.y)
                    p4 = Point(next_vert2.x + other_pos.x, next_vert2.y + other_pos.y)
                    intersec = segment_intersection(p1, p2, p3, p4)
                    if intersec is None:
                        continue
                    if is_out_of_bounds(intersec, x_min, y_min, y_max, strip_height):
                        continue
                    if not check_inside_cand(allocated, nfp_matrix, polygons, intersec, type_idx):
                        continue
                    if candidate_better(intersec, best):
                        best = intersec

    if best is None:
        return None, "Sem candidato viável"
    return best, "Candidato viável encontrado"


def run_mkbl(height: float, polygons: List[polygon], requests: List[Tuple[int, int]]):
    nfp_matrix = Minkowski_Sum(polygons)
    allocated: List[Tuple[int, int]] = []
    results: List[AllocationResult] = []

    for step_idx, (type_idx, copy_idx) in enumerate(requests, start=1):
        if type_idx < 0 or type_idx >= len(polygons):
            results.append(AllocationResult(step_idx, type_idx, copy_idx, "erro", "Tipo inválido", None))
            continue

        poly = polygons[type_idx]
        if poly.copy <= 0:
            results.append(AllocationResult(step_idx, type_idx, copy_idx, "erro", "Sem cópias disponíveis", None))
            continue

        if copy_idx < 0 or copy_idx >= len(poly.position):
            results.append(AllocationResult(step_idx, type_idx, copy_idx, "erro", "Índice de cópia inválido", None))
            continue

        position, msg = find_position_for_piece(type_idx, copy_idx, height, polygons, allocated, nfp_matrix)
        if position is None:
            results.append(AllocationResult(step_idx, type_idx, copy_idx, "falha", msg, None))
            continue

        poly.change_copy()
        poly.position[copy_idx] = Point(position.x, position.y)
        allocated.append((type_idx, copy_idx))
        results.append(AllocationResult(step_idx, type_idx, copy_idx, "ok", msg, position))

    return allocated, results


def plot_layout(polygons: List[polygon], allocated: List[Tuple[int, int]], strip_height: float, max_step: Optional[int] = None):
    fig, ax = plt.subplots(figsize=(5.8, 2.2), dpi=110)
    ax.set_aspect("equal")

    if max_step is None:
        selected = allocated
    else:
        selected = allocated[:max_step]

    x_max = 10.0
    if selected:
        x_values = []
        for type_idx, copy_idx in selected:
            poly = polygons[type_idx]
            base = poly.position[copy_idx]
            for v in poly.vertex_list:
                x_values.append(v.x + base.x)
        if x_values:
            x_max = max(x_values) + 2.0

    colors = plt.cm.tab10.colors
    for step_idx, (type_idx, copy_idx) in enumerate(selected, start=1):
        poly = polygons[type_idx]
        pos = poly.position[copy_idx]
        coords = [(v.x + pos.x, v.y + pos.y) for v in poly.vertex_list]
        closed_coords = coords + [coords[0]]
        xs, ys = zip(*closed_coords)
        ax.plot(xs, ys, color=colors[type_idx % len(colors)], linewidth=2, label=f"Tipo {type_idx}")

        centroid_x = sum(x for x, _ in coords) / len(coords)
        centroid_y = sum(y for _, y in coords) / len(coords)
        ax.text(
            centroid_x,
            centroid_y,
            f"P{step_idx}\nT{type_idx}C{copy_idx}",
            fontsize=7,
            ha="center",
            va="center",
            bbox={"boxstyle": "round,pad=0.15", "facecolor": "white", "alpha": 0.65, "edgecolor": "none"},
        )

    ax.axhline(y=strip_height, color="red", linestyle="--", linewidth=1.5, label="Strip Height")
    ax.set_xlim(0, max(10, x_max))
    ax.set_ylim(0, strip_height + 0.8)
    ax.set_title("Alocação MKBL v04", fontsize=12)
    ax.grid(alpha=0.2)

    handles, labels = ax.get_legend_handles_labels()
    dedup = dict(zip(labels, handles))
    if dedup:
        ax.legend(
            dedup.values(),
            dedup.keys(),
            loc="center left",
            bbox_to_anchor=(1.02, 0.5),
            ncol=1,
            framealpha=0.85,
            fontsize=8,
        )

    fig.subplots_adjust(left=0.08, right=0.74, top=0.85, bottom=0.16)

    return fig


def dataframe_rows(results: List[AllocationResult]):
    rows = []
    for r in results:
        rows.append(
            {
                "passo": r.step,
                "tipo": r.type_idx,
                "copia": r.copy_idx,
                "status": r.status,
                "mensagem": r.message,
                "x": None if r.position is None else round(r.position.x, 6),
                "y": None if r.position is None else round(r.position.y, 6),
            }
        )
    return rows


st.set_page_config(page_title="Strip Packing MKBL v04", layout="wide")
st.title("Strip Packing Explorer - MKBL v04")
st.caption("Explore instâncias da pasta Instances e visualize alocação geométrica com NFP.")

instances_dir = Path("Instances")
instance_files = sorted([p.name for p in instances_dir.glob("*.txt")]) if instances_dir.exists() else []

left, right = st.columns([2, 1])

with left:
    selected_file = st.selectbox("Instância da pasta Instances", options=instance_files, index=0 if instance_files else None)
with right:
    uploaded = st.file_uploader("Ou envie um .txt de instância", type=["txt"])

raw_text = ""
if uploaded is not None:
    raw_text = uploaded.getvalue().decode("utf-8")
elif selected_file:
    raw_text = (instances_dir / selected_file).read_text(encoding="utf-8")

if raw_text:
    st.subheader("Prévia da instância")
    st.code(raw_text, language="text")

    try:
        height, poly_specs, requests = parse_instance_text(raw_text)
        st.success("Instância carregada com sucesso.")

        info_col1, info_col2, info_col3 = st.columns(3)
        info_col1.metric("Strip Height", height)
        info_col2.metric("Tipos de polígonos", len(poly_specs))
        info_col3.metric("Pedidos de alocação", len(requests))

        with st.expander("Geometria por tipo", expanded=False):
            for spec in poly_specs:
                st.write(f"Tipo {spec['type_idx']}: vértices={spec['vertices_count']}, cópias={spec['copies']}")
                st.write(spec["vertices"])

        if st.button("Executar MKBL v04", type="primary"):
            polygons = build_polygons(poly_specs)
            allocated, results = run_mkbl(height, polygons, requests)
            st.session_state["mkbl_run"] = {
                "height": height,
                "polygons": polygons,
                "allocated": allocated,
                "results": results,
            }
            st.session_state["step_view"] = len(allocated) if allocated else 1

        run_data = st.session_state.get("mkbl_run")
        if run_data:
            polygons = run_data["polygons"]
            allocated = run_data["allocated"]
            results = run_data["results"]
            height = run_data["height"]

            st.subheader("Resultado da execução")
            st.dataframe(dataframe_rows(results), use_container_width=True, hide_index=True)

            ok_count = sum(1 for r in results if r.status == "ok")
            fail_count = len(results) - ok_count
            c1, c2 = st.columns(2)
            c1.metric("Alocações bem-sucedidas", ok_count)
            c2.metric("Falhas", fail_count)

            st.subheader("Visualização")
            if allocated:
                if st.session_state.get("step_view", 1) > len(allocated):
                    st.session_state["step_view"] = len(allocated)
                step_view = st.slider("Passo mostrado no gráfico", min_value=1, max_value=len(allocated), step=1, key="step_view")
                fig = plot_layout(polygons, allocated, height, max_step=step_view)
                left_col, mid_col, right_col = st.columns([1, 2, 1])
                with mid_col:
                    st.pyplot(fig, use_container_width=False)
            else:
                st.warning("Nenhuma peça foi alocada para desenhar.")
    except Exception as exc:
        st.error(f"Falha ao processar instância: {exc}")
else:
    st.info("Selecione uma instância da pasta Instances ou faça upload de um arquivo .txt.")
