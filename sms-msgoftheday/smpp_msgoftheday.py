#!/usr/bin/env python2
import logging
import sys
import time

import smpplib.gsm
import smpplib.client
import smpplib.consts

# SMPP Client
CLIENT_IP = '127.0.0.1'
CLIENT_PORT = '2775'

# Auth for SMPP Client
SYSTEM_ID = 'CENSORED'
PASSWORD = 'What is the password? Is it Password!? Damn... '

#functional number of your service
_MYSERVICE='8888'

# Debug Logging
logging.basicConfig(filename='MSG_OF_THE_DAY.log',level='DEBUG')

# Printed when the sms queue is empty. Motivation to participate.
DEFAULT_MSG = 'Welcome to Troopers17! Make the World a Safer Place!'

MSG_FILE = 'todays_messages.txt'

# Connection obj.
client = None

# messages from file
messages = []

def handle_incoming_sms(pdu):
    sms = pdu.short_message         # for logging
    t_stamp = time.strftime('%c')   # for logging

    # Current time (hour only)
    c_time = time.localtime()[3]
    msg = None
    for m in messages:
        if c_time >= m[0] and c_time <= m[1]:
            msg = m[2]

    if msg:
        logging.debug("SMS from {0!s} to {1!s} at {2!s} received: {3!s}".format(\
            pdu.source_addr, pdu.destination_addr, t_stamp, msg))
        send_message(_MYSERVICE, pdu.source_addr, msg)
    else:
        logging.debug("SMS from {0!s} to {1!s} at {2!s} received: {3!s}".format(\
            pdu.source_addr, pdu.destination_addr, t_stamp, DEFAULT_MSG))
        send_message(_MYSERVICE, pdu.source_addr, DEFAULT_MSG)

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

def main():
    global client, messages

    f = open(MSG_FILE)
    logging.info('Opened file: {0!s}'.format(MSG_FILE))
    for l in f:
        line = l.rstrip()
        splitted = line.split('|')
        time_range = splitted[0].split('-')
        one_line = [int(time_range[0]), int(time_range[1]), splitted[1]]
        messages.append(one_line)
    logging.info('file read and parsed')

    client = smpplib.client.Client(CLIENT_IP, CLIENT_PORT)

    # Print Output and Start Handler
    client.set_message_sent_handler(
        lambda pdu: logging.info('sent {} {}\n'.format(pdu.sequence, pdu.message_id)))
    client.set_message_received_handler(handle_incoming_sms)

    client.connect()


    while True:
        try:
            client.bind_transceiver(system_id=SYSTEM_ID, password=PASSWORD)
            print("MSGOFTHEDAY: Successfully bound SMPP")
            client.listen()
            logging.error('listend failed')
            break
        except KeyboardInterrupt:
            break
        except AttributeError:
            logging.error('Bind failed starting again.')
            continue
        except Exception as e:
            logging.exception('Error during listen' + str(e))

if __name__ == "__main__":
    main()
