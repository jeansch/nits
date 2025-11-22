#!/usr/bin/env python3

"""
Nits -- Non Intrusive Test SMTPserver

This is a simple SMTP server. It listens for clients sending mails,
then stores email into an mbox file and may send notifications to the desktop.

It's purpose is to provide a simple debugging tool for applications
sending emails.

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

See: https://www.gnu.org/licenses
"""

import os
import getopt
import sys
from datetime import datetime
from twisted.mail.smtp import SMTP, SMTPFactory
from twisted.internet import reactor

SUCCESSFUL_EXIT = 0
DEFAULT_PORT_NUMBER = 12345
DEFAULT_SPOOL_FILE = os.path.realpath(os.path.join(os.environ.get("HOME"),
                                                   ".fake_spool"))
DEFAULT_NOTIFY = False

notify_help = ""





def gi_notify(title, message):
    n = Notify.Notification.new(title, message)
    n.show()


def osx_notify(title, message):
    cmd = "osascript -e 'display notification \"%s\" with title \"%s\"'" % (
        message, title)
    os.system(cmd)

notifier = None

if os.path.exists("/usr/bin/osascript"):
    notifier = osx_notify


try:
    import gi
    gi.require_version('Notify', '0.7')
    from gi.repository import Notify
    Notify.init('Nits')
    notifier = gi_notify
except ImportError:
    pass


if notifier:
    notify_help = ("-n Send a notification on the desktop "
               "when a mail pass '%(notify)s' by default\n" % {
                   'notify': DEFAULT_NOTIFY})


class Server(SMTP):

    output = None
    subject = None
    from_ = None
    to_ = None

    def connectionMade(self):
        SMTP.connectionMade(self)
        self.data_mode = 0

    def lineReceived(self, line):
        if self.data_mode and self.output:
            if line == b".":
                self.sendCode(250, b"Ok")
                self.data_mode = 0
                try:
                    self.output.close()
                except Exception as e:
                    print("Something strange (%s) appened "
                          "while closing the spool file" % e)
                msg = self.subject or b"A email was sent..."
                title = b"Nits"
                if self.from_:
                    title += b" [From: '%s']" % self.from_
                if self.to_:
                    title += b" [To: '%s']" % self.to_
                if self.notify and notifier:
                    notifier(title.decode(), msg.decode())
                if self.verbose:
                    print(title.decode(), msg.decode())
            else:
                try:
                    self.output.write(line + b'\n')
                    if line.lower().startswith(b"subject:"):
                        self.subject = line[9:]
                    if line.lower().startswith(b"from:"):
                        self.from_ = line[6:]
                    if line.lower().startswith(b"to:"):
                        self.to_ = line[4:]
                except Exception as e:
                    print("Something strange (%s) appened "
                          "while writing to spool file" % e)
        else:
            if line[:4].lower() == b"quit":
                self.sendCode(221, b"Bye bye")
                self.transport.loseConnection()
            if line[:4].lower() in [b"ehlo", b"helo"]:
                self.helo = line[5:]
            if line[:4].lower() == b"data":
                self.data_mode = 1
                try:
                    now = datetime.now()
                    self.output = open(self.spool_file, "ab")
                    _from = bytes("From %s" % self.helo, "utf8")
                    _date = bytes(now.strftime('%a %b %d %H:%M:%S %Y'), "utf8")
                    self.output.write(b'%s  %s\n' % (_from, _date))
                except Exception as e:
                    print("Something strange (%s) appened "
                          "while opening the spool file" % e)
                self.sendCode(354, b"Go ahead")
            else:
                self.sendCode(250, b"Ok")


def usage(binary_name="nits.py"):
    """Prints usage information and terminates execution."""
    print("""Usage: %(binary_name)s [-hv -p port_number -s spool_file]

-h, --help
    Print this help screen.
-v, --verbose
    Tell when a mail pass.
-p xxx, --port-number xxx
    Use xxx as port number to listen incoming SMTP connections.
    By default, the port is %(default_port)s
-s yyy, --spool-file yyy
    Write mails to this file, by default, it's %(default_spool)s
%(notify_help)s
Usage example:
 %(binary_name)s -p 12345 -s /tmp/spool -v
    """ % dict(notify_help=notify_help,
               binary_name=binary_name,
               default_port=DEFAULT_PORT_NUMBER,
               default_spool=DEFAULT_SPOOL_FILE))
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

    if not argv:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(argv[1:],
                                   "hnvp:s:",
                                   ["help", "port-number=", "spool-file="])
    except getopt.GetoptError as msg:
        print("Error processing command line: %s\n" % msg)
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
    if verbose:
        print("Listening on port %s, spooling on %s" % (
            port_number, spool_file))
        if notify and notifier:
            print("Will notify on the desktop")
        print("Will notify on the console")
    reactor.run()


