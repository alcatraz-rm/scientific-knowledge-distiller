library("ASySD")

add_id_citations <- function(raw_citations){

  names(raw_citations)  <- to_any_case(names(raw_citations), case = c("snake"))

  raw_citations_with_id <- raw_citations %>%
    mutate(record_id = ifelse(is.na(record_id), as.character(row_number()+1000), paste(record_id))) %>%
    mutate(record_id = ifelse(record_id=="", as.character(row_number()+1000), paste(record_id)))

}

format_citations <- function(raw_citations_with_id){

  # arrange by Year and presence of an Abstract - we want to keep newer records and records with an abstract preferentially
  formatted_citations <- raw_citations_with_id %>%
    arrange(desc(year), abstract)

  # select relevant columns
  formatted_citations <- formatted_citations  %>%
      select(author, title, year, journal, abstract, doi, number, pages, volume, isbn, record_id, label, source)

  # make sure author is a character
  formatted_citations$author <- as.character(formatted_citations$author)

  # Fix author formatting so similar
  formatted_citations <- formatted_citations %>%
    mutate(author = ifelse(author=="", "Unknown", author)) %>%
    mutate(author = ifelse(is.na(author), "Unknown", author)) %>%
    mutate(author = ifelse(author=="Anonymous", "Unknown", author))

  # Make all upper case
  formatted_citations <- as.data.frame(sapply(formatted_citations, toupper))

  # get rid of punctuation and differnces in doi formatting
  formatted_citations["doi"] <- sapply(formatted_citations["doi"], function(x) gsub("%28", "(", x))
  formatted_citations["doi"] <- as.data.frame(sapply(formatted_citations["doi"], function(x) gsub("%29", ")", x)))
  formatted_citations["doi"] <- as.data.frame(sapply(formatted_citations["doi"], function(x) gsub("HTTP://DX.doi.ORG/", "", x)))
  formatted_citations["doi"] <- as.data.frame(sapply(formatted_citations["doi"], function(x) gsub("HTTPS://doi.ORG/", "", x)))
  formatted_citations["doi"] <- as.data.frame(sapply(formatted_citations["doi"], function(x) gsub("HTTPS://DX.doi.ORG/", "", x)))
  formatted_citations["doi"] <- as.data.frame(sapply(formatted_citations["doi"], function(x) gsub("HTTP://doi.ORG/", "", x)))
  formatted_citations["doi"] <- as.data.frame(sapply(formatted_citations["doi"], function(x) gsub("doi: ", "", x)))
  formatted_citations["doi"] <- as.data.frame(sapply(formatted_citations["doi"], function(x) gsub("doi:", "", x)))
  formatted_citations["doi"] <- as.data.frame(sapply(formatted_citations["doi"], function(x) gsub("doi", "", x)))

  formatted_citations["title"] <- as.data.frame(sapply(formatted_citations["title"], function(x) gsub("[[:punct:]]", "", x)))
  formatted_citations["year"] <- as.data.frame(sapply(formatted_citations["year"], function(x) gsub("[[:punct:]]", "", x)))
  formatted_citations["abstract"] <- as.data.frame(sapply(formatted_citations["abstract"], function(x) gsub("[[:punct:]]", "", x)))

  formatted_citations["isbn"] <- as.data.frame(sapply(formatted_citations["isbn"], function(x) gsub("[[:space:]]\\(PRINT\\).*", "", x)))
  formatted_citations["isbn"] <- as.data.frame(sapply(formatted_citations["isbn"], function(x) gsub("[[:space:]]\\(ELECTRONIC\\).*", "", x)))

  formatted_citations<-formatted_citations %>%
    filter(!is.na(record_id))

  # sort out NA / missing data formatting for optimal matching
  formatted_citations <- formatted_citations %>%
    mutate(author = ifelse(author=="NA", NA, paste(author))) %>%
    mutate(year = ifelse(year=="NA", NA, paste(year))) %>%
    mutate(title = ifelse(title=="NA", NA, paste(title))) %>%
    mutate(number = ifelse(number=="NA", NA, paste(number))) %>%
    mutate(volume = ifelse(volume=="NA", NA, paste(volume))) %>%
    mutate(pages = ifelse(pages=="NA", NA, paste(pages))) %>%
    mutate(abstract = ifelse(abstract=="NA", NA, paste(abstract))) %>%
    mutate(doi = ifelse(doi=="NA", NA, paste(doi))) %>%
    mutate(journal = ifelse(journal=="NA", NA, paste(journal))) %>%
    mutate(isbn = ifelse(isbn=="", NA, paste(isbn)))

  formatted_citations<- formatted_citations %>%
    select(author, title, year, journal, abstract, doi, number, pages, volume, isbn, record_id, source, label)

  return(formatted_citations)

}

