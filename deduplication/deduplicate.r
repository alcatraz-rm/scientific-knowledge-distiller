library("ASySD")

# load citations
citation_data <- load_search("_dump_tmp.csv", method="csv")

# deduplicate
dedup_citations_result <- dedup_citations(citation_data)

# get unique citation dataframe
unique_citations <- dedup_citations_result$unique
manual_dedup <- dedup_citations_result$manual_dedup

write.csv(unique_citations, "unique_citations.csv", row.names=FALSE)
write.csv(manual_dedup, "manual_dedup.csv", row.names=FALSE)
