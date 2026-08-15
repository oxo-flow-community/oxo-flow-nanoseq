# oxo-flow-nanoseq — Nanopore long-read: demultiplexing, QC and alignment

[![CI](https://github.com/oxo-flow-community/oxo-flow-nanoseq/actions/workflows/ci.yml/badge.svg)](https://github.com/oxo-flow-community/oxo-flow-nanoseq/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

> ★ Verified · ⇄ Official port of [`nf-core/nanoseq`](https://github.com/nf-core/nanoseq) @ `3.1.0` — same tools, same versions, same commands. Part of the [oxo-flow-community catalog](https://oxo-flow-community.github.io/).

Run raw nanopore long reads through a complete analysis pipeline: barcode
demultiplexing with qcat, per-sample QC with NanoPlot and FastQC, alignment
to a reference genome with minimap2, BAM conversion/sorting/indexing and
alignment statistics with samtools, BigWig coverage tracks via
bedtools genomecov + UCSC bedGraphToBigWig, and a final MultiQC report that
aggregates everything. The default path is the DNA protocol
(demultiplexing on, minimap2 aligner, all QC and reporting on); the
`protocol` config key switches to the `cDNA`/`directRNA` transcriptome
paths with the same upstream semantics.

## Installation

### 1. Install oxo-flow

Requires **oxo-flow >= 0.12.0**. Prebuilt release binary (recommended):

```bash
curl -fL -o oxo-flow.tar.gz \
  https://github.com/Traitome/oxo-flow/releases/latest/download/oxo-flow-latest-x86_64-unknown-linux-gnu.tar.gz
tar xzf oxo-flow.tar.gz
sudo mv oxo-flow /usr/local/bin/
```

Alternative via conda: `conda install -c bioconda oxo-flow-cli` (note: the
bioconda package may lag behind releases). Other platform binaries are
available on the [releases page](https://github.com/Traitome/oxo-flow/releases).

### 2. Get this workflow

```bash
git clone https://github.com/oxo-flow-community/oxo-flow-nanoseq.git
cd oxo-flow-nanoseq
```

### 3. Requirements

- **Reference data** — you must provide, overriding the checked-in test
  fixtures on the command line:
  - a genome FASTA (`reference` config key, e.g. `reference=/path/genome.fa`)
    — required for alignment, indexing and coverage tracks;
  - a samplesheet CSV (`input` config key) listing your samples;
  - the raw nanopore FASTQ to demultiplex (`input_path` config key; skip it
    with `skip_demultiplexing=true` if your reads are already split);
  - a GTF annotation (`gtf` + `gtf_base` config keys) — optional, only
    needed for the `cDNA`/`directRNA` junction-bed path.
- **Compute** — the largest rule (minimap2 index) requests 12 CPUs and
  84 GB RAM; most medium rules (qcat, fastqc, alignment, sorting, coverage)
  request 6 CPUs and 42 GB. Size your `-j`/thread budget and machine
  accordingly.
- **Tools** — delivered as containers with pinned images: every rule runs
  in the upstream module's exact `quay.io/biocontainers/<tool>:<tag>`
  image via the docker environment backend. Requires Docker (or
  Singularity) at runtime.

## Usage

```bash
# 1. install oxo-flow (see Installation)
# 2. prepare data (default config expects):
#      test/fixtures/samplesheet.csv   (--input samplesheet)
#      test/fixtures/raw/sample.fastq.gz (--input_path raw demultiplexing input)
#      test/fixtures/refs/genome.fa    (reference fasta)
# 3. preview the plan
oxo-flow dry-run main.oxoflow
# 4. run
oxo-flow run main.oxoflow -j 8
# 5. run a subset
oxo-flow run main.oxoflow -t multiqc --samples first:2
```

Configuration overrides mirror the upstream CLI flags, e.g.
`oxo-flow run main.oxoflow protocol=cDNA skip_bigwig=true` (any `[config]`
key can be set on the command line). Outputs are written under
`results/` (configurable via `out_dir`): `results/qcat/`,
`results/nanoplot/`, `results/fastqc/`, `results/minimap2/`,
`results/multiqc/minimap2/` and `results/pipeline_info/`.

## Source

Ported from **[nf-core/nanoseq](https://github.com/nf-core/nanoseq)**, version
`3.1.0` (commit `6e563e54362cddb8e48d15c156251708c22d0e8d`, MIT license).
Created 2026-08-15; this workflow may lag behind upstream releases. Upstream
attribution, the MIT license notice and the list of files copied verbatim
from upstream are in [NOTICE.md](NOTICE.md); the upstream MIT license is
retained verbatim in [LICENSE.upstream](LICENSE.upstream).

> Note: the committee scope summary for this port mentions "Dorado
> demultiplex" and "pycoQC"; **nf-core/nanoseq 3.1.0 actually uses qcat for
> demultiplexing and NanoPlot + FastQC for QC** (pycoQC was removed in
> nanoseq 2.x, Dorado was not yet added in 3.1.0). This port follows the
> real 3.1.0 source.

## Fidelity

Port scope: the **default-parameters main execution path** with
`protocol = DNA`, demultiplexing on (`barcode_kit = Auto`, qcat), minimap2
aligner, and default skip flags (all QC/bigwig/bigbed/reporting on). Rules
are listed in execution order; commands mirror the upstream modules
byte-for-byte under default params (upstream Groovy `params.*` conditionals
are reproduced as bash conditionals over the same config keys).

| Upstream process/rule | oxo-flow rule | Tool (version) | Notes |
|---|---|---|---|
| SAMPLESHEET_CHECK | `samplesheet_check` | python 3.8.3 | identical command (`check_samplesheet.py`, `not_changed` path arg) |
| QCAT | `qcat` | qcat 1.1.0 | identical command (`-f`, `-b`, `--kit`, `--min-score`, zcat preamble, gzip); runs once on `input_path`. Declared outputs are the ported barcode set `barcode01/02` (upstream emits `fastq/*.fastq.gz` dynamically) |
| NANOPLOT | `nanoplot` | NanoPlot 1.41.0 | identical command (`-t N --fastq`); upstream publishes all samples' fixed-named `NanoPlot-report.html` into one dir (silently clobbering) — the port isolates each sample in `nanoplot/<barcode>/` |
| FASTQC | `fastqc` | fastqc 0.11.9 | identical command incl. the symlink-rename preamble; per-sample `<barcode>_fastqc.{html,zip}` |
| GET_CHROM_SIZES | `get_chrom_sizes` | samtools 1.13 | identical (`samtools faidx` + `cut -f 1,2`); upstream conda pin says samtools=1.10, container is 1.13 — port pins the container tag |
| SAMTOOLS_FAIDX | `samtools_faidx` | samtools 1.16.1 | identical (`samtools faidx`); runs on a local copy of the reference like the upstream workdir staging |
| GTF2BED | `gtf2bed` | perl 5.26.2 | identical (`gtf2bed <gtf> > <name>.bed`); **off on the default path** — upstream only runs it when the samplesheet carries a gtf column (`when = config.gtf != ""`) |
| MINIMAP2_INDEX | `minimap2_index` | minimap2 2.17 | identical flags for default params (`-ax map-ont -t 12 -d <fasta>.mmi`); protocol/stranded/junction conditionals preserved |
| MINIMAP2_ALIGN | `minimap2_align` | minimap2 2.17 | identical flags + `> <sample>.sam`; `--MD` conditional preserved (off by default) |
| SAMTOOLS_VIEW_BAM | `samtools_view` | samtools 1.15.1 | identical (`view -b -h -O BAM -@ N -o`) |
| SAMTOOLS_SORT | `samtools_sort` | samtools 1.16.1 | identical (`sort -@ N -o <s>.sorted.bam -T <s>.sorted`; upstream `ext.prefix = <meta.id>.sorted`) |
| SAMTOOLS_INDEX | `samtools_index` | samtools 1.16.1 | identical (`index -@ N-1`) |
| SAMTOOLS_STATS | `samtools_stats` | samtools 1.16.1 | identical (`stats --threads N --reference <fasta>`) |
| SAMTOOLS_IDXSTATS | `samtools_idxstats` | samtools 1.16.1 | identical (`idxstats --threads N-1`) |
| SAMTOOLS_FLAGSTAT | `samtools_flagstat` | samtools 1.16.1 | identical (`flagstat --threads N`) |
| BEDTOOLS_GENOMECOV | `bedtools_genomecov` | bedtools 2.29.2 | identical (`genomecov -split -ibam -bg \| bedtools sort`; upstream hardcodes `-split`) |
| UCSC_BEDGRAPHTOBIGWIG | `ucsc_bedgraphtobigwig` | ucsc-bedgraphtobigwig 377 | identical (`bedGraphToBigWig <bedgraph> <sizes>`) |
| CUSTOM_DUMPSOFTWAREVERSIONS | `dumpsoftwareversions` | python (multiqc 1.13 image) | upstream merges per-process `versions.yml` collected at run time; the port pins the same versions statically in `assets/versions.yml` (values = container tags) and runs the upstream merge script verbatim |
| MULTIQC | `multiqc` | multiqc 1.11 | identical (`multiqc -f .` on a dir with config + report inputs); `--title`/`--config` conditionals preserved; output at `results/multiqc/minimap2/` matching the upstream publishDir path |

Deviation (identity model, see also `main.oxoflow` header): upstream
demultiplexes the raw fastq into **barcode-named** files and then joins them
onto samplesheet rows by barcode, so downstream artifacts are named
`<group>_R<replicate>.bam` etc. oxo-flow has no channel join, so the port
keys all per-sample rules by the barcode itself — outputs are named
`barcode01.sam`, `barcode01.bam`, `barcode01.bigWig`, ... while keeping every
command and intermediate filename upstream-identical. The samplesheet
fixture maps barcodes `01`/`02` exactly like the upstream test data.

Not ported (all off by default upstream, so absent from the default path):

| Upstream step | Reason |
|---|---|
| GRAPHMAP2_INDEX / GRAPHMAP2_ALIGN (aligner `graphmap2`) | off by default (`aligner = minimap2`); committee exclusion `longread_map` |
| NANOLYSE (+ GET_NANOLYSE_FASTA) | off by default (`run_nanolyse = false`) |
| MEDAKA_VARIANT / DEEPVARIANT / PEPPER_MARGIN_DEEPVARIANT (+ bgzip/tabix) | off by default (`call_variants = false`) |
| SNIFFLES / CUTESV (+ sort/tabix) | off by default (`call_variants = false`) |
| BEDTOOLS_BAMBED / UCSC_BED12TOBIGBED | protocol-gated upstream to `cDNA`/`directRNA` (`when: protocol == directRNA \|\| cDNA`) — never runs on the DNA default path; committee exclusion `transcriptome` |
| BAMBU / STRINGTIE2 / SUBREAD_FEATURECOUNTS / DESEQ2 / DEXSEQ | gated on `protocol == cDNA/directRNA` + `skip_quantification = false` — not on the DNA default path; committee exclusion `transcriptome` |
| NANOPOLISH_INDEX_EVENTALIGN / XPORE_DATAPREP / XPORE_DIFFMOD / M6ANET_DATAPREP / M6ANET_INFERENCE (RNA modification) | gated on `protocol == directRNA` — not on the DNA default path; committee exclusion `plotly` (m6anet plots) |
| JAFFAL / GET_JAFFAL_REF / UNTAR (RNA fusion) | gated on `protocol == cDNA/directRNA` — not on the DNA default path |
| BAM_RENAME | only when `skip_alignment = true` |
| GET_TEST_DATA / GET_NANOLYSE_FASTA (test-profile downloads) | `-profile test` only, replaced by checked-in fixtures |
| SAMTOOLS_SORT_INDEX (combined sort+index) | `call_variants` branch only |
| `-profile test*` configs, cluster/container profiles, Tower reporting, completion email | nf-core infrastructure, out of port scope |

## Test

```bash
bash test/run.sh
```

Runs `validate` + `lint` + a `dry-run` plan check (and an expanded-command
wildcard check) against the checked-in fixtures — the same gate CI runs on
every push.

## License

Apache-2.0. Copyright (c) 2026 oxo-flow-community. Upstream attribution in
[NOTICE.md](NOTICE.md); the upstream MIT license is retained verbatim in
[LICENSE.upstream](LICENSE.upstream).
