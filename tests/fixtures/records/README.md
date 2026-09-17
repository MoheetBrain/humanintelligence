# Record fixtures

`valid/` — one record per file, `<kind>__<name>.yaml`, which must validate.
`invalid/` — `<kind>__<name>__<rule>.yaml`, which must FAIL, and whose filename names
the rule it must fail. `tests/test_schemas.py` parametrises over both directories, so
adding a file adds a test and a fixture cannot silently stop testing anything.

Every fixture is obviously synthetic: placeholder ids (`SRC:PMID:00000001`,
`GENE:PLACEHOLDER`), no real identifier and no biological assertion. Two fixtures
contain a number that looks like a probability — `claim__float_uncertainty__V10.yaml`
and the `v9_handwritten_probability` tree — and both exist solely to be rejected.
