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
        self.warns = 3
        self.selfissuedwarn = 4
        
        self.addrole = 0
        self.removerole = 1
        
        self.addwarn = 0
        self.clearwarns = 1
        
    def loadlogchannelid(self):
        self.logchannelid = self.cfg.get("logchannelid")
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
            if mode == self.selfissuedwarn:
                log = "A timeout has been issued to <@" + str(target.id) + "> by " + context.user.name + " for " + duration + " for " + reason + "."
            else:
                log = "A timeout has been issued to <@" + str(target.id) + "> by " + context.author.name + " for " + duration + " for " + reason + "."
        elif category == self.roles:
            if mode == self.addrole:
                log = "A role " + role.name + " has been assigned to <@" + str(target.id) + "> by " + context.author.name + "."
            else:
                log = "A role " + role.name + " has been removed from <@" + str(target.id) + "> by " + context.author.name + "."
        elif category == self.flooders:
            if mode == self.addrole:
                log = "A Flooder role has been issued to <@" + str(target.id) + "> by " + context.author.name + " for " + duration + " for " + reason + "."
            else:
                log = "A Flooder role has been prematurely removed from <@" + str(target.id) + "> by " + context.author.name + " for " + reason + "."
        elif category == self.warns:
            if mode == self.addwarn:
                log = "A warning has been issued to <@" + str(target.id) + "> by " + context.author.name + " for " + reason + "."
            else:
                log = context.author.name + " has cleared all warnings for <@" + str(target.id) + "> for " + reason + "."
        await self.uploadlog(log, context)
        return
    def ready(self):
        guild = self.bot.get_guild(self.cfg.get("guild"))
        self.logchannel = guild.get_channel(self.logchannelid)
        if self.logchannel == None:
            raise Exception("No log channel defined.")
        return