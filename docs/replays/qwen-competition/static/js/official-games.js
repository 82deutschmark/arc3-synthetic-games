/*
Author: Claude Opus 5.5 (Main thread)
Date: 17-October-2026
PURPOSE: The 25 official ARC-AGI-3 public games, by game-id prefix, so a run page can show only those (Son 17-Oct: a
  Score Climb run mixes them with 25 copycats, and generated-level runs with 70 training games). Same list as
  the official games in static/games/manifest.json, without the version hashes.
SRP/DRY check: Pass - one list and one test.
*/
export const OFFICIAL_GAME_PREFIXES = new Set([
  "ar25", "bp35", "cd82", "cn04", "dc22", "ft09", "g50t", "ka59", "lf52", "lp85", "ls20", "m0r0", "r11l",
  "re86", "s5i5", "sb26", "sc25", "sk48", "sp80", "su15", "tn36", "tr87", "tu93", "vc33", "wa30",
]);

// "ar25", "ar25-0c556536" and "ar25-v1" are official; "ar25p0-v1" (a generated version) and copycat ids are not.
export const isOfficialGame = (gameId) =>
  OFFICIAL_GAME_PREFIXES.has(String(gameId || "").split("-")[0].trim().toLowerCase());
