# Slack Setbot

This repository is unaffiliated with Set or PlayMonster Group.

This Slack bot is built to record [daily Set](https://www.setgame.com/set/puzzle)
scores, to allow for Slack-wide competition.

## Configuration
A docker file is provided. Any non-docker setup will need to just follow the
steps from `Dockerfile` modified to your local environment.

Configuration for the app is done via ENV vars.

Required config for Slack connectivity
```
SLACK_VERIFICATION_TOKEN
SLACK_TEAM_ID
```

Optional config
```
DATABASE_URL
```
The database config defaults to a a SQLite3 file. Repo has only been tested with
SQLite3.

### Slack setup
Once you have the server up and running, a Slack app will need to be configured
and aimed at your server. There is currently no publicly available Slack app
built for this.

## Usage

Our Slack app is configured with the keyword `/set`, but this is an ambiguous
keyword, so you might pick something different. However, it will be used for
examples.

Commands are issued into Slack with `/set <command> <params>`

| Command        | Params                                  | ?                                                                                                                             |
| ---            | ---                                     | ---                                                                                                                           |
| help           | -                                       | List of commands                                                                                                              |
| score          | `1 hours 59 minutes and 59.999 seconds` | Records the score, should be the format copied direct from the results page, wrapped in backticks                             |
| past_scores    | -                                       | Lists all of your own previous scores, in chronological order.                                                                |
| compare_scores | slack_username, <today|best>            | Compare your best and/or recent scores to another named user. Just in case you are competitive.                               |
| today          | -                                       | All of the scores for today, ranked by speed.                                                                                 |
| my_best        | -                                       | Your personal top 5 scores.                                                                                                   |
| top10          | -                                       | The top 10 scores of all time.                                                                                                |
| leaderboard    | -                                       | The top 10 users of all time, ranked by their single best score.                                                              |
| overview       | slack_username(optional)                | The first, latest, best, and worst times for a given user (or self by default)                                                |