def main():
    args = process_command_line()
    main_process(*args)


if __name__ == "__main__":
    main()


def test():
    import smtplib
    from email.message import EmailMessage
    msg = EmailMessage()
    msg.set_content("Test email!")
    msg['Subject'] = 'Test !'
    msg['From'] = "Me"
    msg['To'] = "You"
    s = smtplib.SMTP('localhost:%s' % DEFAULT_PORT_NUMBER)
    s.send_message(msg)
    s.quit()


def process_inbox_command_line(argv=None):
    """Process command line arguments for inbox command."""
    if not argv:
        argv = sys.argv

    try:
        opts, args = getopt.getopt(argv[1:], "hfs:n:", ["help", "follow", "spool-file=", "number="])
    except getopt.GetoptError as msg:
        print("Error processing command line: %s\n" % msg)
        usage_inbox()

    spool_file = DEFAULT_SPOOL_FILE
    max_emails = None
    follow = False

    for option, value in opts:
        if option in ("-h", "--help"):
            usage_inbox()
        elif option in ("-s", "--spool-file"):
            spool_file = value
        elif option in ("-n", "--number"):
            max_emails = int(value)
        elif option in ("-f", "--follow"):
            follow = True

    return (spool_file, max_emails, follow)


def usage_inbox():
    """Prints inbox usage information and terminates execution."""
    print("""Usage: nits-inbox [-h -f -s spool_file -n number]

-h, --help
    Print this help screen.
-f, --follow
    Follow mode: wait for new emails and display them as they arrive (like tail -f)
-s yyy, --spool-file yyy
    Read mails from this file, by default, it's %(default_spool)s
-n xxx, --number xxx
    Display at most xxx emails (ignored in follow mode)

Usage examples:
 nits-inbox -s /tmp/spool -n 10
 nits-inbox -f
    """ % dict(default_spool=DEFAULT_SPOOL_FILE))
    sys.exit(1)


def parse_mbox_emails(spool_file):
    """Parse emails from mbox file and return list of email dictionaries."""
    import mailbox
    import email.utils

    if not os.path.exists(spool_file):
        return []

    emails = []
    try:
        mbox = mailbox.mbox(spool_file)
        for idx, message in enumerate(mbox):
            email_data = {
                'number': idx + 1,
                'from': message.get('From', ''),
                'to': message.get('To', ''),
                'subject': message.get('Subject', '(no subject)'),
                'date': message.get('Date', ''),
            }

            # Parse date for sorting
            if email_data['date']:
                try:
                    parsed_date = email.utils.parsedate_to_datetime(email_data['date'])
                    email_data['parsed_date'] = parsed_date
                except:
                    email_data['parsed_date'] = None
            else:
                email_data['parsed_date'] = None

            emails.append(email_data)
        mbox.close()
    except Exception as e:
        print(f"Error reading spool file: {e}")
        return []

    return emails


def display_email(email):
    """Display a single email."""
    print(f"{email['number']}. {email['subject']}")
    print(f"   From: {email['from']}")
    print(f"   To: {email['to']}")
    if email['date']:
        print(f"   Date: {email['date']}")
    print()


def inbox():
    """List emails from the spool file."""
    import time

    spool_file, max_emails, follow = process_inbox_command_line()

    if follow:
        # Follow mode: monitor for new emails
        print(f"Watching {spool_file} for new emails... (press Ctrl+C to stop)")
        print()

        last_count = 0
        try:
            while True:
                emails = parse_mbox_emails(spool_file)
                current_count = len(emails)

                # Check if new emails arrived
                if current_count > last_count:
                    # Get only new emails
                    new_emails = emails[last_count:]

                    # Sort new emails by date (most recent first)
                    emails_with_date = [e for e in new_emails if e['parsed_date'] is not None]
                    emails_without_date = [e for e in new_emails if e['parsed_date'] is None]

                    emails_with_date.sort(key=lambda x: x['parsed_date'], reverse=True)
                    sorted_new = emails_with_date + emails_without_date

                    # Display new emails
                    for idx, email in enumerate(sorted_new, start=last_count + 1):
                        email['number'] = idx
                        display_email(email)

                    last_count = current_count

                # Wait before checking again
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopped watching for new emails.")
            return
    else:
        # Normal mode: list existing emails
        emails = parse_mbox_emails(spool_file)

        if not emails:
            print("No emails found in %s" % spool_file)
            return

        # Sort by date (most recent first)
        # Emails without valid dates go to the end
        emails_with_date = [e for e in emails if e['parsed_date'] is not None]
        emails_without_date = [e for e in emails if e['parsed_date'] is None]

        emails_with_date.sort(key=lambda x: x['parsed_date'], reverse=True)
        sorted_emails = emails_with_date + emails_without_date

        # Renumber after sorting
        for idx, email in enumerate(sorted_emails):
            email['number'] = idx + 1

        # Apply max_emails limit if specified
        if max_emails is not None:
            sorted_emails = sorted_emails[:max_emails]

        # Display emails
        for email in sorted_emails:
            display_email(email)


