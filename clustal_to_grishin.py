#!/usr/bin/env python3
"""
clustal_to_grishin.py

Convert a CLUSTAL/Clustal-Omega .aln multiple-sequence alignment into a Rosetta
Grishin (.grishin) *pairwise* alignment.

Grishin format (typical Rosetta usage):
  ## <TARGET_NAME> <TEMPLATE_NAME>.pdb
  #
  scores from program: 0
  0 <TARGET_ALIGNED_SEQUENCE>
  0 <TEMPLATE_ALIGNED_SEQUENCE>

Notes:
- CLUSTAL .aln often contains multiple sequences; Grishin is usually pairwise.
  You must choose exactly two sequence IDs from the alignment.
- Sequence IDs must match the first column in the .aln blocks (exactly).

Usage:
python new_ch_convert.py <alignment_file.aln> <target_seq.fasta> \
    --target-id <id_target_sequence_in_clustalo_alignment> \
    --template-id <id_template_sequence_in_clustalo_alignment> \
    --target-name <name_target_sequence_in_grishin> \
    --template-name <name_template_sequence_in_grishin> \
    --out <output_file.grishin>
    
Example:
python new_ch_convert.py examples/convert_aln_to_grishin/COX3gg_COX3hs.aln  \
    --target-id "COX3gg"   --template-id "COX3hs"   --target-name COX3gg   \
    --template-name COX3hs   --out COX3gg_COX3hs.grishin
    
    
Created by:
  Name(s):        Carolina Simón Guerrero
  Email(s):       carolina.simon.guerrero@gmail.com
  Since:          2025-12-23

Maintained by:
  Name(s):        Carolina Simón Guerrero, Jose Luis Cabrera Alarcón, Marina Rosa Moreno
  Email(s):       carolina.simon.guerrero@gmail.com, joseluis.cabrera@cnic.es, marina.rosa@cnic.es
  Since:          2025-12-23

Institution:
  Name:           Spanish National Centre for Cardiovascular Research - CNIC
  Unit/Group:     Functional Genetics of the Oxidative Phosphorylation System (GENOXPHOS) Lab
  Address:        Madrid, Spain
  Website:        https://www.cnic.es/en/investigacion/functional-genetics-oxidative-phosphorylation-system-genoxphos

Repository/URL:    https://github.com/csimong/rosetta_cm_utils

"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_clustal_aln(text: str) -> dict[str, str]:
    """
    Parse a CLUSTAL-like .aln file into a dict: {sequence_id: full_aligned_sequence}.

    Rules:
    - Skip header lines starting with 'CLUSTAL' (or 'MUSCLE', for compatibility).
    - Skip empty lines.
    - Skip consensus/annotation lines that start with whitespace.
    - For each alignment block line: <id> <fragment> [optional stuff...]
      Only the first two fields are used.
    """
    seqs: dict[str, str] = {}

    for raw in text.splitlines():
        line = raw.rstrip("\n")

        if not line.strip():
            continue

        if line.startswith(("CLUSTAL", "MUSCLE")):
            continue

        # Consensus line typically begins with whitespace
        if line[0].isspace():
            continue

        parts = line.strip().split()
        if len(parts) < 2:
            continue

        seq_id, fragment = parts[0], parts[1]

        # Sometimes the second token can be a position index (rare). Skip if purely digits.
        if fragment.isdigit():
            continue

        seqs[seq_id] = seqs.get(seq_id, "") + fragment

    return seqs


def build_grishin(
    target_name: str,
    template_name: str,
    template_ext: str,
    target_aln: str,
    template_aln: str,
) -> str:
    """Return the Grishin-formatted string."""
    return "\n".join(
        [
            f"## {target_name} {template_name}{template_ext}",
            "#",
            "scores from program: 0",
            f"0 {target_aln}",
            f"0 {template_aln}",
            "",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert CLUSTAL .aln to Rosetta .grishin (pairwise)."
    )
    parser.add_argument("aln", help="Input CLUSTAL .aln file")
    parser.add_argument("--target-id", required=True, help="Sequence ID for TARGET")
    parser.add_argument("--template-id", required=True, help="Sequence ID for TEMPLATE (structure)")
    parser.add_argument("-o", "--out", required=True, help="Output .grishin file")

    parser.add_argument(
        "--target-name",
        default=None,
        help="Name to write in the Grishin header for TARGET (default: target-id)",
    )
    parser.add_argument(
        "--template-name",
        default=None,
        help="Name to write in the Grishin header for TEMPLATE (default: template-id)",
    )
    parser.add_argument(
        "--template-ext",
        default=".pdb",
        help="Template file extension written in header (default: .pdb)",
    )
    parser.add_argument(
        "--list-ids",
        action="store_true",
        help="List sequence IDs found in the .aln and exit",
    )

    args = parser.parse_args()

    aln_path = Path(args.aln)
    if not aln_path.exists():
        print(f"ERROR: input file does not exist: {aln_path}", file=sys.stderr)
        sys.exit(2)

    text = aln_path.read_text()
    seqs = parse_clustal_aln(text)

    if args.list_ids:
        print("Sequence IDs found in the .aln file:")
        for sid in sorted(seqs.keys()):
            print(f" - {sid}")
        return

    if args.target_id not in seqs or args.template_id not in seqs:
        print("ERROR: one or both requested IDs were not found in the .aln file.", file=sys.stderr)
        print(f"  target-id  = {args.target_id}", file=sys.stderr)
        print(f"  template-id= {args.template_id}", file=sys.stderr)
        print("\nAvailable IDs:", file=sys.stderr)
        for sid in sorted(seqs.keys()):
            print(f" - {sid}", file=sys.stderr)
        sys.exit(3)

    target_name = args.target_name or args.target_id
    template_name = args.template_name or args.template_id

    grishin_text = build_grishin(
        target_name=target_name,
        template_name=template_name,
        template_ext=args.template_ext,
        target_aln=seqs[args.target_id],
        template_aln=seqs[args.template_id],
    )

    Path(args.out).write_text(grishin_text)
    print(f"OK: wrote Grishin file to: {args.out}")


if __name__ == "__main__":
    main()