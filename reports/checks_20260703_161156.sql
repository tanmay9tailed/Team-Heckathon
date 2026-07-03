-- Data Quality Check Queries
-- Generated at: 2026-07-03T16:11:56.447756

-- Category: Completeness | Severity: Critical
-- Question: Are there records in dbo.BallType with missing values in mandatory column BallTypeID?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[BallType] AS t WHERE t.[BallTypeID] IS NULL;

-- Category: Completeness | Severity: Critical
-- Question: Are there records in dbo.BallType with missing values in mandatory column BallType?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[BallType] AS t WHERE (t.[BallType] IS NULL OR NULLIF(LTRIM(RTRIM(CAST(t.[BallType] AS NVARCHAR(MAX)))), '') IS NULL);

-- Category: Uniqueness | Severity: Critical
-- Question: Are there duplicate BallTypeID values present in dbo.BallType?
SELECT COUNT_BIG(*) AS issue_count FROM (SELECT [BallTypeID] FROM [dbo].[BallType] WHERE [BallTypeID] IS NOT NULL GROUP BY [BallTypeID] HAVING COUNT_BIG(*) > 1) AS duplicate_keys;

-- Category: Completeness | Severity: Critical
-- Question: Are there records in dbo.BallbyBallActivity with missing values in mandatory column MatchID?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[BallbyBallActivity] AS t WHERE t.[MatchID] IS NULL;

-- Category: Completeness | Severity: Critical
-- Question: Are there records in dbo.BallbyBallActivity with missing values in mandatory column inningID?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[BallbyBallActivity] AS t WHERE t.[inningID] IS NULL;

-- Category: Completeness | Severity: Critical
-- Question: Are there records in dbo.BallbyBallActivity with missing values in mandatory column OverNo?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[BallbyBallActivity] AS t WHERE t.[OverNo] IS NULL;

-- Category: Completeness | Severity: Critical
-- Question: Are there records in dbo.BallbyBallActivity with missing values in mandatory column BallNO?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[BallbyBallActivity] AS t WHERE t.[BallNO] IS NULL;

-- Category: Completeness | Severity: Critical
-- Question: Are there records in dbo.BallbyBallActivity with missing values in mandatory column BowlerID?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[BallbyBallActivity] AS t WHERE t.[BowlerID] IS NULL;

-- Category: Completeness | Severity: Critical
-- Question: Are there records in dbo.BallbyBallActivity with missing values in mandatory column BatsmanID?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[BallbyBallActivity] AS t WHERE t.[BatsmanID] IS NULL;

-- Category: Completeness | Severity: Critical
-- Question: Are there records in dbo.BallbyBallActivity with missing values in mandatory column NonStrikerID?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[BallbyBallActivity] AS t WHERE t.[NonStrikerID] IS NULL;

-- Category: Completeness | Severity: Critical
-- Question: Are there records in dbo.BallbyBallActivity with missing values in mandatory column ScoringTypeID?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[BallbyBallActivity] AS t WHERE t.[ScoringTypeID] IS NULL;

-- Category: Completeness | Severity: Critical
-- Question: Are there records in dbo.BallbyBallActivity with missing values in mandatory column BallTypeID?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[BallbyBallActivity] AS t WHERE t.[BallTypeID] IS NULL;

-- Category: Uniqueness | Severity: Critical
-- Question: Are there duplicate MatchID, inningID, OverNo, BallNO, ScoringTypeID values present in dbo.BallbyBallActivity?
SELECT COUNT_BIG(*) AS issue_count FROM (SELECT [MatchID], [inningID], [OverNo], [BallNO], [ScoringTypeID] FROM [dbo].[BallbyBallActivity] WHERE [MatchID] IS NOT NULL AND [inningID] IS NOT NULL AND [OverNo] IS NOT NULL AND [BallNO] IS NOT NULL AND [ScoringTypeID] IS NOT NULL GROUP BY [MatchID], [inningID], [OverNo], [BallNO], [ScoringTypeID] HAVING COUNT_BIG(*) > 1) AS duplicate_keys;

-- Category: Referential Integrity | Severity: Critical
-- Question: Are there records in dbo.BallbyBallActivity that reference missing parent records in dbo.BallType?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[BallbyBallActivity] AS c LEFT JOIN [dbo].[BallType] AS p ON c.[BallTypeID] = p.[BallTypeID] WHERE c.[BallTypeID] IS NOT NULL AND p.[BallTypeID] IS NULL;

-- Category: Referential Integrity | Severity: Critical
-- Question: Are there records in dbo.BallbyBallActivity that reference missing parent records in dbo.DismissalType?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[BallbyBallActivity] AS c LEFT JOIN [dbo].[DismissalType] AS p ON c.[DismissalTypeID] = p.[DismissalTypeID] WHERE c.[DismissalTypeID] IS NOT NULL AND p.[DismissalTypeID] IS NULL;

-- Category: Referential Integrity | Severity: Critical
-- Question: Are there records in dbo.BallbyBallActivity that reference missing parent records in dbo.Match?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[BallbyBallActivity] AS c LEFT JOIN [dbo].[Match] AS p ON c.[MatchID] = p.[MatchID] WHERE c.[MatchID] IS NOT NULL AND p.[MatchID] IS NULL;

