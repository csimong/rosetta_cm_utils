#!/usr/bin/env python3
"""threading_over_template.py

Runs Rosetta partial_thread over a template and renames/moves the generated PDB.

Usage:
  python3 threading_over_template.py \
    --fasta seq_to_model.fasta \
    --alignment alignment.grishin \
    --template template.pdb \
    --out output_dir/

You can also set the Rosetta binary explicitly:
  python3 threading_over_template.py \
    -f seq_to_model.fasta \
    -a alignment.grishin \
    -t template.pdb \
    --rosetta-bin /path/to/partial_thread.cxx11threadstatic.linuxgccrelease \
    --out threaded.pdb
  

Example:
  $ python3 threading_over_template.py


Notes:
- This mimics the original bash behavior, including the expected generated output name:
  <template_file>.pdb (e.g. 'template.pdb.pdb').
- If that file is not found, it also checks a common alternative: <template_stem>.pdb.

Created by:
  Name(s):        Laura Cano Almarza
  Since:          2024-07-15

Adapted and maintained by:
  Name(s):        Carolina Simón Guerrero, Jose Luis Cabrera Alarcón, Marina Rosa Moreno
  Email(s):       carolina.simon.guerrero@gmail.com, joseluis.cabrera@cnic.es, marina.rosa@cnic.es
  Since:          2025-12-23

Institution:
  Name:           Spanish National Centre for Cardiovascular Research - CNIC
  Unit/Group:     Functional Genetics of the Oxidative Phosphorylation System (GENOXPHOS) Lab
  Address:        Madrid, Spain
  Website:        https://www.cnic.es/en/investigacion/functional-genetics-oxidative-phosphorylation-system-genoxphos

Repository/URL:   https://github.com/csimong/rosetta_cm_utils

"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_ROSETTA_PARTIAL_THREAD = (
    "/programs/PDB/rosetta-3.13/main/source/bin/"
    "partial_thread.cxx11threadstatic.linuxgccrelease"
)


def strip_suffix_if_present(p: str, suffix: str) -> str:
    """Mimic bash ${var/.ext/} behavior for a single suffix occurrence at the end."""
    return p[: -len(suffix)] if p.endswith(suffix) else p


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="threading_over_template",
        formatter_class=argparse.RawTextHelpFormatter,
        description=(
            "Partial thread a sequence over a template using Rosetta, then rename/move the generated PDB."
        ),
    )
    parser.add_argument(
        "-f",
        "--fasta",
        required=True,
        help="FASTA file with the sequence to model (e.g. seq_to_model.fasta).",
    )
    parser.add_argument(
        "-a",
        "--alignment",
        required=True,
        help="Alignment file in Grishin format (e.g. alignment.grishin).",
    )
    parser.add_argument(
        "-t",
        "--template",
        required=True,
        help="Template PDB file used for threading (e.g. template.pdb).",
    )
    parser.add_argument(
        "--rosetta-bin",
        default=DEFAULT_ROSETTA_PARTIAL_THREAD,
        help=(
            "Path to Rosetta partial_thread binary.\n"
            f"Default: {DEFAULT_ROSETTA_PARTIAL_THREAD}"
        ),
    )
    parser.add_argument(
        "-o",
        "--out",
        default=".",
        help=(
            "Output path.\n"
            "- If it ends with .pdb, it is treated as the output filename.\n"
            "- Otherwise, it is treated as an output directory and the default name is used."
        ),
    )
    return parser


def resolve_output_path(out_arg: str, default_name: str) -> Path:
    out_path = Path(out_arg)
    if out_path.suffix.lower() == ".pdb":
        # treat as file path
        parent = out_path.parent
        if str(parent) != "" and parent != Path("."):
            parent.mkdir(parents=True, exist_ok=True)
        return out_path

    # treat as directory
    out_path.mkdir(parents=True, exist_ok=True)
    return out_path / default_name


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    fasta_file = args.fasta
    alignment_file = args.alignment
    template_file = args.template
    rosetta_bin = args.rosetta_bin

    fasta_name = strip_suffix_if_present(fasta_file, ".fasta")
    template_name = strip_suffix_if_present(template_file, ".pdb")

    cmd = [
        rosetta_bin,
        "-in:file:fasta",
        fasta_file,
        "-in:file:alignment",
        alignment_file,
        "-in:file:template_pdb",
        template_file,
    ]
    print(cmd)

    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        print(f"Error: Rosetta binary not found at: {rosetta_bin}", file=sys.stderr)
        return 2
        exit
    except subprocess.CalledProcessError as e:
        print(f"Error: partial_thread failed with exit code {e.returncode}", file=sys.stderr)
        return e.returncode
        exit

    # Original bash behavior:
    primary_generated = Path(f"{template_file}.pdb")  # e.g. template.pdb.pdb

    default_out_name = f"{Path(fasta_name).name}_on_{Path(template_name).name}.pdb"
    destination = resolve_output_path(args.out, default_out_name)

    if primary_generated.is_file():
        shutil.move(str(primary_generated), str(destination))
        return 0


    print(
        f"Error: Generated PDB file not found. Checked: '{primary_generated}'",
        file=sys.stderr,
    )
    return 3


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))