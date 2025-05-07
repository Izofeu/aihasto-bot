from extrafunctions import isemptyreason, amiauthor, getauthor, sqldatetodateobject, datetotimestamp, gettimedifferencestr, getguild, preparemessagelog, getutctimestamp
import p_timeouts
import p_warns
import g_slowmodes
import discord
import c_ui
import datetime
import notemanager

class cmdmanager:
    def __init__(self, cfg, bot, pm, sql, rolemanager, log, responsemanager):
        # Load managers
        self.cfg = cfg
        self.bot = bot
        self.pm = pm
        self.sqlm = sql
        self.rolem = rolemanager
        self.logm = log
        self.responsem = responsemanager
        self.notem = notemanager.notemanager(cfg, sql, responsemanager, log)
        
        self.timeouts = p_timeouts.timeouts(cfg, bot, pm, log, responsemanager)
        self.warns = p_warns.warns(cfg, bot, pm, log, sql, responsemanager)
        self.slowmodes = g_slowmodes.slowmodes(cfg, bot, pm, log)
        
    async def enablereports(self, context, channel, linkedthread):
        if not str(channel.type) == "text" or not str(linkedthread.type) == "public_thread":
            await self.responsem.respond(context, "The channel must be a text channel and the linked thread must be a public thread.")
            return
        if linkedthread.parent_id != self.cfg.get("modqueuechannelid"):
            await self.responsem.respond(context, "The selected thread does not belong to the mod queue channel.")
            return
        cfgstring = "queuechannel_" + str(channel.id)
        self.cfg.set(cfgstring, linkedthread.id)
        await self.responsem.respond(context, "Enabled reports in <#" + str(channel.id) + "> -> <#" + str(linkedthread.id) + ">.")
        return
        
    async def customreportminlength(self, context, channel, minlimit):
        if minlimit not in range(0, 100):
            await self.responsem.respond(context, "The length must be in range 0-100.")
            return
        cfgstring = "customlimit_" + str(channel.id)
        self.cfg.set(cfgstring, str(minlimit))
        await self.responsem.respond(context, "Set the limit of " + str(minlimit) + " characters for reports in <#" + str(channel.id) + ">.")
        return
        
    async def disablereports(self, context, channel):
        cfgstring = "queuechannel_" + str(channel.id)
        self.cfg.set(cfgstring, None)
        await self.responsem.respond(context, "Disabled reports in <#" + str(channel.id) + ">.")
        return
        
    async def reportmessage(self, context, message):
        if self.cfg.get("maxallowedreports") == 0:
            await self.responsem.respond(context, "The reports system is globally disabled.")
            return
        permissionlevel = await self.pm.getpermissionlevel(message.author)
        if permissionlevel > 0 or message.author.bot:
            await self.responsem.respond(context, "You cannot report moderator messages.")
            return
        reportcount = await self.sqlm.getreportcount(context.author.id)
        if reportcount >= self.cfg.get("maxallowedreports"):
            await self.responsem.respond(context, "You have exceeded the maximum amount of pending reports. Please wait for your reports to get resolved before submitting more reports.")
            return
        cfgstring = "queuechannel_" + str(message.channel.id)
        try:
            threadid = self.cfg.get(cfgstring)
        except:
            await self.responsem.respond(context, "The reporting system is not enabled for this channel.")
            return
        try:
            guild = getguild(self.cfg, self.bot)
            queuechannel = await guild.fetch_channel(self.cfg.get("modqueuechannelid"))
        except:
            await self.responsem.respond(context, "Couldn't fetch the mod queue channel. Contact administrators for help.")
            return
        modthread = queuechannel.get_thread(threadid)
        if modthread is None:
            await self.responsem.respond(context, "Couldn't fetch the queue thread. Contact administrators for help.")
            return
        try:
            cfgstring = "customlimit_" + str(message.channel.id)
            minlength = self.cfg.get(cfgstring)
        except:
            minlength = 10
        reportui = c_ui.reportui(message, modthread, self.submitreport, minlength = minlength)
        await context.send_modal(reportui)
        return
        
    async def submitreport(self, context, message, reason, modthread):
        author = getauthor(context)
        reason = isemptyreason(reason)
        wasreported, modid = await self.sqlm.addreport(author.id, message.id)
        if wasreported:
            await self.responsem.respond(context, "This message has already been reported!")
            return
        embed = discord.Embed()
        embed.title = "Message copy (Report)"
        embed.color = discord.Colour.green()
        preparedmessage, prepareddescription, preparedtitle, attachmentlinks, stickers = preparemessagelog(self.cfg, message)
        embed.description = prepareddescription
        preparedtitle = "Old message:" + preparedtitle
        embed.add_field(name = preparedtitle, value = preparedmessage, inline = False)
        if attachmentlinks:
            embed.add_field(name = "Attachments:", value = attachmentlinks, inline = False)
        if stickers:
            embed.add_field(name = "Stickers:", value = stickers, inline = False)
        
        copiedmessage = await self.logm.uploadembed(embed, ismessagelog = True)
        messagelink = "https://discord.com/channels/" + str(self.cfg.get("guild")) + "/" + str(message.channel.id) + "/" + str(message.id)
        reportedcontent = "Message link: " + messagelink
        reportedcontent += "\nMessage copy: https://discord.com/channels/" + str(self.cfg.get("guild")) + "/" + str(copiedmessage.channel.id) + "/" + str(copiedmessage.id)
        description = "Reason: " + reason
        description += "\n" + reportedcontent

        embed = discord.Embed()
        embed.description = description
        embed.color = discord.Colour.light_gray()
        embed.title = "Report"
        embed.add_field(name = "Target", value = "<@" + str(message.author.id) + ">", inline = False)
        embed.add_field(name = "Reporter", value = "<@" + str(author.id) + ">", inline = False)
        embed.add_field(name = "Case ID", value = str(modid), inline = False)
        embed.add_field(name = "Date", value = "<t:" + getutctimestamp() + ":F>", inline = False)
        resolvedbutton = c_ui.resolvereportbutton(self.sqlm, self.responsem)
        threadmessage = await modthread.send(embed = embed, view = resolvedbutton)
        lines = embed.description.split("\n")
        embed.description = ""
        for line in lines:
            if line.startswith("Message copy:"):
                continue
            embed.description += line + "\n"
        await self.responsem.dm(target = author, message = ("A copy of your submitted report is available below.\nYou will receive a confirmation " +
            "when your report gets resolved."), embed = embed)
        resolvedbutton.sethook(threadmessage)
        await threadmessage.add_reaction("🙋‍♂️")
        await self.responsem.respond(context, ":white_check_mark: Reported " + messagelink + " by <@" + str(message.author.id) + "> successfully.")
        return
        
    async def timeout(self, context, target, duration, reason, untimeout = False):
        await self.timeouts.issuetimeout(context, target, duration, reason, untimeout)
        return
        
    async def setslowmode(self, context, target, delay):
        await self.slowmodes.setslowmode(context, target, delay)
        return
        
    async def warn(self, context, target = False, reason = False, clearwarns = False):
        if clearwarns:
            await self.warns.clearwarns(context, target, reason)
        else:
            await self.warns.addwarn(context, target, reason)
        return
        
    async def showpunishmenthistory(self, context, member):
        await context.defer(ephemeral = True)
        history = await self.sqlm.getpunishments(member.id)
        #[0][0-1] - floodercount, flooders (issuer_id, issue_date, reason)
        #[1][0-1] - warncount, warns (issuer_id, expiration_date, reason, issue_date)
        #[2][0-1] - timeoutcount, timeouts (issuer_id, expiration_date, issue_date, reason)
        if history[0][0] == 0 and history[1][0] == 0 and history[2][0] == 0:
            message = "User <@" + str(member.id) + "> has no punishment history."
        else:
            message = "User <@" + str(member.id) + "> has received following punishments:"
            for flooder in history[0][1]:
                date, timestamp = sqldatetodateobject(flooder[1])
                message += "\n:ocean: <t:" + str(timestamp) + ":R> - <@" + str(flooder[0]) + "> - " + flooder[2]
                
            for warn in history[1][1]:
                date, timestamp = sqldatetodateobject(warn[1])
                issuedate, issuetimestamp = sqldatetodateobject(warn[3])
                diffstr = gettimedifferencestr(date, issuedate)
                message += "\n:warning: <t:" + str(issuetimestamp) + ":R> - " + diffstr + " - <@" + str(warn[0]) + "> - " + warn[2]
                
            for timeout in history[2][1]:
                expirationdate, expirationtimestamp = sqldatetodateobject(timeout[1])
                issuedate, issuetimestamp = sqldatetodateobject(timeout[2])
                timediff = gettimedifferencestr(expirationdate, issuedate)
                message += "\n:mute: <t:" + str(issuetimestamp) + ":R> - " + timediff + " - <@" + str(timeout[0]) + "> - " + timeout[3]
                
        message += "\n"
        
        count, nonremovedroles = await self.sqlm.getactivetemproles(member.id, self.rolem.flooderrole)
        if count == 0:
            message += "\nUser <@" + str(member.id) + "> has no temproles active."
        else:
            message += "\nUser <@" + str(member.id) + "> has following temproles active:"
            # `issuer_id`, `expiration_date`, `role_type`, `reason`
            for record in nonremovedroles:
                _, timestamp = sqldatetodateobject(record[1])
                roleid = self.rolem.getroleid(record[2])
                message += "\n<@&" + str(roleid) + "> - expires <t:" + str(timestamp) + ":R> - <@" + str(record[0]) + "> - " + record[3]
                
        addflooderui = c_ui.newflooderui(member, self.rolem, self.pm.canrun)
        addtimeoutui = c_ui.newtimeoutui(member, self.timeouts.issuetimeout, self.pm.canrun)
        addwarnui = c_ui.newwarnui(member, self.warns.addwarn, self.pm.canrun)
        punishmentbuttons = c_ui.punishmentbuttons(self.pm, member, addwarnui, addtimeoutui, addflooderui)
        response = await self.responsem.respond(context, message, view = punishmentbuttons)
        punishmentbuttons.sethook(response)
        return
        
    async def temprole(self, context, target, mode, roletype, duration = False, reason = False):
        author = getauthor(context)
        await self.rolem.temprole(context, target, mode, roletype, duration = duration, reason = reason)
        return
        
    async def role(self, context, target, role, reason):
        await self.rolem.role(context, target, role, reason)
        return
        
    async def openeditreasonmenu(self, context, message):
        editreasonmenu = c_ui.editreasonui(message, self)
        await context.send_modal(editreasonmenu)
        return
        
    async def editreason(self, context, message, reason):
        author = getauthor(context)
        if not amiauthor(message, self.cfg.get("botid")):
            await self.responsem.respond(context, "Only messages sent by me can be edited.")
            return
        try:
            embed = message.embeds[0]
        except:
            await self.responsem.respond(context, "This message doesn't have embeds.")
            return
        title = embed.title
        fields = embed.fields
        foundfield = alreadyedited = caseid = False
        for field in fields:
            if field.name == "Edited reason":
                alreadyedited = True
            elif field.name == "Case ID":
                caseid = field.value
            elif field.name == "Issuer":
                foundfield = field
                issuerid = field.value
                try:
                    issuerid = issuerid[2:-1]
                    issuerid = int(issuerid)
                    if author.id != issuerid:
                        permlevel = await self.pm.getpermissionlevel(author)
                        if permlevel < 3:
                            await self.responsem.respond(context, "You are not the author of this punishment. Ask Mita's Arms for assistance.")
                            return
                except:
                    await self.responsem.respond(context, "Couldn't fetch permissions for embed edit.")
                    return False
        if not foundfield:
            await self.responsem.respond(context, "This message doesn't have an Issuer field so its reason cannot be edited.")
            return
        if alreadyedited:
            embed.remove_field(0)
        embed.insert_field_at(index = 0, name = "Edited reason", value = "<@" + str(author.id) + "> - " + isemptyreason(reason), inline = False)
        responsemessage = "Successfully edited the embed."
        if caseid:
            if title == "Warn":
                await self.sqlm.updatewarnreason(caseid, isemptyreason(reason))
                responsemessage += " Edited the database record."
            elif title == "Timeout add":
                await self.sqlm.updatetimeoutreason(caseid, isemptyreason(reason))
                responsemessage += " Edited the database record."
            elif title == "Add temprole":
                await self.sqlm.updatetemprolereason(caseid, isemptyreason(reason))
                responsemessage += " Edited the database record."
        await self.logm.editembed(message, embed)
        await self.responsem.respond(context, responsemessage)
        return
        
    async def assign(self, context, target, assigner = False, reason = False, remove = False, root = False):
        author = getauthor(context)
        commandpermissionlevel = 2
        if assigner or root:
            commandpermissionlevel = 4
        canrun = await self.pm.canrun(context, author, target = target, commandpermissionlevel = commandpermissionlevel, useroverride = True, shoulderoverride = True)
        if not canrun:
            return
        if assigner:
            author = assigner
        if remove:
            await self.notem.assign(context, author.id, target.id, self.notem.unassignnote)
        else:
            await self.notem.assign(context, author.id, target.id, self.notem.assignnote, reason, root)
        return
        
    async def showassigner(self, context, target):
        await self.notem.getnote(context, target.id, self.notem.t_assign)
        return
        
    async def generatemodtree(self, context):
        await self.notem.generatetree(context)
        return