-- Category: Referential Integrity | Severity: Critical
-- Question: Are there records in dbo.BallbyBallActivity that reference missing parent records in dbo.Player?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[BallbyBallActivity] AS c LEFT JOIN [dbo].[Player] AS p ON c.[BatsmanID] = p.[PlayerID] WHERE c.[BatsmanID] IS NOT NULL AND p.[PlayerID] IS NULL;

-- Category: Referential Integrity | Severity: Critical
-- Question: Are there records in dbo.BallbyBallActivity that reference missing parent records in dbo.ScoringType?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[BallbyBallActivity] AS c LEFT JOIN [dbo].[ScoringType] AS p ON c.[ScoringTypeID] = p.[ScoringTypeID] WHERE c.[ScoringTypeID] IS NOT NULL AND p.[ScoringTypeID] IS NULL;

-- Category: Completeness | Severity: Critical
-- Question: Are there records in dbo.BattingScoreCard with missing values in mandatory column MatchID?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[BattingScoreCard] AS t WHERE t.[MatchID] IS NULL;

-- Category: Completeness | Severity: Critical
-- Question: Are there records in dbo.BattingScoreCard with missing values in mandatory column InningID?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[BattingScoreCard] AS t WHERE t.[InningID] IS NULL;

-- Category: Completeness | Severity: Critical
-- Question: Are there records in dbo.BattingScoreCard with missing values in mandatory column BatsmanID?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[BattingScoreCard] AS t WHERE t.[BatsmanID] IS NULL;

-- Category: Uniqueness | Severity: Critical
-- Question: Are there duplicate MatchID, InningID, BatsmanID values present in dbo.BattingScoreCard?
SELECT COUNT_BIG(*) AS issue_count FROM (SELECT [MatchID], [InningID], [BatsmanID] FROM [dbo].[BattingScoreCard] WHERE [MatchID] IS NOT NULL AND [InningID] IS NOT NULL AND [BatsmanID] IS NOT NULL GROUP BY [MatchID], [InningID], [BatsmanID] HAVING COUNT_BIG(*) > 1) AS duplicate_keys;

-- Category: Referential Integrity | Severity: Critical
-- Question: Are there records in dbo.BattingScoreCard that reference missing parent records in dbo.DismissalType?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[BattingScoreCard] AS c LEFT JOIN [dbo].[DismissalType] AS p ON c.[DismissalTypeID] = p.[DismissalTypeID] WHERE c.[DismissalTypeID] IS NOT NULL AND p.[DismissalTypeID] IS NULL;

-- Category: Referential Integrity | Severity: Critical
-- Question: Are there records in dbo.BattingScoreCard that reference missing parent records in dbo.Match?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[BattingScoreCard] AS c LEFT JOIN [dbo].[Match] AS p ON c.[MatchID] = p.[MatchID] WHERE c.[MatchID] IS NOT NULL AND p.[MatchID] IS NULL;

-- Category: Referential Integrity | Severity: Critical
-- Question: Are there records in dbo.BattingScoreCard that reference missing parent records in dbo.Player?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[BattingScoreCard] AS c LEFT JOIN [dbo].[Player] AS p ON c.[BatsmanID] = p.[PlayerID] WHERE c.[BatsmanID] IS NOT NULL AND p.[PlayerID] IS NULL;

-- Category: Completeness | Severity: Critical
-- Question: Are there records in dbo.BowlingScoreCard with missing values in mandatory column MatchID?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[BowlingScoreCard] AS t WHERE t.[MatchID] IS NULL;

-- Category: Completeness | Severity: Critical
-- Question: Are there records in dbo.BowlingScoreCard with missing values in mandatory column InningID?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[BowlingScoreCard] AS t WHERE t.[InningID] IS NULL;

-- Category: Completeness | Severity: Critical
-- Question: Are there records in dbo.BowlingScoreCard with missing values in mandatory column bowlerID?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[BowlingScoreCard] AS t WHERE t.[bowlerID] IS NULL;

-- Category: Uniqueness | Severity: Critical
-- Question: Are there duplicate MatchID, InningID, bowlerID values present in dbo.BowlingScoreCard?
SELECT COUNT_BIG(*) AS issue_count FROM (SELECT [MatchID], [InningID], [bowlerID] FROM [dbo].[BowlingScoreCard] WHERE [MatchID] IS NOT NULL AND [InningID] IS NOT NULL AND [bowlerID] IS NOT NULL GROUP BY [MatchID], [InningID], [bowlerID] HAVING COUNT_BIG(*) > 1) AS duplicate_keys;

-- Category: Referential Integrity | Severity: Critical
-- Question: Are there records in dbo.BowlingScoreCard that reference missing parent records in dbo.Match?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[BowlingScoreCard] AS c LEFT JOIN [dbo].[Match] AS p ON c.[MatchID] = p.[MatchID] WHERE c.[MatchID] IS NOT NULL AND p.[MatchID] IS NULL;

