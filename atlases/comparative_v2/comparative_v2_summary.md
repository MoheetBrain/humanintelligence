# Comparative Intelligence 2.0 — summary

**Sprint 2, Task G, 2026-09-18.** Status: **panel defined, orthology audited, no
comparative analysis run.**

> **The headline is a resource finding, not a biology finding.** The species-first design
> is sound and the data resource cannot support its most informative arm. **Both avian
> convergence candidates — New Caledonian crow and budgerigar — are absent from Ensembl
> Compara, while both avian *controls* — chicken and zebra finch — are present.** The
> available birds are the uninformative ones, so a scan run over "the birds in the
> database" would return a null for birds that is absence of *measurement*, not evidence
> about avian cognition.

---

## 1. Why a second comparative atlas at all

Sprint 1's comparative work was **gene-first**: it took the seed list and asked what other
species do with those genes. That design cannot discover anything — the answer is bounded
by the input — and it cannot separate a gene that matters for cognition from one that
matters for being large and long-lived.

This atlas inverts it. It starts from **species**, chosen so that cognitive specialisation
is *dissociated* from the traits that normally travel with it, and only then asks what the
genomes say. The controls are the design, not an afterthought:

| Control | Breaks the correlation between | Why it is here |
|---|---|---|
| **Cattle** | body mass, absolute brain mass ↔ cognition | Also the closest outgroup to cetaceans: a dolphin signal shared with cattle is an *artiodactyl* signal. The most load-bearing species in the panel. |
| **Naked mole rat** | lifespan, eusociality ↔ cognition | Longevity genes are the commonest false positive in scans of "intelligent" species, because long life and big brains covary. |
| **Chicken** | avian genome background ↔ smart-bird biology | Separates "a bird thing" from "a corvid thing". |
| **Zebra finch** | vocal learning ↔ general cognition | Vocal learning is the avian trait with the biggest molecular literature, so it is the one most likely to be mistaken for the trait of interest. |

**The hard rule this atlas enforces:** *a pathway repeatedly changing in long-lived large
mammals is not automatically an intelligence pathway.*

## 2. What was actually computed

One thing: an **orthology availability audit** — for each of 52 seed and discovered genes,
which panel species have an orthologue call, and of what type. Every response is
snapshotted and checksummed.

That is a question about a **database**, not about biology. It answers only: *where is a
cross-species comparison even possible?*

### Results

* **11 of 13** non-human panel species are in Ensembl Compara. Crow and budgerigar are not.
* **46 of 52** genes queried successfully; 6 errored (timeouts/HTTP) and are recorded as
  `query_status: failed` — **not** as genes lacking orthologues.
* **26 of 46** genes have a one-to-one orthologue in *all* 11 available species.

| Species | genes with 1:1 orthologue | |
|---|---|---|
| Bonobo | 46 / 46 | 100% |
| Chimpanzee, **mouse**, **rat** | 44 / 46 | 96% |
| Macaque, cattle | 43 / 46 | 93% |
| Dolphin | 42 / 46 | 91% |
| Elephant, chicken | 41 / 46 | 89% |
| Naked mole rat | 38 / 46 | 83% |
| **Zebra finch** | 36 / 46 | **78%** |

## 3. The one genuinely useful result

**Mouse and rat carry a one-to-one orthologue for 96% of this repository's targets.**

That matters because the repository's recurring problem is animal evidence failing to
transfer to humans — HCN1's dendritic physiology, GRM5's fragile-X trial, GRIN2B's
life-stage mismatch. This audit shows that **the failures are not orthology failures.**
The gene is there, one-to-one, in the species the experiments were done in. What differs is
physiology, timing, dose and circuit architecture.

That is a sharper diagnosis than "animal models are unreliable", and it points somewhere
specific: stop looking for missing genes and start looking at where the *same* gene behaves
differently. HCN1 is already the worked example — human layer-5 dendrites couple more
weakly and carry lower channel density than rat, with the two direct comparisons
disagreeing in sign by cortical layer, for a gene that is perfectly 1:1 orthologous.

