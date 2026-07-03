# Cricket Database Business Rules

## Match Rules

- A match must have exactly two different teams.
- Team1 and Team2 cannot be the same.
- Toss winning team must be one of the participating teams.
- Player of the Match must have participated in the match.
- Every match must contain exactly one or two innings (depending on match completion).
- MatchResult must contain exactly one record per participating team.
- Only one winning team is allowed unless the match is tied or abandoned.
- Winning team must have the higher score unless DLS or No Result is applied.
- Match date must belong to the specified season.

---

## Team Rules

- Every player must belong to one team for the corresponding season.
- A player cannot represent both teams in the same match.
- Every player appearing in a match must belong to one of the two participating teams.
- Only registered players can participate in a match.
- Every participating team should have a valid squad for the season.
- Every team should have at least 11 registered players.
- Batting team and bowling team of an innings cannot be the same.

---

## Player Participation Rules

A player is considered to have played the match if they appear in any of the following:

- BattingScoreCard
- BowlingScoreCard
- BallByBallActivity.BatsmanID
- BallByBallActivity.NonStrikerID
- BallByBallActivity.BowlerID
- BallByBallActivity.FielderID

- A player appearing only as a Non-Striker is still considered to have played.
- A player appearing only as a Fielder is still considered to have played.
- A player appearing only as a Bowler is still considered to have played.
- A player cannot participate if they do not belong to the playing teams.
- A player cannot appear in more than one team in the same match.

---

## Batting Rules

- There must always be exactly one striker.
- There must always be exactly one non-striker.
- Striker and Non-Striker cannot be the same player.
- Both batsmen must belong to the batting team.
- Exactly two batsmen must be active until a wicket falls.
- A batsman cannot bat after being dismissed.
- A retired hurt batsman may return later.
- A batsman cannot appear twice in the batting order.
- Every batsman should have only one BattingScoreCard record per innings.
- Runs in BattingScoreCard must equal the sum of runs scored from BallByBallActivity.
- Balls faced must equal the number of legal deliveries faced.
- Wide deliveries must not increase balls faced.
- Dot balls must equal legal deliveries where batsman runs are zero.
- Boundary count must equal number of fours.
- Six count must equal number of sixes.
- Strike changes after odd runs.
- Strike changes at the end of every completed over.
- A new batsman can enter only after a wicket or retirement.
- Only one new batsman can enter after a wicket.
- Opening batsmen must face the first delivery of the innings.
- No batsman can face the same delivery more than once.

---

## Bowling Rules

- Every over must be bowled by only one bowler.
- A bowler cannot bowl consecutive overs.
- A bowler must belong to the bowling team.
- Bowler cannot belong to the batting team.
- Bowler cannot be the striker.
- Bowler cannot be the non-striker.
- Bowler cannot dismiss himself.
- Bowler can field only if he is the catcher on a caught-and-bowled dismissal.
- Balls bowled must count only legal deliveries.
- Wide deliveries do not increase balls bowled.
- No Ball deliveries do not increase legal balls bowled.
- Runs conceded must equal batsman runs plus extras.
- Maiden overs contain zero runs conceded.
- Wickets credited to bowlers should exclude Run Outs, Retired Hurt and Obstructing the Field.
- A bowler cannot exceed the maximum overs allowed in the format.

---

## Ball-by-Ball Rules

- Every ball must have a unique combination of MatchID, InningID, OverNo and BallNo.
- Ball numbers must start from one.
- Ball sequence cannot skip.
- Ball numbers reset after every over.
- Every ball must have one striker.
- Every ball must have one non-striker.
- Every ball must have one bowler.
- Striker and Non-Striker cannot be the same.
- Runs cannot be negative.
- Every ball must have exactly one ScoringType.
- Every ball must have exactly one BallType.
- Every dismissal must have exactly one DismissalType.
- Only one dismissal can occur on a ball.
- Every legal over must contain exactly six legal deliveries.
- Wide and No Ball deliveries create extra deliveries.
- Runs should not exceed six unless overthrows are recorded.
- Boundary of four must have four runs.
- Boundary of six must have six runs.
- Bye and Leg Bye cannot occur together.
- Wide and Bye cannot occur together.
- Wide and Leg Bye cannot occur together.
- Ball records must be continuous within an innings.

---

## Dismissal Rules