-- Category: Referential Integrity | Severity: Critical
-- Question: Are there records in dbo.BowlingScoreCard that reference missing parent records in dbo.Player?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[BowlingScoreCard] AS c LEFT JOIN [dbo].[Player] AS p ON c.[bowlerID] = p.[PlayerID] WHERE c.[bowlerID] IS NOT NULL AND p.[PlayerID] IS NULL;

-- Category: Completeness | Severity: Critical
-- Question: Are there records in dbo.DismissalType with missing values in mandatory column DismissalTypeID?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[DismissalType] AS t WHERE t.[DismissalTypeID] IS NULL;

-- Category: Completeness | Severity: Critical
-- Question: Are there records in dbo.DismissalType with missing values in mandatory column DismissalType?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[DismissalType] AS t WHERE (t.[DismissalType] IS NULL OR NULLIF(LTRIM(RTRIM(CAST(t.[DismissalType] AS NVARCHAR(MAX)))), '') IS NULL);

-- Category: Uniqueness | Severity: Critical
-- Question: Are there duplicate DismissalTypeID values present in dbo.DismissalType?
SELECT COUNT_BIG(*) AS issue_count FROM (SELECT [DismissalTypeID] FROM [dbo].[DismissalType] WHERE [DismissalTypeID] IS NOT NULL GROUP BY [DismissalTypeID] HAVING COUNT_BIG(*) > 1) AS duplicate_keys;

-- Category: Completeness | Severity: Critical
-- Question: Are there records in dbo.InningScoreCard with missing values in mandatory column MatchID?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[InningScoreCard] AS t WHERE t.[MatchID] IS NULL;

-- Category: Completeness | Severity: Critical
-- Question: Are there records in dbo.InningScoreCard with missing values in mandatory column InningID?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[InningScoreCard] AS t WHERE t.[InningID] IS NULL;

-- Category: Completeness | Severity: Critical
-- Question: Are there records in dbo.InningScoreCard with missing values in mandatory column BattingTeamID?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[InningScoreCard] AS t WHERE t.[BattingTeamID] IS NULL;

-- Category: Completeness | Severity: Critical
-- Question: Are there records in dbo.InningScoreCard with missing values in mandatory column BowlingTeamID?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[InningScoreCard] AS t WHERE t.[BowlingTeamID] IS NULL;

-- Category: Uniqueness | Severity: Critical
-- Question: Are there duplicate MatchID, InningID values present in dbo.InningScoreCard?
SELECT COUNT_BIG(*) AS issue_count FROM (SELECT [MatchID], [InningID] FROM [dbo].[InningScoreCard] WHERE [MatchID] IS NOT NULL AND [InningID] IS NOT NULL GROUP BY [MatchID], [InningID] HAVING COUNT_BIG(*) > 1) AS duplicate_keys;

-- Category: Referential Integrity | Severity: Critical
-- Question: Are there records in dbo.InningScoreCard that reference missing parent records in dbo.Match?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[InningScoreCard] AS c LEFT JOIN [dbo].[Match] AS p ON c.[MatchID] = p.[MatchID] WHERE c.[MatchID] IS NOT NULL AND p.[MatchID] IS NULL;

-- Category: Referential Integrity | Severity: Critical
-- Question: Are there records in dbo.InningScoreCard that reference missing parent records in dbo.Team?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[InningScoreCard] AS c LEFT JOIN [dbo].[Team] AS p ON c.[BattingTeamID] = p.[TeamID] WHERE c.[BattingTeamID] IS NOT NULL AND p.[TeamID] IS NULL;

-- Category: Cross-Table Reconciliation | Severity: Critical
-- Question: Does the 'Score' in dbo.InningScoreCard reconcile with the sum of 'Runs' from dbo.BallbyBallActivity for the corresponding inning?
SELECT COUNT(*) AS issue_count FROM dbo.InningScoreCard isc JOIN ( SELECT MatchID, inningID, SUM(Runs) AS CalculatedScore FROM dbo.BallbyBallActivity GROUP BY MatchID, inningID ) bba_sum ON isc.MatchID = bba_sum.MatchID AND isc.InningID = bba_sum.inningID WHERE isc.Score IS NOT NULL AND isc.Score <> bba_sum.CalculatedScore;

-- Category: Cross-Table Reconciliation | Severity: Critical
-- Question: Does the 'Wickets' in dbo.InningScoreCard reconcile with the count of distinct 'DismissedPlayerID' from dbo.BallbyBallActivity for the corresponding inning where a dismissal occurred?
SELECT COUNT(*) AS issue_count FROM dbo.InningScoreCard isc JOIN ( SELECT bba.MatchID, bba.inningID, COUNT(DISTINCT bba.DismissedPlayerID) AS CalculatedWickets FROM dbo.BallbyBallActivity bba JOIN dbo.DismissalType dt ON bba.DismissalTypeID = dt.DismissalTypeID WHERE dt.IsDismissal = 1 GROUP BY bba.MatchID, bba.inningID ) bba_wickets ON isc.MatchID = bba_wickets.MatchID AND isc.InningID = bba_wickets.inningID WHERE isc.Wickets IS NOT NULL AND isc.Wickets <> bba_wickets.CalculatedWickets;

