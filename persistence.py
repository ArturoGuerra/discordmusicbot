import config
import pymysql
import musicbot
from peewee import *
cfg = musicbot.MusicApplication().config
try:
    my_db = MySQLDatabase(
            cfg.database,
            host=cfg.dbhost,
            port=3306,
            user=cfg.dbuser,
            password=cfg.dbpass,
            charset='utf8mb4')
except Exception as e:
    my_db=None

class BaseModel(Model):
    class Meta:
        database=my_db
class Servers(BaseModel):
    server = BigIntegerField(null=False, primary_key=True)
    channel = BigIntegerField(null=True)
    playlist = CharField(null=True)
class Playlists(BaseModel):
    playlist = CharField(null=False)
    link = CharField(null=False)
    class Meta:
        primary_key = None
