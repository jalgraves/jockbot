import logging
import os
import time

from libs import slack

from utils.helpers import setup_logger


class JockBot(object):
    """
    Create slackbot object
    """
    def __init__(self, slack_token):
        """
        Initialize JockBot

        :param slack_token: Slack API token
        """
        self.slack_token = slack_token
        self.slack = slack.Slack(self.slack_token)

    def slackbot(self, *args, **kwargs):
        """
        Run JockBot as daemon for live interaction through Slack
        """
        while True:
            self.slack.api_connect()

def main():
    """Main function run when called from command line"""
    setup_logger()
    token = os.environ.get('JAL_SLACK_TOKEN')
    jockbot = JockBot(token)
    logging.info('Starting JockBot')
    output = jockbot.slackbot()
    if output:
        print(output)


if __name__ == '__main__':
    main()
