#!/usr/bin/env python3
"""
get_span_file.py

Master wrapper for getting span file using topcons_launch.py:
- submits a job
- parses jobid from stdout
- polls until finished
- downloads results (via topcons_launch.py -m get)
- unzips results
- finds ONLY the "outermost" (shallowest) query.result.txt under extracted directory
- writes a single .octopus file to a user-specified path


Example:
$ python3 /home/csimon/cnic/rosetta_cm_utils/get_span_file.py \
    --topcons-script /home/csimon/cnic/rosetta_cm_utils/topcons_launch.py    \
    --seq /home/csimon/cnic/rosetta_cm_utils/examples/topcons/COX3gg.fasta\
    --output-topcons /home/csimon/cnic/rosetta_cm_utils/examples/topcons/output_topcons\
    --jobname COX3_gg     --poll 60  \
    --octopus-out /home/csimon/cnic/rosetta_cm_utils/examples/topcons/


Notes:
- This script calls topcons_launch.py as a subprocess (no WSDL logic here).
- Writes everything from file start through the TOPCONS predicted topology block.


Created by:
  Name(s):        Carolina Simón Guerrero
  Email(s):       carolina.simon.guerrero@gmail.com
  Since:          2015-02-04, updated 2018-01-12, 

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

import argparse
import os
import re
import sys
import time
import zipfile
import subprocess
from datetime import datetime
from typing import Optional, Tuple, List


JOBID_RE = re.compile(r"jobid\s*=\s*([A-Za-z0-9_]+)")


def run_cmd(cmd: List[str]) -> Tuple[int, str, str]:
    """Run command and return (returncode, stdout, stderr)."""
    p = subprocess.run(cmd, text=True, capture_output=True)
    return p.returncode, p.stdout, p.stderr


def parse_jobid(stdout: str) -> Optional[str]:
    m = JOBID_RE.search(stdout)
    return m.group(1) if m else None


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def fasta_stem(path: str) -> str:
    """
    Return filename stem for fasta path:
      COX3_gg.fasta -> COX3_gg
      COX3_gg.fa.gz -> COX3_gg
    """
    base = os.path.basename(path)
    if base.endswith(".gz"):
        base = os.path.splitext(base)[0]  # strip .gz
    return os.path.splitext(base)[0]      # strip last extension (.fa/.fasta/.faa...)


def submit_job(topcons_script: str, seq: str, jobname: Optional[str], email: Optional[str]) -> str:
    cmd = ["python3", topcons_script, "-m", "submit", "-seq", seq]
    if jobname:
        cmd += ["-jobname", jobname]
    if email:
        cmd += ["-email", email]

    rc, out, err = run_cmd(cmd)
    if rc != 0:
        raise RuntimeError(
            f"Submit command failed (returncode={rc}).\nSTDOUT:\n{out}\nSTDERR:\n{err}"
        )

    jobid = parse_jobid(out)
    if not jobid:
        raise RuntimeError(
            "Could not parse jobid from submit output.\n"
            f"STDOUT:\n{out}\nSTDERR:\n{err}"
        )

    return jobid


def unzip_result(zip_path: str, extract_dir: str) -> None:
    ensure_dir(extract_dir)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_dir)


def poll_until_finished(
    topcons_script: str,
    jobid: str,
    output_topcons: str,
    poll_seconds: int,
    max_polls: int,
) -> str:
    """
    Poll using topcons_launch.py -m get -jobid ...
    Returns the zip path when downloaded.
    """
    ensure_dir(output_topcons)
    zip_path = os.path.join(output_topcons, f"{jobid}.zip")

    for attempt in range(1, max_polls + 1):
        cmd = ["python3", topcons_script, "-m", "get", "-jobid", jobid, "-outpath", output_topcons]
        rc, out, err = run_cmd(cmd)

        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{ts}] Poll {attempt}/{max_polls} for jobid={jobid}")

        if rc != 0:
            raise RuntimeError(
                f"Get command failed (returncode={rc}).\nSTDOUT:\n{out}\nSTDERR:\n{err}"
            )

        low = out.lower()
        if "is failed" in low:
            raise RuntimeError(f"TOPCONS job failed.\nSTDOUT:\n{out}\nSTDERR:\n{err}")

        if "does not exist" in low:
            raise RuntimeError(f"TOPCONS jobid does not exist (server says so).\nSTDOUT:\n{out}")

        if os.path.exists(zip_path) and os.path.getsize(zip_path) > 0:
            print(f"Result zip detected: {zip_path}")
            return zip_path

        if attempt < max_polls:
            time.sleep(poll_seconds)

    raise TimeoutError(
        f"Reached max polls ({max_polls}) without getting result zip for jobid={jobid}.\n"
        f"Expected: {zip_path}"
    )


def extract_topcons_block(text: str) -> str:
    """
    Keep from file start through:
      TOPCONS predicted topology:
      <topology line(s) until blank line>
    Then stop.
    """
    lines = text.splitlines(True)  # keep line endings
    kept: List[str] = []

    i = 0
    while i < len(lines):
        kept.append(lines[i])
        if lines[i].startswith("TOPCONS predicted topology:"):
            # include following lines until the first blank line after the topology
            j = i + 1
            while j < len(lines):
                kept.append(lines[j])
                if lines[j].strip() == "":
                    break
                j += 1
            break
        i += 1

    return "".join(kept)


def find_outermost_query_result(extract_dir: str) -> Optional[str]:
    """
    Find the 'outermost' (shallowest) query.result.txt under extract_dir.
    Shallowest = minimal number of path components relative to extract_dir.
    If ties, pick lexicographically smallest path for determinism.
    """
    candidates: List[Tuple[int, str]] = []

    for root, _, files in os.walk(extract_dir):
        if "query.result.txt" in files:
            full = os.path.join(root, "query.result.txt")
            rel = os.path.relpath(full, extract_dir)
            depth = rel.count(os.sep)  # 0 means directly under extract_dir
            candidates.append((depth, full))

    if not candidates:
        return None

    candidates.sort(key=lambda x: (x[0], x[1]))
    return candidates[0][1]


def resolve_octopus_out(octopus_out: str, seq_path: str) -> str:
    """
    If octopus_out is a directory (exists and isdir) OR ends with a path separator,
    write <fasta_stem>.octopus inside it. Otherwise treat as full file path.
    """
    base = fasta_stem(seq_path)
    if octopus_out.endswith(os.sep) or (os.path.exists(octopus_out) and os.path.isdir(octopus_out)):
        out_dir = octopus_out
        ensure_dir(out_dir)
        return os.path.join(out_dir, f"{base}.octopus")

    # treat as file path
    parent = os.path.dirname(octopus_out) or "."
    ensure_dir(parent)
    return octopus_out


def write_single_octopus(extract_dir: str, out_path: str) -> str:
    """
    Find outermost query.result.txt, extract TOPCONS block, write to out_path.
    Returns the output path written.
    """
    in_path = find_outermost_query_result(extract_dir)
    if not in_path:
        raise FileNotFoundError(f"No query.result.txt found under: {extract_dir}")

    with open(in_path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()

    block = extract_topcons_block(text)

    with open(out_path, "w", encoding="utf-8") as out:
        out.write(block)

    return out_path


def main() -> int:
    ap = argparse.ArgumentParser(description="Master wrapper for topcons_launch.py")
    ap.add_argument("--topcons-script", default="topcons_launch.py",
                    help="Path to topcons_launch.py (default: ./topcons_launch.py)")
    ap.add_argument("--seq", required=True, help="Input FASTA file for TOPCONS")
    ap.add_argument("--jobname", default=None, help="Job name to pass to TOPCONS")
    ap.add_argument("--email", default=None, help="Email to pass to TOPCONS (optional)")
    ap.add_argument("--output-topcons", default="output_topcons", help="Output folder for TOPCONS results (default: output_topcons)")
    ap.add_argument("--poll", type=int, default=60, help="Polling interval in seconds (default: 60)")
    ap.add_argument("--max-polls", type=int, default=240,
                    help="Maximum number of polls before giving up (default: 240)")
    ap.add_argument("--extract-subdir", default=None,
                    help="Where to extract zip. Default: <output_topcons>/<jobid>/")
    ap.add_argument("--keep-zip", action="store_true", help="Do not delete the zip after extraction")
    ap.add_argument("--no-octopus", action="store_true",
                    help="Do not generate .octopus from query.result.txt")
    ap.add_argument("--octopus-out", default=None,
                    help="Output path for the .octopus file (file path or directory). Required unless --no-octopus.")
    args = ap.parse_args()

    if not os.path.isfile(args.topcons_script):
        print(f"ERROR: topcons script not found: {args.topcons_script}", file=sys.stderr)
        return 2
    if not os.path.isfile(args.seq):
        print(f"ERROR: seq file not found: {args.seq}", file=sys.stderr)
        return 2

    if not args.no_octopus and not args.octopus_out:
        print("ERROR: --octopus-out is required unless you use --no-octopus", file=sys.stderr)
        return 2

    # 1) Submit
    print("Submitting job to TOPCONS...")
    jobid = submit_job(args.topcons_script, args.seq, args.jobname, args.email)
    print(f"Submitted OK. jobid={jobid}")

    # 2) Poll + download
    print("Polling until finished (will download zip on completion)...")
    zip_path = poll_until_finished(
        args.topcons_script,
        jobid,
        args.output_topcons,
        args.poll,
        args.max_polls,
    )

    # 3) Unzip
    extract_dir = args.extract_subdir or os.path.join(args.output_topcons, jobid)
    print(f"Unzipping {zip_path} -> {extract_dir}")
    unzip_result(zip_path, extract_dir)

    # 4) Optionally cleanup zip
    if not args.keep_zip:
        try:
            os.remove(zip_path)
            print(f"Deleted zip: {zip_path}")
        except OSError as e:
            print(f"WARNING: could not delete zip ({zip_path}): {e}", file=sys.stderr)

    # 5) Write ONLY the outermost query.result.txt to the user-specified path
    if not args.no_octopus:
        out_path = resolve_octopus_out(args.octopus_out, args.seq)
        written = write_single_octopus(extract_dir, out_path)
        print(f"Wrote .octopus: {written}")

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
