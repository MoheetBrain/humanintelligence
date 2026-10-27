#!/usr/bin/env python3
"""Fast offline public-release verification using the Python standard library."""
from pathlib import Path
import csv,hashlib,json,re,subprocess,sys,urllib.parse
R=Path(__file__).resolve().parents[2]
def rows(f):return list(csv.DictReader((R/f).open()))
def main():
 errors=[]
 def check(ok,message):
  if not ok:errors.append(message)
 manifest=json.loads((R/'RELEASE_MANIFEST.json').read_text())
 for x in manifest['files']:
  p=R/x['path'];check(p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==x['sha256'],'Missing/changed release file: '+x['path'])
 g=rows('reports/gene_tournament/direct_cognition_rank.csv');sig=[x for x in g if x['bonferroni_davies'].lower()=='true']
 check((len(g),len(sig),len({x['ld_block_r0.2'] for x in sig}))==(18418,375,159),'Gene-screen denominator mismatch')
 w=rows('reports/sprint4/within_family_locus_concordance.csv');v=[x for x in w if x['status']=='TESTABLE']
 check((len(w),len(v),sum(float(x['wf_aligned_z'])>0 for x in v))==(159,146,109),'Within-family counts mismatch')
 m=rows('data/release/gene_assessments.csv');check(len(m)==531,'Assessment row count')
 check({x['gene'] for x in m if x['gene_class']=='CAUSAL_GENE_MODERATE'}=={'DNPH1','TTBK1','FAM131A'},'Moderate set differs')
 check(not any(x['gene_class']=='CAUSAL_GENE_HIGH' or x['direction_stratum']=='D1' for x in m),'Unexpected high/D1 claim')
 check(not any('SEQUENCE_MODEL' in x['classes'] for x in m),'Unresolved AlphaGenome vote in current matrix')
 check(len(rows('data/release/adult_candidates.csv'))==0,'Adult shortlist must remain empty')
 check(len(rows('data/release/locus_confidence.csv'))==152,'Locus signal denominator')
 check(len(rows('reports/sprint5/TOP10_CAUSAL_GENE_CANDIDATES.csv'))==10,'Historical top-ten size')
 check(len(rows('reports/sprint5/TOP20_RESEARCH_PRIORITY_GENES.csv'))==25,'Historical Pareto panel size')
 decision=json.loads((R/'data/release/decision.json').read_text());check(decision['chemistry_gate']=='CLOSED','Intervention gate')
 check('COMPLETED' in decision['gate_a_within_family'],'Stale Gate A status');check('EXCLUDED' in decision['alphagenome'],'Stale AlphaGenome status')
 for line in (R/'.env.example').read_text().splitlines():check(not line or line.startswith('#') or line.endswith('=') and line.count('=')==1,'Nonempty env template assignment')
 for d in json.loads((R/'data/release/source_manifest.json').read_text())['datasets']:
  for kind in ['scripts','outputs','provenance']:
   for f in d[kind]:check((R/f).exists(),f'Missing source-manifest {kind}: {f}')
 docs=['README.md','METHODOLOGY.md','DATASETS.md','RESULTS.md','LIMITATIONS.md','REPRODUCIBILITY.md','CONTRIBUTING.md','SECURITY.md','DATA_LICENSE.md','CHANGELOG.md','data/release/README.md']
 docs += [str(p.relative_to(R)) for base in ['docs/corrections','docs/security','reports/release'] for p in (R/base).glob('*.md')]
 docs += ['docs/ZENODO.md','docs/ANNOUNCEMENT_X.md']
 for f in docs:
  p=R/f
  for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
   if re.match(r'^[a-z]+:',target) or target.startswith('#'):continue
   target=urllib.parse.unquote(target.split('#')[0]);check((p.parent/target).exists(),f'Broken local link in {f}: {target}')
 if errors:print('\n'.join(errors));return 1
 print(f'PASS: {len(manifest["files"])} file hashes; gene/locus/family counts; corrected classes; empty adult gate; dataset references; {len(docs)} documents; credential template.')
 return 0
if __name__=='__main__':sys.exit(main())
