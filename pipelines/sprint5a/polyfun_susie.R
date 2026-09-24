# Sprint 5A — plain vs functionally informed SuSiE-RSS at one locus.
#
# Settings are the Sprint-4 frozen sensitivity settings (pipelines/sprint4/gate_c_finemap.py) with ONE
# change for the functional fit: prior_weights = PolyFun precomputed per-SNP heritabilities (approach 1).
# The plain fit is rerun in the same process so that reproduction of the Sprint-4 PIPs can be checked.
#
# usage: Rscript polyfun_susie.R <locus_dir> <n>
#   <locus_dir>/z.txt       z for the bim A1 allele, one per line
#   <locus_dir>/R.bin       p x p LD (1000G EUR), column-major float64
#   <locus_dir>/prior.txt   PolyFun SNPVAR per SNP (same order); normalised to sum 1 here
suppressMessages(library(susieR))
suppressMessages(library(jsonlite))
args <- commandArgs(trailingOnly = TRUE)
d <- args[1]
n <- as.numeric(args[2])
z <- scan(file.path(d, "z.txt"), quiet = TRUE)
p <- length(z)
R <- matrix(readBin(file.path(d, "R.bin"), "double", n = p * p), p, p)
w <- scan(file.path(d, "prior.txt"), quiet = TRUE)
stopifnot(length(w) == p, all(w > 0))
w <- w / sum(w)

fit_one <- function(pw) {
  fit <- tryCatch(
    if (is.null(pw)) {
      susie_rss(z = z, R = R, n = n, L = 10, coverage = 0.95, min_abs_corr = 0.5,
                estimate_residual_variance = FALSE, max_iter = 1000)
    } else {
      susie_rss(z = z, R = R, n = n, L = 10, coverage = 0.95, min_abs_corr = 0.5,
                estimate_residual_variance = FALSE, max_iter = 1000, prior_weights = pw)
    }, error = function(e) e)
  if (inherits(fit, "error")) return(list(error = conditionMessage(fit)))
  cs <- fit$sets$cs
  pur <- fit$sets$purity
  list(pip = as.numeric(fit$pip), converged = fit$converged, niter = fit$niter,
       cs = if (is.null(cs)) list() else lapply(names(cs), function(k) list(
         name = k, idx = as.integer(cs[[k]]),
         coverage = as.numeric(fit$sets$coverage[match(k, names(cs))]),
         min_abs_corr = if (is.null(pur)) NA else pur[k, "min.abs.corr"])))
}

s <- tryCatch(estimate_s_rss(z, R, n = n), error = function(e) NA)
out <- list(susieR_version = as.character(packageVersion("susieR")), s = s,
            plain = fit_one(NULL), polyfun = fit_one(w))
writeLines(toJSON(out, auto_unbox = TRUE, digits = 8, na = "null"), file.path(d, "fit_sprint5a.json"))
