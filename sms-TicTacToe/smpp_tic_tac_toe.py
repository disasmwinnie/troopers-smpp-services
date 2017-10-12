#!/usr/bin/env python2
import logging
import sys
import time
from threading import Thread, Lock
from Queue import Queue

import smpplib.gsm
import smpplib.client
import smpplib.consts

import tictactoe as t

# SMPP Client
CLIENT_IP = '127.0.0.1'
CLIENT_PORT = '2775'

# Auth for SMPP Client
SYSTEM_ID = 'CENSORED'
PASSWORD = 'What is the password? Is it Password!? Damn... '

#functional number of your service
_MYSERVICE='2024'

# Locked access to the game.
mutex = Lock()

# Debug Logging
logging.basicConfig(filename='TIC_TAC_TOE.log',level='DEBUG')

# The sleep time between messages been printed (in seconds).
BETWEEN_MSG_SLEEP = 5

# Max ammount of SMS should be queued.
SMS_QUEUE_MAX = 30

# Status Messages for the sender.
SMS_INVALID = 'Invalid SMS. You are allowed to use join/leave to enter the game \
or, in case you are playing, the coordinates X:Y, where as values from 0-2 are \
allowed.'
SMS_GAME_RUNNING = 'A game is currently running. Sorry, you have to wait :-/'
SMS_GAME_JOINED_WAIT = 'You joined the game. Try to recruit a second Trooper. \
Then we can start.'
SMS_GAME_JOINED_START = 'Excellent. Let the game begin.'
SMS_GAME = 'Congrats, you won \o/'
SMS_LOST = 'You lost :-('
SMS_WRONG_MOVE = 'This field is already taken. Try again.'
SMS_OK = 'Move {0!s}:{1!s} by player {2!s} accepted.'

# Some token to cancell the readering thread
is_running = False # TODO use it ;)

# Connection obj.
client = None

gf = None


def is_sms_valid(text=''):
    """
    Only ASCII messages with a lenth of 160 or less are allowed.
    """
    try:
        text.decode('ascii')
    except:
        return False
    if len(text) > 160:
        return False

    return True

def handle_incoming_sms(pdu):
    sms = pdu.short_message
    src = str(pdu.source_addr)
    t_stamp = time.strftime('%c')
    logging.debug("SMS from {0!s} to {1!s} at {2!s} received: {3!s}".format(\
            pdu.source_addr, pdu.destination_addr, t_stamp, sms))
    if not is_sms_valid(sms):
        send_message(_MYSERVICE, pdu.source_addr, SMS_INVALID)
        logging.error('SMS from {0!s} is invalid: {1!s}'.format(\
                pdu.source_addr, sms))
        return
    mutex.acquire()
    game_input = None
    try:
        if len(sms) == 3:
            logging.debug("incomming msg len: 3")
            x = None
            y = None
            coords = sms.split(' ')[0:2]
            try:
                x = coords[0]
                y = coords[1]
                if x > 2 or x < 0 or y > 2 or y < 0:
                    raise ValueError('Values are not allowed.')
                logging.debug("its coords are x:{0!s}, y:{1!s}".format(x,y))
                game_input = t.Input('set', src, x, y)
            except:
                send_message(_MYSERVICE, pdu.source_addr, SMS_INVALID)
        elif sms[0:4] == 'join':
            game_input = t.Input('join', src)
            logging.debug('join received.')
        elif sms[0:4] == 'exit':
            game_input = t.Input('exit', src)
            logging.debug('exit received.')
        else:
            send_message(_MYSERVICE, pdu.source_addr, SMS_INVALID)
    finally:
        # If game_input is None, then an invalid SMS was received
        if game_input:
            gf.next_move(game_input)
            logging.debug('move made')
        else:
            logging.debug('NO move made. Invalid message {0!s}'.format(sms))
        mutex.release()

def send_message(src, dest, string):
    parts, encoding_flag, msg_type_flag = smpplib.gsm.make_parts(string)

    logging.info('Sending SMS "%s" to %s' % (string, dest))
    for part in parts:
        pdu = client.send_message(
            source_addr_ton=smpplib.consts.SMPP_TON_INTL,
            source_addr_npi=smpplib.consts.SMPP_NPI_ISDN,
            source_addr=src,
            dest_addr_ton=smpplib.consts.SMPP_TON_INTL,
            dest_addr_npi=smpplib.consts.SMPP_NPI_ISDN,
            destination_addr=dest,
            short_message=part,
            data_coding=encoding_flag,
            esm_class=msg_type_flag,
            registered_delivery=False,
    )
"""
=== WEBAPP SHIT
"""
import json
from flask import Flask, render_template
from flask.ext.socketio import SocketIO, emit
from flask_assets import Environment, Bundle

app = Flask(__name__)
assets = Environment()
assets.init_app(app)
app.config['SECRET_KEY'] = 'WUUAAAA$Ahkek2933hj!' # CHANGE ME for redeployment!
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('move-event', namespace='/tictactoe')
def update_gamefields(status_msg, gamefields):
    """
    status_msg: is status message, as string
    gamefields: is a list of lists (2 dimensional list)
    """
    req = { 'status' : status_msg, 'game_f' : gamefields }
    req = json.dumps(req)
    emit('update_game', { 'data': req })

@socketio.on('player-info', namespace='/tictactoe')
def player_info(player_nfo):
    """
    status_msg: is status message, as string
    gamefields: is a list of lists (2 dimensional list)
    """
    req = { 'player_info': player_nfo }
    req = json.dumps(req)
    emit('update_players', { 'data' : req } )

@socketio.on('connect', namespace='/tictactoe')
def connect():
    gf.start_game(update_gamefields, player_info)
"""
=== WEBAPP SHIT
"""

def main():
    global client, is_running, gf
    client = smpplib.client.Client(CLIENT_IP, CLIENT_PORT)

    # Print Output and Start Handler
    client.set_message_sent_handler(
        lambda pdu: logging.info('sent {} {}\n'.format(pdu.sequence, pdu.message_id)))
    client.set_message_received_handler(handle_incoming_sms)

    client.connect()

    client.bind_transceiver(system_id=SYSTEM_ID, password=PASSWORD)
    print("TIC_TAC_TOE: Successfully bound SMPP")

    # Since bind was sucessful, we assume the show started.
    is_running = True

    th = Thread(target=client.listen)
    th.start()

    gf = t.GameFlow()
    while True:
        try:
            socketio.run(app, host='0.0.0.0', debug=False, use_reloader=False)
            break
        except KeyboardInterrupt:
            break
        except Exception as e:
            logging.exception('Error during listen' + str(e))
    is_running = False


if __name__ == "__main__":
    main()
