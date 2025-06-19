from extrafunctions import isvalidtime, isemptyreason, sanitizereason, getauthor

class timeouts:
    def __init__(self, cfg, bot, permmanager, log, responsemanager):
        self.cfg = cfg
        self.bot = bot
        self.pm = permmanager
        self.logm = log
        self.responsem = responsemanager
        
    async def issuetimeout(self, context, target, duration, reason, untimeout = False):
        author = getauthor(context)
        if untimeout:
            modreason = sanitizereason(author.name, reason = reason, duration = duration)
            if not target.timed_out:
                await self.responsem.respond(context, ":x: User isn't timed out.")
                return
            try:
                await target.timeout(until = None, reason = modreason)
            except:
                await self.responsem.respond(context, ":x: Couldn't remove timeout. I don't have permission.")
                return
            dmsuccess = await self.responsem.dm(target, ":warning: Your timeout has been removed by <@" + str(author.id) + "> for " + isemptyreason(reason) + ".")
            await self.responsem.respond(context, ":white_check_mark: Removed timeout from <@" + str(target.id) + ">.", dmsuccess = dmsuccess)
            await self.logm.sendlog(self.logm.timeouts, author, mode = self.logm.removetimeout, target = target.id, reason = isemptyreason(reason), dmsuccess = dmsuccess)
        else:
            time, untiltimestamp = isvalidtime(duration)
            if not time:
                await self.responsem.respond(context, ":x: Invalid timeout duration.")
                return
            # Issue timeout
            if target.timed_out:
                await self.responsem.respond(context, ":x: User is timed out already!")
                return
            modreason = sanitizereason(author.name, reason = reason, duration = duration)
            try:
                await target.timeout(time, reason = modreason)
            except:
                await self.responsem.respond(context, ":x: Couldn't issue timeout. I don't have permission.")
                return
            dmsuccess = await self.responsem.dm(target, ":warning: You have been timed out by <@" + str(author.id) + "> for " + isemptyreason(reason) + " until <t:" + str(untiltimestamp) + ":F>.")
            await self.responsem.respond(context, ":white_check_mark: Issued a timeout to <@" + str(target.id) + "> for " + duration + ".", dmsuccess = dmsuccess)
            await self.logm.sendlog(self.logm.timeouts, author, target = target.id, duration = [time, untiltimestamp], reason = isemptyreason(reason), dmsuccess = dmsuccess)
            return