match_citations <- function(formatted_citations){

  # ROUND 1: run compare.dedup function and block by title&pages OR title&author OR title&abstract OR doi
#   try(newpairs <- compare.dedup(formatted_citations, blockfld = list(c(2,8), c(1,2), c(2,5), 6), strcmp = TRUE, exclude=c("record_id", "source", "label")), silent=TRUE)
  try(newpairs <- compare.dedup(formatted_citations, blockfld = list(2, c(1,2), c(2,5), 6), strcmp = TRUE, exclude=c("record_id", "source", "label")), silent=TRUE)
  linkedpairs <- as.data.frame(if(exists("newpairs")) newpairs$pairs)
  print(paste('round 1 pairs', nrow(linkedpairs)))

  # ROUND 2: run compare.dedup function and block by author&year&pages OR journal&volume&pages or isbn&volume&pages OR title&isbn
#   try(newpairs2 <- compare.dedup(formatted_citations, blockfld = list(c(1,3,8), c(4,9,8), c(10,9,8), c(2,10)), strcmp = TRUE, exclude= c("record_id", "source", "label")), silent=TRUE)
#   linkedpairs2 <- as.data.frame(if(exists("newpairs2")) newpairs2$pairs)
#    print(paste('round 2 pairs', nrow(linkedpairs2)))

  # ROUND 3: run compare.dedup function and block by year&pages&volume OR year&number&volume or year&pages&number
#   try(newpairs3 <- compare.dedup(formatted_citations, blockfld = list(c(3,8,9), c(3,7,9), c(3,8,7)), strcmp = TRUE, exclude=c("record_id", "source", "label")), silent = TRUE)
#   linkedpairs3 <- as.data.frame(if(exists("newpairs3")) newpairs3$pairs)
#   print(paste('round 3 pairs', nrow(linkedpairs3)))

  # ROUND 4: run compare.dedup function and block by author&year OR year&title OR title&volume OR title&journal
#   try(newpairs4 <- compare.dedup(formatted_citations, blockfld = list(c(1,3), c(3,2), c(2,9), c(2,4)), strcmp = TRUE, exclude=c("record_id", "source", "label")), silent = TRUE)
  try(newpairs4 <- compare.dedup(formatted_citations, blockfld = list(c(1,3), c(3,2), c(2,4)), strcmp = TRUE, exclude=c("record_id", "source", "label")), silent = TRUE)
  linkedpairs4 <- as.data.frame(if(exists("newpairs4")) newpairs4$pairs)
  print(paste('round 4 pairs', nrow(linkedpairs4)))

  # Combine all possible pairs
  pairs <- rbind(if(exists("linkedpairs")) linkedpairs,
#                  if(exists("linkedpairs2")) linkedpairs2,
#                  if(exists("linkedpairs3")) linkedpairs3,
                 if(exists("linkedpairs4")) linkedpairs4)
  print(paste('total pairs', nrow(pairs)))

  pairs <- unique(pairs)

  # Obtain metadata for matching pairs
  pairs <- pairs  %>%
    mutate(author1 =formatted_citations$author[id1]) %>%
    mutate(author2 =formatted_citations$author[id2]) %>%
    mutate(title1 =formatted_citations$title[id1]) %>%
    mutate(title2 =formatted_citations$title[id2]) %>%
    mutate(abstract1 =formatted_citations$abstract[id1]) %>%
    mutate(abstract2 =formatted_citations$abstract[id2]) %>%
    mutate(doi1= formatted_citations$doi[id1]) %>%
    mutate(doi2 =formatted_citations$doi[id2]) %>%
    mutate(year1=formatted_citations$year[id1]) %>%
    mutate(year2=formatted_citations$year[id2]) %>%
    mutate(number1 =formatted_citations$number[id1]) %>%
    mutate(number2 =formatted_citations$number[id2]) %>%
    mutate(pages1 =formatted_citations$pages[id1]) %>%
    mutate(pages2 =formatted_citations$pages[id2]) %>%
    mutate(volume1 =formatted_citations$volume[id1]) %>%
    mutate(volume2 =formatted_citations$volume[id2]) %>%
    mutate(journal1 =formatted_citations$journal[id1]) %>%
    mutate(journal2 =formatted_citations$journal[id2]) %>%
    mutate(isbn1 =formatted_citations$isbn[id1]) %>%
    mutate(isbn2 =formatted_citations$isbn[id2]) %>%
    mutate(record_id1=formatted_citations$record_id[id1]) %>%
    mutate(record_id2 =formatted_citations$record_id[id2]) %>%
    mutate(label1 =formatted_citations$label[id1]) %>%
    mutate(label2 =formatted_citations$label[id2]) %>%
    mutate(source1 =formatted_citations$source[id1]) %>%
    mutate(source2 =formatted_citations$source[id2])

  pairs <- pairs %>%
    select(id1, id2, author1, author2, author, title1, title2, title, abstract1, abstract2, abstract, year1, year2, year, number1, number2, number, pages1, pages2, pages, volume1, volume2, volume, journal1, journal2, journal, isbn, isbn1, isbn2, doi1, doi2, doi, record_id1, record_id2, label1, label2, source1, source2)
  print(paste('total unique pairs', nrow(pairs)))

  pairs <- pairs %>%
    mutate(abstract = ifelse(is.na(abstract1) & is.na(abstract2), 0, abstract)) %>%
    mutate(pages = ifelse(is.na(pages1) & is.na(pages2), 1, pages)) %>%
    mutate(volume = ifelse(is.na(volume1) & is.na(volume2), 1, volume)) %>%
    mutate(number = ifelse(is.na(number1) & is.na(number2), 1, number)) %>%
    mutate(doi = ifelse(is.na(doi1) & is.na(doi2), 0, doi)) %>%
    mutate(isbn = ifelse(is.na(isbn1) & is.na(isbn2), 0, isbn))
}