-- Category: Completeness | Severity: Critical
-- Question: Are there records in dbo.Match with missing values in mandatory column MatchID?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[Match] AS t WHERE t.[MatchID] IS NULL;

-- Category: Completeness | Severity: Critical
-- Question: Are there records in dbo.Match with missing values in mandatory column MatchDate?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[Match] AS t WHERE t.[MatchDate] IS NULL;

-- Category: Completeness | Severity: Critical
-- Question: Are there records in dbo.Match with missing values in mandatory column Team1ID?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[Match] AS t WHERE t.[Team1ID] IS NULL;

-- Category: Completeness | Severity: Critical
-- Question: Are there records in dbo.Match with missing values in mandatory column Team2ID?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[Match] AS t WHERE t.[Team2ID] IS NULL;

-- Category: Completeness | Severity: Critical
-- Question: Are there records in dbo.Match with missing values in mandatory column City?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[Match] AS t WHERE (t.[City] IS NULL OR NULLIF(LTRIM(RTRIM(CAST(t.[City] AS NVARCHAR(MAX)))), '') IS NULL);

-- Category: Completeness | Severity: Critical
-- Question: Are there records in dbo.Match with missing values in mandatory column Venue?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[Match] AS t WHERE (t.[Venue] IS NULL OR NULLIF(LTRIM(RTRIM(CAST(t.[Venue] AS NVARCHAR(MAX)))), '') IS NULL);

-- Category: Completeness | Severity: Critical
-- Question: Are there records in dbo.Match with missing values in mandatory column DLMethodApplied?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[Match] AS t WHERE t.[DLMethodApplied] IS NULL;

-- Category: Completeness | Severity: Critical
-- Question: Are there records in dbo.Match with missing values in mandatory column TossWinningTeamID?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[Match] AS t WHERE t.[TossWinningTeamID] IS NULL;

-- Category: Uniqueness | Severity: Critical
-- Question: Are there duplicate MatchID values present in dbo.Match?
SELECT COUNT_BIG(*) AS issue_count FROM (SELECT [MatchID] FROM [dbo].[Match] WHERE [MatchID] IS NOT NULL GROUP BY [MatchID] HAVING COUNT_BIG(*) > 1) AS duplicate_keys;

-- Category: Referential Integrity | Severity: Critical
-- Question: Are there records in dbo.Match that reference missing parent records in dbo.Player?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[Match] AS c LEFT JOIN [dbo].[Player] AS p ON c.[PlayerOfMatchID] = p.[PlayerID] WHERE c.[PlayerOfMatchID] IS NOT NULL AND p.[PlayerID] IS NULL;

-- Category: Referential Integrity | Severity: Critical
-- Question: Are there records in dbo.Match that reference missing parent records in dbo.Team?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[Match] AS c LEFT JOIN [dbo].[Team] AS p ON c.[Team1ID] = p.[TeamID] WHERE c.[Team1ID] IS NOT NULL AND p.[TeamID] IS NULL;

-- Category: Completeness | Severity: Critical
-- Question: Are there records in dbo.MatchResult with missing values in mandatory column MatchID?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[MatchResult] AS t WHERE t.[MatchID] IS NULL;

-- Category: Completeness | Severity: Critical
-- Question: Are there records in dbo.MatchResult with missing values in mandatory column TeamID?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[MatchResult] AS t WHERE t.[TeamID] IS NULL;

-- Category: Completeness | Severity: Critical
-- Question: Are there records in dbo.MatchResult with missing values in mandatory column Result?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[MatchResult] AS t WHERE (t.[Result] IS NULL OR NULLIF(LTRIM(RTRIM(CAST(t.[Result] AS NVARCHAR(MAX)))), '') IS NULL);

-- Category: Uniqueness | Severity: Critical
-- Question: Are there duplicate MatchID, TeamID values present in dbo.MatchResult?
SELECT COUNT_BIG(*) AS issue_count FROM (SELECT [MatchID], [TeamID] FROM [dbo].[MatchResult] WHERE [MatchID] IS NOT NULL AND [TeamID] IS NOT NULL GROUP BY [MatchID], [TeamID] HAVING COUNT_BIG(*) > 1) AS duplicate_keys;

-- Category: Referential Integrity | Severity: Critical
-- Question: Are there records in dbo.MatchResult that reference missing parent records in dbo.Match?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[MatchResult] AS c LEFT JOIN [dbo].[Match] AS p ON c.[MatchID] = p.[MatchID] WHERE c.[MatchID] IS NOT NULL AND p.[MatchID] IS NULL;

-- Category: Referential Integrity | Severity: Critical
-- Question: Are there records in dbo.MatchResult that reference missing parent records in dbo.Team?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[MatchResult] AS c LEFT JOIN [dbo].[Team] AS p ON c.[TeamID] = p.[TeamID] WHERE c.[TeamID] IS NOT NULL AND p.[TeamID] IS NULL;

