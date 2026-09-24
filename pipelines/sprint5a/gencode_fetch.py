#!/usr/bin/env python3
"""Sprint 5A — fetch GENCODE gene annotations (EBI FTP, open) for releases used across sources and reduce each
to gene-level rows: v26 (GTEx v8), v29lift37 (devBrain STAR alignment, Wen 2024), v39 (GTEx v10 / eQTL Catalogue r7),
v40 (requested comparison release), v47 (GTEx V11)."""
import gzip
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_util import ROOT, fetch  # noqa: E402

B = "https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human"
DEST = ROOT / "data/interim/sprint5a/gencode"
REL = {"v26": f"{B}/release_26/gencode.v26.annotation.gtf.gz",
       "v29lift37": f"{B}/release_29/GRCh37_mapping/gencode.v29lift37.annotation.gtf.gz",
       "v39": f"{B}/release_39/gencode.v39.annotation.gtf.gz",
       "v40": f"{B}/release_40/gencode.v40.annotation.gtf.gz",
       "v47": f"{B}/release_47/gencode.v47.annotation.gtf.gz"}
if __name__ == "__main__":
    for k, u in REL.items():
        p = DEST / Path(u).name
        r = fetch(u, p, DEST / "download_log.jsonl")
        print(r["status"], r["file"], r.get("bytes"), flush=True)
        out = DEST / f"genes_{k}.tsv"
        with gzip.open(p, "rt") as fh, open(out, "w") as o:
            o.write("chr\tstart\tend\tstrand\tgene_id\tgene_name\tgene_type\n")
            for line in fh:
                if line.startswith("#"):
                    continue
                f = line.split("\t", 8)
                if f[2] != "gene":
                    continue
                at = dict(x.strip().split(" ", 1) for x in f[8].strip().strip(";").split(";") if x.strip())
                g = {a: b.strip('"') for a, b in at.items()}
                o.write(f"{f[0]}\t{f[3]}\t{f[4]}\t{f[6]}\t{g['gene_id']}\t{g.get('gene_name')}\t{g.get('gene_type')}\n")
        print("wrote", out, flush=True)
