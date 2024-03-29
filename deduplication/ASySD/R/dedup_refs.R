####------ Assign id ------ ####

#' This function adds an id to citation data if missing
#' @param raw_citations Citation dataframe with relevant columns
#' @return Dataframe of citations with id

add_id_citations <- function(raw_citations){

  names(raw_citations)  <- to_any_case(names(raw_citations), case = c("snake"))

  raw_citations_with_id <- raw_citations %>%
    mutate(record_id = ifelse(is.na(record_id), as.character(row_number()+1000), paste(record_id))) %>%
    mutate(record_id = ifelse(record_id=="", as.character(row_number()+1000), paste(record_id)))

}

####------ Format citation data ------ ####

#' This function formats citation data for deduplication
#' @param raw_citations_with_id Citation dataframe with relevant columns and id column
#' @return Dataframe of formatted citations with id

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

####------ Identify all possible matching pairs of citations ------ ####

#' This function identifies matching pairs of citations
#' @param formatted_citations Formatted citation dataframe with relevant columns and id column
#' @return Dataframe of citation pairs

match_citations <- function(formatted_citations){

  # ROUND 1: run compare.dedup function and block by title&pages OR title&author OR title&abstract OR doi
#   try(newpairs <- compare.dedup(formatted_citations, blockfld = list(c(2,8), c(1,2), c(2,5), 6), strcmp = TRUE, exclude=c("record_id", "source", "label")), silent=TRUE)
    try(newpairs <- compare.dedup(formatted_citations, blockfld = list(2, c(1,2), c(2,5), 6), strcmp = TRUE, exclude=c("record_id", "source", "label")), silent=TRUE)
  linkedpairs <- as.data.frame(if(exists("newpairs")) newpairs$pairs)

  # ROUND 2: run compare.dedup function and block by author&year&pages OR journal&volume&pages or isbn&volume&pages OR title&isbn
#   try(newpairs2 <- compare.dedup(formatted_citations, blockfld = list(c(1,3,8), c(4,9,8), c(10,9,8), c(2,10)), strcmp = TRUE, exclude= c("record_id", "source", "label")), silent=TRUE)
#   linkedpairs2 <- as.data.frame(if(exists("newpairs2")) newpairs2$pairs)

  # ROUND 3: run compare.dedup function and block by year&pages&volume OR year&number&volume or year&pages&number
#   try(newpairs3 <- compare.dedup(formatted_citations, blockfld = list(c(3,8,9), c(3,7,9), c(3,8,7)), strcmp = TRUE, exclude=c("record_id", "source", "label")), silent = TRUE)
#   linkedpairs3 <- as.data.frame(if(exists("newpairs3")) newpairs3$pairs)

  # ROUND 4: run compare.dedup function and block by author&year OR year&title OR title&volume OR title&journal
#   try(newpairs4 <- compare.dedup(formatted_citations, blockfld = list(c(1,3), c(3,2), c(2,9), c(2,4)), strcmp = TRUE, exclude=c("record_id", "source", "label")), silent = TRUE)
    try(newpairs4 <- compare.dedup(formatted_citations, blockfld = list(c(1,3), c(3,2), c(2,4)), strcmp = TRUE, exclude=c("record_id", "source", "label")), silent = TRUE)
  linkedpairs4 <- as.data.frame(if(exists("newpairs4")) newpairs4$pairs)

  # Combine all possible pairs
  pairs <- rbind(if(exists("linkedpairs")) linkedpairs,
#                  if(exists("linkedpairs2")) linkedpairs2,
#                  if(exists("linkedpairs3")) linkedpairs3,
                 if(exists("linkedpairs4")) linkedpairs4)

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

  pairs <- pairs %>%
    mutate(abstract = ifelse(is.na(abstract1) & is.na(abstract2), 0, abstract)) %>%
    mutate(pages = ifelse(is.na(pages1) & is.na(pages2), 1, pages)) %>%
    mutate(volume = ifelse(is.na(volume1) & is.na(volume2), 1, volume)) %>%
    mutate(number = ifelse(is.na(number1) & is.na(number2), 1, number)) %>%
    mutate(doi = ifelse(is.na(doi1) & is.na(doi2), 0, doi)) %>%
    mutate(isbn = ifelse(is.na(isbn1) & is.na(isbn2), 0, isbn))
}


#' This function identifies true pairs from matching pairs of citations and pairs which may be duplicates - for manual deduplication
#' @param pairs citation matches which may be duplicates
#' @return Dataframe of true citation pairs

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

  true_pairs$record_id1 <- as.character(true_pairs$record_id1)
  true_pairs$record_id2 <- as.character(true_pairs$record_id2)

  # Get potential duplicates for manual deduplication
  maybe_pairs <- rbind(true_pairs_mismatch_doi, year_mismatch_major)

  return(list("true_pairs" = true_pairs,
              "maybe_pairs" = maybe_pairs))

}

#' This function generates a duplicate ID for sets of matching citations
#' @param true_pairs citation matches which are true duplicates'
#' @param formatted_citations formatted citation data
#' @return Dataframe of formatted citation data with duplicate id

