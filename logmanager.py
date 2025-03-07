class logmanager:
    def __init__(self, cfg, bot):
        self.cfg = cfg
        self.bot = bot
        self.logchannelid = ""
        self.logchannel = ""
        self.loadlogchannelid()
        # categories of logs
        self.timeouts = 0
        self.roles = 1
        self.flooders = 2
        
        self.addrole = 0
        self.removerole = 1
        
    def loadlogchannelid(self):
        self.logchannelid = self.cfg.get("logchannelid")
        if not self.logchannelid or self.logchannelid == 0:
            raise Exception("test")
        return
    async def uploadlog(self, content):
        await self.logchannel.send(content)
        return
    async def sendlog(self, category, author, mode = False, target = False, duration = False, reason = False, rolename = False):
        log = "No appropriate log category has been found."
        if category == self.timeouts:
            log = "A timeout has been issued to " + target + " by " + author + " for " + duration + " for " + reason + "."
        elif category == self.roles:
            if mode == self.addrole:
                log = "A role " + rolename + " has been assigned to " + target + " by " + author + "."
            else:
                log = "A role " + rolename + " has been removed from " + target + " by " + author + "."
        elif category == self.flooders:
            if mode == self.addrole:
                log = "A Flooder role has been issued to " + target + " by " + author + " for " + duration + " for " + reason + "."
            else:
                log = "A Flooder role has been prematurely removed from " + target + " by " + author + " for " + reason + "."
        await self.uploadlog(log)
        return
    def ready(self):
        guild = self.bot.get_guild(self.cfg.get("guild"))
        self.logchannel = guild.get_channel(self.logchannelid)
        if self.logchannel == None:
            raise NoLogChannelException
        return