-- Category: Completeness | Severity: Critical
-- Question: Are there records in dbo.Player with missing values in mandatory column PlayerID?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[Player] AS t WHERE t.[PlayerID] IS NULL;

-- Category: Completeness | Severity: Critical
-- Question: Are there records in dbo.Player with missing values in mandatory column PlayerName?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[Player] AS t WHERE (t.[PlayerName] IS NULL OR NULLIF(LTRIM(RTRIM(CAST(t.[PlayerName] AS NVARCHAR(MAX)))), '') IS NULL);

-- Category: Uniqueness | Severity: Critical
-- Question: Are there duplicate PlayerID values present in dbo.Player?
SELECT COUNT_BIG(*) AS issue_count FROM (SELECT [PlayerID] FROM [dbo].[Player] WHERE [PlayerID] IS NOT NULL GROUP BY [PlayerID] HAVING COUNT_BIG(*) > 1) AS duplicate_keys;

-- Category: Completeness | Severity: Critical
-- Question: Are there records in dbo.PlayerSeason with missing values in mandatory column Season?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[PlayerSeason] AS t WHERE t.[Season] IS NULL;

-- Category: Completeness | Severity: Critical
-- Question: Are there records in dbo.PlayerSeason with missing values in mandatory column PlayerID?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[PlayerSeason] AS t WHERE t.[PlayerID] IS NULL;

-- Category: Completeness | Severity: Critical
-- Question: Are there records in dbo.PlayerSeason with missing values in mandatory column TeamID?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[PlayerSeason] AS t WHERE t.[TeamID] IS NULL;

-- Category: Uniqueness | Severity: Critical
-- Question: Are there duplicate Season, PlayerID values present in dbo.PlayerSeason?
SELECT COUNT_BIG(*) AS issue_count FROM (SELECT [Season], [PlayerID] FROM [dbo].[PlayerSeason] WHERE [Season] IS NOT NULL AND [PlayerID] IS NOT NULL GROUP BY [Season], [PlayerID] HAVING COUNT_BIG(*) > 1) AS duplicate_keys;

-- Category: Referential Integrity | Severity: Critical
-- Question: Are there records in dbo.PlayerSeason that reference missing parent records in dbo.Player?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[PlayerSeason] AS c LEFT JOIN [dbo].[Player] AS p ON c.[PlayerID] = p.[PlayerID] WHERE c.[PlayerID] IS NOT NULL AND p.[PlayerID] IS NULL;

-- Category: Referential Integrity | Severity: Critical
-- Question: Are there records in dbo.PlayerSeason that reference missing parent records in dbo.Team?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[PlayerSeason] AS c LEFT JOIN [dbo].[Team] AS p ON c.[TeamID] = p.[TeamID] WHERE c.[TeamID] IS NOT NULL AND p.[TeamID] IS NULL;

-- Category: Completeness | Severity: Critical
-- Question: Are there records in dbo.ScoringType with missing values in mandatory column ScoringTypeID?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[ScoringType] AS t WHERE t.[ScoringTypeID] IS NULL;

-- Category: Uniqueness | Severity: Critical
-- Question: Are there duplicate ScoringTypeID values present in dbo.ScoringType?
SELECT COUNT_BIG(*) AS issue_count FROM (SELECT [ScoringTypeID] FROM [dbo].[ScoringType] WHERE [ScoringTypeID] IS NOT NULL GROUP BY [ScoringTypeID] HAVING COUNT_BIG(*) > 1) AS duplicate_keys;

-- Category: Completeness | Severity: Critical
-- Question: Are there records in dbo.Team with missing values in mandatory column TeamID?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[Team] AS t WHERE t.[TeamID] IS NULL;

-- Category: Completeness | Severity: Critical
-- Question: Are there records in dbo.Team with missing values in mandatory column TeamName?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[Team] AS t WHERE (t.[TeamName] IS NULL OR NULLIF(LTRIM(RTRIM(CAST(t.[TeamName] AS NVARCHAR(MAX)))), '') IS NULL);

-- Category: Uniqueness | Severity: Critical
-- Question: Are there duplicate TeamID values present in dbo.Team?
SELECT COUNT_BIG(*) AS issue_count FROM (SELECT [TeamID] FROM [dbo].[Team] WHERE [TeamID] IS NOT NULL GROUP BY [TeamID] HAVING COUNT_BIG(*) > 1) AS duplicate_keys;

-- Category: Completeness | Severity: Critical
-- Question: Are there records in dbo.TeamSeason with missing values in mandatory column TeamID?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[TeamSeason] AS t WHERE t.[TeamID] IS NULL;

-- Category: Completeness | Severity: Critical
-- Question: Are there records in dbo.TeamSeason with missing values in mandatory column Season?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[TeamSeason] AS t WHERE t.[Season] IS NULL;

-- Category: Uniqueness | Severity: Critical
-- Question: Are there duplicate Season, TeamID values present in dbo.TeamSeason?
SELECT COUNT_BIG(*) AS issue_count FROM (SELECT [Season], [TeamID] FROM [dbo].[TeamSeason] WHERE [Season] IS NOT NULL AND [TeamID] IS NOT NULL GROUP BY [Season], [TeamID] HAVING COUNT_BIG(*) > 1) AS duplicate_keys;

