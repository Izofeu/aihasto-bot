from extrafunctions import isemptyreason, amiauthor, getauthor, sqldatetodateobject, datetotimestamp, gettimedifferencestr
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
        #[1][0-1] - warncount, warns (issuer_id, expiration_date, reason)
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
                # Warns only have expiration date which is 3 days into the future
                date = date - datetime.timedelta(days = 3)
                timestamp = datetotimestamp(date)
                message += "\n:warning: <t:" + str(timestamp) + ":R> - <@" + str(warn[0]) + "> - " + warn[2]
                
            for timeout in history[2][1]:
                expirationdate, expirationtimestamp = sqldatetodateobject(timeout[1])
                issuedate, issuetimestamp = sqldatetodateobject(timeout[2])
                timediff = gettimedifferencestr(expirationdate, issuedate)
                message += "\n:mute: <t:" + str(issuetimestamp) + ":R> - " + timediff + " - <@" + str(timeout[0]) + "> - " + timeout[3]
                
        addflooderui = c_ui.newflooderui(member, self.rolem, self.pm.canrun)
        addtimeoutui = c_ui.newtimeoutui(member, self.timeouts.issuetimeout, self.pm.canrun)
        addwarnui = c_ui.newwarnui(member, self.warns.addwarn, self.pm.canrun)
        punishmentbuttons = c_ui.punishmentbuttons(self.pm, member, addwarnui, addtimeoutui, addflooderui)
        response = await self.responsem.respond(context, message, view = punishmentbuttons)
        punishmentbuttons.sethook(response)
        return
        
    async def temprole(self, context, target, mode, roletype, duration = False, reason = False):
        author = getauthor(context)
        role, timestamp, reason = await self.rolem.temprole(context, target, mode, roletype, duration = duration, reason = reason)
        if not role:
            return
        if mode == self.rolem.addtemprole:
            message = "You have been issued a " + role.name + " role by <@" + str(author.id) + "> until <t:" + str(timestamp) + ":F> for " + reason + "."
        else:
            message = "You have been prematurely removed from a " + role.name + " role by <@" + str(author.id) + "> for " + reason + "."
        try:
            await target.send(message)
        except:
            pass
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
        fields = embed.fields
        foundfield = alreadyedited = False
        for field in fields:
            if field.name == "Edited reason":
                alreadyedited = True
            elif field.name == "Issuer":
                foundfield = field
                issuerid = field.value
                try:
                    issuerid = issuerid[2:-1]
                    issuerid = int(issuerid)
                    if author.id != issuerid:
                        permlevel = self.pm.getpermissionlevel(author)
                        if permlevel < 3:
                            await self.responsem.respond(context, "You are not the author of this punishment. Ask Mita's Arms for assistance.")
                            return
                except:
                    await self.responsem.respond(context, "Couldn't fetch permissions for embed edit.")
                    return False
                break
        if not foundfield:
            await self.responsem.respond(context, "This message doesn't have an Issuer field so its reason cannot be edited.")
            return
        if alreadyedited:
            embed.remove_field(0)
        embed.insert_field_at(index = 0, name = "Edited reason", value = "<@" + str(author.id) + "> - " + isemptyreason(reason), inline = False)
        await self.logm.editembed(message, embed)
        await self.responsem.respond(context, "Successfully edited the embed.")
        return
        
    async def assign(self, context, target, assigner = False, reason = False, remove = False):
        author = getauthor(context)
        commandpermissionlevel = 2
        if assigner:
            commandpermissionlevel = 4
        canrun = await self.pm.canrun(context, author, target = target, commandpermissionlevel = commandpermissionlevel, useroverride = True)
        if not canrun:
            return
        if assigner:
            author = assigner
        if remove:
            await self.notem.assign(context, author.id, target.id, self.notem.unassignnote)
        else:
            await self.notem.assign(context, author.id, target.id, self.notem.assignnote, reason)
        return
        
    async def showassigner(self, context, target):
        await self.notem.getnote(context, target, self.notem.t_assign)
        return