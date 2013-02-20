#!/usr/bin/env python

"""

NITS -- like TITS but with an N. In fact it means,
Non-Intrusive-Test-SMTPserver

This is a simple SMTP server. It listens for clients sending mails,
then stores mail into an mbox file and may send notifications to the desktop.

It's purpose is to provide a simple debugging tool for applications
sending mails.

Copyright (c) Jean Schurger <jean@schurger.org>

Based on the work of Grzegorz Adam Hankiewicz <gradha@efaber.net>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published
by the Free Software Foundation; either version 2 of the License,
or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""

import os

SUCCESSFUL_EXIT = 0
DEFAULT_PORT_NUMBER = 12345
DEFAULT_SPOOL_FILE = os.path.realpath(os.path.join(os.environ.get("HOME"),
                                                   ".fake_spool"))
DEFAULT_NOTIFY = False


import sys
from datetime import datetime
from twisted.mail.smtp import SMTP, SMTPFactory
from twisted.internet import reactor


class Server(SMTP):

    def connectionMade(self):
        SMTP.connectionMade(self)
        self.data_mode = 0

    def lineReceived(self, line):
        if self.data_mode:
            if line == ".":
                self.sendCode(250, "Ok")
                self.data_mode = 0
                try:
                    self.output.close()
                except BaseException, e:
                    print 'Something strange (%s) appened '
                    'while closing the spool file' % e
                if self.verbose:
                    print "A mail was sent..."
                if self.notify:
                    import pygtk
                    pygtk.require('2.0')
                    import pynotify
                    n = pynotify.Notification("Fake smtpserver",
                                              "a mail was sent...")
                    n.show()
            else:
                try:
                    self.output.write(line + '\n')
                except BaseException, e:
                    print 'Something strange (%s) appened '
                    'while writing to spool file' % e
        else:
            if line[:4].lower() == "quit":
                self.sendCode(221, "Bye bye")
                self.transport.loseConnection()
            if line[:4].lower() in ["ehlo", "helo"]:
                self.helo = line[5:]
            if line[:4].lower() == "data":
                self.data_mode = 1
                try:
                    now = datetime.now()
                    self.output = open(self.spool_file, "a")
                    _from = "From %s" % self.helo
                    _date = now.strftime('%a %b %d %H:%M:%S %Y')
                    self.output.write('%s  %s\n' % (_from, _date))
                except BaseException, e:
                    print 'Something strange (%s) appened '
                    'while opening the spool file' % e
                self.sendCode(354, "Go ahead")
            else:
                self.sendCode(250, "Ok")


def usage(binary_name="nits.py"):
    """Prints usage information and terminates execution."""
    print """Usage: %(binary_name)s [-hv -p port_number -s spool_file]

-h, --help
    Print this help screen.
-v, --verbose
    Tell when a mail pass.
-p xxx, --port-number xxx
    Use xxx as port number to listen incoming SMTP connections.
    By default, the port is %(default_port)s
-s yyy, --spool-file yyy
    Write mails to this file, by default, it's %(default_spool)s
-n Send a notification on the desktop with a mail pass %(notify)s by default
Usage example:
 %(binary_name)s -p 12345 -s /tmp/spool -v
 """ % \
    dict(binary_name=binary_name,
         default_port=DEFAULT_PORT_NUMBER,
         default_spool=DEFAULT_SPOOL_FILE,
         notify=DEFAULT_NOTIFY)
    sys.exit(1)


def process_command_line(argv=None):
    """Extracts from argv the options and returns them in a tuple.

    This function is a command line wrapper against main_process,
    it returns a tuple which you can `apply' calling main_process. If
    something in the command line is missing, the program will exit
    with a hopefully helpfull message.

    args should be a list with the full command line. If it is None
    or empty, the arguments will be extracted from sys.argv. The
    correct format of the accepted command line is documented by
    usage_information.
    """
    import getopt
    if not argv:
        argv = sys.argv

    try:
        opts, args = getopt.getopt(argv[1:],
                                   "hnvp:s:",
                                   ["help", "port-number=", "spool-file="])
    except getopt.GetoptError, msg:
        print "Error processing command line: %s\n" % msg
        usage()

    port_number = DEFAULT_PORT_NUMBER
    spool_file = DEFAULT_SPOOL_FILE
    verbose = False
    notify = DEFAULT_NOTIFY
    for option, value in opts:
        if option in ("-h", "--help"):
            usage()
        elif option in ("-p", "--port-number"):
            port_number = int(value)
        elif option in ("-v", "--verbose"):
            verbose = True
        elif option in ("-n", "--notify"):
            notify = True
        elif option in ("-s", "--spool-file"):
            spool_file = value
    return (port_number, spool_file, verbose, notify)


def main_process(port_number, spool_file, verbose, notify):
    factory = SMTPFactory()
    factory.protocol = Server
    factory.protocol.spool_file = spool_file
    factory.protocol.verbose = verbose
    factory.protocol.notify = notify
    factory.timeout = 200
    reactor.listenTCP(port_number, factory)
    print "Listening on port %s, spooling on %s" % (port_number,
                                                    spool_file)
    if notify:
        print "Will notify on the desktop"
    if verbose:
        print "Will notify on the console"
    reactor.run()


if __name__ == "__main__":
    args = process_command_line()
    main_process(*args)
