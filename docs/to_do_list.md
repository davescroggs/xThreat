### Pass networks to do

 - There's often information about a kick afterwards, need to include. Most often when the kick doesn't go to a player (ie. goal, out of bounds)
      - ~~Need to get the last disposal (Kick, Handball, Ground Kick) and see if there's anything after it~~
      - Look at what happens when a) pass to team mate, b) turnover, c) some game event (goal, end of quarter, kick out bounds)

 - Readme/landing page
 - ~~Viz passing network (network diagrams in python)~~
 - Viz chains
    - ~~Remove superflous events, just keep the ones important for understanding~~
 - Viz footy oval (with/without normalised values?)
   - Early version = DONE
   - ~~Flatten the goal line, add goal + point posts~~
 - ~~summarise effective disposal position for each player~~
 - build xThreat model based on whether 
 - Think about cacluating a delta threat before and after possession
 - Get most effective possession in a given game
 - Add information about free kicks in possessions (not start)
 - ~~Determine continuity/discontiuity between posessions for start and end position calculations~~
 - ~~Weird thing at the end of qtr when last poss is at 0,0~~
       - Look at what happens when a) pass to team mate, b) turnover, c) some game event (goal, end of quarter, kick out bounds)
 - Spoils for opposition appear in a chain where they're not a turnover
 - 50 m penalties look long carries
 - Distance measures are stuffed
 - ~~End of quarter possession probaly needs to go. Ball ends up at the centre bounce.~~
 - Look at passing networks, see if next reciever works
 - Kicks after marks appear as player movement



Examples of wierd chains
 - 2023_13_Hawthorn_C147
 - 2023_6_Fremantle_C206_P5 - This chain ends in a Freo spoil in a WB chain, but isn't a turnover hence ins't duplicated. Damn.
 - 2023_3_GWS_Giants_C187_P1 - Weird kickin, starting location for kickin maybe wrong