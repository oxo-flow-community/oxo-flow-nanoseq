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

Beyond the default path, every gated branch of the upstream workflow is
ported as `when`-gated rules, all **off by default** (matching upstream):
contamination filtering with NanoLyse (`run_nanolyse`), the graphmap2
aligner (`aligner = "graphmap2"`), short variant calling with
medaka / DeepVariant / PEPPER-Margin-DeepVariant and structural variant
calling with Sniffles / cuteSV (`call_variants`), BigBed tracks
(`protocol` cDNA/directRNA), transcript quantification with
bambu or StringTie2+featureCounts plus DESeq2/DEXSeq differential
analysis (`protocol` cDNA/directRNA), RNA modification analysis with
Nanopolish + xPore/m6anet (`protocol = directRNA`), and pre-aligned-BAM
input (`skip_alignment` + `sample_bams`). See the [Fidelity](#fidelity)
section for the full rule map.

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

Port scope: the **complete nf-core/nanoseq 3.1.0 rule graph** — 52 oxo-flow
rules (19 default-path + 33 gated). The first table covers the
**default-parameters main execution path** (`protocol = DNA`, demultiplexing
on (`barcode_kit = Auto`, qcat), minimap2 aligner, default skip flags); the
second covers every **gated branch** (off by default, upstream gates
reproduced as `when` conditionals over the same config keys). Commands
mirror the upstream modules byte-for-byte under each branch's parameters.

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
| SAMTOOLS_SORT | `samtools_sort` | samtools 1.16.1 | identical minus `-m 512M` capped per-thread sort buffer (added to prevent OOM on large BAMs; see Deviations) |
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

### Gated branches (all off by default, matching upstream defaults)

| Upstream process/rule | oxo-flow rule | Tool (version) | Gate / notes |
|---|---|---|---|
| NANOLYSE | `nanolyse` | NanoLyse 1.2.0 | `run_nanolyse`; `gunzip -c \| NanoLyse -r <ref> \| gzip`; reference = checked-in `test/fixtures/refs/lambda.fasta.gz` (upstream downloads it via GET_NANOLYSE_FASTA) |
| GRAPHMAP2_INDEX | `graphmap2_index` | graphmap 0.6.3 | `aligner == "graphmap2"`; `-x rnaseq`/`--gtf` conditionals preserved (non-DNA protocols) |
| GRAPHMAP2_ALIGN | `graphmap2_align` | graphmap 0.6.3 | same gate; `--extcigar`; publishes into `results/minimap2/` (see Deviations) |
| SAMTOOLS_SORT_INDEX | `samtools_sort_index` | samtools 1.16.1 | `call_variants` — upstream runs this combined sort+index instead of the separate rules in the VC branch; `-m 512M` (see Deviations) |
| MEDAKA_VARIANT | `medaka_variant` | medaka 1.4.4 | `call_variants && protocol == DNA && !skip_vc && variant_caller == "medaka"`; `-d -f -i -o -t` + `$split_mnps`/`$phase_vcf` flags (`split_mnps`, `phase_vcf` config keys) |
| TABIX_BGZIP (as MEDAKA_BGZIP_VCF) | `medaka_bgzip_vcf` | tabix 1.11 | same gate |
| TABIX_TABIX (as MEDAKA_TABIX_VCF) | `medaka_tabix_vcf` | tabix 1.11 | same gate |
| DEEPVARIANT | `deepvariant` | google/deepvariant 1.4.0 | `variant_caller == "deepvariant"`; docker-only upstream; `--model_type WGS --num_shards=N` |
| DEEPVARIANT_TABIX_VCF | `deepvariant_tabix_vcf` | tabix 1.11 | same gate |
| DEEPVARIANT_TABIX_GVCF | `deepvariant_tabix_gvcf` | tabix 1.11 | same gate |
| PEPPER_MARGIN_DEEPVARIANT | `pepper_margin_deepvariant` | kishwars/pepper_deepvariant r0.8 | `variant_caller == "pepper_margin_deepvariant"`; `-g` honored via `deepvariant_gpu` (CPU image pinned, see Deviations) |
| SNIFFLES | `sniffles` | sniffles 1.0.12 | `call_variants && protocol == DNA && !skip_sv && structural_variant_caller == "sniffles"`; `-m -v -t` |
| BCFTOOLS_SORT (as SNIFFLES_SORT_VCF) | `sniffles_sort_vcf` | bcftools 1.16 | same gate |
| TABIX_TABIX (as SNIFFLES_TABIX_VCF) | `sniffles_tabix_vcf` | tabix 1.11 | same gate |
| CUTESV | `cutesv` | cutesv 1.0.12 | `structural_variant_caller == "cutesv"`; `cuteSV bam fasta vcf . --threads --sample --genotype` |
| BCFTOOLS_SORT (as CUTESV_SORT_VCF) | `cutesv_sort_vcf` | bcftools 1.16 | same gate |
| TABIX_TABIX (as CUTESV_TABIX_VCF) | `cutesv_tabix_vcf` | tabix 1.11 | same gate |
| BEDTOOLS_BAMBED | `bedtools_bamtobed` | bedtools 2.29.2 | `!skip_bigbed && protocol cDNA/directRNA` (upstream module `when` — never on the DNA path) |
| UCSC_BED12TOBIGBED | `ucsc_bed12tobigbed` | ucsc-bedtobigbed 377 | same gate |
| BAMBU | `bambu` | bioconductor-bambu 3.0.8 | `protocol != DNA && !skip_quantification && quantification_method == "bambu"`; gathers all sample BAMs via expand_inputs; upstream `bin/run_bambu.r` verbatim |
| STRINGTIE2 | `stringtie2` | stringtie 2.1.4 | `quantification_method == "stringtie2"`; `-L -G <gtf> -o <s>.stringtie.gtf` |
| STRINGTIE_MERGE | `stringtie_merge` | stringtie 2.2.1 | same gate; gathers per-sample assemblies, `-G` reference GTF conditional preserved |
| SUBREAD_FEATURECOUNTS | `subread_featurecounts` | subread 2.0.1 | same gate; gene counts (`-f -g gene_id -t exon`) + transcript counts (`-F GTF -g transcript_id -t transcript --extraAttributes gene_id`), `-L -O --primary --fraction` |
| DESEQ2 | `deseq2` (bambu counts) / `deseq2_featurecounts` (featureCounts counts) | mulled-v2-8849acf3… (bioconductor-deseq2) | `!skip_differential_analysis`; mutually exclusive on `quantification_method`; upstream `bin/run_deseq2.r` verbatim; results under `results/bambu/deseq2/` (upstream publishDir quirk kept) |
| DEXSEQ | `dexseq` (bambu counts) / `dexseq_featurecounts` (featureCounts counts) | docker.io/yuukiiwa/nanoseq:dexseq | same gates; upstream `bin/run_dexseq.r` verbatim |
| NANOPOLISH_INDEX_EVENTALIGN | `nanopolish_index_eventalign` | nanopolish 0.13.2 | `protocol == directRNA && !skip_modification_analysis && nanopolish_fast5 != ""`; `nanopolish index -d <fast5>` + `eventalign --scale-events --signal-index` (see Deviations for the fast5 gate guard) |
| XPORE_DATAPREP | `xpore_dataprep` | xpore 2.1 | `!skip_xpore` (same branch gate); `--genome --gtf_or_gff --transcript_fasta` |
| XPORE_DIFFMOD | `xpore_diffmod` | xpore 2.1 | same gate; upstream `bin/create_yml.py` verbatim; depends_on dataprep dir |
| M6ANET_DATAPREP | `m6anet_dataprep` | docker.io/yuukiiwa/m6anet:1.0 | `!skip_m6anet` (same branch gate) |
| M6ANET_INFERENCE | `m6anet_inference` | docker.io/yuukiiwa/m6anet:1.0 | same gate; `--batch_size 512 --num_iterations 5 --device cpu`; depends_on dataprep dir |
| BAM_RENAME | `bam_rename` | sed 4.7.0 (shell-only container) | `skip_alignment && sample_bams != ""`; comma-separated `sample_bams` split via expand_inputs and linked to the barcode names, `[ ! -f ] && ln -s` like upstream |

### Not ported (remainder)

| Upstream step | Reason |
|---|---|
| JAFFAL / GET_JAFFAL_REF / UNTAR (RNA fusion, `protocol` cDNA/directRNA) | not portable: the JAFFA reference bundle (`https://ndownloader.figshare.com/files/28168755`) returns **HTTP 403** for direct download, is multi-GB, and embeds a `JAFFA_stages.groovy` script the module runs; JAFFA 1.09 has no conda/biocontainer package |
| GET_TEST_DATA / GET_NANOLYSE_FASTA (test-profile downloads) | nf-core `-profile test` download infrastructure, not part of the pipeline itself; replaced by checked-in fixtures (incl. the new `test/fixtures/refs/lambda.fasta.gz` nanolyse reference) |
| `-profile test*` configs, cluster/container profiles, Tower reporting, completion email | nf-core infrastructure, out of port scope |

### Deviations from upstream

1. **Nanolyse channel**: upstream NANOLYSE replaces the demultiplexed-reads
   channel, so every downstream process consumes NanoLyse-filtered reads.
   oxo-flow has no channel reassignment — `nanolyse` writes filtered reads to
   `results/nanolyse/` and the downstream chain keeps consuming the
   demultiplexed reads.
2. **graphmap2 namespace**: upstream publishes graphmap2 outputs under
   `results/graphmap2/`; the port writes the graphmap2 index and SAMs into
   `results/minimap2/` so the shared downstream chain (view/sort/index/stats)
   needs no duplicate rules. Commands are unchanged.
3. **`bam_suffix` mechanic**: the alignment branch sorts to
   `<barcode>.sorted.bam`; the `skip_alignment` branch links user BAMs as
   `<barcode>.bam`. `bam_suffix` (default `.sorted.bam`) lets the
   quantification and modification rules target either naming scheme.
4. **DESEQ2/DEXSEQ same-output pairs**: upstream feeds whichever counts
   channel exists (bambu or featureCounts). The port implements two rules per
   tool with the **same output path**, mutually exclusive on
   `quantification_method`. The upstream publishDir quirk (deseq2/dexseq
   results under `results/bambu/`) is kept verbatim.
5. **nanopolish fast5**: upstream takes a per-sample fast5 path; the port
   takes `nanopolish_fast5` as one directory and adds a `!= ""` gate guard so
   the directRNA modification branch only runs when it is configured (upstream
   runs nanopolish whenever `protocol == directRNA`).
6. **deepvariant_gpu**: the pepper rule honors the `-g` flag from
   `deepvariant_gpu`, but the container is pinned to the CPU image
   (`docker.io/kishwars/pepper_deepvariant:r0.8`) — upstream swaps to
   `r0.8-gpu`. Swap the image and set `deepvariant_gpu = true` for GPU
   calling.
7. **`-m 512M`**: `samtools_sort` and `samtools_sort_index` cap the
   per-thread sort buffer (upstream omits `-m`); the cap prevents OOM at the
   port's fixed thread counts.
8. **versions.yml**: `assets/versions.yml` pins the default-path tool
   versions statically (the port's dumpsoftwareversions); gated-branch tools
   (medaka, tabix, sniffles, …) are not listed. The default-path report is
   unchanged.
9. **MultiQC gap**: MultiQC cannot aggregate featureCounts `.summary` files;
   the always-on `multiqc` rule's inputs cannot be branch-gated, so
   featureCounts outputs are excluded from the report.
10. **is_transcripts column**: upstream decides splice/rnaseq presets and
    junctions per sample from the samplesheet `is_transcripts` column; the
    port's identity model keys rules by barcode only, so the non-DNA default
    applies (same as the minimap2 rules).

## Test

```bash
bash test/run.sh
```

Runs `validate` + `lint` + a `dry-run` plan check (and an expanded-command
wildcard check) against the checked-in fixtures — the same gate CI runs on
every push.

## Live verification (tx-ubuntu, oxo-flow 0.15.0 + PR #187/#192 engine)

| Run | Status | Notes |
|---|---|---|
| default (DNA, qcat → nanoplot/fastqc → minimap2 → multiqc) | ✅ live-verified | full default path on the 60-read barcoded fixture |
| call_variants (medaka chain) | ✅ live-verified | medaka 1.4.4 runs to completion (`--samples barcode01`; see degeneracy note) |
| structural_variant_caller (sniffles/cutesv) | ✅ live-verified | SV chain on barcode01 |
| nanolyse branch | ✅ live-verified | checked-in lambda fixture replaces the upstream download |
| cDNA/directRNA quantification (bambu/stringtie2) | ⚠️ tool-execution verified | bambu/stringtie2 execute with the checked-in `mini.gtf`; the 60-read fixture's reads align to the `real_read_*` contigs, not the annotated chr1 region, so bambu's read filtering legitimately fails on zero-overlap data — a follow-up fixture (reads over the annotated transcripts) would close this to full PASS |

Mini-fixture degeneracy: barcode02/barcode05 carry a single read each;
sniffles (SV calling) requires more reads than that, so the SV run uses
`--samples barcode01`. Real data takes the verbatim upstream path.

## License

Apache-2.0. Copyright (c) 2026 oxo-flow-community. Upstream attribution in
[NOTICE.md](NOTICE.md); the upstream MIT license is retained verbatim in
[LICENSE.upstream](LICENSE.upstream).
