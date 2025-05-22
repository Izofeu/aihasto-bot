from extrafunctions import getauthor, sanitizereason, isemptyreason

class bans:
    def __init__(self, cfg, bot, pm, log, sql, responsem):
        self.cfg = cfg
        self.bot = bot
        self.pm = permmanager
        self.logm = log
        self.sqlm = sql
        self.responsem = responsem
        
    async def ban(self, context, target, reason, deletemessages):
        # Command permission level
        commandpermissionlevel = 2
        # Permission check
        canrun = await pm.canrun(context, context.author, target = target, commandpermissionlevel = commandpermissionlevel)
        if not canrun:
            return
        author = getauthor(context)
        banreason = sanitizereason(author.name, reason = reason, ban = True)
        secondscount = 86400 if deletemessages else 0
        try:
            await author.guild.ban(target, secoundscount, banreason)
        except:
            await self.responsem.respond(context, ":x: Couldn't ban the user! The user either left the server, or I don't have sufficient permissions!")
            return
        await self.logm.sendlog(logm.bans, context = author, target = target.id, reason = isemptyreason(reason))
        await self.responsem.respond(context, ":white_check_mark: Successfully banned <@" + str(target.id) + ">!")
        return
        
    async def unban(self, context, target, reason):
        # Command permission level
        commandpermissionlevel = 3
        # Permission check
        canrun = await pm.canrun(context, context.author, commandpermissionlevel = commandpermissionlevel)
        if not canrun:
            return
        author = getauthor(context)
        unbanreason = sanitizereason(author.name, reason = reason, unban = True)
        try:
            await author.guild.unban(target, unbanreason)
        except:
            await self.responsem.respond(context, ":x: Couldn't unban the user! The user isn't banned!")
            return
        await self.logm.sendlog(logm.unbans, context = author, target = target.id, reason = isemptyreason(reason))
        await self.responsem.respond(context, ":white_check_mark: Successfully unbanned <@" + str(target.id) + ">!")
        return