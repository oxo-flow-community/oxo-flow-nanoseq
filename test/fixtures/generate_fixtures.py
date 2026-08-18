#!/usr/bin/env python3
"""Generate the synthetic nanopore fixtures for oxo-flow-nanoseq.

The previous hand-made kit was 11 reads: qcat split them into the two
barcodes and barcode02's share had no read-length variation, so
NanoPlot skipped its bivariate plots AND wrote no log file (live:
'mv: can't rename NanoPlot_*.log: No such file or directory'). This
generator emits 60 reads (30 per barcode) with the RBK001 barcode01/
barcode02 sequences at the 5' end (the exact sequences from qcat's own
kit table) and varied 300-3000bp genome-derived bodies, so demultiplex
splits evenly and every per-barcode NanoPlot has real length
variation.

Regenerate with:  python3 test/fixtures/generate_fixtures.py
"""
import gzip
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
REF = os.path.join(HERE, "refs", "genome.fa")
READS_PER_BARCODE = 30
SEED = 9

# RBK001 kit (qcat's resources/kits/RBK001.yml)
BARCODES = {
    "01": "AAGAAAGTTGTCGGTGTCTTTGTG",
    "02": "TCGATTCCGTTTGTAGTCGTCTGT",
}


def main():
    genome = "".join(l.strip() for l in open(REF) if not l.startswith(">"))
    rng = random.Random(SEED)
    reads = []
    for bc_id, bc_seq in BARCODES.items():
        for i in range(READS_PER_BARCODE):
            length = rng.randint(300, 3000)
            start = rng.randrange(0, len(genome) - length)
            seq = bc_seq + genome[start : start + length - len(bc_seq)]
            rid = f"@{bc_id}-{i:04d}"
            reads.append((rid, seq))
    rng.shuffle(reads)
    with gzip.open(os.path.join(RAW, "sample.fastq.gz"), "wt") as fh:
        for rid, seq in reads:
            fh.write(f"{rid}\n{seq}\n+\n{'I' * len(seq)}\n")
    print(f"nanoseq fixtures regenerated: {len(reads)} reads (30 per barcode, 300-3000bp)")


if __name__ == "__main__":
    main()
