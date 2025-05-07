from extrafunctions import isemptyreason, isvalidtime, getauthor, getdatefordb, sqldatetodateobject, gettimedifferencestr
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
    
    async def addwarn(self, context, target, reason, until):
        author = getauthor(context)
        expirydate, timestamp = isvalidtime(until)
        if not expirydate:
            await self.responsem.respond(context, "Invalid warn duration.")
            return
        untildate = expirydate.strftime("%Y-%m-%d %H:%M:%S")
        issuedate = getdatefordb()
        modreason = isemptyreason(reason)
        caseid = await self.sqlm.addwarning(author.id, target.id, issuedate, untildate, modreason)
        dmsuccess = await self.responsem.dm(target, "You have been issued a warning by <@" + str(author.id) + "> for " + modreason + ". This warning expires at <t:" + str(timestamp) + ":F>.")
        await self.responsem.respond(context, "User <@" + str(target.id) + "> has been issued a warning for " + isemptyreason(reason) + ".", dmsuccess = dmsuccess)
        await self.logm.sendlog(self.logm.warns, author, mode = self.logm.addwarn, target = target, reason = modreason, caseid = caseid, duration = timestamp)
        return
        
    async def clearwarns(self, context, target, reason):
        author = getauthor(context)
        permlevel = await self.pm.getpermissionlevel(author)
        try:
            if permlevel == 1:
                await self.sqlm.removewarnings(target.id, author.id)
                await self.responsem.respond(context, "Warnings for user <@" + str(target.id) + "> issued by you have been removed.")
                await self.logm.sendlog(self.logm.warns, author, target = target, mode = self.logm.selfclearwarns, reason = isemptyreason(reason))
            else:
                await self.sqlm.removewarnings(target.id)
                await self.responsem.respond(context, "All warnings for user <@" + str(target.id) + "> have been removed.")
                await self.logm.sendlog(self.logm.warns, author, target = target, mode = self.logm.clearwarns, reason = isemptyreason(reason))
        except:
            await self.responsem.respond(context, "Error removing warnings.")
        return
        
    async def getwarningmessage(self, member):
        warningscount, warnings = await self.sqlm.getwarnings(member.id)
        if warningscount == 0:
            message = "<@" + str(member.id) + "> has not received any warnings."
        else:
            message = "<@" + str(member.id) + "> has received " + str(warningscount) + " warnings. Here's the date, issuer and reason of the last ten warnings:"
            for warns in warnings:
                date, timestamp = sqldatetodateobject(warns[4])
                timediff = gettimedifferencestr(warns[4], warns[1])
                message += "\n<t:" + str(time) + ":R> - " + timediff + " - <@" + str(warns[0]) + "> - " + str(warns[2])
                message = message[:1999]
        return message