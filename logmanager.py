from extrafunctions import discorddatetodateobject, isemptyreason, getutctimestamp

import discord
import datetime

class logmanager:
    def __init__(self, cfg, bot):
        self.cfg = cfg
        self.bot = bot
        self.guild = ""
        self.logchannelid = ""
        self.logchannel = ""
        self.messagelogchannelid = ""
        self.messagelogchannel = ""
        self.loadlogchannelid()
        # categories of logs
        self.timeouts = 1
        self.roles = 2
        self.flooders = 3 # obsolete
        self.warns = 4
        self.selfissuedwarn = 5
        self.slowmodes = 6
        self.unbans = 7
        self.unbanreasons = 8 # obsolete
        self.temproles = 9
        self.bans = 10
        self.kicks = 11
        
        self.addrole = 1
        self.removerole = 2
        
        self.addwarn = 1
        self.clearwarns = 2
        self.noreason = 3
        self.selfclearwarns = 3
        
        self.removetimeout = 2
        
    def loadlogchannelid(self):
        self.logchannelid = self.cfg.get("logchannelid")
        self.messagelogchannelid = self.cfg.get("messagelogchannelid")
        if not self.logchannelid or self.logchannelid == 0 or not self.messagelogchannelid or self.messagelogchannelid == 0:
            raise Exception("Invalid log channel id")
        return
    async def getmodlogmessage(self, messageid):
        try:
            message = await self.logchannel.fetch_message(int(messageid))
        except:
            return False
        return message
    async def uploadlog(self, content, context):
        try:
            message = await self.logchannel.send(content)
        except:
            if not context:
                return None
            await context.respond("Error sending a message in the log channel.", ephemeral = False)
            return None
        return message
    async def editembed(self, message, embed):
        #try:
        await message.edit(embed = embed)
        #except:
        #    return False
        return True
    async def uploadembed(self, embed, ismessagelog = False):
        try:
            embed.add_field(name = "Date", value = "<t:" + getutctimestamp() + ":F>", inline = False)
            if ismessagelog:
                await self.messagelogchannel.send(embed = embed)
            else:
                await self.logchannel.send(embed = embed)
        except Exception as e:
            print(datetime.datetime.now())
            print(e)
        return
    async def sendlog(self, category, context, mode = False, target = False, duration = False, reason = False, role = False, channelid = False):
        embed = discord.Embed()
        if category == self.timeouts:
            embed.title = "Timeout add"
            embed.description = reason
            embed.color = discord.Colour.purple()
            embed.add_field(name = "Target", value = "<@" + str(target) + ">", inline = False)
            if mode == self.selfissuedwarn:
                embed.add_field(name = "Issuer", value = "<@" + str(context.user.id) + ">", inline = False)
                embed.add_field(name = "Until", value = "<t:" + str(duration) + ":F>", inline = False)
            elif mode == self.removetimeout:
                embed.add_field(name = "Issuer", value = "<@" + str(context.id) + ">", inline = False)
                embed.title = "Timeout remove"
            else:
                embed.add_field(name = "Issuer", value = "<@" + str(context.id) + ">", inline = False)
                embed.add_field(name = "Until", value = "<t:" + str(duration) + ":F>", inline = False)
        elif category == self.roles:
            embed.description = "Role: <@&" + str(role.id) + ">\nReason: " + reason
            embed.color = discord.Colour.magenta()
            if mode == self.addrole:
                embed.title = "Role added"
            else:
                embed.title = "Role removed"
            embed.add_field(name = "Target", value = "<@" + str(target.id) + ">", inline = False)
            embed.add_field(name = "Issuer", value = "<@" + str(context.author.id) + ">", inline = False)
        elif category == self.warns:
            embed.color = discord.Colour.dark_gray()
            embed.description = reason
            embed.add_field(name = "Target", value = "<@" + str(target.id) + ">", inline = False)
            embed.add_field(name = "Issuer", value = "<@" + str(context.author.id) + ">", inline = False)
            if mode == self.addwarn:
                embed.title = "Warn"
            elif mode == self.clearwarns:
                embed.title = "Clear all warns"
            else:
                embed.title = "Clear self-issued warns"
        elif category == self.slowmodes:
            embed.color = discord.Colour.teal()
            embed.title = "Slowmode"
            embed.add_field(name = "Target", value = "<#" + str(channelid) + ">", inline = False)
            embed.add_field(name = "Delay", value = str(duration) + " seconds", inline = False)
            embed.add_field(name = "Issuer", value = "<@" + str(context.author.id) + ">", inline = False)
        elif category == self.unbans:
            embed.title = "Unban"
            embed.description = reason
            embed.color = discord.Colour.green()
            embed.add_field(name = "Target", value = "<@" + str(target) + ">", inline = False)
            embed.add_field(name = "Issuer", value = "<@" + str(context.id) + ">", inline = False)
            #log = ""
            #if mode == self.noreason:
                #log = "Caution! "
            #try:
            #    log += "User <@" + str(target) + "> (user id " + str(target) + " ) has been unbanned by " + context + " for " + reason + "."
            #    logmessage = await self.uploadlog(log, context)
                #if logmessage is None:
                #    return
                #id = logmessage.id
                #message = log + "\nRun `/addunbanreason " + str(id) + " reason` to add an unban reason."
                #await logmessage.edit(content = message)
            #    return
            #except:
            #    return
        elif category == self.temproles:
            embed.description = "Role: <@&" + str(role.id) + ">\nReason: " + reason
            embed.color = discord.Colour.dark_blue()
            embed.add_field(name = "Target", value = "<@" + str(target.id) + ">", inline = False)
            embed.add_field(name = "Issuer", value = "<@" + str(context.author.id) + ">", inline = False)
            if mode == self.addrole:
                embed.title = "Add temprole"
                embed.add_field(name = "Until", value = "<t:" + str(duration) + ":F>", inline = False)
            else:
                embed.title = "Remove temprole"
        elif category == self.bans:
            embed.title = "Ban"
            embed.description = reason
            embed.color = discord.Colour.dark_red()
            embed.add_field(name = "Target", value = "<@" + str(target) + ">", inline = False)
            embed.add_field(name = "Issuer", value = "<@" + str(context.id) + ">", inline = False)
            #log = "A ban has been issued for <@" + str(target) + "> by " + str(context.name) + " for " + reason + "."
        elif category == self.kicks:
            embed.title = "Kick"
            embed.description = reason
            embed.color = discord.Colour.yellow()
            embed.add_field(name = "Target", value = "<@" + str(target) + ">", inline = False)
            embed.add_field(name = "Issuer", value = "<@" + str(context.id) + ">", inline = False)
        await self.uploadembed(embed)
        return
    def ready(self):
        self.guild = self.bot.get_guild(self.cfg.get("guild"))
        self.logchannel = self.guild.get_channel(self.logchannelid)
        self.messagelogchannel = self.guild.get_channel(self.messagelogchannelid)
        if self.logchannel is None or self.messagelogchannel is None:
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
                await self.sendlog(self.unbans, context = mod, target = targetid, mode = self.noreason, reason = isemptyreason(""))
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