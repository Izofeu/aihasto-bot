import p_flooders
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
        
        self.flooders = p_flooders.flooders(cfg, bot, pm, log, sql)
        self.timeouts = p_timeouts.timeouts(cfg, bot, pm, log)
        self.warns = p_warns.warns(cfg, bot, pm, log, sql)
        self.slowmodes = g_slowmodes.slowmodes(cfg, bot, pm, log)
        
    async def flooder(self, context, target, duration, reason, isslash, unflooder):
        await self.flooders.issueflooder(context, target, duration, reason, isslash, unflooder)
        return
        
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