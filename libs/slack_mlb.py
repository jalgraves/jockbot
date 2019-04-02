import datetime
import logging
import json

from jockbot_mlb import MLB
from jockbot_mlb import MLBTeam

from utils.helpers import get_config
from utils.exceptions import MLBException


class SlackMLB:
    """
    Create a Slack response object`
    """
    def __init__(self, args, option=None, team=None, player=None):
        self.args = args
        self.option = option
        self.team = team
        self.player = player
        self.config = get_config('mlb.json')
        self.emojis = self.config['emojis']
        self.mlb = MLB()

    @property
    def reply(self):
        """
        Return Slack formatted message reply
        """
        options = {
            'scores': self.mlb_scores_reply,
            'schedule': self.mlb_schedule_reply,
            'stats': self.mlb_stats_reply,
            'standings': self.mlb_standings
        }
        option = options.get(self.option)
        response = option()
        return response

    def mlb_scores_reply(self):
        if not self.team:
            reply = self._league_scores()
        else:
            reply = self._team_scores()
        return reply

    def mlb_schedule_reply(self):
        if not self.team:
            reply = self._league_schedule()
        else:
            reply = self._team_schedule()
        return reply

    def mlb_stats_reply(self):
        if not self.team and not self.player:
            err_message = [
                'Missing player or team to retrieve stats for:',
                'To get MLB team stats run command like this for example',
                'jalbot sports stats -l mlb -t boston',
                'Or for player stats run like this',
                'jalbot sports stats -l mlb -p brad marchand'
            ]
            raise MLBException("\n".join(err_message))
        if self.team:
            reply = self.mlb_team_stats()
        elif self.player:
            reply = self.mlb_player_stats()
        return reply

    def _team_schedule(self, title=True, limit=None, type=None):
        """Format slack reply"""
        team = MLBTeam(self.team)
        games = team.remaining_games
        num_games = self.args.get('games')
        emoji = self.emojis.get(str(team.name))
        if limit:
            games = games[:limit]
        elif num_games:
            games = games[:int(num_games)]
        if not title:
            reply = []
        else:
            reply = [f":{emoji}: *Scheduled Games*"]
        for game in games:
            reply.append(self._scheduled_game_reply(game, date=True, records=False))
        return "\n".join(reply)

    def _league_schedule(self, title=True, limit=None, type=None):
        """Format slack reply"""
        mlb = MLB()
        games = mlb.todays_games
        reply = [f":mlb: *Scheduled Games*"]
        for game in games:
            reply.append(self._scheduled_game_reply(game))
        return "\n".join(reply)

    def _team_scores(self, title=True, limit=None, type=None):
        """Format slack reply"""
        team = MLBTeam(self.team)
        games = team.played_games
        num_games = self.args.get('games')
        emoji = self.emojis.get(str(team.name))
        if limit:
            games = games[:limit]
        elif num_games:
            games = games[:int(num_games)]
        if not title:
            reply = []
        else:
            reply = [f":{emoji}: *Scores*"]
        for game in games:
            reply.append(self._game_final_reply(game, date=True))
        return "\n".join(reply)

    def _league_scores(self):
        mlb = MLB()
        games = mlb.todays_games
        if not games:
            return f":mlb: *_No Scores Today*_"
        game_date = self._format_date(games[0]['date'])
        reply = [f":mlb: *{game_date}*"]

        live_games = [x for x in games if x['state'] == 'Live']
        if live_games:
            live_games_reply = [f":mlb: *Live*"]
            for game in live_games:
                live_games_reply.append(self._live_game_reply(game))
            reply.append("\n".join(live_games_reply))

        final_games = [x for x in games if x['state'] == 'Final']
        if final_games:
            final_games_reply = [f":mlb: *Final*"]
            for game in final_games:
                final_games_reply.append(self._game_final_reply(game))
            reply.append("\n".join(final_games_reply))

        scheduled_games = [x for x in games if x['state'] == 'Preview']
        if scheduled_games:
            scheduled_games_reply = [f":mlb: *Scheduled*"]
            for game in scheduled_games:
                scheduled_games_reply.append(self._scheduled_game_reply(game))
            reply.append("\n".join(scheduled_games_reply))
        return "\n".join(reply)

    def _get_at_bat(self, linescore):
        """Get the pitcher, hitter, hitter's count, outs, and base runners"""
        pitcher = linescore['defense']['pitcher']['fullName']
        batter = linescore['offense']['batter']['fullName']
        outs = linescore['outs']
        balls = linescore['balls']
        strikes = linescore['strikes']
        if outs > 0:
            outs = f"*Outs* {':out:' * outs}"
        else:
            outs = "*Outs* :no_count:"
        if balls > 0:
            balls = f"*Balls* {':ball:' * balls}"
        else:
            balls = "*Balls* :no_count:"
        if strikes > 0:
            strikes = f"*Strikes* {':strike:' * strikes}"
        else:
            strikes = "*Strikes* :no_count:"
        count = [
            f">*P*: *`{pitcher}`* *AB*: *`{batter}`*",
            f">{balls} {strikes} {outs}",
            self._get_base_runners(linescore)
        ]
        return "\n".join(count)

    def _get_base_runners(self, linescore):
        bases = [f">*Bases*"]
        first = linescore['offense'].get('first')
        second = linescore['offense'].get('second')
        third = linescore['offense'].get('third')
        if first:
            bases.append(":green_dot:")
        else:
            bases.append(":no_count:")
        if second:
            bases.append(":green_dot:")
        else:
            bases.append(":no_count:")
        if third:
            bases.append(":green_dot:")
        else:
            bases.append(":no_count:")
        return "".join(bases)

    def _live_game_reply(self, game):
        inning = game['linescore']['currentInningOrdinal']
        inning_state = game['linescore']['inningState']
        away_team = self.emojis.get(game['away_team'])
        home_team = self.emojis.get(game['home_team'])
        away_stats = game['linescore']['teams']['away']
        home_stats = game['linescore']['teams']['home']

        if 'Delayed' in game['detailed_state']:
            game_info = f"*{inning_state} of the {inning} {game['detailed_state']}*\n"
        else:
            game_info = f"*{inning_state} of the {inning}*"
        if inning_state != 'Middle' and inning_state != 'End':
            reply = [
                game_info,
                f">:{away_team}: *`{away_stats['runs']}` `{away_stats['hits']}` `{away_stats['errors']}`*",
                f">:{home_team}: *`{home_stats['runs']}` `{home_stats['hits']}` `{home_stats['errors']}`*\n>",
                self._get_at_bat(game['linescore'])
            ]
        else:
            reply = [
                game_info,
                f">:{away_team}: *`{away_stats['runs']}` `{away_stats['hits']}` `{away_stats['errors']}`*",
                f">:{home_team}: *`{home_stats['runs']}` `{home_stats['hits']}` `{home_stats['errors']}`*\n"
            ]
        return "\n".join(reply)

    def _scheduled_game_reply(self, game, date=False, records=True):
        away_team = self.emojis.get(game['away_team'])
        home_team = self.emojis.get(game['home_team'])
        away_record = game['away_team_record']
        home_record = game['home_team_record']

        if 'Delayed' in game['detailed_state']:
            game_info = f"*{game['detailed_state']}*\n"
        else:
            if date:
                game_info = f">*{self._format_date(game['date'], day_name=False)}* "
            else:
                game_time = game['start_time']
                if len(game_time) == 4:
                    game_info = f">*{game_time}*   "
                else:
                    game_info = f">*{game_time}* "

        if records:
            reply = [
                game_info,
                f":{away_team}: *`{away_record['wins']}`–`{away_record['losses']}`  @*  ",
                f":{home_team}: *`{home_record['wins']}`–`{home_record['losses']}`*",
            ]
        else:
            reply = [
                game_info,
                f":{away_team}:  *@*  :{home_team}:"
            ]

        return "".join(reply)

    def _game_final_reply(self, game, date=False):
        away_team = self.emojis.get(game['away_team'])
        home_team = self.emojis.get(game['home_team'])
        away_record = game['away_team_record']
        home_record = game['home_team_record']
        game_date = self._format_date(game['date'], day_name=False)

        if game['detailed_state'] == 'Postponed':
            if date:
                title = f"*{game_date} Postponed*"
            else:
                title = "*Postponed*"
            reply = [
                title,
                f">:{away_team}: *`{away_record['wins']}`–`{away_record['losses']}`*",
                f">:{home_team}: *`{home_record['wins']}`–`{home_record['losses']}`*\n"
            ]
        else:
            away_stats = game['linescore']['teams']['away']
            home_stats = game['linescore']['teams']['home']
            if date:
                reply = [
                    f"*{game_date}*",
                    f">:{away_team}: *`{away_stats['runs']}` `{away_stats['hits']}` `{away_stats['errors']}`*",
                    f">:{home_team}: *`{home_stats['runs']}` `{home_stats['hits']}` `{home_stats['errors']}`*\n"
                ]
            else:
                reply = [
                    f">:{away_team}: *`{away_stats['runs']}` `{away_stats['hits']}` `{away_stats['errors']}`*",
                    f">:{home_team}: *`{home_stats['runs']}` `{home_stats['hits']}` `{home_stats['errors']}`*\n"
                ]

        return "\n".join(reply)

    def mlb_standings(self):
        division = self.args.get('division')
        conference = self.args.get('conference')
        if not division and not conference:
            return self.mlb_league_standings()
        elif conference:
            return self.mlb_conference_standings()
        elif division:
            return self.mlb_division_standings()

    def mlb_division_standings(self):
        standings = self.mlb.standings['division']
        records = self.mlb.standings['records']
        reply = []
        division_emojis = {
            'Metropolitan': 'mlb_met',
            'Atlantic': 'mlb_atl',
            'Central': 'mlb_cen',
            'Pacific': 'mlb_pac'
        }
        for division, teams in standings.items():
            div_emoji = division_emojis.get(division)
            standings = [f":{div_emoji}: *{division} Division*"]
            sorted_teams = sorted(teams.items(), key=lambda k: int(k[1]))
            for team in sorted_teams:
                name, rank = team
                emoji = self.emojis.get(self.get_team_id(name))
                record = records.get(name)
                if len(rank) == 1:
                    standings.append(f">*{rank}  :{emoji}:  `{record}`*")
                else:
                    standings.append(f">*{rank} :{emoji}:  `{record}`*")
            reply.append("\n".join(standings))
        return "\n".join(reply)

    def mlb_conference_standings(self):
        """
        Build and return Slack formatted reply for MLB conference standings
        """
        conference_standings = self.mlb.standings['conference']
        records = self.mlb.standings['records']
        reply = []
        for conference, teams in conference_standings.items():
            if conference == 'Eastern':
                conf_emoji = 'mlb_east'
            else:
                conf_emoji = 'mlb_west'
            standings = [f":{conf_emoji}: *{conference} Conference Standings*"]
            sorted_teams = sorted(teams.items(), key=lambda k: int(k[1]))
            for team in sorted_teams:
                name, rank = team
                emoji = self.emojis.get(self.get_team_id(name))
                record = records.get(name)
                if len(rank) == 1:
                    standings.append(f">*{rank}  :{emoji}:  `{record}`*")
                else:
                    standings.append(f">*{rank} :{emoji}:  `{record}`*")
            reply.append("\n".join(standings))
        return "\n".join(reply)

    def mlb_league_standings(self):
        standings = self.mlb.standings['league']
        records = self.mlb.standings['records']
        reply = [f":mlb: *Current League Standings*"]
        sorted_standings = sorted(standings.items(), key=lambda k: int(k[1]))
        for team in sorted_standings:
            name, rank = team
            emoji = self.emojis.get(self.get_team_id(name))
            record = records.get(name)
            if len(rank) == 1:
                reply.append(f">*{rank}  :{emoji}:  `{record}`*")
            else:
                reply.append(f">*{rank} :{emoji}:  `{record}`*")
        return "\n".join(reply)

    def get_team_id(self, team):
        team_ids = self.config['teams']
        team_id = team_ids.get(team.lower())
        return str(team_id)

    def _format_date(self, date, day_name=True):
        """
        Format date from API into Month Day
        """
        if 'T' in date:
            date, game_time = date.split('T')
        game_date = datetime.datetime.strptime(date, "%Y-%m-%d")
        day = game_date.strftime("%d")
        if day.startswith('0'):
            day = day[1:]
        if not day_name:
            formatted_date = game_date.strftime(f"%B {day}")
        else:
            formatted_date = game_date.strftime(f"%A, %B {day}")
        return formatted_date
