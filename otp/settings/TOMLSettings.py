"""
OpenTTTools Settings
Slight override of a typical dict to make the file auto save when a change is made
"""

import collections
import tomllib
import os
from typing import Union, List, Dict, Iterator, Any

import tomli_w


class TOMLSettings(collections.abc.MutableMapping):

    def __init__(self, filename: str):
        """
        :param filename: File path to json file
        """
        self.filename = filename

        self.data = {}

        # Make sure the file exists
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'rb') as f:
                    self.data = tomllib.load(f)
            except:
                # Something went wrong with the file, probable corruption, make a new one
                self.save()
        # If not, create it
        else:
            self.save()

    def setSetting(self, category: str, key: str, value: Any):
        if category not in self.data:
            self.data[category] = {}
        self.data[category][key] = value
        self.save()

    def save(self):
        """
        Write settings changes to the json file
        """
        if os.path.dirname(self.filename) and not os.path.exists(os.path.dirname(self.filename)):
            os.makedirs(os.path.dirname(self.filename))
        with open(self.filename, 'wb') as jsonFile:
            tomli_w.dump(self.data, jsonFile)

    ''' Overrides '''

    def __getitem__(self, key: str):
        """
        x = settings['setting'] override

        :param key: Setting Key
        :return: Setting value
        """
        return self.data[key]

    def __setitem__(self, key: str, value: Union[str, bool, int, float, List, Dict]):
        """
        settings['setting'] = 'value' override

        :param key: Setting Key
        :param value: The value to set the setting to
        """
        self.data[key] = value
        # Save the file
        self.save()

    def __delitem__(self, key: str):
        """
        del settings['setting'] override

        :param key: Setting Key to remove
        """
        del self.data[key]
        # Save the file
        self.save()

    def __iter__(self) -> Iterator:
        """
        iteration override (e.g. for x in settings)

        :return: Iterable of settings
        """
        return iter(self.data)

    def __len__(self) -> int:
        """
        len(settings) Override

        :return: Number of settings as integer
        """
        return len(self.data)