def process_cat_command_line(argv=None):
    """Process command line arguments for cat command."""
    if not argv:
        argv = sys.argv

    try:
        opts, args = getopt.getopt(argv[1:], "hs:", ["help", "spool-file="])
    except getopt.GetoptError as msg:
        print("Error processing command line: %s\n" % msg)
        usage_cat()

    spool_file = DEFAULT_SPOOL_FILE
    email_number = None

    for option, value in opts:
        if option in ("-h", "--help"):
            usage_cat()
        elif option in ("-s", "--spool-file"):
            spool_file = value

    # Get email number from remaining args
    if args:
        try:
            email_number = int(args[0])
        except ValueError:
            print(f"Error: '{args[0]}' is not a valid email number\n")
            usage_cat()

    return (spool_file, email_number)


def usage_cat():
    """Prints cat usage information and terminates execution."""
    print("""Usage: nits-cat [number] [-h -s spool_file]

Display the full content of an email.

Arguments:
    number              The email number to display (1 = most recent, 2 = second most recent, etc.)
                        If not specified, displays the most recent email (1)

Options:
-h, --help
    Print this help screen.
-s yyy, --spool-file yyy
    Read mails from this file, by default, it's %(default_spool)s

Usage examples:
 nits-cat              # Display most recent email
 nits-cat 1            # Display most recent email (same as above)
 nits-cat 3            # Display third most recent email
 nits-cat 5 -s /tmp/spool
    """ % dict(default_spool=DEFAULT_SPOOL_FILE))
    sys.exit(1)


def cat():
    """Display full content of a specific email."""
    import mailbox

    spool_file, email_number = process_cat_command_line()

    # Default to most recent email (number 1) if not specified
    if email_number is None:
        email_number = 1

    if email_number < 1:
        print("Error: email number must be at least 1")
        sys.exit(1)

    if not os.path.exists(spool_file):
        print(f"No emails found in {spool_file}")
        sys.exit(1)

    # Parse all emails
    emails = parse_mbox_emails(spool_file)

    if not emails:
        print(f"No emails found in {spool_file}")
        sys.exit(1)

    # Sort by date (most recent first)
    emails_with_date = [e for e in emails if e['parsed_date'] is not None]
    emails_without_date = [e for e in emails if e['parsed_date'] is None]

    emails_with_date.sort(key=lambda x: x['parsed_date'], reverse=True)
    sorted_emails = emails_with_date + emails_without_date

    # Check if requested email exists
    if email_number > len(sorted_emails):
        print(f"Error: only {len(sorted_emails)} email(s) found in {spool_file}")
        sys.exit(1)

    # Get the requested email (convert to 0-based index)
    target_idx = email_number - 1

    # Now get the full content from the mbox
    try:
        mbox = mailbox.mbox(spool_file)

        # Find the email that matches our sorted position
        # We need to match by comparing headers since mbox order may differ
        target_email_data = sorted_emails[target_idx]

        found = False
        for message in mbox:
            # Match by comparing from, to, subject, and date
            if (message.get('From', '') == target_email_data['from'] and
                message.get('To', '') == target_email_data['to'] and
                message.get('Subject', '(no subject)') == target_email_data['subject'] and
                message.get('Date', '') == target_email_data['date']):

                # Display headers
                print(f"Email #{email_number} (of {len(sorted_emails)})")
                print(f"From: {message.get('From', '')}")
                print(f"To: {message.get('To', '')}")
                print(f"Subject: {message.get('Subject', '(no subject)')}")
                print(f"Date: {message.get('Date', '')}")
                print()
                print("-" * 70)
                print()

                # Display body
                if message.is_multipart():
                    for part in message.walk():
                        content_type = part.get_content_type()
                        if content_type == 'text/plain':
                            payload = part.get_payload(decode=True)
                            if payload:
                                print(payload.decode(part.get_content_charset() or 'utf-8', errors='replace'))
                        elif content_type == 'text/html':
                            # If no plain text found, show HTML as fallback
                            payload = part.get_payload(decode=True)
                            if payload:
                                print("[HTML Content]")
                                print(payload.decode(part.get_content_charset() or 'utf-8', errors='replace'))
                else:
                    payload = message.get_payload(decode=True)
                    if payload:
                        print(payload.decode(message.get_content_charset() or 'utf-8', errors='replace'))
                    else:
                        print(message.get_payload())

                found = True
                break

        mbox.close()

        if not found:
            print(f"Error: could not find email #{email_number}")
            sys.exit(1)

    except Exception as e:
        print(f"Error reading email: {e}")
        sys.exit(1)
