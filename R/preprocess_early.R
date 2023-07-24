library(tidyverse)

chains <- read_csv("data/chains_data.csv") %>% 
  rowid_to_column() %>%
  filter(!is.na(team), !str_detect(description, "50")) %>% 
  mutate(chain_id = consecutive_id(playerId), 
         .by = c(roundNumber, homeTeam.teamName, period, chain_number))

outcome_summary <- 
  chains %>% 
  group_by(roundNumber, homeTeam.teamName, period,chain_number, chain_id) %>%
  summarise(outcomes = paste(description, collapse = ", "),
            n = n(),
            rowid_start = first(rowid),
            .groups = "drop")

outcome_summary %>% 
  sample_n(size = 1) %>% 
  inner_join(chains) %>%
  mutate(chain_num = consecutive_id(playerId), 
         .by = c(roundNumber, homeTeam.teamName, period, chain_number)) %>% 
  View()

chains %>% 
  mutate(chain_num = consecutive_id(playerId), 
         .by = c(roundNumber, homeTeam.teamName, period, chain_number)) %>% 
  slice(13019:(13019+4)) %>% View

chains %>% 
  rowid_to_column() %>% 
  filter(!is.na(team), description != "Kick Into F50") %>% 
  filter(roundNumber == 5, str_detect(homeTeam.teamName, "Brisba"), period == 2, chain_number == 93) %>% 
  mutate(chain_id = consecutive_id(playerId), 
         .by = c(roundNumber, homeTeam.teamName, period, chain_number)) %>%
  select(team, chain_number, period, periodSeconds, playerId, surname, description, disposal, chain_id)

### Create a match number column

### Create a 

### Gather a table of possessions

# - gained pos
# - position run
# - outcome
# - score/goal/behind

chains %>% 
  group_by(seasonroundNumber, homeTeam.teamName, period,chain_number, chain_id) %>%
  summarise(outcomes = paste(description, collapse = ", "),
            n = n(),
            rowid_start = first(rowid),
            .groups = "drop")