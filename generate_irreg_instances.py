from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class PieceGeometry:
    parts: list[list[tuple[float, float]]]


@dataclass
class SourceInstance:
    name: str
    height: int
    demands: list[int]
    pieces: list[PieceGeometry]


GENERAL_DATA_HEIGHT_RE = re.compile(r"^height\s*#\s*([0-9]+(?:\.[0-9]+)?)\s*$", re.IGNORECASE)
GENERAL_DATA_TYPES_RE = re.compile(r"^Number type piece\s*#\s*(\d+)\s*$", re.IGNORECASE)
GENERAL_DATA_DEMAND_RE = re.compile(r"^identity piece\s*#\s*(\d+)\s*demand\s*#\s*(\d+)", re.IGNORECASE)
PARTS_RE = re.compile(r"^Number of part by piece\s*#\s*(\d+)\s*$", re.IGNORECASE)
VERTICES_RE = re.compile(r"^number of vertices \(part (\d+)\)\s*#\s*(\d+)\s*$", re.IGNORECASE)


def _format_number(value: float) -> str:
    if abs(value - round(value)) < 1e-9:
        return f"{int(round(value))}.00"
    return f"{value:.2f}"


def _parse_float_pair(line: str) -> tuple[float, float]:
    parts = line.split()
    if len(parts) != 2:
        raise ValueError(f"Invalid coordinate line: {line!r}")
    return float(parts[0]), float(parts[1])


def parse_general_data(path: Path) -> tuple[int, int, dict[int, int]]:
    height: int | None = None
    type_count: int | None = None
    demands: dict[int, int] = {}

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue

        height_match = GENERAL_DATA_HEIGHT_RE.match(line)
        if height_match:
            height = int(float(height_match.group(1)))
            continue

        types_match = GENERAL_DATA_TYPES_RE.match(line)
        if types_match:
            type_count = int(types_match.group(1))
            continue

        demand_match = GENERAL_DATA_DEMAND_RE.match(line)
        if demand_match:
            piece_index = int(demand_match.group(1))
            demands[piece_index] = int(demand_match.group(2))

    if height is None:
        raise ValueError(f"Could not find strip height in {path}")
    if type_count is None:
        raise ValueError(f"Could not find number of piece types in {path}")

    return height, type_count, demands


def parse_piece_file(path: Path) -> PieceGeometry:
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        raise ValueError(f"Empty piece file: {path}")

    parts_match = next((PARTS_RE.match(line) for line in lines if PARTS_RE.match(line)), None)
    if parts_match is None:
        raise ValueError(f"Could not find part count in {path}")

    expected_parts = int(parts_match.group(1))
    parsed_parts: list[list[tuple[float, float]]] = []

    index = 0
    while index < len(lines):
        vertices_match = VERTICES_RE.match(lines[index])
        if vertices_match is None:
            index += 1
            continue

        vertex_count = int(vertices_match.group(2))
        index += 1

        if index < len(lines) and lines[index].lower().startswith("vertices (x,y)"):
            index += 1

        polygon_vertices: list[tuple[float, float]] = []
        for _ in range(vertex_count):
            if index >= len(lines):
                raise ValueError(f"Unexpected end of file while reading vertices in {path}")
            polygon_vertices.append(_parse_float_pair(lines[index]))
            index += 1

        parsed_parts.append(polygon_vertices)

    if len(parsed_parts) != expected_parts:
        raise ValueError(
            f"Piece file {path} declares {expected_parts} parts but {len(parsed_parts)} were parsed"
        )

    return PieceGeometry(parts=parsed_parts)


def discover_instances(source_root: Path) -> list[Path]:
    instance_dirs = [path for path in source_root.iterdir() if path.is_dir()]
    return sorted(instance_dirs, key=lambda path: path.name.lower())


