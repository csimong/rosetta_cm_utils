#!/usr/bin/env python3
"""
Convert OCTOPUS/TOPCONS topology output to Rosetta .span format.

This is a Python port of the classic Perl script octopus2span.pl in Rosetta:
- Reads the amino-acid sequence (after 'Sequence:')
- Reads predicted topology string (after 'OCTOPUS predicted topology:' or 'TOPCONS predicted topology:')
- Extracts contiguous 'M' segments as TM helices
- Writes .span format (comment line + "Nhelix length" + antiparallel + n2c + helix ranges)


Example:
 $ python octopus2span.py examples/topcons/COX3gg.octopus -o examples/topcons/COX3gg.span


Notes on helix-line format:
- Default outputs 4 columns: start end start end (numbers repeated once).
- Can switch to 2 columns (start end) with --columns 2 if needed.
- If a directory is passed, it will search recursively and use the first file named 'query.result.txt'.


Created by:
  Name(s):        Bjorn Wallner, Vladimir Yarov-Yarovoy

Adapted and maintained by:
  Name(s):        Carolina Simón Guerrero, Jose Luis Cabrera Alarcón, Marina Rosa Moreno
  Email(s):       carolina.simon.guerrero@gmail.com, joseluis.cabrera@cnic.es, marina.rosa@cnic.es
  Since:          2025-12-23

Institution:
  Name:        Spanish National Centre for Cardiovascular Research - CNIC
  Unit/Group:  Functional Genetics of the Oxidative Phosphorylation System (GENOXPHOS) Lab
  Address:     Madrid, Spain
  Website:     https://www.cnic.es/en/investigacion/functional-genetics-oxidative-phosphorylation-system-genoxphos

Repository/URL: https://github.com/csimong/rosetta_cm_utils

"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple


TOPO_MARKERS = (
    "OCTOPUS predicted topology:",
    "TOPCONS predicted topology:",
)


def eprint(*args, **kwargs) -> None:
    print(*args, file=sys.stderr, **kwargs)


def find_first_query_result_txt(root: Path) -> Optional[Path]:
    # Depth-first, deterministic order
    for p in sorted(root.rglob("query.result.txt")):
        if p.is_file():
            return p
    return None


def sanitize_name(raw: str) -> str:
    """
    Make a filesystem-friendly name.
    Keeps letters, digits, '.', '_', '-' ; converts others to '_'.
    Collapses multiple underscores.
    """
    raw = raw.strip()
    raw = re.sub(r"\s+", "_", raw)
    raw = re.sub(r"[^A-Za-z0-9._-]+", "_", raw)
    raw = re.sub(r"_+", "_", raw).strip("_")
    return raw or "sequence"


def guess_seq_id(seq_name_line: Optional[str], fallback_path: Path) -> str:
    """
    Try to derive an ID from 'Sequence name:' line, else use input basename.
    For a name like 'sp|P18945|COX3_CHICK ...', we take the first token before spaces.
    """
    if seq_name_line:
        # after "Sequence name:"
        name = seq_name_line.split(":", 1)[1].strip()
        first_token = name.split()[0] if name else ""
        return sanitize_name(first_token) if first_token else sanitize_name(fallback_path.stem)
    return sanitize_name(fallback_path.stem)


def parse_topcons_octopus_file(path: Path) -> Tuple[str, str, str]:
    """
    Returns: (sequence, topology, predictor_label)
    """
    seq_name_line = None
    seq_chunks: List[str] = []
    topo_chunks: List[str] = []

    in_seq = False
    in_topo = False
    predictor = "UNKNOWN"

    allowed_topo_re = re.compile(r"^[A-Za-z]+$")  # be permissive; we only care about 'M'

    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            line = raw.strip()

            # capture sequence name if present
            if line.startswith("Sequence name:"):
                seq_name_line = line

            # topology marker?
            if any(line.startswith(m) for m in TOPO_MARKERS):
                in_seq = False
                in_topo = True
                predictor = "OCTOPUS" if line.startswith("OCTOPUS") else "TOPCONS"
                continue

            # sequence marker?
            if line.startswith("Sequence:"):
                in_seq = True
                in_topo = False
                continue

            # collect sequence lines
            if in_seq:
                if line:  # ignore blanks
                    seq_chunks.append(line)
                continue

            # collect topology lines: take only lines that look like topology strings
            if in_topo:
                if line and allowed_topo_re.match(line):
                    topo_chunks.append(line)
                    continue
                # if we hit a non-topology line after starting topology, stop collecting
                if topo_chunks:
                    break

    seq = "".join(seq_chunks).replace(" ", "").replace("\t", "")
    topo = "".join(topo_chunks).replace(" ", "").replace("\t", "")

    if not seq:
        raise ValueError(f"Could not find sequence in: {path}")
    if not topo:
        raise ValueError(f"Could not find predicted topology in: {path} (looked for {TOPO_MARKERS})")

    if len(seq) != len(topo):
        raise ValueError(
            "Length difference between seq and topology!\n"
            f"seq_len={len(seq)} topo_len={len(topo)}\n"
            f"{seq}$\n{topo}$\n"
        )

    seq_id = guess_seq_id(seq_name_line, path)
    return seq, topo, predictor, seq_id  # type: ignore[misc]


def extract_tm_spans(topo: str) -> List[Tuple[int, int]]:
    """
    Extract contiguous 'M' segments, 1-based inclusive (start, end).
    """
    spans: List[Tuple[int, int]] = []
    i = 0
    n = len(topo)
    while i < n:
        if topo[i] == "M":
            start = i + 1
            j = i
            while j < n and topo[j] == "M":
                j += 1
            end = j  # because j is 0-based index after run, so end is j in 1-based
            spans.append((start, end))
            i = j
        else:
            i += 1
    return spans


def format_span_block(
    spans: List[Tuple[int, int]],
    total_len: int,
    comment_label: str,
    columns: int = 4,
    offset: int = 0,
) -> str:
    """
    Build a .span text block with a given offset (for multimers).
    """
    # Apply offset
    spans_off = [(s + offset, e + offset) for (s, e) in spans]

    header = (
        f"TM region prediction for {comment_label} predicted using TOPCONS\n"
        f"{len(spans_off)} {total_len}\n"
        "antiparallel\n"
        "n2c\n"
    )

    lines = []
    for s, e in spans_off:
        if columns == 2:
            lines.append(f"{s:4d}  {e:4d}\n")
        elif columns == 4:
            lines.append(f"{s:4d}  {e:4d}  {s:4d}  {e:4d}\n")
        else:
            raise ValueError("--columns must be 2 or 4")

    return header + "".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Convert OCTOPUS/TOPCONS topology file (e.g., TOPCONS2 query.result.txt) to Rosetta .span."
    )
    ap.add_argument(
        "input",
        help="Path to topology file OR a directory (will pick first query.result.txt recursively).",
    )
    ap.add_argument(
        "-o",
        "--out",
        default=None,
        help="Output .span path OR output directory. If omitted, prints to stdout.",
    )
    ap.add_argument(
        "--name",
        default=None,
        help="Override output base name (without .span). If omitted, uses 'Sequence name:' when possible.",
    )
    ap.add_argument(
        "--monomers",
        type=int,
        default=1,
        help="Number of monomers to replicate spans (default: 1).",
    )
    ap.add_argument(
        "--len",
        dest="monomer_len",
        type=int,
        default=0,
        help="Monomer length (required if --monomers > 1). Used to compute offsets.",
    )
    ap.add_argument(
        "--columns",
        type=int,
        default=4,
        choices=[2, 4],
        help="Helix line columns: 4 -> 'start end start end' (default), 2 -> 'start end'.",
    )

    args = ap.parse_args()

    in_path = Path(args.input).expanduser().resolve()

    if in_path.is_dir():
        picked = find_first_query_result_txt(in_path)
        if not picked:
            eprint(f"ERROR: No 'query.result.txt' found under: {in_path}")
            return 2
        topo_path = picked
    else:
        topo_path = in_path

    try:
        seq, topo, predictor, seq_id = parse_topcons_octopus_file(topo_path)
    except Exception as ex:
        eprint(f"ERROR: {ex}")
        return 2

    if args.name:
        out_base = sanitize_name(args.name)
    else:
        out_base = seq_id

    spans = extract_tm_spans(topo)

    monomers = args.monomers
    if monomers < 1:
        eprint("ERROR: --monomers must be >= 1")
        return 2
    if monomers > 1 and args.monomer_len <= 0:
        eprint("ERROR: --len must be provided and > 0 when --monomers > 1")
        return 2

    # Decide output destination
    out_text_parts: List[str] = []
    for i in range(1, monomers + 1):
        offset = (i - 1) * (args.monomer_len if monomers > 1 else 0)
        total_len = (args.monomer_len * monomers) if monomers > 1 else len(seq)
        comment_label = f"{out_base}.span"
        block = format_span_block(
            spans=spans,
            total_len=total_len,
            comment_label=comment_label,
            columns=args.columns,
            offset=offset,
        )
        out_text_parts.append(block)

    out_text = "".join(out_text_parts)

    if args.out is None:
        sys.stdout.write(out_text)
        return 0

    out_path = Path(args.out).expanduser().resolve()
    if out_path.exists() and out_path.is_dir():
        out_file = out_path / f"{out_base}.span"
    else:
        # treat as a file path (parent directory must exist or be creatable)
        out_file = out_path
        if out_file.suffix.lower() != ".span":
            out_file = out_file.with_suffix(".span")

    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(out_text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
