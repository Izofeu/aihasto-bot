import p_timeouts
import p_warns
import g_slowmodes

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
        
    async def timeout(self, context, target, duration, reason, isslash):
        await self.timeouts.issuetimeout(context, target, duration, reason, isslash)
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
        
    async def temprole(self, context, target, mode, roletype, duration = False, reason = False):
        role, timestamp, reason, success = await self.rolem.temprole(context, target, mode, roletype, duration = duration, reason = reason)
        if not role:
            return
        if mode == self.rolem.addtemprole:
            message = "You have been issued a " + role.name + " role by <@" + str(context.author.id) + "> until <t:" + str(timestamp) + ":F> for " + reason + "."
        else:
            if success:
                message = "You have been prematurely removed from a " + role.name + " role by <@" + str(context.author.id) + " for " + reason + "."
            else:
                return
        await target.send(message)
        return