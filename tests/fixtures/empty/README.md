# Fixture: empty repository

No records at all. The validator must exit 0 here with an honest
"0 claims, 0 sources" summary: an empty repository is a CORRECT state for Sprint 1,
not a missing one. A build that failed on emptiness would pressure agents into writing
records to make it pass, which is the opposite of what the contract wants.