-- Category: Referential Integrity | Severity: Critical
-- Question: Are there records in dbo.TeamSeason that reference missing parent records in dbo.Team?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[TeamSeason] AS c LEFT JOIN [dbo].[Team] AS p ON c.[TeamID] = p.[TeamID] WHERE c.[TeamID] IS NOT NULL AND p.[TeamID] IS NULL;

-- Category: Completeness | Severity: Critical
-- Question: Are there records in dbo.sysdiagrams with missing values in mandatory column name?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[sysdiagrams] AS t WHERE (t.[name] IS NULL OR NULLIF(LTRIM(RTRIM(CAST(t.[name] AS NVARCHAR(MAX)))), '') IS NULL);

-- Category: Completeness | Severity: Critical
-- Question: Are there records in dbo.sysdiagrams with missing values in mandatory column principal_id?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[sysdiagrams] AS t WHERE t.[principal_id] IS NULL;

-- Category: Completeness | Severity: Critical
-- Question: Are there records in dbo.sysdiagrams with missing values in mandatory column diagram_id?
SELECT COUNT_BIG(*) AS issue_count FROM [dbo].[sysdiagrams] AS t WHERE t.[diagram_id] IS NULL;

-- Category: Uniqueness | Severity: Critical
-- Question: Are there duplicate diagram_id values present in dbo.sysdiagrams?
SELECT COUNT_BIG(*) AS issue_count FROM (SELECT [diagram_id] FROM [dbo].[sysdiagrams] WHERE [diagram_id] IS NOT NULL GROUP BY [diagram_id] HAVING COUNT_BIG(*) > 1) AS duplicate_keys;

-- Category: Validity | Severity: High
-- Question: Are there any records in dbo.BallbyBallActivity where 'Runs' is a negative value?
SELECT COUNT(*) AS issue_count FROM dbo.BallbyBallActivity WHERE Runs < 0;

-- Category: Validity | Severity: High
-- Question: Are there any records in dbo.BallbyBallActivity where 'OverNo' or 'BallNO' are zero or negative?
SELECT COUNT(*) AS issue_count FROM dbo.BallbyBallActivity WHERE OverNo <= 0 OR BallNO <= 0;

-- Category: Consistency | Severity: High
-- Question: Are there any records in dbo.BallbyBallActivity where 'DismissedPlayerID' is populated but 'DismissalTypeID' is NULL, or vice-versa?
SELECT COUNT(*) AS issue_count FROM dbo.BallbyBallActivity WHERE (DismissedPlayerID IS NOT NULL AND DismissalTypeID IS NULL) OR (DismissedPlayerID IS NULL AND DismissalTypeID IS NOT NULL);

-- Category: Consistency | Severity: High
-- Question: Are there any records in dbo.BallbyBallActivity where the 'BatsmanID' is the same as the 'BowlerID'?
SELECT COUNT(*) AS issue_count FROM dbo.BallbyBallActivity WHERE BatsmanID = BowlerID;

-- Category: Business Rule Conformance | Severity: High
-- Question: Are there any records in dbo.BallbyBallActivity where the 'BatsmanID' and 'NonStrikerID' belong to different teams for the same match and inning?
SELECT COUNT(*) AS issue_count FROM dbo.BallbyBallActivity bba JOIN dbo.InningScoreCard isc ON bba.MatchID = isc.MatchID AND bba.inningID = isc.InningID JOIN dbo.PlayerSeason ps_batsman ON bba.BatsmanID = ps_batsman.PlayerID AND isc.MatchID IN (SELECT MatchID FROM dbo.Match WHERE Season = ps_batsman.Season) JOIN dbo.PlayerSeason ps_nonstriker ON bba.NonStrikerID = ps_nonstriker.PlayerID AND isc.MatchID IN (SELECT MatchID FROM dbo.Match WHERE Season = ps_nonstriker.Season) WHERE ps_batsman.TeamID <> ps_nonstriker.TeamID;

-- Category: Business Rule Conformance | Severity: High
-- Question: Are there any records in dbo.BallbyBallActivity where the 'BowlerID' belongs to the batting team for that match and inning?
SELECT COUNT(*) AS issue_count FROM dbo.BallbyBallActivity bba JOIN dbo.InningScoreCard isc ON bba.MatchID = isc.MatchID AND bba.inningID = isc.InningID JOIN dbo.Match m ON bba.MatchID = m.MatchID JOIN dbo.PlayerSeason ps_bowler ON bba.BowlerID = ps_bowler.PlayerID AND m.Season = ps_bowler.Season WHERE ps_bowler.TeamID = isc.BattingTeamID;

