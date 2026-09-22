# Intelligence Blueprint — reproducible Sprint-1 pipeline.
#
# Two classes of target:
#   * network targets  (fetch-*)  : reach public APIs, write IMMUTABLE snapshots to data/raw/
#   * offline targets  (all else) : derive everything else from data/raw/ + curated YAML
#
# The offline chain must succeed with no network access. That is the
# reproducibility contract for this repository.

# PYTHONPATH=src keeps `python -m blueprint.…` working even in a tree where the
# project has not been installed editable (a fresh clone that skipped `make setup`).
# Without it those targets fail while graph/*.py still works, because the scripts
# bootstrap sys.path themselves and a -m invocation cannot.
PY ?= PYTHONPATH=src .venv/bin/python
PIP ?= .venv/bin/pip

.DEFAULT_GOAL := help
.PHONY: help setup validate build store graph rank reports test test-network all tournament identifiers \
        fetch-sources fetch-identifiers fetch-gwas fetch-tractability clean-derived \
        check-ownership hooks index-sources

help: ## Show available targets
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Create .venv and install the project (editable) + dev deps
	uv venv --python python3.12 .venv
	. .venv/bin/activate && uv pip install -e ".[dev]"

# ---------------------------------------------------------------- network -----
fetch-sources: ## Verify every cited source against PubMed / ClinicalTrials.gov (network)
	$(PY) scripts/fetch_source_metadata.py --all

fetch-identifiers: ## Resolve gene identifiers from HGNC for every seed target (network)
	$(PY) scripts/fetch_gene_identifiers.py

fetch-gwas: ## Ingest GWAS Catalog associations for seed genes x cognitive traits (network)
	$(PY) pipelines/alphacognition/fetch_gwas_catalog.py

fetch-tractability: ## Ingest Open Targets tractability / safety annotations (network)
	$(PY) pipelines/integration/fetch_target_annotations.py

# ---------------------------------------------------------------- offline -----
index-sources: ## Rebuild the source-verification index from raw snapshots (offline)
	-$(PY) scripts/fetch_source_metadata.py --all --offline
# A non-zero exit here only means some source is unverified; that is the validator's
# call to make (rule V6), not the index builder's, hence the leading '-'.

validate: index-sources ## Validate ontology, schemas, records, provenance and audit rules
	$(PY) graph/validate_graph.py --strict

store: ## Build the Parquet + DuckDB evidence store from curated records
	$(PY) -m blueprint.store.build

graph: ## Compile the three-layer NetworkX graph
	$(PY) graph/build_graph.py

rank: ## Run the uncertainty + ranking model over audited targets
	$(PY) models/ranking/rank_targets.py

reports: ## Generate reports/ (interactive graph HTML, ranking CSV, audit summary)
	$(PY) graph/export_graph.py --html
	$(PY) -m blueprint.reports.build

identifiers: ## Rebuild the HGNC identifier index from committed snapshots (offline)
	$(PY) scripts/fetch_gene_identifiers.py --offline

build: validate identifiers store graph ## Validate then build identifiers + store + graph

tournament: ## Sprint-3 gene tournament from committed snapshots + local MAGMA outputs (offline)
	$(PY) pipelines/gene_tournament/classify_studies.py
	$(PY) pipelines/gene_tournament/build_master_universe.py
	$(PY) pipelines/gene_tournament/analyse_extreme_tail.py
	$(PY) pipelines/gene_tournament/build_gene_ranks.py
	$(PY) pipelines/gene_tournament/run_pathway_enrichment.py --collect-only
	$(PY) pipelines/gene_tournament/build_pathway_panel.py
	$(PY) pipelines/gene_tournament/build_modules.py
	$(PY) pipelines/gene_tournament/fetch_gwas_credible_sets.py
	$(PY) pipelines/gene_tournament/build_consensus.py
	$(PY) pipelines/gene_tournament/build_red_team_and_cards.py

test: ## Run the offline test suite
	$(PY) -m pytest -m "not network"

test-network: ## Run tests that need outbound network access
	$(PY) -m pytest -m network

check-ownership: ## Check that changed paths respect docs/OWNERSHIP.yaml
	$(PY) scripts/check_ownership.py

hooks: ## Install the repository git hooks (commit-continuity + validation gate)
	bash scripts/install-git-hooks.sh

all: validate store graph rank reports test ## Full offline pipeline + tests

clean-derived: ## Remove derived artefacts (never touches data/raw/ or curated YAML)
	rm -rf data/interim/* data/processed/* .pytest_cache
	@echo "derived artefacts removed; data/raw/ and curated records untouched"
