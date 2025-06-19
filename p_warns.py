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
            await self.responsem.respond(context, ":x: Invalid warn duration.")
            return
        untildate = expirydate.strftime("%Y-%m-%d %H:%M:%S")
        issuedate = getdatefordb()
        modreason = isemptyreason(reason)
        caseid = await self.sqlm.addwarning(author.id, target.id, issuedate, untildate, modreason)
        dmsuccess = await self.responsem.dm(target, (":warning: You have been issued a warning by <@" + str(author.id) + "> for " + modreason +
        " (Case ID: " + str(caseid) + "). This warning expires at <t:" + str(timestamp) + ":F>."))
        await self.responsem.respond(context, ":white_check_mark: User <@" + str(target.id) + "> has been issued a warning for " + isemptyreason(reason) + ".", dmsuccess = dmsuccess)
        await self.logm.sendlog(self.logm.warns, author, mode = self.logm.addwarn, target = target, reason = modreason, caseid = caseid, duration = timestamp, dmsuccess = dmsuccess)
        return