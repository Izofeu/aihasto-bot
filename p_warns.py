from extrafunctions import isemptyreason, isvalidtime
import datetime
import discord
import c_ui

class warns:
    def __init__(self, cfg, bot, permmanager, log, sql, responsem):
        self.cfg = cfg
        self.bot = bot
        self.pm = permmanager
        self.logm = log
        self.sqlm = sql
        self.responsem = responsem
    
    async def addwarn(self, context, target, reason, interaction = False):
        expirydate = isvalidtime("3d")[0].strftime("%Y-%m-%d %H:%M:%S")
        modreason = isemptyreason(reason)
        await self.sqlm.addwarning(context.author.id, target.id, expirydate, modreason)
        await self.responsem.respond(context, self.responsem.s_addedwarning, target.id, modreason)
        await self.logm.sendlog(self.logm.warns, context, mode = self.logm.addwarn, target = target, reason = modreason)
        try:
            await target.send("You have been issued a warning by <@" + str(context.author.id) + "> for " + modreason + ".")
        except:
            pass
        return
        
    async def clearwarns(self, context, target, reason):
        permlevel = self.pm.getpermissionlevel(context.author)
        try:
            if permlevel == 1:
                await self.sqlm.removewarnings(target.id, context.author.id)
                await context.respond("Warnings for user <@" + str(target.id) + "> issued by you have been removed.", ephemeral = True)
                await self.logm.sendlog(self.logm.warns, context, target = target, mode = self.logm.selfclearwarns, reason = isemptyreason(reason))
            else:
                await self.sqlm.removewarnings(target.id)
                await context.respond("All warnings for user <@" + str(target.id) + "> have been removed.", ephemeral = True)
                await self.logm.sendlog(self.logm.warns, context, target = target, mode = self.logm.clearwarns, reason = isemptyreason(reason))
        except:
            await self.pm.throwerror(context, "Error removing warnings.")
        return
        
    async def getwarningmessage(self, member):
        warningscount, warnings = await self.sqlm.getwarnings(member.id)
        if warningscount == 0:
            message = "<@" + str(member.id) + "> has not received any warnings."
        else:
            message = "<@" + str(member.id) + "> has received " + str(warningscount) + " warnings. Here's the date, issuer and reason of the last ten warnings:"
            #print(warnings)
            #print(len(warnings))
            format = "%Y-%m-%d %H:%M:%S %z"
            for warns in warnings:
                date = warns[1] - datetime.timedelta(days = 3)
                # datetime object assumes timezone of the machine
                # this part of code recreates the object with utc timezone
                date = str(date)
                date += " +0000"
                date = datetime.datetime.strptime(date, format)
                time = int(date.timestamp())
                message += "\n<t:" + str(time) + ":R> - <@" + str(warns[0]) + "> - " + str(warns[2])
                message = message[:1999]
        return message