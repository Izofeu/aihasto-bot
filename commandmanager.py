from extrafunctions import isemptyreason, amiauthor
import p_timeouts
import p_warns
import g_slowmodes
import discord
import c_ui

class cmdmanager:
    def __init__(self, cfg, bot, pm, sql, rolemanager, log):
        # Load managers
        self.cfg = cfg
        self.bot = bot
        self.pm = pm
        self.sqlm = sql
        self.rolem = rolemanager
        self.logm = log
        
        self.timeouts = p_timeouts.timeouts(cfg, bot, pm, log)
        self.warns = p_warns.warns(cfg, bot, pm, log, sql)
        self.slowmodes = g_slowmodes.slowmodes(cfg, bot, pm, log)
        
    async def timeout(self, context, target, duration, reason, isslash, untimeout = False):
        await self.timeouts.issuetimeout(context, target, duration, reason, isslash, untimeout)
        return
        
    async def setslowmode(self, context, target, delay):
        await self.slowmodes.setslowmode(context, target, delay)
        return
        
    async def warn(self, context, target = False, reason = False, clearwarns = False, showwarns = False):
        if showwarns:
            await self.warns.showwarnings(context, target)
        elif clearwarns:
            await self.warns.clearwarns(context, target, reason)
        else:
            await self.warns.addwarn(context, target, reason)
        return
        
    async def temprole(self, context, target, mode, roletype, duration = False, reason = False, interaction = False):
        role, timestamp, reason = await self.rolem.temprole(context, target, mode, roletype, duration = duration, reason = reason, interaction = interaction)
        if not role:
            return
        if mode == self.rolem.addtemprole:
            message = "You have been issued a " + role.name + " role by <@" + str(context.author.id) + "> until <t:" + str(timestamp) + ":F> for " + reason + "."
        else:
            message = "You have been prematurely removed from a " + role.name + " role by <@" + str(context.author.id) + "> for " + reason + "."
        try:
            await target.send(message)
        except:
            pass
        return
        
    async def openfloodermenu(self, context, target):
        flooderui = c_ui.flooderui(context, target, self.rolem, self.temprole)
        await context.send_modal(flooderui)
        return
        
    async def editreason(self, context, messageid, reason):
        message = await self.logm.getmodlogmessage(messageid)
        if not message:
            await self.pm.throwerror(context, "Could not fetch the message. Check the message ID.")
            return
        if not amiauthor(message, self.cfg.get("botid")):
            await self.pm.throwerror(context, "Only messages sent by me can be edited.")
            return
        try:
            embed = message.embeds[0]
        except:
            await self.pm.throwerror(context, "This message doesn't have embeds.")
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
                    if context.author.id != issuerid:
                        permlevel = self.pm.getpermissionlevel(context.author)
                        if permlevel < 3:
                            await self.pm.throwerror(context, "You are not the author of this punishment. Ask Mita's Arms for assistance.")
                            return
                except:
                    await self.pm.throwerror(context, "Couldn't fetch permissions for embed edit.")
                    return False
                break
        if not foundfield:
            await self.pm.throwerror(context, "This message doesn't have an Issuer field so its reason cannot be edited.")
            return
        if alreadyedited:
            embed.remove_field(0)
        embed.insert_field_at(index = 0, name = "Edited reason", value = "<@" + str(context.author.id) + "> - " + isemptyreason(reason), inline = False)
        await self.logm.editembed(message, embed)
        await context.respond("Successfully edited the embed.", ephemeral = True)
        return