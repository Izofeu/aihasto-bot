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
            try:
                # Unissue timeout
                modreason = sanitizereason(author.name, reason = reason, duration = duration)
                if not target.timed_out:
                    raise Exception("User is not timed out.")
                await target.timeout(until = None, reason = modreason)
                await self.responsem.respond(context, "User <@" + str(target.id) + "> has had their time-out removed for " + isemptyreason(reason) + ".")
                await self.logm.sendlog(self.logm.timeouts, author, mode = self.logm.removetimeout, target = target.id, reason = isemptyreason(reason))
            except:
                await self.responsem.respond(context, "Error removing a timeout. User probably isn't timed out.")
        else:
            time, untiltimestamp = isvalidtime(duration)
            if not time:
                await self.responsem.respond(context, "Invalid timeout duration.")
                return
            try:
                # Issue timeout
                if target.timed_out:
                    await self.responsem.respond(context, "User is timed out already!")
                    return
                modreason = sanitizereason(author.name, reason = reason, duration = duration)
                await target.timeout(time, reason = modreason)
                dmsuccess = await self.responsem.dm(target, "You have been timed out by <@" + str(author.id) + "> for " + isemptyreason(reason) + " until <t:" + str(untiltimestamp) + ":F>.")
                await self.responsem.respond(context, "User <@" + str(target.id) + "> has been timed out for " + duration + ".", dmsuccess = dmsuccess)
                await self.logm.sendlog(self.logm.timeouts, author, target = target.id, duration = [time, untiltimestamp], reason = isemptyreason(reason))
            except:
                await self.responsem.respond(context, "Error issuing a timeout. Check bot permissions.")
            return