import discord
import aiomysql as sql
import configparse

cfg = configparse.parseconfig("config.cfg")
cfg.load()
token = cfg.loadtoken()
