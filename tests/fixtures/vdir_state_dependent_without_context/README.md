# Fixture: minimal valid repository

One verified source and one claim that satisfies every implemented rule. The validator
must exit 0 here even under --strict: if this fixture ever fails, a rule has become
stricter than the contract and the rule is what needs looking at.
