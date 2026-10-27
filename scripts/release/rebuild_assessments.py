#!/usr/bin/env python3
"""Re-adjudicate cached Sprint 5A evidence without suspect AlphaGenome votes.
No downloads, fine-mapping, model calls, or genome-wide analyses. Original outputs stay intact.
"""
import json
import csv
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import hashlib
import pandas as pd
R = Path(__file__).resolve().parents[2]

def main():
    source = R / 'reports/sprint5a/s5_integrated'
    dat = R / 'data/sprint5a/s5_integrated'
    with tempfile.TemporaryDirectory(prefix='cognition-release-') as td:
        out, data = Path(td)/'reports', Path(td)/'data'
        shutil.copytree(source, out); shutil.copytree(dat, data)
        units = pd.read_parquet(data/'evidence_units.parquet')
        excluded = (units.v2g_class == 'SEQUENCE_MODEL') & (units.status == 'OK')
        affected = sorted(units.loc[excluded, 'gene'].dropna().unique())
        units.loc[excluded, 'status'] = 'UNRESOLVED_DIRECTION_AGGREGATION'
        units.loc[excluded, 'notes'] = 'Excluded by release correction; original raw AlphaGenome predictions absent from Git.'
        units.to_parquet(data/'evidence_units.parquet', index=False)
        env = dict(os.environ, S5_OUT=str(out), S5_DATA=str(data), S5A_INTEGRATION='1', PYTHONPATH=str(R/'src'))
        for stage in ['classify_genes', 'decide_sprint5']:
            result = subprocess.run([sys.executable,str(R/f'pipelines/sprint5/{stage}.py')], cwd=R, env=env, capture_output=True, text=True)
            if result.returncode: raise RuntimeError(f'{stage} failed: {result.stderr[-3000:]}')
        dest = R/'data/release'; dest.mkdir(exist_ok=True)
        old = pd.read_csv(source/'causal_gene_evidence_matrix.csv').set_index('gene')
        new = pd.read_csv(out/'causal_gene_evidence_matrix.csv').set_index('gene')
        original_rows=list(csv.DictReader((source/'causal_gene_evidence_matrix.csv').open()))
        regenerated={x['gene']:x for x in csv.DictReader((out/'causal_gene_evidence_matrix.csv').open())}
        def equivalent(a,b):
            if a==b:return True
            try:
                x,y=float(a),float(b)
                return math.isclose(x,y,rel_tol=1e-14,abs_tol=1e-15) or (math.isnan(x) and math.isnan(y))
            except (ValueError,TypeError):pass
            try:
                x,y=json.loads(a),json.loads(b)
                if isinstance(x,dict) and isinstance(y,dict) and x.keys()==y.keys():
                    return all(equivalent(str(x[k]),str(y[k])) for k in x)
            except (ValueError,TypeError):pass
            return False
        changes=[]
        for row in original_rows:
            for field,value in regenerated[row['gene']].items():
                if not equivalent(row[field],value):
                    changes.append(dict(gene=row['gene'],field=field,historical=row[field],release=value))
                    row[field]=value
        # Preserve the exact original textual scientific values where unchanged,
        # including JSON-embedded floats; only changed adjudication fields are replaced.
        with (dest/'gene_assessments.csv').open('w',newline='') as f:
            w=csv.DictWriter(f,lineterminator="\n",fieldnames=list(original_rows[0]));w.writeheader();w.writerows(original_rows)
        shutil.copyfile(source/'locus_confidence_rank.csv',dest/'locus_confidence.csv')
        negatives=list(csv.DictReader((R/'reports/sprint5/negative_results.csv').open()))
        for row in negatives:row['analysis_stage']='HISTORICAL_SPRINT5_SUPERSEDED_WHERE_UPDATED'
        def negative(category,subject,result,status,evidence):
            negatives.append(dict(category=category,subject=subject,result=result,status=status,evidence_file=evidence,analysis_stage='RELEASE_CORRECTED_SPRINT5A'))
        lc=pd.read_csv(dest/'locus_confidence.csv')
        for row in lc[lc.locus_stratum.isin(['L4_DISCORDANT','NT'])].itertuples():
            negative('LOCUS_CLASS',row.lead_snp,row.locus_stratum,'DISCORDANT' if row.locus_stratum=='L4_DISCORDANT' else 'NOT_TESTABLE','data/release/locus_confidence.csv')
        for row in new[new.gene_class.isin(['LOCUS_HIGH_GENE_UNRESOLVED','LIKELY_QTL_PASSENGER','V2G_SUPPORTED_WEAK_LOCUS'])].reset_index().itertuples():
            negative('GENE_ASSIGNMENT',row.gene,row.gene_class,'UNRESOLVED_OR_DOWNGRADED','data/release/gene_assessments.csv')
        negative('ALPHAGENOME','directional model evidence','Sign aggregation defect; raw predictions absent','EXCLUDED_UNRESOLVED','docs/corrections/ALPHAGENOME_DIRECTION.md')
        negative('ADULT_CANDIDATES','all assessed genes','No gene meets locus + gene + adult QTL + D1 criteria','EMPTY_BY_RULE','data/release/adult_candidates.csv')
        negative('BRAINSCOPE_COLOC','public significant-only files','Full colocalisation not possible from released significant-only associations','NOT_TESTABLE','reports/sprint5a/brainscope_coloc_testability.json')
        with (dest/'negative_results.csv').open('w',newline='') as f:
            w=csv.DictWriter(f,lineterminator="\n",fieldnames=list(negatives[0]));w.writeheader();w.writerows(negatives)
        shutil.copyfile(data/'evidence_units.parquet',dest/'evidence_units.parquet')
        m=new.reset_index()
        eligible=m[(m.locus_stratum.isin(['L1','L2'])) & m.gene_class.isin(['CAUSAL_GENE_MODERATE','CAUSAL_GENE_HIGH']) & m.classes.fillna('').str.contains('QTL') & m.direction_stratum.eq('D1')]
        eligible.to_csv(dest/'adult_candidates.csv',index=False)
        pd.DataFrame(changes,columns=['gene','field','historical','release']).to_csv(dest/'correction_changes.csv',index=False)
        decision=json.loads((out/'decision.json').read_text())
        decision.pop('created_utc',None)
        # Emit valid interoperable JSON; historical files used non-standard NaN.
        decision=json.loads(pd.Series([decision]).to_json(orient='values'))[0]
        (dest/'decision.json').write_text(json.dumps(decision,indent=2,allow_nan=False)+'\n')
        summary={'basis_commit':'49effba82f8b1861', 'source':'reports/sprint5a/s5_integrated',
                 'reproduction_scope':'Cached gene classification and gates only; upstream analyses inherited',
                 'excluded_sequence_model_units':int(excluded.sum()),'affected_genes':affected,
                 'gene_assessments':len(m),'moderate_genes':sorted(m.loc[m.gene_class.eq('CAUSAL_GENE_MODERATE'),'gene']),
                 'high_genes':int(m.gene_class.eq('CAUSAL_GENE_HIGH').sum()),'direction_D1':int(m.direction_stratum.eq('D1').sum()),
                 'adult_candidates':len(eligible),'changes':changes,
                 'input_sha256':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [dat/'evidence_units.parquet',source/'causal_gene_evidence_matrix.csv',R/'research/sprint5/protocol_rules.json']}}
        summary['basis_commit']=subprocess.check_output(['git','rev-parse','origin/sprint-5a/open-data-exhaustion'],cwd=R,text=True).strip()
        (R/'reports/release/correction_validation.json').write_text(json.dumps(summary,indent=2)+'\n')
        print(json.dumps({k:v for k,v in summary.items() if k not in ['changes','input_sha256']},indent=2))
if __name__=='__main__':main()