- A dismissal must reference a valid dismissal type.
- Caught dismissal must have a FielderID.
- Bowled dismissal must not have a FielderID.
- LBW dismissal must not have a FielderID.
- Hit Wicket dismissal must not have a FielderID.
- Stumped dismissal must have the wicketkeeper as the fielder.
- Run Out may dismiss either striker or non-striker.
- Run Out is not credited to the bowler.
- Caught dismissal is credited to the bowler.
- LBW dismissal is credited to the bowler.
- Bowled dismissal is credited to the bowler.
- Hit Wicket dismissal is credited to the bowler.
- Retired Hurt is not credited to the bowler.
- Obstructing the Field is not credited to the bowler.
- If IsDismissal is false then wickets must not increase.
- Dismissed batsman cannot appear in subsequent deliveries.
- Only one wicket can fall on one delivery.
- A wicket must reference the dismissed player.

---

## Fielding Rules

- Fielder must belong to the bowling team.
- Fielder cannot be the striker.
- Fielder cannot be the non-striker.
- Fielder cannot catch his own batting team's player.
- Catch must have exactly one fielder.
- A caught dismissal cannot have a null fielder.
- A run out may or may not have a recorded fielder depending on available data.
- Fielder cannot be the dismissed batsman.
- Fielder can be the bowler only for caught-and-bowled dismissals.

---

## Innings Rules

- Every innings must have one batting team.
- Every innings must have one bowling team.
- Batting and bowling teams cannot be the same.
- Innings score must equal total runs plus extras.
- Innings wickets cannot exceed ten.
- Innings legal balls cannot exceed the format limit unless super over.
- Innings must end after ten wickets.
- Innings must end immediately when the chasing team reaches the target.
- Extras must equal Wides + No Balls + Byes + Leg Byes.
- Total runs must equal Batsman Runs + Extras.

---

## Batting Scorecard Rules

- One BattingScoreCard per batsman per innings.
- BattingScoreCard runs must equal BallByBallActivity runs.
- BattingScoreCard balls must equal legal deliveries faced.
- BattingScoreCard boundaries must equal number of fours.
- BattingScoreCard sixes must equal number of sixes.
- BattingScoreCard dot balls must equal legal scoreless deliveries.

---

## Bowling Scorecard Rules

- One BowlingScoreCard per bowler per innings.
- Balls bowled must equal legal deliveries.
- Runs given must equal batsman runs plus extras.
- Wickets taken must equal credited dismissals.
- Maidens must equal overs with zero runs conceded.
- Dot balls must equal legal deliveries where no runs were conceded.

---

## Match Result Rules

- MatchResult should contain exactly one record for each participating team.
- Winning team must match the innings scores.
- Run margin must equal score difference.
- Wicket margin must equal remaining wickets.
- Match result cannot exist before innings completion.

---

## Season Rules

- Every Match season must exist in TeamSeason.
- Every PlayerSeason must reference a valid TeamSeason.
- A player cannot belong to multiple teams in the same season.
- Every participating player must be registered for the season.

---

## Data Integrity Rules

- No duplicate BattingScoreCard records.
- No duplicate BowlingScoreCard records.
- No duplicate innings.
- No duplicate matches.
- No duplicate ball records.
- All foreign keys must exist.
- No orphan records should exist.
- Primary keys must be unique.

---

## Aggregate Validation Rules

- Sum of batsman runs must equal innings batsman runs.
- Sum of extras must equal innings extras.
- Sum of innings runs must equal match total.
- Sum of batting scorecard runs must equal BallByBallActivity runs.
- Sum of batting scorecard balls must equal legal deliveries.
- Sum of bowling balls must equal innings legal deliveries.
- Sum of bowling wickets must equal credited dismissals.
- Sum of bowling runs must equal innings runs.
- Total wickets must equal number of dismissals.
- Match winner must have the highest score.

---

## Cricket Logic Rules

- Exactly two active batsmen must always be on the field until a wicket falls.
- New batsman replaces only the dismissed batsman.
- Partnership resets after every wicket.
- Opening pair must start the innings.
- Last wicket ends the innings.
- Chasing innings ends immediately after reaching the target.
- No deliveries should exist after innings completion.
- A player dismissed earlier cannot appear as striker or non-striker again unless retired hurt and returned.
- Every delivery must have valid batting and bowling players.
- Every scoring event must contribute correctly to innings totals.

