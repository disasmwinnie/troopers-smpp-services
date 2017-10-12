from Queue import Queue

import smpplib.gsm
import smpplib.client
import smpplib.consts

"""
======== LED STUFF ========
"""
from luma.core.serial import spi, noop
from luma.core.render import canvas
from luma.core.virtual import viewport
from luma.led_matrix.device import neopixel
from luma.core.legacy import text, show_message
from luma.core.legacy.font import proportional, LCD_FONT

LED_MAPPING = [
0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,
39,38,37,36,35,34,33,32,31,30,29,28,27,26,25,24,23,22,21,20,
40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,
79,78,77,76,75,74,73,72,71,70,69,68,67,66,65,64,63,62,61,60,
80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,
119,118,117,116,115,114,113,112,111,110,109,108,107,106,105,104,103,102,101,100,
120,121,122,123,124,125,126,127,128,129,130,131,132,133,134,135,136,137,138,139,
159,158,157,156,155,154,153,152,151,150,149,148,147,146,145,144,143,142,141,140,
160,161,162,163,164,165,166,167,168,169,170,171,172,173,174,175,176,177,178,179,
199,198,197,196,195,194,193,192,191,190,189,188,187,186,185,184,183,182,181,180,
200,201,202,203,204,205,206,207,208,209,210,211,212,213,214,215,216,217,218,219,
239,238,237,236,235,234,233,232,231,230,229,228,227,226,225,224,223,222,221,220]

device = neopixel(width=12, height=20, rotate=1, mapping=LED_MAPPING)
"""
======== LED STUFF ========
"""

# SMPP Client
CLIENT_IP = '127.0.0.1'
CLIENT_PORT = '2775'

# Auth for SMPP Client
SYSTEM_ID = 'CENSORED'
PASSWORD = 'What is the password? Is it Password!? Damn... '

#functional number of your service
_MYSERVICE='20001'

# Debug Logging
logging.basicConfig(filename='LED_WALL.log',level='DEBUG')

# The sleep time between messages been printed (in seconds).
BETWEEN_MSG_SLEEP = 8

# Printed when the sms queue is empty. Motivation to participate.
DEFAULT_MSG = 'SMS2WALL: send your text to {0!s}.'\
        .format(_MYSERVICE)

# Max ammount of SMS should be queued.
SMS_QUEUE_MAX = 30

# Status Messages for the sender.
SMS_INVALID = 'Your SMS must consist of ASCII chars/numbers only and must not exceed \
160 signs.'
SMS_QUEUE_FULL = 'SMS queue is full. Lots of people using me at the moment. We \
had to reject you message for now, Sorry :-/ Try again later in couple of \
minutes.'
SMS_OK = 'Your SMS is published on the LED WALL right now.'
SMS_QUEUED = 'Your SMS is queued for publishing. There are {0!s} messages \
before you. Waiting time until your message is shown is ~{0!s} secs.'

# Some token to cancell the readering thread
is_running = False

# SMS Queue
sms_q = Queue(maxsize=SMS_QUEUE_MAX)

# Connection obj.
client = None

def print2wall(msg=''):
    with canvas(device) as draw:
        show_message(device, msg, fill='orange', font=proportional(LCD_FONT), scroll_delay=0.12, y_offset=3)

def process_sms_queue():
    global sms_q
    while is_running:
        msg = None
        if sms_q.empty():
            msg = DEFAULT_MSG
        else:
            msg = sms_q.get()
        print2wall(msg)
        time.sleep(BETWEEN_MSG_SLEEP)

def is_sms_valid(text=''):
    """
    Only ASCII messages with a lenth of 160 or less are allowed.
    """
    try:
        text.decode('ascii')
    except:
       return False

    # The smpp lib screws ups letters like german oe.
    # Can't do shit about it. Best checks one can get.
    for c in text:
        if ord(c) > 126 or ord(c) < 32:
            return False

    if len(text) > 160:
        return False

    return True

def handle_incoming_sms(pdu):
    global sms_q
    sms = pdu.short_message
    t_stamp = time.strftime('%c')
    logging.debug("SMS from {0!s} to {1!s} at {2!s} received: {3!s}".format(\
            pdu.source_addr, pdu.destination_addr, t_stamp, sms))
    if not is_sms_valid(sms):
        send_message(_MYSERVICE, pdu.source_addr, SMS_INVALID)
        logging.error('SMS from {0!s} is invalid: {1!s}'.format(\
                pdu.source_addr, sms))
        return
    if sms_q.full():
        send_message(_MYSERVICE, pdu.source_addr, SMS_QUEUE_FULL)
        logging.error('Queue Full. SMS from {0!s} at {1!s} REJECTED.'.format(\
                pdu.source_addr, t_stamp))
        return
    sms_q.put(sms)
    # qsize() returns approximated size and it is possible get() been called in
    # other thread. Sooo... check both. This is kinda sugar, don't care if check
    # fails
    if sms_q.qsize() <= 1 or sms_q.empty():
        send_message(_MYSERVICE, pdu.source_addr, SMS_OK)
        logging.info('SMS from {0!s} is published at {1!s}'.format(\
                pdu.source_addr, t_stamp))
    else:
        send_message(_MYSERVICE, pdu.source_addr, SMS_QUEUED.format(\
                sms_q.qsize(), sms_q.qsize()*BETWEEN_MSG_SLEEP))
        logging.info('SMS from {0!s} is queued at {1!s}'.format(\
                pdu.source_addr, t_stamp))

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
    global client, is_running
    client = smpplib.client.Client(CLIENT_IP, CLIENT_PORT)

    # Print Output and Start Handler
    client.set_message_sent_handler(
        lambda pdu: logging.info('sent {} {}\n'.format(pdu.sequence, pdu.message_id)))
    client.set_message_received_handler(handle_incoming_sms)

    client.connect()


    # Since bind was sucessful, we assume the show started.
    is_running = True
    t = Thread(target=process_sms_queue)
    t.start()

    while True:
        try:
            client.bind_transceiver(system_id=SYSTEM_ID, password=PASSWORD)
            print("LED_WALL: Successfully bound SMPP")
            client.listen()
            break
        except AttributeError:
            print("Binding to smpp service FAILED. Retrying.")
            continue
        except KeyboardInterrupt:
            break
        except Exception as e:
            logging.exception('Error during listen' + str(e))
    is_running = False

if __name__ == "__main__":
    main()
