# Intelligence Blueprint — reproducible Sprint-1 pipeline.
#
# Two classes of target:
#   * network targets  (fetch-*)  : reach public APIs, write IMMUTABLE snapshots to data/raw/
#   * offline targets  (all else) : derive everything else from data/raw/ + curated YAML
#
# The offline chain must succeed with no network access. That is the
# reproducibility contract for this repository.

PY ?= .venv/bin/python
PIP ?= .venv/bin/pip

.DEFAULT_GOAL := help
.PHONY: help setup validate build store graph rank reports test test-network all \
        fetch-sources fetch-identifiers fetch-gwas fetch-tractability clean-derived \
        check-ownership hooks

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
validate: ## Validate ontology, schemas, records, provenance and audit rules
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

build: validate store graph ## Validate then build store + graph

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
