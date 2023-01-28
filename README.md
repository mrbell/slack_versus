# Slack Versus

A Slack app for logging gameplay results and keeping leaderboards.

Different games can be tracked using the app in different channels. A game logged in `#ping-pong` will not affect rankings on the `#chess` leaderboard.

Rankings are based on the Elo rating system.

Usage:
- `/versus init` - Create a leaderboard in the current channel to accept other command below 
- `/versus @mike loss` - Logs a loss against user `@mike`
- `/versus @scott win` - Logs a win against user `@scott`
- `/versus leaderboard` - Displays standings for all players
- `/versus record` - Displays user record
- `/versus @mike record` - Displays record against user `@mike`
- `/versus @mike undo` - Undoes the last game logged against user `@mike`

Records are kept separately for different channels in which the app is used, so make sure to issue the commands in the appropriate channel.

TODOs:
- Mock some interfaces to Dynamo and stuff
- Write remaining functions
- Create tests
- Create app
- Create DB tables
- Deploy app
- Test
