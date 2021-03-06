#!/usr/bin/python
# -*- encoding: utf-8 -*-
""" wicd -- wireless internet connection daemon

This module implements the wicd daemon that provides network connection
management, for both wireless and wired networks. The daemon must be run as root
to control the networks, however the user interface components should be run as
a normal user.

class WicdDaemon -- The main DBus daemon for Wicd.
def usage() -- Print usage information.
def daemonize() -- Daemonize the current process with a double fork.
def main() -- The wicd daemon main loop.

"""

# Copyright © 2013, David Paleino <d.paleino@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License Version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import gobject
import argparse

import dbus
import dbus.service

from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)

import logging, logging.handlers


def setup_logging():
    """
    Setup the logging facility.
    This function must be called before everything else, to allow
    very early logging of messages.

    Initial logging will be to console.
    """

    logging.basicConfig(level=logging.DEBUG,
        format='%(asctime)s %(levelname)-8s %(filename)s %(lineno)s %(message)s',
        datefmt='%H:%M:%S')

def daemonize():
    """ Disconnect from the controlling terminal.

    Fork twice, once to disconnect ourselves from the parent terminal and a
    second time to prevent any files we open from becoming our controlling
    terminal.

    For more info see:
    http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66012

    """
    # Fork the first time to disconnect from the parent terminal and
    # exit the parent process.
    logging.info("Sending daemon to the background")
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError, e:
        logging.critical("Fork #1 failed: %d (%s)" % (e.errno, e.strerror))
        sys.exit(1)

    # Decouple from parent environment to stop us from being a zombie.
    os.setsid()
    os.umask(0)

    # Fork the second time to prevent us from opening a file that will
    # become our controlling terminal.
    try:
        pid = os.fork()
        if pid > 0:
            pidfile = open('pidfile', 'w')
            pidfile.write(str(pid) + '\n')
            pidfile.close()
            sys.exit(0)
    except OSError, e:
        logging.critical("Fork #2 failed: %d (%s)" % (e.errno, e.strerror))
        sys.exit(1)

    sys.stdout.flush()
    sys.stderr.flush()
    os.close(sys.__stdin__.fileno())
    os.close(sys.__stdout__.fileno())
    os.close(sys.__stderr__.fileno())

    # stdin always from /dev/null
    sys.stdin = open('/dev/null', 'r')


class WicdDaemon(dbus.service.Object):
    def __init__(self, bus_name, options, object_path="/org/wicd"):
        """ Creates a new WicdDaemon object. """
        super(WicdDaemon, self).__init__(
			bus_name=bus_name, object_path=object_path
		)

    @dbus.service.method('org.wicd')
    def GetVersion(self):
        """ Returns the version number. """
        return "2.0"


def main(argv):
    """ The main daemon program.

    Keyword arguments:
    argv -- The arguments passed to the script.

    """

    p = argparse.ArgumentParser()
    p.add_argument('-v',
                    dest="verbose",
                    action='count',
                    default=0)
    p.add_argument('-l', '--logfile',
                    dest="logfile",
                    action="store",
                    default="/var/log/wicd/wicd.log")
    p.add_argument('-f', '--no-daemon',
                   dest="no_daemon",
                   action='store_true',
                   default=False)
    p.add_argument('-o', '--no-stdout',
                   dest="no_stdout",
                   action='store_true',
                   default=False)
    p.add_argument('-e', '--no-stderr',
                   dest="no_stderr",
                   action='store_true',
                   default=False)

    options = p.parse_args()

    if options.verbose >= 2:
        loglevel=logging.DEBUG
    elif options.verbose >=1:
        loglevel=logging.INFO
    else:
        loglevel=logging.WARN

    if not options.no_daemon:
        logging.debug("Setting log file to %s" % options.logfile)
        # Set file logging to loglevel
        logfile = logging.handlers.RotatingFileHandler(
            options.logfile,
            maxBytes=1024*1024,
            backupCount=3
        )
        logfile.setFormatter(
            logging.Formatter(
            '%(asctime)s:%(levelname)s:%(filename)s:%(funcName)s:%(lineno)d: %(message)s'
            )
        )
        logfile.setLevel(loglevel)
        logging.getLogger().addHandler(logfile)
        # put screen logging threshold to something not in logging
        # so terminal doesn't get funky messages if they leave it open
        logging.basicConfig(level=logging.CRITICAL*2)
        daemonize()
    else:
        # Staying foreground so set log level accordingly
        logging.basicConfig(level=loglevel)

    logging.info('Wicd starting...')

    # Open the DBUS session
    try:
        bus = dbus.SystemBus()
        wicd_bus = dbus.service.BusName('org.wicd', bus=bus)
        daemon = WicdDaemon(wicd_bus, options)
    except dbus.exceptions.DBusException, e:
        logging.critical("DBus issue: %s" % e.message)
        logging.critical("Wicd exiting")
        sys.exit(1)

    gobject.threads_init()

    # Enter the main loop
    mainloop = gobject.MainLoop()
    logging.debug("mainloop.run() starting")
    mainloop.run()


if __name__ == '__main__':
    setup_logging()
    # Check if the root user is running
    if os.getuid() != 0:
        logging.critical("Root privileges are required for the daemon to run properly.")
        logging.critical("Wicd exiting")
        sys.exit(1)

    logging.debug("Initializing services")
    main(sys.argv)