def load_instance(instance_dir: Path) -> SourceInstance:
    general_data_path = instance_dir / "general_data.txt"
    if not general_data_path.exists():
        raise FileNotFoundError(f"Missing general_data.txt in {instance_dir}")

    height, type_count, demands = parse_general_data(general_data_path)
    pieces: list[PieceGeometry] = []

    for piece_index in range(1, type_count + 1):
        piece_path = instance_dir / f"piece{piece_index}.txt"
        if not piece_path.exists():
            raise FileNotFoundError(f"Missing piece file {piece_path}")
        pieces.append(parse_piece_file(piece_path))

    ordered_demands = [demands.get(piece_index, 1) for piece_index in range(1, type_count + 1)]
    return SourceInstance(name=instance_dir.name, height=height, demands=ordered_demands, pieces=pieces)


def build_instance_text(instance: SourceInstance, copies_mode: str, copies_value: int) -> str:
    lines: list[str] = [str(instance.height), str(len(instance.pieces))]

    for piece_index, piece in enumerate(instance.pieces):
        lines.append(str(len(piece.parts)))
        if copies_mode == "fixed":
            lines.append(str(copies_value))
        elif copies_mode == "demand":
            lines.append(str(instance.demands[piece_index]))
        else:
            raise ValueError(f"Unsupported copies mode: {copies_mode}")

    for piece in instance.pieces:
        for polygon in piece.parts:
            lines.append(str(len(polygon)))
            for x, y in polygon:
                lines.append(f"{_format_number(x)} {_format_number(y)}")

    return "\n".join(lines) + "\n"


def write_output_file(output_path: Path, content: str, overwrite: bool) -> bool:
    if output_path.exists() and not overwrite:
        return False

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8", newline="\n")
    return True


def iter_suffixes(raw_suffixes: Iterable[str] | None) -> list[str]:
    if raw_suffixes is None:
        return ["area", "len", "ratio"]
    suffixes = [suffix.strip() for suffix in raw_suffixes if suffix.strip()]
    return suffixes or ["area", "len", "ratio"]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert Instancias_euler folders into the flat text format consumed by Strip_packing_MKBL_v05_test.py."
    )
    parser.add_argument(
        "--source-root",
        default="zip/Instancias_euler",
        help="Folder that contains one subfolder per source instance.",
    )
    parser.add_argument(
        "--output-root",
        default="irreg_instances",
        help="Folder where the converted instances will be written.",
    )
    parser.add_argument(
        "--suffixes",
        nargs="*",
        default=None,
        help="Instance name suffixes to generate. Default: area len ratio.",
    )
    parser.add_argument(
        "--copies-mode",
        choices=("fixed", "demand"),
        default="demand",
        help="Use the demand from general_data.txt or force a fixed number of copies for every type.",
    )
    parser.add_argument(
        "--copies-value",
        type=int,
        default=1,
        help="Copies value used when --copies-mode fixed is selected.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite files that already exist in the output folder.",
    )
    args = parser.parse_args()

    source_root = Path(args.source_root)
    output_root = Path(args.output_root)
    suffixes = iter_suffixes(args.suffixes)

    if not source_root.exists():
        raise FileNotFoundError(f"Source root not found: {source_root}")

    instance_dirs = discover_instances(source_root)
    if not instance_dirs:
        raise FileNotFoundError(f"No instance folders found in {source_root}")

    converted = 0
    skipped = 0

    for instance_dir in instance_dirs:
        instance = load_instance(instance_dir)
        content = build_instance_text(instance, args.copies_mode, args.copies_value)

        for suffix in suffixes:
            output_name = f"instance_{instance.name}_{suffix}" if suffix else f"instance_{instance.name}"
            output_path = output_root / output_name
            if write_output_file(output_path, content, args.overwrite):
                converted += 1
                print(f"Wrote {output_path}")
            else:
                skipped += 1
                print(f"Skipped existing file {output_path}")

    print(f"Done. Converted {converted} file(s), skipped {skipped} existing file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())