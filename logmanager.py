from extrafunctions import discorddatetodateobject, isemptyreason

import discord

class logmanager:
    def __init__(self, cfg, bot):
        self.cfg = cfg
        self.bot = bot
        self.guild = ""
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
        self.bans = 10
        self.kicks = 11
        
        self.addrole = 1
        self.removerole = 2
        
        self.addwarn = 1
        self.clearwarns = 2
        self.noreason = 3
        
        self.removetimeout = 2
        
    def loadlogchannelid(self):
        self.logchannelid = self.cfg.get("logchannelid")
        if not self.logchannelid or self.logchannelid == 0:
            raise Exception("Invalid log channel id")
        return
    async def uploadlog(self, content, context):
        try:
            message = await self.logchannel.send(content)
        except:
            if not context:
                return None
            await context.respond("Error sending a message in the log channel.", ephemeral = False)
            return None
        return message
    async def sendlog(self, category, context, mode = False, target = False, duration = False, reason = False, role = False, channelid = False):
        log = "No appropriate log category has been found."
        if category == self.timeouts:
            if mode == self.selfissuedwarn:
                log = "A timeout has been issued to <@" + str(target) + "> by " + context.user.name + " until <t:" + str(duration) + ":F> for " + reason + "."
            elif mode == self.removetimeout:
                log = "A timeout has been prematurely removed from <@" + str(target) + "> by " + context.name + " for " + reason + "."
            else:
                log = "A timeout has been issued to <@" + str(target) + "> by " + context.name + " until <t:" + str(duration) + ":F> for " + reason + "."
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
                log += "User <@" + str(target) + "> (user id " + str(target) + " ) has been unbanned by " + context + " for " + reason + "."
                logmessage = await self.uploadlog(log, context)
                if logmessage is None:
                    return
                id = logmessage.id
                message = log + "\nRun `/addunbanreason " + str(id) + " reason` to add an unban reason."
                await logmessage.edit(content = message)
                return
            except:
                return
        elif category == self.unbanreasons:
            log = "An unban reason has been provided by " + context.author.name + " for unbanning of <@" + str(target.id) + "> ( " + str(target.id) + " ): " + reason + "."
        elif category == self.temproles:
            if mode == self.addrole:
                log = "A temprole " + role.name + " has been issued to <@" + str(target.id) + "> by " + context.author.name + " until <t:" + str(duration) + ":F> for " + reason + "."
            else:
                log = "A temprole " + role.name + " has been prematurely removed from <@" + str(target.id) + "> by " + context.author.name + " for " + reason + "."
        elif category == self.bans:
            log = "A ban has been issued for <@" + str(target) + "> by " + str(context.name) + " for " + reason + "."
        elif category == self.kicks:
            log = "A kick has been issued for <@" + str(target) + "> by " + str(context.name) + " for " + reason + "."
        await self.uploadlog(log, context)
        return
    def ready(self):
        self.guild = self.bot.get_guild(self.cfg.get("guild"))
        self.logchannel = self.guild.get_channel(self.logchannelid)
        if self.logchannel == None:
            raise Exception("No log channel defined.")
        return
        
    async def parserawauditlogentry(self, logentry, recentunbans, recenttimeouts):
        modid = logentry.user_id
        targetid = logentry.target_id
        
        kick = discord.AuditLogAction.kick
        ban = discord.AuditLogAction.ban
        unban = discord.AuditLogAction.unban
        member_update = discord.AuditLogAction.member_update
        
        loggableactions = [kick, ban, unban, member_update]
        type = logentry.action_type
        if type not in loggableactions:
            #print("Action: " + str(logentry.action) + " not in " + str(loggableactions))
            return
        #print("code continue")
        mod = self.guild.get_member(modid)
        if mod is None:
            try:
                mod = await self.guild.fetch_member(modid)
            except:
                return
        if mod.bot:
            return
        if type == unban:
            try:
                recentunbans.index(target.id)
                return
            except:
                await self.sendlog(self.unbans, context = mod.name, target = targetid, mode = self.noreason, reason = isemptyreason(""))
        elif type == member_update:
            for x in logentry.changes:
                if x.get("key") == "communication_disabled_until":
                    if x.get("new_value"):
                        date, timestamp = discorddatetodateobject(x.get("new_value"))
                        await self.sendlog(self.timeouts, context = mod, target = targetid, duration = timestamp, reason = isemptyreason(logentry.reason))
                    else:
                        await self.sendlog(self.timeouts, context = mod, mode = self.removetimeout, target = targetid, reason = isemptyreason(logentry.reason))
        elif type == ban:
            await self.sendlog(self.bans, context = mod, target = targetid, reason = isemptyreason(logentry.reason))
        elif type == kick:
            await self.sendlog(self.kicks, context = mod, target = targetid, reason = isemptyreason(logentry.reason))
        return