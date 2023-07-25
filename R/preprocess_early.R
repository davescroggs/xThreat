library(tidyverse)
library(janitor)

## Helper functions

calc_dist <- function(x0, y0, x1, y1){
  pass_dist = sqrt((x1-x0)^2 + (y1 - y0)^2)
  return(pass_dist)
}

## Column rename

map_names <- 
  c(round = "roundNumber",
  homeTeam = "homeTeam.teamName",
  awayTeam = "awayTeam.teamName",
  homeTeamScore = "homeTeamScore.totalScore",
  awayTeamScore = "awayTeamScore.totalScore",
  chainNumber = "chain_number",
  venueName = "venue.name",
  playingFor = "team")

## Read in data
## Rename columns
chains <- read_csv("data/chains_data.csv") %>% 
  rowid_to_column() %>% 
  # Rename columns
  rename(any_of(map_names)) %>% 
  # Also remove Inside 50 rows
  filter(!str_detect(description, "50")) %>% 
  # Create an id for each possession
  replace_na(list(playerId = "CONTEXT")) %>% 
  mutate(possession_id = consecutive_id(playerId), 
         .by = c(round, homeTeam, period, chainNumber)) %>% 
  # Normalise x/y loc
  mutate(x_norm = x/venueLength/2,
         y_norm = y/venueWidth/2)

## Create context dataframe

context_data <- read_csv("data/chains_data.csv") %>%
  rename(any_of(map_names)) %>% 
  rowid_to_column() %>% 
  filter(is.na(playingFor))

## Create venue dimensions datafram

venue_dims <- chains %>% 
  distinct(venueName, venueWidth, venueLength)

## Create possession summary

# - gained pos
# - position run
# - outcome
# - score/goal/behind
# - #fumbles/drops

possession_summary <- 
  chains %>% 
  group_by(round, homeTeam, period, chainNumber, possession_id) %>%
  summarise(outcomes = paste(description, collapse = ", "),
            n = n(),
            bounces = sum(description == "Bounce"),
            handballs = sum(description == "Handball"),
            ballGet = sum(str_detect(description, "Ball Get")),
            crumb = sum(str_detect(description, "(C|c)rumb")),
            rowid_start = first(rowid),
            initialState = first(initialState),
            finalState = first(finalState),
            xInitialPoss = first(x),
            yInitialPoss = first(y),
            xFinalPoss = last(x),
            yFinalPoss = last(y),
            distanceFromPoss = calc_dist(xInitialPoss, yInitialPoss, xFinalPoss, yFinalPoss),
            initialDistFromGoal = calc_dist(xInitialPoss, yInitialPoss, first(venueLength), 0),
            finalDistFromGoal = calc_dist(xFinalPoss, yFinalPoss, first(venueLength), 0),
            deltaDistFromGoal = finalDistFromGoal - initialDistFromGoal,
            .groups = "drop") %>% 
  mutate(disposalDist = pmap_dbl(list(xFinalPoss, yFinalPoss, lead(xInitialPoss), lead(yInitialPoss)),  calc_dist),
         possessionDist = pmap_dbl(list(xInitialPoss, yInitialPoss, lead(xInitialPoss), lead(yInitialPoss)),  calc_dist))

chains %>% 
inner_join(possession_summary %>% 
  slice_max(possessionDist, n = 5) %>%
  slice(3) %>% 
    select(round, homeTeam, period, chainNumber, possession_id))

chains %>% 
  inner_join(chains %>% 
               sample_n(1) %>% 
               select(season, round, homeTeam, period, chainNumber, possession_id)) %>% View

chains %>% 
  filter(between(rowid, 271668-5, 271668+5)) %>% View

### Create a match number column

### Create a schedule df
## Maybe source this from fitzRoy
chains %>% 
  distinct(date, season, round, homeTeam, awayTeam, venueName)



chains %>% 
  group_by(seasonroundNumber, homeTeam.teamName, period,chain_number, chain_id) %>%
  summarise(outcomes = paste(description, collapse = ", "),
            n = n(),
            rowid_start = first(rowid),
            .groups = "drop")