identify_true_matches <- function(pairs){

  ####------ Filter matching pairs - retain correct matches ------ ####
  true_pairs <- pairs %>%
    filter(
      (pages>0.8 & volume>0.8 & title>0.90 & abstract>0.90 & author>0.50 & isbn>0.99) |
        (pages>0.8 & volume>0.8 & title>0.90 & abstract>0.90 & author>0.50 & journal>0.6) |
        (pages>0.8 & number>0.8 & title>0.90 & abstract>0.90 & author>0.50 & journal>0.6) |
        (volume >0.8 & number>0.8 & title>0.90 & abstract>0.90 & author>0.50  & journal>0.6) |

        (volume >0.8 & number>0.8 & title>0.90 & abstract>0.90 & author>0.8) |
        (volume>0.8 & pages>0.8 & title>0.90 & abstract>0.9 & author>0.8) |
        (pages>0.8 & number>0.8 & title>0.90 & abstract>0.9 & author>0.8) |

        (doi>0.95 & author>0.75 & title>0.9) |

        (title>0.80 & abstract>0.90 & volume>0.85 & journal>0.65 & author>0.9) |
        (title>0.90 & abstract>0.80 & volume>0.85 & journal>0.65 & author>0.9)|

        (pages>0.8 & volume>0.8 & title>0.90 & abstract>0.8 & author>0.9 & journal>0.75) |
        (pages>0.8 & number>0.8 & title>0.90 & abstract>0.80 & author>0.9 & journal>0.75) |
        (volume>0.8 & number>0.8 & title>0.90 & abstract>0.8 & author>0.9  & journal>0.75) |

        (title>0.9 & author>0.9 & abstract>0.9 & journal >0.7)|
        (title>0.9 & author>0.9 & abstract>0.9 & isbn >0.99)|

        (pages>0.9 & number>0.9 & title>0.90 & author>0.80 & journal>0.6) |
        (number>0.9 & volume>0.9 & title>0.90 & author>0.90 & journal>0.6) |
        (pages>0.9 & volume>0.9 & title>0.90 & author>0.80 & journal>0.6) |
        (pages>0.9 & number>0.9 & title>0.90 & author>0.80 & isbn>0.99) |
        (pages>0.9 & number>0.9 & title>0.90 & author>0.80 & isbn>0.99) |
        (pages>0.9 & number>0.9 & title>0.90 & author>0.80 & isbn>0.99) |

        (pages>0.8 & volume>0.8 & title>0.95 & author>0.80 & journal>0.9) |
        (number>0.8 & volume>0.8 & title>0.95 & author>0.80 & journal>0.9)|
        (number>0.8 & pages>0.8 & title>0.95 & author>0.80 & journal>0.9) |
        (pages>0.8 & volume>0.8 & title>0.95 & author>0.80 & isbn>0.99) |
        (pages>0.8 & volume>0.8 & title>0.95 & author>0.80 & isbn>0.99) |
        (pages>0.8 & volume>0.8 & title>0.95 & author>0.80 & isbn>0.99))

  # Find papers with low matching dois - often indicates FALSE positive matches
  true_pairs_mismatch_doi <- true_pairs %>%
    filter(!(is.na(doi)| doi ==0 | doi > 0.99)) %>%
    filter(!(title > 0.9 & abstract > 0.9 & (journal|isbn > 0.9)))

  # Remove papers with low matching dois from filtered matched
  true_pairs <- true_pairs %>%
    filter(is.na(doi)| doi > 0.99 | doi == 0 | (title > 0.9 & abstract>0.9 & (journal|isbn > 0.9)))

  true_pairs <- unique(true_pairs)

  # Make year numeric, then find matches where year differs
  true_pairs$year1 <- as.numeric(as.character(true_pairs$year1))
  true_pairs$year2 <- as.numeric(as.character(true_pairs$year2))
  year_mismatch <- true_pairs[which(true_pairs$year1 != true_pairs$year2),]
  year_mismatch_minor1 <- year_mismatch[which(year_mismatch$year1 == year_mismatch$year2+1 ),]
  year_mismatch_minor2 <- year_mismatch[which(year_mismatch$year1 == year_mismatch$year2-1 ),]

  year_mismatch_minor <- rbind(year_mismatch_minor1,year_mismatch_minor2)
  year_mismatch_minor <- unique(year_mismatch_minor)

  # Identify where year differs >1 and remove from filtered dataset - need to manually deduplicate
  year_mismatch_major <- year_mismatch[which(!rownames(year_mismatch) %in% rownames(year_mismatch_minor)),]

  true_pairs <- true_pairs[which(!rownames(true_pairs) %in% rownames(year_mismatch_major)),]

  true_pairs <- unique(true_pairs)
  print(paste('true pairs', nrow(true_pairs)))

  true_pairs$record_id1 <- as.character(true_pairs$record_id1)
  true_pairs$record_id2 <- as.character(true_pairs$record_id2)

  # Get potential duplicates for manual deduplication
  maybe_pairs <- rbind(true_pairs_mismatch_doi, year_mismatch_major)

  return(list("true_pairs" = true_pairs,
              "maybe_pairs" = maybe_pairs))

}

# load citations
citation_data <- load_search("_dump_tmp.csv", method="csv")

# deduplicate
dedup_citations_result <- dedup_citations(citation_data)

# get unique citation dataframe
# unique_citations <- dedup_citations_result$unique
manual_dedup <- dedup_citations_result$manual_dedup

# write.csv(unique_citations, "_unique_citations.csv", row.names=FALSE)

raw_citations_with_id <- add_id_citations(citation_data)
formatted_citations <- format_citations(raw_citations_with_id)
pairs <- match_citations(formatted_citations)
pair_types <- identify_true_matches(pairs)
true_pairs <- pair_types$true_pairs

print(paste('manual dedup before removing true_pairs', nrow(manual_dedup)))

# remove true pairs from manual dedup list
manual_dedup <- manual_dedup[which(!rownames(manual_dedup) %in% rownames(true_pairs)),]
print(paste('manual dedup', nrow(manual_dedup)))

write.csv(true_pairs, "_true_pairs.csv", row.names=FALSE)
write.csv(manual_dedup, "_manual_dedup.csv", row.names=FALSE)
