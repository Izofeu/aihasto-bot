from extrafunctions import isvalidtime, isemptyreason, sanitizereason

class timeouts:
    def __init__(self, cfg, bot, permmanager, log):
        self.cfg = cfg
        self.bot = bot
        self.pm = permmanager
        self.logm = log
    async def issuetimeout(self, context, target, duration, reason, isslash, untimeout):
        if untimeout:
            try:
                # Issue timeout
                modreason = sanitizereason(context.author.name, reason = reason, duration = duration)
                if not target.timed_out:
                    raise Exception("User is not timed out.")
                await target.timeout(until = None, reason = modreason)
                await context.respond("User <@" + str(target.id) + "> has had their time-out removed for " + isemptyreason(reason) + ".", ephemeral = True)
                await self.logm.sendlog(self.logm.timeouts, context.author, mode = self.logm.removetimeout, target = target.id, reason = isemptyreason(reason))
            except:
                await context.respond("Error removing a timeout. User probably isn't timed out.", ephemeral = True)
        elif isslash:
            time, untiltimestamp = isvalidtime(duration)
            if not time:
                await self.pm.throwerror(context, "Invalid timeout duration.")
                return
            try:
                # Issue timeout
                modreason = sanitizereason(context.author.name, reason = reason, duration = duration)
                await target.timeout(time, reason = modreason)
                try:
                    await target.send(content = "You have been timed out by <@" + str(context.author.id) + "> for " + isemptyreason(reason) + " until <t:" + str(untiltimestamp) + ":F>.")
                except:
                    pass
                await context.respond("User <@" + str(target.id) + "> has been timed out for " + duration + ".", ephemeral = True)
                await self.logm.sendlog(self.logm.timeouts, context.author, target = target.id, duration = [time, untiltimestamp], reason = isemptyreason(reason))
            except:
                await context.respond("Error issuing a timeout. Check bot permissions.", ephemeral = True)
            return
        else:
            return