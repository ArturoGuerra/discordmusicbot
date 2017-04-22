import json
class configLoader():
    def __init__(self, configFile, app):
        self.configFile = configFile
        self.app = app
    def loadecorator(func):
        def wrapper(self, *args):
            try:
                with open(self.configFile, 'r') as f:
                    self.data = json.load(f)
                    self.app.logger.info("Loaded file...")
            except FileNotFoundError as e:
                if not self.app.args.dry_run:
                   raise FileNotFoundError("File was not found")
            else:
                return func(self, *args)
        return wrapper
    @loadecorator
    def load(self):
        self.app.logger.info("Trying to load file...")
    @loadecorator
    def get(self, key):
        try:
            value = self.data[key]
        except KeyError as e:
            raise KeyError(f"{key} was not found")
        else:
            return value
    @loadecorator
    def write(self, key, data):
        try:
            self.data[key] = data
        except NameError as e:
            self.data = dict()
            self.data[key] = data
        with open(self.configFile, 'w') as f:
            json.dump(self.configFile, f)

class Config():
    def __init__(self, app):
        self.app = app
        self.__config = dict()
        try:
            with open("./config/config.json", 'r') as f:
                self.__config = json.load(f)
        except IOError:
            if not self.app.args.dry_run:
                self.app.logger.error("Config file not found")
    @property
    def token(self):
        try:
            return self.__config['token']
        except KeyError as e:
            self.app.logger.error(f"Key Error: {e}")
    @property
    def prefix(self):
        try:
            return self.__config['prefix']
        except KeyError as e:
            self.app.logger.error(f"Key Error: {e}")
    @property
    def owners(self):
        try:
            return self.__config['owners']
        except KeyError as e:
            self.app.logger.error(f"Key Error: {e}")
class Channels():
    def __init__(self, app):
        self.app = app
        self.__channels = list()
        try:
            with open("./config/channels.json", 'r') as f:
                self.__channels = json.load(f)
        except IOError:
            if not self.app.args.dry_run:
                self.app.logger.error("Channel file not found")
    @property
    def channels(self):
        return self.__channels
