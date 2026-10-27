#!/usr/bin/env python3
"""Offline documentation, provenance and table schema index; no new analysis."""
from pathlib import Path
import csv
import hashlib
import json
import subprocess
import re
import pandas as pd
R=Path(__file__).resolve().parents[2]
D=R/'data/release'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def link(p,prefix=''):return f'[{p}]({prefix}{p})'
def main():
    registry=json.loads((D/'source_manifest.json').read_text())
    lines=['# Datasets and provenance','',
    'This guide documents the actual research resources, as distinct from datasets only found by a search. The machine-readable [source manifest](data/release/source_manifest.json) contains full author lists, titles, DOI/year, populations, phenotype definitions, uses, scripts, outputs and source terms for each analytical/resource family. Unknown quantities are explicitly stated rather than inferred. Research snapshot: 24 September 2026; release metadata checks: 27 October 2026.','',
    '**Hamiltonian Labs recruited no participants.** The programme used published summary statistics, molecular association summaries, annotation databases and literature. Participant genotypes, clinical records and identifiable exceptional individuals are not release data.','',
    '## Cohort and phenotype boundaries','',
    '- Davies discovery analysed the public N=282,014 file, not all 300,486 participants in the publication. Savage shares UKB/COGENT. Do not sum their participant counts.',
    '- Zabaneh cases were selected from approximately the top 0.03% via above-level SAT/ACT testing in Duke TIP. Its HRS controls overlap Davies. This is a sensitivity dataset, not independent replication or identified high-IQ individuals.',
    '- G&C executive function is the counted non-UKB recruitment lineage; individual participant overlap has not been comprehensively checked. Howe within-family estimates share some UKB/Generation Scotland people with discovery: they add a family-design contrast, not a disjoint sample.',
    '- GenLang PIQ includes BATS (1,414/18,722 = 7.6%) shared with Davies. Mathematics self-report/course-taking (Gq), objective arithmetic and education are distinct from general intelligence.',
    '- Molecular study names are not independent donor sets. ROSMAP/CommonMind recur in bulk, Bryois, SingleBrain and brainSCOPE. GTEx versions reuse donors. Transcript-level rows are not independent gene-level evidence.',
    '- Most cognitive discovery and reference LD are European. Molecular cross-ancestry inputs do not make the whole analysis ancestry-general.',
    '', '## Complete record indexes','',
    '- [419 tournament study metadata records](data/gene_tournament/study_metadata.jsonl): phenotype, accession, cohort/ancestry strings, sample-size descriptions and full-summary availability. Search inclusion is not evidence of execution.',
    '- [Study classification implementation](pipelines/gene_tournament/classify_studies.py) and [phenotype model](research/sprint5a/phenotype_model.md) separate direct cognition, proxies, clinical and excluded evidence.',
    '- [132-publication bibliography](data/release/catalogue_publications.json): verified publication metadata for all unique PMIDs in the tournament and selected QTL metadata; original titles, full authors, years and DOI where assigned.',
    '- [Selected QTL assay inventory](data/sprint4/eqtl_catalogue_brain_datasets.csv): QTD/QTS identifiers, tissue, assay, sample size, adult/fetal classification, eligibility/exclusion, PMID and exact URLs. [Complete R7 catalogue metadata](data/raw/sprint4/eqtl_catalogue/metadata/dataset_metadata_r7.tsv) includes resources not used.',
    '- [brainSCOPE file inventory](data/sprint5/brainscope_datasets.csv): cell-specific sample sizes, significance scope, build/alleles and hashes.',
    '- [Cohort overlap ledger](data/sprint5/cohort_overlap_ledger.csv): includes candidate-only/unavailable studies and dated provisional findings; the 5A update takes precedence on completed within-family access.',
    '- [Acquisition/provenance index](data/release/provenance_index.json): every committed provenance/manifest record, plus a pointer to the raw snapshot spine. Original and sanitised file hashes are distinguished.',
    '', '## Analytical and reference resources','']
    for x in registry['datasets']:
        p=x['publication'];authors=p.get('authors') or 'No single author list assigned';short=authors.split(',')[0]+(' et al.' if ',' in authors else '')
        citation=f"{short} ({p.get('year') or 'versioned resource'}). *{p['title']}*"
        if p.get('doi'):citation+=f". [DOI](https://doi.org/{p['doi']})"
        lines += [f"### {x['name']} (`{x['id']}`)",'',citation+'. Full author metadata is in the source manifest.', '',
                  f"**Phenotype / selection:** {x['phenotype']}. {x['selection']}.",
                  f"**Population / N:** {x['population']}. {x['sample_size']}.",
                  f"**Obtained and used:** {x['files_obtained']}. {x['project_use']}.",
                  '**Implementation:** '+', '.join(link(p) for p in x['scripts'])+'.',
                  '**Dependent outputs:** '+', '.join(link(p) for p in x['outputs'])+'.',
                  f"**Dependence / limitations:** {x['limitations']}.",
                  f"**Rights/access:** {x['licence_and_redistribution']}. [Official source]({x['official_source']}).",
                  '**Provenance:** '+', '.join(link(p) for p in x['provenance'])+'.','']
    lines+=['## Access-blocked or candidate-only resources','',
            'Tan larger family GWAS, full brainSCOPE associations, TGFM controlled GTEx inputs, 23andMe full Gq GWAS, AstraZeneca PheWAS and individual-level rare-variant burden analyses were not completed from those inputs. Other studies in the overlap ledger may have been searched or assessed for eligibility only. Do not label a search hit as a new analysis. [Access queue](reports/sprint5a/USER_ACCESS_REQUIRED.md).','',
            'Reacquire exact versions from the recorded source URLs and verify the original hashes; do not silently replace them with current releases. If a missing licence, ancestry or sample-size detail matters to reuse, verify it with the original steward. No new permission is implied by this catalogue. [Reproduction](REPRODUCIBILITY.md) · [Rights](DATA_LICENSE.md).']
    (R/'DATASETS.md').write_text('\n'.join(lines)+'\n')
    files=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard'],cwd=R,text=True).splitlines()
    prov=[]
    for f in sorted(set(files)):
        p=R/f
        if not p.is_file() or f.startswith('data/release/') or f=='RELEASE_MANIFEST.json':continue
        if 'provenance' in f.lower() or 'manifest' in p.name.lower():
            prov.append({'path':f,'sha256_release_bytes':sha(p),'bytes':p.stat().st_size})
    (D/'provenance_index.json').write_text(json.dumps({'schema':'provenance-index/1.0','raw_snapshot_spine':'data/raw/MANIFEST.jsonl','privacy_transforms':'docs/security/sanitisation_manifest.json','records':prov},indent=2)+'\n')
    inventory=[]
    for f in sorted(set(files)):
        p=R/f
        if not p.is_file() or not f.startswith('reports/') or p.suffix not in ['.csv','.tsv','.parquet','.json','.md','.html']:continue
        status='HISTORICAL_FOUNDATIONAL'
        if f.startswith('reports/sprint5/'):status='HISTORICAL_SPRINT5_SUPERSEDED'
        if f.startswith('reports/sprint5a/'):status='HISTORICAL_SPRINT5A_SEE_RELEASE_CORRECTIONS'
        if 'alphagenome' in f.lower():status='UNRESOLVED_DIRECTION_AGGREGATION'
        if f.startswith('reports/release/'):status='RELEASE_VALIDATION'
        inventory.append({'path':f,'stage_status':status,'format':p.suffix[1:]})
    with (D/'historical_output_index.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,lineterminator="\n",fieldnames=['path','stage_status','format']);w.writeheader();w.writerows(inventory)
    descriptions={
      'gene':'Original gene-symbol label. NULL.MODEL is a historical FOCUS null-model placeholder, not a gene.',
      'locus_id':'Project LD locus identifier; not a causal-gene ID. Empty for panel/rare-coding entities without a mapped locus.',
      'classes':'Semicolon-separated independent variant-to-gene evidence classes; related QTL rows collapse into one class.',
      'n_classes':'Count of eligible distinct V2G classes; not number of studies or participants.',
      'class_detail':'JSON object containing per-class evidence counts or maximum coding PIP; semantics depend on class.',
      'gene_class':'Frozen categorical gene adjudication. MODERATE is a hypothesis; HIGH is absent.',
      'locus_stratum':'L1 strongest, L2 moderate, L3 weak, L4_DISCORDANT discordant, NT untestable under frozen integration.',
      'direction_stratum':'D1–D5 protocol tiers; D1 requires credible gene, replication and robust independent adult direction. No D1 here.',
      'log10BF_independent':'Sum of base-10 Bayes factors for counted design lineages; cohort overlap caveat applies; not posterior probability.',
      'locus_rank_interval':'Historical 5th–95th percentile rank interval encoded as text.',
      'focus_primary_pip':'FOCUS primary gene/tissue-model posterior inclusion probability; model-dependent.',
      'focus_contradiction':'Whether FOCUS favours a competing gene enough to trigger the frozen contradiction rule.',
      'contested':'Competing gene assignment indicator; not evidence of an intervention effect.',
      'max_classes_other_gene_in_locus':'Largest V2G class count among alternative genes in the same locus.',
      'other_genes_with_classes':'Semicolon-separated competing genes carrying qualifying evidence.',
      'adult_brain_median_tpm_gtex':'GTEx adult-brain median transcript abundance, TPM; not causal direction.',
      'developmental_class':'Timing class derived from expression context; BrainSpan-derived terms remain noncommercial.',
      'direction_n_rows':'Count of eligible direction rows; rows are not independent donor cohorts.',
      'direction_n_cohort_units':'Number of collapsed molecular cohort units counted by the direction rule.',
      'perturbation_stratum':'P1–P5 human perturbation evidence tier under frozen rules; loss of function is not enhancement.',
      'rank':'Mechanical locus ordering under the frozen method; not a calibrated gene rank.',
      'rank_p05':'5th percentile of historical bootstrap locus rank.', 'rank_p95':'95th percentile of historical bootstrap locus rank.',
      'p_top10':'Fraction of historical bootstrap runs in top ten; not probability of causality.', 'p_top20':'Fraction in top twenty; not probability of causality.',
      'lead_snp':'Original rsID defining the deduplicated GWAS signal.',
      'labels':'Semicolon-separated project locus IDs sharing the lead SNP.',
      'top_gene_labels':'Positional gene names used to label loci; not causal assignments.',
      'cognition_increasing_allele':'Harmonised allele associated with higher cognitive performance; not treatment guidance.',
      'wf_aligned_z':'Within-family effect z statistic aligned to the cognition-increasing allele.',
      'gc_aligned_z':'G&C trail-making z statistic, polarity-reversed for better cognition.',
      'status':'Execution/evidence state; UNRESOLVED and NOT_TESTABLE never mean NO_EFFECT.',
      'analysis_stage':'Mandatory stage label: historical Sprint 5 rows may be superseded; release rows reflect current adjudication.',
      'evidence_file':'Repository-relative supporting evidence file; preserve stage context.',
      'independence_unit':'Label used to collapse dependent evidence; does not guarantee disjoint participants.',
      'v2g_class':'Variant-to-gene class; sequence-model units are unresolved/excluded in release.',
      'value':'Original evidence-unit numerical value; interpret with method/assay, not as a universal score.',
      'field':'Column changed during cached release correction.', 'historical':'Exact pre-correction textual value.', 'release':'Replacement textual value after correction.',
    }
    dictionary=[]
    targets=['gene_assessments.csv','locus_confidence.csv','negative_results.csv','evidence_units.parquet','adult_candidates.csv','correction_changes.csv']
    for n in targets:
        p=D/n;df=pd.read_parquet(p) if p.suffix=='.parquet' else pd.read_csv(p)
        for col in df:
            desc=descriptions.get(col)
            if not desc:
                if col.startswith('rank_') or col=='pareto_layer_E':desc='Mechanical ranking/Pareto field from classify_genes.py; lower is higher priority, not causal probability.'
                elif col.startswith('log10BF'):desc='Historical base-10 Bayes factor component; phenotype and sensitivity status are encoded in the column name.'
                elif col.endswith('_z'):desc='Historical allele-aligned z statistic for the named study/processing stage; dimensionless.'
                else:desc='Original source field: '+col.replace('_',' ')+'. Interpret using the linked classifier, protocol and source-specific method; missing values mean unavailable, not zero.'
            dictionary.append(dict(table='data/release/'+n,column=col,dtype=str(df[col].dtype),missing=int(df[col].isna().sum()),description=desc,definition_source='METHODOLOGY.md; research/sprint5/protocol_rules.json; pipelines/sprint5/classify_genes.py'))
    with (D/'data_dictionary.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,lineterminator="\n",fieldnames=list(dictionary[0]));w.writeheader();w.writerows(dictionary)
    (D/'README.md').write_text('''# Public research data — v0.1.1

These are hypotheses and evidence records, not enhancement targets. The corrected release excludes unresolved AlphaGenome sequence-model votes. Exact original scientific values are preserved where unchanged; the complete original files remain in historical directories.

| File | Scope |
|---|---|
| [gene_assessments.csv](gene_assessments.csv) | Complete 531-row cached re-adjudication, including competing genes, uncertainty, direction and mechanical rank fields. The inherited `NULL.MODEL` row is a FOCUS placeholder, not a biological gene. |
| [locus_confidence.csv](locus_confidence.csv) | Exact historical Sprint 5A 152-signal locus table, including rank intervals and cohort-sensitive support. |
| [evidence_units.parquet](evidence_units.parquet) | Complete 1,603-unit inherited evidence table; three AlphaGenome units marked unresolved. Join historical dependencies by unit ID with [dependency graph](../sprint5a/s5_integrated/evidence_dependency_graph.parquet). |
| [adult_candidates.csv](adult_candidates.csv) | Header-only, zero qualifying rows. This is an intended result. |
| [decision.json](decision.json) | Current closed intervention gate, with valid JSON nulls and corrected access/status descriptions. |
| [negative_results.csv](negative_results.csv) | Complete original Sprint 5 negative record plus current release negatives; **filter `analysis_stage`**. Historical access/biology statements may be superseded. |
| [correction_changes.csv](correction_changes.csv) | Every changed adjudication field, including competitor counts and mechanically shifted ranks. |
| [source_manifest.json](source_manifest.json) | Dataset/resource bibliography, populations, uses, limits and rights. |
| [catalogue_publications.json](catalogue_publications.json) | Complete 132-publication metadata lookup for tournament/QTL provenance; not a list of new analyses. |
| [provenance_index.json](provenance_index.json) | Acquisition-record locations and release-byte checksums. |
| [historical_output_index.csv](historical_output_index.csv) | Complete report navigation with stage and unresolved-status labels. |
| [data_dictionary.csv](data_dictionary.csv) | Every column in the principal release data tables; dtype and missingness plus interpretation. |

CSV is UTF-8, comma-delimited with quoted fields as needed; embedded JSON/semicolon lists remain intact. Empty values mean missing/not applicable, never a zero effect. Parquet preserves typed identifiers and values. `locus_id` is project-specific; gene symbols, Ensembl/HGNC/Entrez IDs and rsIDs retain their original roles. Original full gene identifiers are in the [18,418-gene screen](../../reports/gene_tournament/direct_cognition_rank.csv).

The historical [top ten](../../reports/sprint5/TOP10_CAUSAL_GENE_CANDIDATES.csv) and [top-twenty-labelled panel](../../reports/sprint5/TOP20_RESEARCH_PRIORITY_GENES.csv) predate 5A; the latter has 25 entries. The [5A shortlists](../../reports/sprint5a) and dossiers are preserved but AlphaGenome directional fields are unresolved. Use [RESULTS.md](../../RESULTS.md) for current interpretation.

No combined-data permissive licence is asserted. [DATA_LICENSE.md](../../DATA_LICENSE.md) and source terms apply, including BrainSpan restrictions on developmental fields. [Rebuild commands](../../REPRODUCIBILITY.md) · [Correction](../../docs/corrections/ALPHAGENOME_DIRECTION.md).
''')
    print(f'Indexed {len(registry["datasets"])} resource families, {len(prov)} provenance records, {len(inventory)} reports, {len(dictionary)} columns.')
if __name__=='__main__':main()