## 4. The avian problem, stated precisely

The zebra finch — the only passerine available, and the closest thing in the panel to a
corvid — has the **lowest** orthologue coverage at 78%. So the avian arm is weak twice
over: the informative species are absent, and the one bird closest to them has the
patchiest gene calls.

This creates a specific trap, and it is the reason this section exists:

> Running the analysis on the available birds would produce "no signal in birds". A reader
> would take that as evidence that the mechanism is mammal-specific. It would be evidence
> that the crow is not in the database.

**No avian statement may be made from this panel in either direction.** Not "no convergence
in birds", not "convergence is mammal-specific". `not_assessable`.

## 5. What was deliberately NOT computed

| Artefact | Status | Why |
|---|---|---|
| `trait_covariates.yaml` | **schema only, zero values** | Brain mass, lifespan, generation time and group size are the control variables this design depends on. Filling them from memory would corrupt exactly the controls that stop body size masquerading as cognition. An empty schema is honest; a populated one with recalled numbers is a fabrication that looks like data. |
| `selection_signals.yaml` | **NOT COMPUTED** | No species tree, no generation-time data, no multiple-testing frame — and the avian arm is inoperable. Each is a prerequisite, not an excuse. |
| `pathway_convergence.yaml` | **NOT COMPUTED** | Depends on selection signals. With crow, budgerigar and octopus all unavailable, what remains is two mammalian lineages — the weakest possible convergence test, since mammals share a cortical plan. |

A dN/dS scan across these species would have taken an afternoon and produced output that
looked like a finding. The prerequisites above are the reasons it would have been wrong in
a direction that flattered the hypothesis.

## 6. Species wanted and unobtainable

* **Orca** — a second cetacean; would give the cetacean arm an internal control.
* **Common raven** — a second corvid; internal replication for the corvid arm.
* **Kea** — a parrot with strong problem-solving that is not a vocal mimic; would dissociate
  parrot cognition from vocal learning.
* **Octopus** — the most independent cognitive lineage available anywhere: a protostome with
  a distributed nervous system. Convergence with an octopus would be near-decisive evidence
  that a mechanism is a general requirement of cognition rather than a vertebrate
  idiosyncrasy. It sits in Ensembl *Metazoa*, a separate resource with a separate Compara,
  so including it needs a second pipeline and cross-resource orthology this repository does
  not have. **This is the single largest gap in the design.**

## 7. Honest limitations

1. **Phylogenetic pseudoreplication.** These species are not independent observations.
   Chimpanzee and bonobo share ~2 Myr; dolphin and cattle are both cetartiodactyls; mouse
   and rat are both murids. Any statistic from this panel must be tree-aware; a raw count of
   species sharing a state is inadmissible.
2. **The cognitive trait is not operationalised.** "Cognitive specialisation" is assigned by
   `panel_role` from the behavioural literature — a categorical curator judgement, not blind
   to the hypothesis. It is a declared prior and must never be the dependent variable in a
   test run on this same panel.
3. **Assembly quality is uneven.** GRCh38.p14 to turTru1, a low-coverage draft with no
   accession. Only *presence* of an orthologue is usable; absence is `not_assessable`.
4. **Six genes failed to query** and are unresolved.

## 8. Next actions

1. Ingest a species tree and trait covariates from citable sources, with snapshots and
   checksums. Both are prerequisites for anything else here.
2. Evaluate a non-Compara orthology route (NCBI Orthologs, OrthoDB, or reciprocal best hits
   over the assemblies) that includes corvids and parrots — the only way to make the avian
   arm operable.
3. Re-run the six failed gene queries.
4. **Then decide whether to continue at all.** The honest possibility is that a
   two-mammalian-lineage convergence test is not worth running, and that this atlas's real
   output is the resource gap it documented plus the orthology result in §3.
