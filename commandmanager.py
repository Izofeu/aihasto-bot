import p_flooders

class cmdmanager:
    def __init__(self, cfg, bot, permmanager, sql, rolemanager, log):
        # Load managers
        self.cfg = cfg
        self.bot = bot
        self.pm = permmanager
        self.sqlm = sql
        self.rolem = rolemanager
        self.logm = log
        
        self.flooders = p_flooders.flooders(cfg, bot, permmanager, log, sql)
        
    async def flooder(self, context, target, duration, reason, isslash, unflooder):
        await self.flooders.issueflooder(context, target, duration, reason, isslash, unflooder)
        return