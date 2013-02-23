#!/usr/bin/python -i
# -*- encoding: utf-8 -*-
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

import dbus
if getattr(dbus, 'version', (0, 0, 0)) < (0, 80, 0):
    import dbus.glib
else:
    from dbus.mainloop.glib import DBusGMainLoop
    DBusGMainLoop(set_as_default=True)

bus = dbus.SystemBus()
proxy = bus.get_object('org.wicd', '/org/wicd')
daemon = dbus.Interface(proxy, 'org.wicd')

print 'Console ready.'
