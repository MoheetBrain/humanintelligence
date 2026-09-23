###Author: Jonathan Coleman
###Date: 2018-03-05
###README: Describe contents of Coleman_[PMID]_Sumstats.txt

##Background

The file Coleman_[PMID]_Sumstats.txt contains sumstats for cognitive ability derived from a meta-analysis of a previous meta-analysis of cognitive ability (Sniekers, PMID 28530673) with a GWAS of extremely high IQ (Zabaneh, PMID pending). Meta-analysis was performed in METAL using fixed weights for each study (see publication), with additional variant information added programatically. 

##Format

CHR BP SNP A1 A2 Z P

    where CHR is variant chromosome;
    	  BP is base pair from hg19;
	  A1 is effect allele;
	  A2 is non-effect allele;
	  Z is meta-analysis Z-score;
	  P is meta-analysis p-value