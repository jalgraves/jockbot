import json
import os
import sys
import unittest
import nose

from utils.slackparse import SlackArgParse


def get_config():
    """
    Get configuration for command
    :return:
    """
    with open('utils/config/config.json', 'r') as f:
        config = json.load(f)
    if 'env' not in config.keys():
        config['env'] = None
    if config['env']:
        for env_var in config['env']:
            config[env_var] = os.environ[env_var]
        del config['env']
    return config


class JockBotTest(unittest.TestCase):

    def setUp(self):
        self.config = get_config()
        self.options = self.config['options']
        self.valid_args = self.config['valid_args']
 
    def test_option_parse(self):
        """Test text from slack is parsed correctly"""
        text = 'scores mlb'
        parsed_args = SlackArgParse(self.valid_args, self.options, text)
        option = parsed_args.option
        self.assertEqual(option, 'mlb', "Incorrect Option")

    def test_arge_parse(self):
        """Test text from slack is parsed correctly"""
        text = 'scores -t boston -l nhl'
        parsed_args = SlackArgParse(self.valid_args, self.options, text)
        args = parsed_args.args
        print(args)
        team = args.get('team')
        league = args.get('league')
        self.assertEqual(team, 'boston', "Incorrect Team")
        self.assertEqual(league, 'nhl', "Incorrect League")


if __name__ == '__main__':
    sys.path.insert(1, "/jockbot/")
    nose.main()
