'''
This file is part of SimMeR, an educational mechatronics robotics simulator.
Initial development funded by the University of Toronto MIE Department.
Copyright (C) 2023  Ian G. Bennett

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''

# Basic echo client, for testing purposes
# Code modified from examples on https://realpython.com/python-sockets/
# and https://www.geeksforgeeks.org/python-display-text-to-pygame-window/

import socket
import struct
import math
import time
import _thread
from datetime import datetime
import serial

# Wrapper functions
def transmit(data):
    if SIMULATE:
        transmit_tcp(data)
    else:
        transmit_serial(data)
    time.sleep(TRANSMIT_PAUSE)

def receive():
    if SIMULATE:
        return receive_tcp()
    else:
        return receive_serial()

# TCP communication functions
def transmit_tcp(data):
    '''Send a command over the TCP connection.'''
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, PORT_TX))
            s.send(data.encode('utf-8'))
        except (ConnectionRefusedError, ConnectionResetError):
            print('Tx Connection was refused or reset.')
            _thread.interrupt_main()
        except TimeoutError:
            print('Tx socket timed out.')
            _thread.interrupt_main()
        except EOFError:
            print('\nKeyboardInterrupt triggered. Closing...')
            _thread.interrupt_main()

def receive_tcp():
    '''Receive a reply over the TCP connection.'''
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s2:
        try:
            s2.connect((HOST, PORT_RX))
            response_raw = s2.recv(1024)
            if response_raw:
                # return the data received as well as the current time
                return [bytes_to_list(response_raw), datetime.now().strftime("%H:%M:%S")]
            else:
                return [[False], None]
        except (ConnectionRefusedError, ConnectionResetError):
            print('Rx connection was refused or reset.')
            _thread.interrupt_main()
        except TimeoutError:
            print('Response not received from robot.')
            _thread.interrupt_main()

# Serial communication functions
def transmit_serial(data):
    '''Transmit a command over a serial connection.'''
    SER.write(data.encode('ascii'))

def receive_serial():
    '''Receive a reply over a serial connection.'''
    # If responses are ascii characters, use this
    # response_raw = (SER.readline().strip().decode('ascii'),)

    # If responses are a series of 4-byte floats, use this
    available_bytes = SER.in_waiting
    read_bytes = max(4, available_bytes - (available_bytes % 4))
    if read_bytes >= 4:
        response_raw = bytes_to_list(SER.read(read_bytes))

    # If response received, return it
    if response_raw[0]:
        return [response_raw, datetime.now().strftime("%H:%M:%S")]
    else:
        return [[False], datetime.now().strftime("%H:%M:%S")]

def clear_serial(delay_time):
    '''Wait some time (delay_time) and then clear the serial buffer.'''
    time.sleep(delay_time)
    SER.read(SER.in_waiting())

# Convert string of bytes to a list of values
def bytes_to_list(msg):
    '''
    Convert a sequence of single precision floats (Arduino/SimMerR float format)
    to a list of numerical responses.
    '''
    num_responses = int(len(msg)/4)
    if num_responses:
        data = struct.unpack(f'{str(num_responses)}f', msg)
        return data
    else:
        return ([False])


# Set whether to use TCP (SimMeR) or serial (Arduino)
SIMULATE = True

# Time to pause after transmitting (seconds)
TRANSMIT_PAUSE = 0.1

### Network Setup ###
HOST = '127.0.0.1'      # The server's hostname or IP address
PORT_TX = 61200         # The port used by the *CLIENT* to receive
PORT_RX = 61201         # The port used by the *CLIENT* to send data

### Serial Setup ###
BAUDRATE = 115200       # Baudrate in bps
PORT_SERIAL = 'COM4'    # COM port identification
try:
    SER = serial.Serial(PORT_SERIAL, BAUDRATE, timeout=0)
except serial.SerialException:
    pass

# Received responses
responses = [False]
time_rx = 'Never'

# The sequence of commands to run
cmd_sequence = ['w0-36', 'r0-90', 'w0-36', 'r0-90', 'w0-12', 'r0--90', 'w0-24', 'r0--90', 'w0-6', 'r0-720']

# Main loop
RUNNING = True
ct = 0
while RUNNING:

    if ct < len(cmd_sequence):
        transmit('u0')
        [responses, time_rx] = receive()
        print(f"Ultrasonic 0 reading: {round(responses[0], 3)}")

        transmit('u1')
        [responses, time_rx] = receive()
        print(f"Ultrasonic 1 reading: {round(responses[0], 3)}")

        # transmit('u2')
        # [responses, time_rx] = receive()
        # print(f"Ultrasonic 2 reading: {round(responses[0], 3)}")

        # transmit('u3')
        # [responses, time_rx] = receive()
        # print(f"Ultrasonic 3 reading: {round(responses[0], 3)}")

        transmit(cmd_sequence[ct])
        [responses, time_rx] = receive()
        print(f"Drive command response: {round(responses[0], 3)}")

        if responses[0] == math.inf:
            ct += 1

    else:
        RUNNING = False
        print("Sequence complete!")
