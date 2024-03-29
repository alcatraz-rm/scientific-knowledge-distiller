% Generated by roxygen2: do not edit by hand
% Please edit documentation in R/dedup_refs.R
\name{dedup_citations}
\alias{dedup_citations}
\title{Deduplicate citations}
\usage{
dedup_citations(
  raw_citations,
  manual_dedup = FALSE,
  merge_citation = FALSE,
  preferred_source = ""
)
}
\arguments{
\item{raw_citations}{Citation dataframe with relevant columns}

\item{manual_dedup}{Logical value. Do you want to retrieve dataframe for manual deduplication?}
}
\value{
A list of 2 dataframes - unique citations and citations to be manually deduplicated if option selected
}
\description{
This function deduplicates citation data
}
