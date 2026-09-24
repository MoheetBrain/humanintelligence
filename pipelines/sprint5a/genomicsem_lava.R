#!/usr/bin/env Rscript
# Sprint 5A section 11A/11B — multivariable LDSC + common-factor Genomic SEM, and LAVA local genetic correlation.
# Inputs: data/interim/sprint5a/ldsc/inputs/<TRAIT>.tsv.gz (SNP A1 A2 Z N P; positive Z = better cognition)
# Usage: Rscript genomicsem_lava.R <trait1,trait2,...> <out_tag>
invisible(Sys.setlocale("LC_ALL", "en_US.UTF-8"))
suppressMessages({library(GenomicSEM); library(LAVA); library(data.table)})
args <- commandArgs(trailingOnly = TRUE)
traits <- strsplit(args[1], ",")[[1]]
tag <- args[2]
R <- normalizePath(".")
W <- file.path(R, "data/interim/sprint5a/ldsc"); IN <- file.path(W, "inputs"); OUTD <- "../../../../reports/sprint5a"
setwd(W)  # relative paths below: vroom mis-encodes the emoji in the absolute project path
LD <- "eur_w_ld_chr/"; HM3 <- "eur_w_ld_chr/w_hm3.snplist"
prev <- list(ZABANEH_XIQ = c(1238 / (1238 + 8172), 0.0003))   # sample / population prevalence (Duke TIP ~ top 0.03%)
files <- file.path("inputs", paste0(traits, ".tsv.gz"))
munged <- paste0(traits, ".sumstats.gz")
need <- !file.exists(munged)
if (any(need)) munge(files = files[need], hm3 = HM3, trait.names = traits[need], info.filter = 0.9, maf.filter = 0.01)
sp <- sapply(traits, function(t) if (!is.null(prev[[t]])) prev[[t]][1] else NA)
pp <- sapply(traits, function(t) if (!is.null(prev[[t]])) prev[[t]][2] else NA)
rds <- paste0("ldsc_", tag, ".rds")
L <- if (file.exists(rds)) readRDS(rds) else ldsc(traits = munged, sample.prev = sp, population.prev = pp, ld = LD, wld = LD, trait.names = traits,
          ldsc.log = paste0("ldsc_", tag))
S <- L$S; I <- L$I; V <- L$V
k <- length(traits); se <- matrix(sqrt(diag(V))[match(seq_len(k*(k+1)/2), seq_len(k*(k+1)/2))], 1)
rg <- cov2cor(S)
out <- list(traits = traits, h2 = diag(S), rg = rg, intercepts = I)
fwrite(data.table(trait1 = rep(traits, each = k), trait2 = rep(traits, k), rg = as.vector(rg),
                  intercept = as.vector(I)), file.path(OUTD, paste0("ldsc_rg_", tag, ".csv")))
fwrite(data.table(trait = traits, h2_obs = diag(S), intercept = diag(I)), file.path(OUTD, paste0("ldsc_h2_", tag, ".csv")))
cf <- tryCatch(commonfactor(covstruc = L, estimation = "DWLS"), error = function(e) e)
if (!inherits(cf, "error")) {
  fwrite(as.data.table(cf$results), file.path(OUTD, paste0("genomicsem_commonfactor_", tag, ".csv")))
  fwrite(as.data.table(cf$modelfit), file.path(OUTD, paste0("genomicsem_commonfactor_fit_", tag, ".csv")))
} else writeLines(conditionMessage(cf), file.path(OUTD, paste0("genomicsem_commonfactor_", tag, "_ERROR.txt")))
saveRDS(L, paste0("ldsc_", tag, ".rds"))
cat("LDSC done\n"); print(round(rg, 3)); print(round(I, 3))

# ---------------- LAVA at the LD blocks containing the Gate-C locus leads ----------------
loc <- fread("../../../sprint5a/lava_loci.tsv")
info <- data.table(phenotype = traits, cases = NA_real_, controls = NA_real_, prevalence = NA_real_,
                   filename = files)
if ("ZABANEH_XIQ" %in% traits) info[phenotype == "ZABANEH_XIQ", `:=`(cases = 1238, controls = 8172, prevalence = 0.0003)]
fwrite(info, paste0("lava_info_", tag, ".txt"), sep = "\t", na = "NA")
ov <- cov2cor(I); dimnames(ov) <- list(traits, traits)
ovf <- paste0("lava_overlap_", tag, ".txt"); write.table(round(ov, 5), ovf, quote = FALSE)
REF <- "/Users/moheet/Documents/ChatGPT/intelligence-codex/research/extreme_cognition/x01/genetics_tools/reference/g1000_eur"
inp <- process.input(input.info.file = paste0("lava_info_", tag, ".txt"), sample.overlap.file = ovf,
                     ref.prefix = REF, phenos = traits)
res <- list(); uni <- list()
for (i in seq_len(nrow(loc))) {
  L1 <- tryCatch(process.locus(loc[i], inp), error = function(e) NULL)
  if (is.null(L1)) next
  r <- tryCatch(run.univ.bivar(L1, univ.thresh = 0.05 / nrow(loc)), error = function(e) NULL)
  if (is.null(r)) next
  u <- as.data.table(r$univ); u[, `:=`(locus = loc$LOC[i], label = loc$label[i])]; uni[[length(uni) + 1]] <- u
  if (!is.null(r$bivar)) { b <- as.data.table(r$bivar); b[, `:=`(locus = loc$LOC[i], label = loc$label[i])]; res[[length(res) + 1]] <- b }
}
fwrite(rbindlist(uni, fill = TRUE), file.path(OUTD, paste0("lava_univariate_", tag, ".csv")))
fwrite(rbindlist(res, fill = TRUE), file.path(OUTD, paste0("lava_bivariate_", tag, ".csv")))
cat("LAVA done:", length(uni), "loci with univariate output;", length(res), "with bivariate\n")
