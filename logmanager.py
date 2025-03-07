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
        print(self.logchannelid)
        if not self.logchannelid or self.logchannelid == 0:
            raise Exception("Invalid log channel id")
        return
    async def uploadlog(self, content, context):
        try:
            await self.logchannel.send(content)
        except:
            await context.respond("Error sending a message in the log channel.", ephemeral = False)
        return
    async def sendlog(self, category, context, mode = False, target = False, duration = False, reason = False, role = False):
        log = "No appropriate log category has been found."
        if category == self.timeouts:
            log = "A timeout has been issued to " + target.name + " by " + context.author.name + " for " + duration + " for " + reason + "."
        elif category == self.roles:
            if mode == self.addrole:
                log = "A role " + role.name + " has been assigned to " + target.name + " by " + context.author.name + "."
            else:
                log = "A role " + role.name + " has been removed from " + target.name + " by " + context.author.name + "."
        elif category == self.flooders:
            if mode == self.addrole:
                log = "A Flooder role has been issued to " + target.name + " by " + context.author.name + " for " + duration + " for " + reason + "."
            else:
                log = "A Flooder role has been prematurely removed from " + target.name + " by " + context.author.name + " for " + reason + "."
        await self.uploadlog(log, context)
        return
    def ready(self):
        guild = self.bot.get_guild(self.cfg.get("guild"))
        self.logchannel = guild.get_channel(self.logchannelid)
        if self.logchannel == None:
            raise NoLogChannelException
        return