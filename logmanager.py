class logmanager:
    def __init__(self, cfg, bot):
        self.cfg = cfg
        self.bot = bot
        self.logchannelid = ""
        self.logchannel = ""
        self.loadlogchannelid()
        # categories of logs
        self.timeouts = 1
        self.roles = 2
        self.flooders = 3 # obsolete
        self.warns = 4
        self.selfissuedwarn = 5
        self.slowmodes = 6
        self.unbans = 7
        self.unbanreasons = 8
        self.temproles = 9
        
        self.addrole = 1
        self.removerole = 2
        
        self.addwarn = 1
        self.clearwarns = 2
        self.noreason = 3
        
    def loadlogchannelid(self):
        self.logchannelid = self.cfg.get("logchannelid")
        if not self.logchannelid or self.logchannelid == 0:
            raise Exception("Invalid log channel id")
        return
    async def uploadlog(self, content, context):
        try:
            await self.logchannel.send(content)
        except:
            if not context:
                return
            await context.respond("Error sending a message in the log channel.", ephemeral = False)
        return
    async def sendlog(self, category, context, mode = False, target = False, duration = False, reason = False, role = False, channelid = False):
        log = "No appropriate log category has been found."
        if category == self.timeouts:
            if mode == self.selfissuedwarn:
                log = "A timeout has been issued to <@" + str(target.id) + "> by " + context.user.name + " until <t:" + str(duration) + ":F> for " + reason + "."
            else:
                log = "A timeout has been issued to <@" + str(target.id) + "> by " + context.author.name + " until <t:" + str(duration) + ":F> for " + reason + "."
        elif category == self.roles:
            if mode == self.addrole:
                if role.id == self.cfg.get("gladiatorid"):
                    log = "A role " + role.name + " has been assigned to <@" + str(target.id) + "> by " + context.author.name + " until <t:" + str(duration) + ":F>."
                else:
                    log = "A role " + role.name + " has been assigned to <@" + str(target.id) + "> by " + context.author.name + "."
            else:
                log = "A role " + role.name + " has been removed from <@" + str(target.id) + "> by " + context.author.name + "."
        elif category == self.warns:
            if mode == self.addwarn:
                log = "A warning has been issued to <@" + str(target.id) + "> by " + context.author.name + " for " + reason + "."
            else:
                log = context.author.name + " has cleared all warnings for <@" + str(target.id) + "> for " + reason + "."
        elif category == self.slowmodes:
            log = "Slowmode for channel <#" + str(channelid) + "> has been set to " + str(duration) + " seconds by " + context.author.name + "."
        elif category == self.unbans:
            log = ""
            if mode == self.noreason:
                log = "Caution! "
            try:
                log += "User <@" + str(target) + "> (user id " + str(target) + " ) has been unbanned by " + context.author.name + " for " + reason + "."
            except:
                return
        elif category == self.unbanreasons:
            log = "An unban reason has been provided by " + context.author.name + " for unbanning of <@" + str(target.id) + "> ( " + str(target.id) + " ): " + reason + "."
        elif category == self.temproles:
            if mode == self.addrole:
                log = "A temprole " + role.name + " has been issued to <@" + str(target.id) + "> by " + context.author.name + " until <t:" + str(duration) + ":F> for " + reason + "."
            else:
                log = "A temprole " + role.name + " has been prematurely removed from <@" + str(target.id) + "> by " + context.author.name + " for " + reason + "."
        await self.uploadlog(log, context)
        return
    def ready(self):
        guild = self.bot.get_guild(self.cfg.get("guild"))
        self.logchannel = guild.get_channel(self.logchannelid)
        if self.logchannel == None:
            raise Exception("No log channel defined.")
        return
        
    async def parseauditlogentry(self, logentry, recentunbans, recenttimeouts):
        print("got here2")
        mod = logentry.user
        target = logentry.target
        if mod.bot:
            print("got here3")
            return
        if log.action.unban:
            print("got here4")
            try:
                recentunbans.index(target.id)
                return
            except:
                await self.sendlog(self.unbans, context = mod.name, target = target.id, mode = self.noreason, reason = isemptyreason(""))
        elif log.action.member_update:
            print("Changes: " + str(log.changes))
        return