-- Category: Cross-Table Reconciliation | Severity: High
-- Question: Does the 'Runs' in dbo.BattingScoreCard reconcile with the sum of 'Runs' scored by the 'BatsmanID' in dbo.BallbyBallActivity for the corresponding inning?
SELECT COUNT(*) AS issue_count FROM dbo.BattingScoreCard bsc JOIN ( SELECT MatchID, InningID, BatsmanID, SUM(Runs) AS CalculatedRuns FROM dbo.BallbyBallActivity GROUP BY MatchID, InningID, BatsmanID ) bba_runs ON bsc.MatchID = bba_runs.MatchID AND bsc.InningID = bba_runs.InningID AND bsc.BatsmanID = bba_runs.BatsmanID WHERE bsc.Runs IS NOT NULL AND bsc.Runs <> bba_runs.CalculatedRuns;

-- Category: Cross-Table Reconciliation | Severity: High
-- Question: Does the 'Balls' faced in dbo.BattingScoreCard reconcile with the count of balls faced by the 'BatsmanID' in dbo.BallbyBallActivity for the corresponding inning?
SELECT COUNT(*) AS issue_count FROM dbo.BattingScoreCard bsc JOIN ( SELECT MatchID, InningID, BatsmanID, COUNT(*) AS CalculatedBalls FROM dbo.BallbyBallActivity bba JOIN dbo.ScoringType st ON bba.ScoringTypeID = st.ScoringTypeID WHERE st.ScoringType NOT IN ('Wide', 'No Ball') GROUP BY MatchID, InningID, BatsmanID ) bba_balls ON bsc.MatchID = bba_balls.MatchID AND bsc.InningID = bba_balls.InningID AND bsc.BatsmanID = bba_balls.BatsmanID WHERE bsc.Balls IS NOT NULL AND bsc.Balls <> bba_balls.CalculatedBalls;

-- Category: Cross-Table Reconciliation | Severity: High
-- Question: Does the 'RunsGiven' in dbo.BowlingScoreCard reconcile with the sum of 'Runs' conceded by the 'bowlerID' in dbo.BallbyBallActivity for the corresponding inning?
SELECT COUNT(*) AS issue_count FROM dbo.BowlingScoreCard bosc JOIN ( SELECT MatchID, InningID, BowlerID, SUM(Runs) AS CalculatedRunsGiven FROM dbo.BallbyBallActivity GROUP BY MatchID, InningID, BowlerID ) bba_runs_given ON bosc.MatchID = bba_runs_given.MatchID AND bosc.InningID = bba_runs_given.InningID AND bosc.bowlerID = bba_runs_given.BowlerID WHERE bosc.RunsGiven IS NOT NULL AND bosc.RunsGiven <> bba_runs_given.CalculatedRunsGiven;

-- Category: Cross-Table Reconciliation | Severity: High
-- Question: Does the 'WicketsTaken' in dbo.BowlingScoreCard reconcile with the count of wickets taken by the 'bowlerID' in dbo.BallbyBallActivity for the corresponding inning, considering 'BowlersWicket' type?
SELECT COUNT(*) AS issue_count FROM dbo.BowlingScoreCard bosc JOIN ( SELECT bba.MatchID, bba.inningID, bba.BowlerID, COUNT(DISTINCT bba.DismissedPlayerID) AS CalculatedWicketsTaken FROM dbo.BallbyBallActivity bba JOIN dbo.DismissalType dt ON bba.DismissalTypeID = dt.DismissalTypeID WHERE dt.IsDismissal = 1 AND dt.BowlersWicket = 1 GROUP BY bba.MatchID, bba.inningID, bba.BowlerID ) bba_wickets_taken ON bosc.MatchID = bba_wickets_taken.MatchID AND bosc.InningID = bba_wickets_taken.inningID AND bosc.bowlerID = bba_wickets_taken.BowlerID WHERE bosc.WicketsTaken IS NOT NULL AND bosc.WicketsTaken <> bba_wickets_taken.CalculatedWicketsTaken;

-- Category: Consistency | Severity: High
-- Question: Are there any records in dbo.InningScoreCard where 'BattingTeamID' is the same as 'BowlingTeamID'?
SELECT COUNT(*) AS issue_count FROM dbo.InningScoreCard WHERE BattingTeamID = BowlingTeamID;

-- Category: Consistency | Severity: High
-- Question: Are there any records in dbo.Match where 'Team1ID' is the same as 'Team2ID'?
SELECT COUNT(*) AS issue_count FROM dbo.Match WHERE Team1ID = Team2ID;

-- Category: Consistency | Severity: High
-- Question: Are there any records in dbo.Match where 'TossWinningTeamID' is neither 'Team1ID' nor 'Team2ID'?
SELECT COUNT(*) AS issue_count FROM dbo.Match WHERE TossWinningTeamID NOT IN (Team1ID, Team2ID);

-- Category: Temporal Consistency | Severity: High
-- Question: Are there any records in dbo.Match where 'MatchDate' is in the future?
SELECT COUNT(*) AS issue_count FROM dbo.Match WHERE MatchDate > GETDATE();

-- Category: Temporal Consistency | Severity: High
-- Question: Are there any records in dbo.Match where the 'Season' does not match the year of the 'MatchDate'?
SELECT COUNT(*) AS issue_count FROM dbo.Match WHERE Season IS NOT NULL AND Season <> YEAR(MatchDate);

