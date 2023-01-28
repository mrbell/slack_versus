import boto3
from boto3.dynamodb.conditions import Key, Attr
import json
import logging
import os
import requests
from datetime import datetime, timedelta
from datetime import time as dt_time
from zappa.asynchronous import task
from traceback import format_exc
import time
from flask import abort, Flask, jsonify, request
from elo import Elo


VERSION = '1.0.0'

help_text = "Use this command to log games and check leaderboards in a channel."
help_attachment_text = (
    "Use `/versus [subcommand] [option]` with one of the following subcommands:\n"
    "\t -`/versus init` to enable game logging/leaderboards in the current channel \n" + 
    "\t -`/versus @mike loss` to log a loss against user @mike \n" + 
    "\t -`/versus @scott win` to log a win against user @scott \n" + 
    "\t -`/versus @mike undo` to undo the last game logged against user @mike \n" + 
    "\t -`/versus record` to view your overall record \n" + 
    "\t -`/versus @mike record` to view your record against user @mike \n" + 
    "\t -`/versus leaderboard` to view the leaderboard \n" + 
    "\t -`/versus help` to view this help message"
)

# Various tokens that we will need
logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamo = boto3.resource('dynamodb')
log_table_name = 'slack-versus-log'
log_ratings_table_name = 'slack-versus-ratings'
active_games_table_name = 'slack-versus-active-games'

webhook_url = os.environ['SLACK_WEBHOOK_URL']

elo_k_factor = 20
elo_g_factor = 1

app = Flask(__name__)


def is_request_valid(request):
    is_token_valid = request.form['token'] == os.environ['SLACK_VERIFICATION_TOKEN']
    is_team_id_valid = request.form['team_id'] == os.environ['SLACK_TEAM_ID']

    return is_token_valid and is_team_id_valid


def parse_subcommand(command_text):
    """
    Parse the subcommand from the given COMMAND_TEXT, which is everything that
    follows `/versus`.  The subcommand is the option passed to the command, e.g.
    'wfh' in the case of `/pickem wfh tomorrow`.
    """
    return command_text.strip().split()[0].lower()


def parse_options(command_text):
    """
    Parse options passed into the command, e.g. returns 'tomorrow' from the
    command `/iam wfh tomorrow`, where `iam` is the command, `wfh` is the
    subcommand, and `tomorrow` is the option passed to the subcommand.
    """
    sc = parse_subcommand(command_text)
    return command_text.replace(sc, '').strip()


def get_active_games():
    table = dynamo.Table(active_games_table_name)
    response = table.scan()
    return [item['id'] for item in response['Items']]


def create_game(id):
    if id in get_active_games():
        return False
    else:
        table = dynamo.Table(active_games_table_name)
        table.put_item(Item={'id': id})
        return True


def get_user_name(user_id):
    url = 'https://slack.com/api/users.info'
    params = {
        'token': os.environ['SLACK_ACCESS_TOKEN'],
        'user': user_id,
    }
    response = requests.get(url, params=params)
    return response.json()['user']['name']


def get_user_elo(user_id):
    pass


def get_record(user_id, other_user_id == None):
    pass


def get_leaderboard():
    pass


def log_game(user_id, other_user_id, channel_id, result):

    elo = Elo(elo_k_factor, elo_g_factor)
    
    user_elo = get_user_elo(user_id)
    other_user_elo = get_user_elo(other_user_id)

    elo.addPlayer(user_id, user_elo)
    elo.addPlayer(other_user_id, other_user_elo)

    if result == 'win':
        elo.gameOver(user_id, other_user_id)    
    else:
        elo.gameOver(other_user_id, user_id)

    table = dynamo.Table(log_table_name)
    table.put_item(
        Item={
            'id': str(int(time.time())),
            'user_id': user_id,
            'other_user_id': other_user_id,
            'channel_id': channel_id,
            'result': result,
            'timestamp': str(datetime.now()),
        }
    )

    table = dynamo.Table(log_ratings_table_name)
    table.put_item(
        Item={
            'id': str(int(time.time())),
            'user_id': user_id,
            'rating': elo.ratingDict[user_id],
            'timestamp': str(datetime.now()),
        }
    )
    table.put_item(
        Item={
            'id': str(int(time.time())),
            'user_id': other_user_id,
            'rating': elo.ratingDict[other_user_id],
            'timestamp': str(datetime.now()),
        }
    )


@app.route('/versus', methods=['POST'])
def iam():
    if not is_request_valid(request):
        abort(400)

    request_text = request.form['text']

    subcommand = parse_subcommand(request_text)
    options = parse_options(request_text)

    user_id = request.form['user_id']
    user_name = request.form['user_name']
    channel_id = request.form['channel_id']
    channel_name = request.form['channel_name']

    if subcommand == 'init':

        if create_game(channel_id):
            return jsonify(
                response_type='in_channel',
                text=f'New game created in {channel_name} by {user_name}! GLHF!'
            )
        else:
            return jsonify(
                response_type='in_channel',
                text=f'Game already exists in {channel_name}!'
            )

    elif '<@' in subcommand and options in ['win', 'loss']:

        other_user_id = subcommand.replace('<@', '').replace('>', '')
        log_game(user_id, other_user_id, channel_id, options)

        if options == 'win':
            user1 = user_name
            user2 = get_user_name(other_user_id)
        else:
            user1 = get_user_name(other_user_id)
            user2 = user_name

        return jsonify(
            response_type='in_channel',
            text=f'{user1} wins against {user2}! Congrats :tada:',
        )

    elif '<@' in subcommand and options == 'record':
        other_user_id = subcommand.replace('<@', '').replace('>', '')
        other_user_name = get_user_name(other_user_id)
        wins, losses = get_record(user_id, other_user_id)
        return jsonify(
            response_type='ephemeral',
            text=f'You have {wins} wins and {losses} losses against {other_user_name}.',
        )

    elif '<@' in subcommand and options == 'undo':
        pass

    elif subcommand == 'record':
        wins, losses = get_record(user_id)
        return jsonify(
            response_type='ephemeral',
            text=f'You have {wins} wins and {losses} losses.',
        )

    elif subcommand == 'leaderboard':
        try:
            leaderboard = get_leaderboard()
            leaderboard_text = '\n'.join([f'{i+1}. {user_name} ({elo})' for i, (user_name, elo) in enumerate(leaderboard)])
        except:
            return jsonify(
                response_type='ephemeral',
                text="Oops! Something went wrong!",
                attachments=[
                    dict(text=format_exc()),
                ]
            )
            
        return jsonify(
            response_type='in_channel',
            text="Current Leaderboard:",
            attachments=[
                dict(text=leaderboard_text),
            ]
        )

    elif subcommand == 'version':
        return jsonify(
            text=VERSION
        )      
    
    elif subcommand == 'help':
        return jsonify(
            text=help_text,
            attachments=[
                dict(text=help_attachment_text),
            ]
        )

    else:
        return jsonify(
            text="Unknown subcommand!",
            attachments=[
                dict(text=help_attachment_text),
            ]
        )
