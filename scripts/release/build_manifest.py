#!/usr/bin/env python3
"""Record SHA-256 for every distributed tracked file; manifest excludes itself."""
from pathlib import Path
import hashlib,json,subprocess
R=Path(__file__).resolve().parents[2]
files=sorted(set(subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard'],cwd=R,text=True).splitlines()))
records=[{'path':f,'bytes':(R/f).stat().st_size,'sha256':hashlib.sha256((R/f).read_bytes()).hexdigest()} for f in files if f!='RELEASE_MANIFEST.json' and (R/f).is_file()]
manifest={'schema':'cognition-release/1.0','version':'0.1.0','release_date':'2026-10-27','scientific_basis_commit':'49effbaa3bcde35f58bc770d0e122a57c05e526d','verification_scope':'Distributed bytes and cached adjudication; no upstream end-to-end reproduction','licence_scope':'MIT project code; DATA_LICENSE.md for documentation and third-party material','files':records}
(R/'RELEASE_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Manifest files:',len(records))
