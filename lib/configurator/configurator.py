"""
Copyright (C) 2014 Bob Igo, http://bob.igo.name, bob@igo.name

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
from configparser import ConfigParser
import logging
import os
import threading
import time


class Configurator(threading.Thread):
    """
    Read the configuration file and inform interested classes of relevant values.
    This thread runs parallel to the other top-level thread, Doorbell.
    """

    def __init__(self, config_file):
        """
        Watches config_file and informs ding, dong, and/or ha_informer of changes
        they should incorporate while running.
        """
        threading.Thread.__init__(self)
        self.daemon = True
        self.running = True
        self.config_file = config_file
        self.timestamp = 0.0  # when the file was last updated
        self.scp = ConfigParser()
        self.ding = None
        self.dong = None
        self.ha_informer = None
        self.logging = logging.getLogger(self.__class__.__name__)

    def run(self):
        """
        If the timestamp has changed, (re)load config_file and send the latest
        values to the interested parties. It is up to the receiving classes to
        decide if the 'new' value is actually different.
        """
        while self.running:
            new_ts = os.stat(self.config_file).st_mtime
            if new_ts != self.timestamp:
                self.scp.read(self.config_file)
                self.logging.info("(" + self.__class__.__name__ + ") (re)parsed " + self.config_file)
                self.timestamp = new_ts

                if self.ding is not None:
                    self.ding.setsoundfile(self.scp.get('sound', 'ding_soundfile'))
                    self.ding.setlocation(self.scp.get('sound', 'noise_location'))
                if self.dong is not None:
                    self.dong.setsoundfile(self.scp.get('sound', 'dong_soundfile'))
                    self.dong.setlocation(self.scp.get('sound', 'noise_location'))
                    self.dong.setdelay(self.scp.getfloat('sound', 'dong_delay'))
                if self.ha_informer is not None:
                    self.ha_informer.set_openhab(self.scp.get('openhab', 'openhab_base_URL'),
                                                 self.scp.get('openhab', 'item_name'))
                    self.ha_informer.set_hass(self.scp.get('hass', 'ha_base_URL'),
                                              self.scp.get('hass', 'entity_id'))
                    self.ha_informer.settimeout(self.scp.getint('ha', 'timeout'))
                    self.ha_informer.setcollapseinterval(self.scp.getint('ha', 'button_press_collapse_interval'))
            
            time.sleep(1)

    def getint(self, section, option):
        """
        A wrapper to self.scp.getinteger()
        """
        return self.scp.getint(section, option)

    def getboolean(self, section, option):
        """
        A wrapper to self.scp.getboolean()
        """
        return self.scp.getboolean(section, option)

    def register_listeners(self, ding, dong, ha_informer):
        self.ding = ding
        self.dong = dong
        self.ha_informer = ha_informer

    def ready(self):
        return self.timestamp != 0.0

    def stop(self):
        self.running = False
