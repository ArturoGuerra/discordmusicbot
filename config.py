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
        try:
            with open("./config/config.json", 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            if not self.app.args.dry_run:
                self.app.logger.error("Config file not found")
    def token(self):
        return self.config['token']
    def prefix(self):
        return self.config['prefix']
    def owners(self):
        return self.config['owners']
class Channels():
    def __init__(self, app):
        self.app = app
        try:
            with open("./config/channels.json", 'r') as f:
                self.channels = json.load(f)
        except IOError:
            if not self.app.args.dry_run:
                self.app.logger.error("Channel file not found")
    def channels(self):
        return self.channels

