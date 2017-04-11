import json

class Config():
    def __init__(self, app):
        self.app = app
        try:
            with open("./config/config.json", 'r') as f:
                self.config = json.load(f)
        except IOError:
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
            self.app.logger.error("Channel file not found")
    def channels(self):
        return self.channels

