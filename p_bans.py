from extrafunctions import getauthor, sanitizereason, isemptyreason

class bans:
    def __init__(self, cfg, bot, pm, log, sql, responsem):
        self.cfg = cfg
        self.bot = bot
        self.pm = pm
        self.logm = log
        self.sqlm = sql
        self.responsem = responsem
        
    async def ban(self, context, target, reason, deletemessages):
        author = getauthor(context)
        # Command permission level
        commandpermissionlevel = 2
        # Permission check
        canrun = await self.pm.canrun(context, author, target = target, commandpermissionlevel = commandpermissionlevel, useroverride = True)
        if not canrun:
            return
        banreason = sanitizereason(author.name, reason = reason, ban = True)
        secondscount = 86400 if deletemessages else 0
        try:
            await author.guild.fetch_ban(target)
            await self.responsem.respond(context, ":x: The user is already banned!")
            return
        except:
            pass
        caseid = await self.sqlm.insertban(target.id, author.id, reason = isemptyreason(reason))
        dmsuccess = await self.responsem.dm(target, (":x: You have been banned from " + self.cfg.get("servername") + " by " + str(author.name) + " for " + isemptyreason(reason) + ".\n" +
        "To appeal the ban, add either the ban issuer or one of the following admins to your friends list: `goldautumnleaf`, `illidaaan`, `doxx.me` .\n" +
        "When appealing the ban, provide the following Case ID: " + str(caseid) + ".\n" +
        "Server rules can be accessed at this link: " + self.cfg.get("ruleslink") + ""))
        try:
            #await author.guild.ban(target, delete_message_seconds = secondscount, reason = banreason)
            pass
        except Exception as e:
            print(e)
            await self.responsem.respond(context, ":x: Couldn't ban the user! I don't have sufficient permissions!")
            return
        await self.logm.sendlog(self.logm.bans, context = author, mode = False, target = target.id, reason = isemptyreason(reason), caseid = caseid)
        await self.responsem.respond(context, ":white_check_mark: Successfully banned <@" + str(target.id) + ">!", dmsuccess = dmsuccess)
        return
        
    async def unban(self, context, target, reason):
        author = getauthor(context)
        # Command permission level
        commandpermissionlevel = 3
        # Permission check
        canrun = await self.pm.canrun(context, author, commandpermissionlevel = commandpermissionlevel)
        if not canrun:
            return
        unbanreason = sanitizereason(author.name, reason = reason, unban = True)
        try:
            await author.guild.unban(target, reason = unbanreason)
        except:
            await self.responsem.respond(context, ":x: Couldn't unban the user! The user isn't banned!")
            return
        await self.logm.sendlog(self.logm.unbans, context = author, target = target.id, reason = isemptyreason(reason))
        await self.responsem.respond(context, ":white_check_mark: Successfully unbanned <@" + str(target.id) + ">!")
        return