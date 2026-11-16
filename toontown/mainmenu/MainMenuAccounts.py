"""
OpenTTTools Settings
Slight override of a typical dict to make the file auto save when a change is made
"""

import collections
import json
import os

class MainMenuAccounts(collections.abc.MutableMapping):

    def __init__(self):
        self.filename = 'accounts.json'

        self.data = {}

        # Make sure the file exists
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    self.data = json.load(f)
            except:
                # Something went wrong with the file, probable corruption, make a new one
                self.save()
        # If not, create it
        else:
            self.save()

    def save(self):
        """
        Write settings changes to the json file
        """
        with open(self.filename, 'w') as jsonFile:
            json.dump(self.data, jsonFile, indent = 4)

    ''' Overrides '''

    def __getitem__(self, key):
        """
        x = settings['setting'] override

        :param key: Setting Key
        :type: key: str
        :return: Setting value
        """
        return self.data[key]

    def __setitem__(self, key, value):
        """
        settings['setting'] = 'value' override

        :param key: Setting Key
        :param value: The value to set the setting to
        :type key: str
        :type value: str
        """
        self.data[key] = value
        # Save the file
        self.save()

    def __delitem__(self, key):
        """
        del settings['setting'] override

        :param key: Setting Key to remove
        :type key: str
        """
        del self.data[key]
        # Save the file
        self.save()

    def __iter__(self):
        """
        iteration override (e.g. for x in settings)

        :return: Iterable of settings
        """
        return iter(self.data)

    def __len__(self):  # type: () -> int
        """
        len(settings) Override

        :return: Number of settings as integer
        """

        return len(self.data)