-- Category: Cross-Table Reconciliation | Severity: High
-- Question: Does the 'Runs' in dbo.MatchResult for a team reconcile with the 'Score' from dbo.InningScoreCard for that team's innings in the corresponding match?
SELECT COUNT(*) AS issue_count FROM dbo.MatchResult mr JOIN dbo.Match m ON mr.MatchID = m.MatchID JOIN dbo.InningScoreCard isc ON mr.MatchID = isc.MatchID AND ( (mr.TeamID = m.Team1ID AND isc.BattingTeamID = m.Team1ID) OR (mr.TeamID = m.Team2ID AND isc.BattingTeamID = m.Team2ID) ) WHERE mr.Runs IS NOT NULL AND isc.Score IS NOT NULL AND mr.Runs <> isc.Score;

-- Category: Consistency | Severity: Medium
-- Question: Are there any records in dbo.DismissalType where 'IsDismissal' is 1 but 'DismissalType' clearly indicates a non-dismissal event (e.g., 'Not Out', 'Retired Hurt' if not considered a dismissal)?
SELECT COUNT(*) AS issue_count FROM dbo.DismissalType WHERE IsDismissal = 1 AND DismissalType IN ('Not Out', 'Retired Hurt');

-- Category: Consistency | Severity: Medium
-- Question: Are there any records in dbo.DismissalType where 'BowlersWicket' is 1 but 'DismissalType' is not typically credited to a bowler (e.g., 'Run Out', 'Stumped' without bowler credit, 'Retired Hurt')?
SELECT COUNT(*) AS issue_count FROM dbo.DismissalType WHERE BowlersWicket = 1 AND DismissalType IN ('Run Out', 'Retired Hurt');

-- Category: Business Rule Conformance | Severity: Medium
-- Question: Is the 'PlayerOfMatchID' in dbo.Match a player who actually participated in that match (i.e., present in dbo.BattingScoreCard or dbo.BowlingScoreCard for that match)?
SELECT COUNT(*) AS issue_count FROM dbo.Match m WHERE m.PlayerOfMatchID IS NOT NULL AND NOT EXISTS ( SELECT 1 FROM dbo.BattingScoreCard bsc WHERE bsc.MatchID = m.MatchID AND bsc.BatsmanID = m.PlayerOfMatchID UNION ALL SELECT 1 FROM dbo.BowlingScoreCard bosc WHERE bosc.MatchID = m.MatchID AND bosc.bowlerID = m.PlayerOfMatchID );

-- Category: Validity | Severity: Medium
-- Question: Are there any records in dbo.MatchResult where 'Result' contains unexpected or inconsistent values (e.g., not 'Win', 'Loss', 'Draw', 'Tie', 'No Result')?
SELECT COUNT(*) AS issue_count FROM dbo.MatchResult WHERE Result NOT IN ('Win', 'Loss', 'Draw', 'Tie', 'No Result', 'Abandoned', 'Forfeit');

-- Category: Business Rule Conformance | Severity: Medium
-- Question: Are there any players listed in dbo.BallbyBallActivity for a match who are not registered in dbo.PlayerSeason for one of the participating teams in that match's season?
SELECT COUNT(DISTINCT bba.PlayerID) AS issue_count FROM ( SELECT MatchID, BatsmanID AS PlayerID, inningID FROM dbo.BallbyBallActivity UNION ALL SELECT MatchID, BowlerID AS PlayerID, inningID FROM dbo.BallbyBallActivity UNION ALL SELECT MatchID, NonStrikerID AS PlayerID, inningID FROM dbo.BallbyBallActivity UNION ALL SELECT MatchID, DismissedPlayerID AS PlayerID, inningID FROM dbo.BallbyBallActivity WHERE DismissedPlayerID IS NOT NULL UNION ALL SELECT MatchID, FielderID AS PlayerID, inningID FROM dbo.BallbyBallActivity WHERE FielderID IS NOT NULL ) bba JOIN dbo.Match m ON bba.MatchID = m.MatchID LEFT JOIN dbo.PlayerSeason ps ON bba.PlayerID = ps.PlayerID AND m.Season = ps.Season LEFT JOIN dbo.TeamSeason ts1 ON m.Team1ID = ts1.TeamID AND m.Season = ts1.Season LEFT JOIN dbo.TeamSeason ts2 ON m.Team2ID = ts2.TeamID AND m.Season = ts2.Season WHERE ps.PlayerID IS NULL OR (ps.TeamID <> m.Team1ID AND ps.TeamID <> m.Team2ID);

-- Category: Uniqueness | Severity: Medium
-- Question: Are there duplicate principal_id, name values present in dbo.sysdiagrams?
SELECT COUNT_BIG(*) AS issue_count FROM (SELECT [principal_id], [name] FROM [dbo].[sysdiagrams] WHERE [principal_id] IS NOT NULL AND [name] IS NOT NULL GROUP BY [principal_id], [name] HAVING COUNT_BIG(*) > 1) AS duplicate_keys;
