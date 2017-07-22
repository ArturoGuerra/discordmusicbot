import sys
import json
import getpass

#Creates bot config file
class ConfigGenerator():
    def __init__(self):
        self.__config = dict()
        with open("./config/sample.config.json", 'r') as f:
            self.__sample_config = json.load(f)
    def bot_setup(self):
        special = ['token']
        for key in self.__sample_config:
            if key in special:
                special_key = getpass.getpass(f"{key}: ")
                self.__config[key]  = special_key
            elif isinstance(self.__sample_config[key], list):
                self.__config[key] = list()
                keys = input(f"{key}: ")
                for i in keys.split(' '):
                    self.__config[key].append(i)
            else:
                key_input = input(f"{key}: ")
                self.__config[key] = key_input
        with open("./config/config.json", "w") as f:
            json.dump(self.__config, f)
        return self.__config

#Loads bot config file
class Config():
    def __init__(self, app):
        self.app = app
        self.__config = dict()
        try:
            with open('./config/config.json', 'r') as f:
                self.__config = json.load(f)
        except FileNotFoundError as e:
            if not self.app.args.setup and not self.app.args.dry_run:
                self.app.logger.info("Config file not found, Creating...")
                self.__config = ConfigGenerator().bot_setup()
                self.app.logger.info("Config file created successfully")
            else:
                 self.app.logger.error(e)
        for attr in self.__config:
            setattr(self.__class__, attr, self.__config[attr])

#Loads random file
class jsonLoader():
    def __init__(self, configFile, app):
        self.app = app
        self.data = dict()
        self.configFile = configFile
    def datadecorator(func):
        def wrapper(self, *args, **kwargs):
            try:
                with open(self.configFile, 'r') as f:
                    self.data = json.load(f)
            except FileNotFoundError as e:
                raise FileNotFoundError("File was not found")
            else:
                func(*args, **kwargs)
        return wrapper
    @datadecorator
    def load(self):
        self.app.logger.info("Loaded file...")
    @datadecorator
    def get(self, key):
        try:
            value = self.data[key]
        except KeyError as e:
            raise KeyError(f"{key} was not found")
        else:
            return value
    @datadecorator
    def write(self, key, data):
        try:
            self.data[key] = data
        except NameError as e:
            self.data = dict()
            self.data[key] = data
        with open(self.configFile, 'w') as f:
            json.dump(self.configFile, f)
