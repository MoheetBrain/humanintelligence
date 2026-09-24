# Sprint 5A Goal B — HyPrColoc runner. Inputs are written by multitrait_coloc.py:
#   <work>/<locus>.<run>.betas.tsv / .ses.tsv (rows = SNPs, cols = traits; betas aligned to Davies EA)
# HyPrColoc (jrs95/hyprcoloc 0.0.2, commit 0348bbd, Eigen index-cast patch) with package defaults:
#   prior.1 = 1e-4, prior.c = 0.02, uniform priors, reg.thresh = align.thresh = 0.5.
# binary.outcomes = 1 for XIQ_zabaneh (case/control log OR) and FI4_ukb (binary item).
# NOTE: HyPrColoc assumes the studies are independent; see multitrait_coloc.py for the overlap caveats.
suppressMessages(library(hyprcoloc))
args <- commandArgs(trailingOnly = TRUE)
work <- args[1]
man <- read.csv(file.path(work, "manifest.csv"), stringsAsFactors = FALSE)
out <- list()
for (i in seq_len(nrow(man))) {
  loc <- man$locus_id[i]; run <- man$run[i]
  B <- as.matrix(read.delim(file.path(work, paste0(loc, ".", run, ".betas.tsv")), row.names = 1, check.names = FALSE))
  S <- as.matrix(read.delim(file.path(work, paste0(loc, ".", run, ".ses.tsv")), row.names = 1, check.names = FALSE))
  tr <- colnames(B)
  if (nrow(B) < 50 || ncol(B) < 2) {
    out[[length(out) + 1]] <- data.frame(locus_id = loc, run = run, cluster = NA, traits_clustered = "None",
      posterior_prob = NA, regional_prob = NA, candidate_snp = NA, posterior_explained_by_snp = NA,
      dropped_trait = NA, status = paste0("NOT_TESTABLE: ", nrow(B), " complete SNPs x ", ncol(B), " traits"))
    next
  }
  bin <- as.integer(tr %in% c("XIQ_zabaneh", "FI4_ukb"))
  set.seed(1)
  r <- tryCatch(hyprcoloc(B, S, trait.names = tr, snp.id = rownames(B), binary.outcomes = bin),
                error = function(e) e)
  if (inherits(r, "error")) {
    out[[length(out) + 1]] <- data.frame(locus_id = loc, run = run, cluster = NA, traits_clustered = "None",
      posterior_prob = NA, regional_prob = NA, candidate_snp = NA, posterior_explained_by_snp = NA,
      dropped_trait = NA, status = paste0("ERROR: ", conditionMessage(r)))
    next
  }
  x <- r$results
  names(x)[names(x) == "traits"] <- "traits_clustered"
  names(x)[names(x) == "iteration"] <- "cluster"
  x$locus_id <- loc; x$run <- run; x$status <- "OK"
  out[[length(out) + 1]] <- x[, c("locus_id", "run", "cluster", "traits_clustered", "posterior_prob", "regional_prob",
                                  "candidate_snp", "posterior_explained_by_snp", "dropped_trait", "status")]
  cat(loc, run, nrow(B), "SNPs", ncol(B), "traits;", sum(x$traits_clustered != "None"), "clusters\n")
}
res <- do.call(rbind, out)
res$hyprcoloc_version <- as.character(packageVersion("hyprcoloc"))
res$R_version <- R.version.string
write.table(res, file.path(work, "hyprcoloc_results.tsv"), sep = "\t", row.names = FALSE, quote = FALSE)