generate_dup_id <- function(true_pairs, formatted_citations){

  # generate duplicate IDs
  dup_ids <- true_pairs %>%
    group_by(record_id1) %>%
    mutate(duplicate_id = first(record_id1)) %>%
    ungroup() %>%
    group_by(record_id2) %>%
    mutate(duplicate_id = first(duplicate_id)) %>%
    ungroup() %>%
    select(record_id1, record_id2, duplicate_id) %>%
    unique()

  citations_with_dup_id1 <- inner_join(formatted_citations, dup_ids, by=c("record_id"="record_id1")) %>%
    select(-record_id2) %>%
    unique()

  citations_with_dup_id2 <- inner_join(formatted_citations, dup_ids, by=c("record_id"="record_id2")) %>%
    select(-record_id1) %>%
    unique()

  citations_with_dup_id <- rbind(citations_with_dup_id1, citations_with_dup_id2) %>% unique()

  unique_citations <- formatted_citations %>%
    filter(!record_id %in% citations_with_dup_id$record_id) %>%
    mutate(duplicate_id = record_id)

  citations_with_dup_id <- rbind(unique_citations, citations_with_dup_id)
  matched_pairs_with_ids <- unique(citations_with_dup_id)

  return(matched_pairs_with_ids)

}

# Remove duplicate papers ----------------------------------------------
#' This function retains one citation in a set of matching records
#' @param matched_pairs_with_ids citation data with duplicate ids
#' @param raw_citations_with_id original citation data with ids
#' @return Dataframe of citation data with duplicate citation rows removed
keep_one_unique_citation <- function(raw_citations_with_id, matched_pairs_with_ids, preferred_source){

  duplicate_id <- matched_pairs_with_ids %>%
    select(duplicate_id, record_id) %>%
    unique()

  all_metadata_with_duplicate_id <- left_join(duplicate_id, raw_citations_with_id)

  if(!is.null(preferred_source)){


  citations_with_dup_id_pick <- all_metadata_with_duplicate_id %>%
    mutate_all(~replace(., .=='NA', NA)) %>%
    group_by(duplicate_id) %>%
    arrange(doi, abstract) %>%
     mutate(Order = ifelse(source == preferred_source, 1, 2)) %>%
    arrange(Order) %>%
    select(-Order, -preferred_source) %>%
    slice_head()
  }

  else{
    citations_with_dup_id_pick <- all_metadata_with_duplicate_id %>%
      mutate_all(~replace(., .=='NA', NA)) %>%
      group_by(duplicate_id) %>%
      arrange(doi, abstract) %>%
      slice_head()

  }
}

  get_manual_dedup_list <- function(maybe_pairs, matched_pairs_with_ids, pairs){

    maybe_also_pairs <- pairs %>%
      filter(record_id1 %in% matched_pairs_with_ids$record_id &
               record_id2 %in% matched_pairs_with_ids$record_id) %>%
      filter(doi > 0.99 |
               title>0.85 & author>0.75 |
               title>0.80 & abstract>0.80 |
               title>0.80 & isbn>0.99 |
               title>0.80 & journal>0.80)

    # Add in problem doi matching pairs and different year data in ManualDedup
    maybe_pairs <- rbind(maybe_pairs, maybe_also_pairs)
    maybe_pairs <- unique(maybe_pairs)

  maybe_pairs <- maybe_pairs %>%
    filter(record_id1 %in% matched_pairs_with_ids$record_id &
             record_id2 %in% matched_pairs_with_ids$record_id)

  }
  #' This function generates a duplicate ID for sets of matching citations
  #' @param matched_pairs_with_ids citation data with duplicate ids
  #' @param raw_citations_with_id  original citation data with unique ids
  #' @return Dataframe of formatted citation data with duplicate id

  merge_metadata <- function(raw_citations_with_id, matched_pairs_with_ids){

    duplicate_id <- matched_pairs_with_ids %>%
      select(duplicate_id, record_id) %>%
      unique()

    all_metadata_with_duplicate_id <- left_join(duplicate_id, raw_citations_with_id)

    citations_with_dup_id_merged <- all_metadata_with_duplicate_id %>%
      mutate_all(~replace(., .=='NA', NA)) %>%
      group_by(duplicate_id) %>%
      summarise_all(funs(trimws(paste(na.omit(.), collapse = ';;;')))) %>%
      mutate(across(c(everything(), -label, -source), gsub, pattern = ";;;.*", replacement = "")) %>%
      mutate(across(label, gsub, pattern = ";;;", replacement = ", ")) %>%
      mutate(across(source, gsub, pattern = ";;;", replacement = ", "))

  }

  #' Deduplicate citations
  #'
  #' This function deduplicates citation data
  #' @export
  #' @param raw_citations Citation dataframe with relevant columns
  #' @param manual_dedup Logical value. Do you want to retrieve dataframe for manual deduplication?
  #' @param manual_dedup Logical value. Do you want to retrieve dataframe for manual deduplication?
  #' @return A list of 2 dataframes - unique citations and citations to be manually deduplicated if option selected

  dedup_citations <- function(raw_citations, manual_dedup = TRUE, merge_citations=FALSE, preferred_source=NULL) {

    raw_citations_with_id <- add_id_citations(raw_citations)
    formatted_citations <- format_citations(raw_citations_with_id)
    pairs <- match_citations(formatted_citations)
    pair_types <- identify_true_matches(pairs)

    true_pairs <- pair_types$true_pairs
    maybe_pairs <- pair_types$maybe_pairs
    matched_pairs_with_ids <- generate_dup_id(true_pairs, formatted_citations)

    if(manual_dedup == TRUE){

      manual_dedup <- get_manual_dedup_list(maybe_pairs, formatted_citations, pairs)
    }

    if(merge_citations == TRUE){

      unique_citations_with_metadata <- merge_metadata(raw_citations_with_id, matched_pairs_with_ids)
    }

    else{
      unique_citations_with_metadata <- keep_one_unique_citation(raw_citations_with_id, matched_pairs_with_ids, preferred_source)

    }

    return(list("unique" = unique_citations_with_metadata,
                "manual_dedup" = manual_dedup))
  }
