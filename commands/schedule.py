
import datetime
import logging  # noqa


from libs.slack_nhl import SlackNHL
from libs.slack_nfl import SlackNFL
from libs.slack_mlb import SlackMLB
from utils.exceptions import JockBotException
from utils.helpers import get_config, try_request
from utils.slackparse import SlackArgParse


class SlackNBA:
    def __init__(self):
        pass


class BotCommand(object):
    """Create Geo object from Slack event"""
    def __init__(self, event, user):
        self.text = event['text']
        self.config = get_config('config.json')
        self.parsed_args = SlackArgParse(self.config['valid_args'], self.config['options'], event['text'].lower())
        self.args = self.parsed_args.args
        self.option = self.parsed_args.option
        self.league = self._get_league()
        self.team_name = self._get_team_name()
        self.response = self.run_cmd()

    def run_cmd(self):
        self._verify_command()
        if self.text.split()[1] == 'help':
            response = "\n".join(self.config['help'])
        elif not self.option:
            response = self._all_scores()
        else:
            league_command = {
                'nba': SlackNBA,
                'nfl': SlackNFL,
                'nhl': SlackNHL,
                'mlb': SlackMLB
            }
            command = league_command.get(self.option)
            response = command(self.args, option='schedule', team=self.team_name)
        return response.reply

    def _all_scores(self):
        """example request using try_request wrapper"""
        url = self.config['url']
        request = try_request('example', 'POST', url, data="", verify=False, timeout=10)
        return request

    def _get_league(self):
        """Get the league for the requested command"""
        league = self.args.get('league')
        return league

    def _get_team_name(self):
        """Get team name from Slack args"""
        return self.args.get('team')

    def _verify_command(self):
        if self.team_name and not self.league and not self.option:
            raise JockBotException(f"Please specify a league for {self.team_name}")

    def _format_date(self, date):
        """Format date from API into Month Day"""
        if 'T' in date:
            date, game_time = date.split('T')
        game_date = datetime.datetime.strptime(date, "%Y-%m-%d")
        day = game_date.strftime("%d")
        if day.startswith('0'):
            day = day[1:]
        formatted_date = game_date.strftime(f"%A, %B {day}")
        return formatted_date

    def _format_number(self, num):
        """Get suffix to append to number"""
        num = int(num)
        if num in [1, 21, 31]:
            suffix = 'st'
        elif num in [2, 22, 32]:
            suffix = 'nd'
        elif num in [3, 23, 33]:
            suffix = 'rd'
        else:
            suffix = 'th'

        return f"{num}{suffix}"
