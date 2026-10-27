#!/usr/bin/env python3
"""Supplementary redacted credential/privacy scan (not a replacement for Gitleaks)."""
from pathlib import Path
import gzip,json,re,subprocess,sys
R=Path(__file__).resolve().parents[2]
PATTERNS={
 'jwt':re.compile(rb'ey'+rb'J[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}'),
 'google_api_key':re.compile(rb'AI'+rb'za[0-9A-Za-z_-]{35}'),
 'github_token':re.compile(rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})'),
 'private_key':re.compile(rb'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----'),
 'personal_machine_path':re.compile(rb'/Us'+rb'ers/(?![^/]*\[)[A-Za-z][A-Za-z0-9_.-]+/'),
}
def main():
 files=sorted(set(subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard'],cwd=R,text=True).splitlines()))
 findings=[];counts={'files':0,'gzip_decoded':0,'parquet_decoded':0}
 for f in files:
  p=R/f
  if not p.is_file():continue
  b=p.read_bytes();counts['files']+=1
  if b[:2]==b'\x1f\x8b':b=gzip.decompress(b);counts['gzip_decoded']+=1
  if p.suffix=='.parquet':
   import pandas as pd
   b=pd.read_parquet(p).to_json().encode();counts['parquet_decoded']+=1
  for category,pat in PATTERNS.items():
   if pat.search(b):findings.append({'path':f,'category':category})
  if p.name.startswith('.env') and p.name!='.env.example':findings.append({'path':f,'category':'environment_file'})
 print(json.dumps({'scope':'Current distributed files, including decoded gzip and Parquet; findings contain no values','counts':counts,'findings':findings},indent=2))
 return bool(findings)
if __name__=='__main__':sys.exit(main())
