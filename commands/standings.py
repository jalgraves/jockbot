
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
        self.response = self.run_cmd()

    def run_cmd(self):
        if self.text.split()[1] == 'help':
            response = "\n".join(self.config['help'])
        else:
            self._verify_command()
            league_command = {
                'nba': SlackNBA,
                'nfl': SlackNFL,
                'nhl': SlackNHL,
                'mlb': SlackMLB
            }
            command = league_command.get(self.option)
            response = command(self.args, option='standings')
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

    def _verify_command(self):
        if not self.league and not self.option:
            raise JockBotException(f"Please specify a league to display standings for")
