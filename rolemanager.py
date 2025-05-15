from extrafunctions import isemptyreason, sanitizereason, isvalidtime, getauthor

class rolemanager:
    def __init__(self, cfg, pm, bot, sql, log, responsemanager):
        self.cfg = cfg
        self.pm = pm
        self.bot = bot
        self.sqlm = sql
        self.logm = log
        self.responsem = responsemanager
        self.addtemprole = 1
        self.removetemprole = 2
        self.flooderrole = 1
        self.gladiatorrole = 2
        self.mrmustardrole = 3
        self.puppetrole = 4
        self.handrole = 5
        self.contentcreatorrole = 6
        self.argrole = 7
        
    def getroleid(self, rolemode):
        if rolemode == self.sqlm.flooderrole:
            roleid = self.cfg.get("flooderrole")
        elif rolemode == self.sqlm.gladiatorrole:
            roleid = self.cfg.get("gladiatorid")
        elif rolemode == self.sqlm.mrmustardrole:
            roleid = self.cfg.get("mustardid")
        elif rolemode == self.puppetrole:
            roleid = self.cfg.get("puppetrole")
        elif rolemode == self.handrole:
            roleid = self.cfg.get("handrole")
        elif rolemode == self.contentcreatorrole:
            roleid = self.cfg.get("contentcreatorrole")
        elif rolemode == self.argrole:
            roleid = self.cfg.get("argrole")
        return roleid
        
    async def fetchroleandmember(self, rolemode, memberid):
        roleid = self.getroleid(rolemode)
        guild = self.bot.get_guild(self.cfg.get("guild"))
        role = guild.get_role(roleid)
        member = await guild.fetch_member(memberid)
        return role, member

    async def removeexpiredroles(self, date):
        await self.sqlm.deleteoldtemproles()
        result = await self.sqlm.getexpiredtemproles(date)
        guild = self.bot.get_guild(self.cfg.get("guild"))
        for toremove in result:
            try:
                role, member = await self.fetchroleandmember(toremove[1], toremove[0])
            except:
                print("Error getting member for temprole removal (or role but that's unlikely). They've likely left the server.")
                continue
            reason = "Expired " + role.name + " role."
            try:
                await member.remove_roles(role, reason = reason)
            except:
                print("Couldn't remove role")
        await self.sqlm.markexpiredtemprolesasremoved(date)
        return
    
    async def temprole(self, context, target, mode, role_type, duration = False, reason = False):
        author = getauthor(context)
        roleid = self.getroleid(role_type)
        guild = self.bot.get_guild(self.cfg.get("guild"))
        role = guild.get_role(roleid)
        maxduration = 365
        if mode == self.addtemprole:
            modreason = sanitizereason(author.name, reason = reason, addedrolename = role.name, duration = duration)
            reason = isemptyreason(reason)
            if role_type == self.flooderrole:
                if self.pm.hasrole(target, role.id):
                    await self.responsem.respond(context, "User has " + role.name + " role already!")
                    return
            date, timestamp = isvalidtime(duration, maxduration = maxduration)
            if not date:
                await self.responsem.respond(context, "Invalid time duration.")
                return
            date = date.strftime("%Y-%m-%d %H:%M:%S")
            await target.add_roles(role, reason = modreason)
            rowid = await self.sqlm.addtemprole(target.id, author.id, date, role_type, reason)
            dmsuccess = await self.responsem.dm(target, "You have been issued a " + role.name + " role by <@" + str(author.id) + "> until <t:" + str(timestamp) + ":F> for " + reason + ".")
            await self.responsem.respond(context, "Added " + role.name + " to <@" + str(target.id) + "> until <t:" + str(timestamp) + ":F> for " + reason + ".", dmsuccess = dmsuccess)
            await self.logm.sendlog(self.logm.temproles, author, mode = self.logm.addrole, target = target, duration = timestamp, reason = reason, role = role, caseid = rowid)
            return
        else:
            modreason = sanitizereason(author.name, reason = reason, removedrolename = role.name, duration = duration)
            reason = isemptyreason(reason)
            if not self.pm.hasrole(target, role.id):
                await self.responsem.respond(context, "User doesn't have " + role.name + " role!")
                return
            await target.remove_roles(role, reason = modreason)
            await self.sqlm.removetemprole(target.id, role_type)
            dmsuccess = await self.responsem.dm(target, "You have been prematurely removed from a " + role.name + " role by <@" + str(author.id) + "> for " + reason + ".")
            await self.responsem.respond(context, "Removed " + role.name + " from <@" + str(target.id) + "> for " + reason + ".", dmsuccess = dmsuccess)
            await self.logm.sendlog(self.logm.temproles, author, mode = self.logm.removerole, target = target, reason = reason, role = role)
            return
            
    async def role(self, context, target, role, reason):
        roleid = self.getroleid(role)
        guild = self.bot.get_guild(self.cfg.get("guild"))
        role = guild.get_role(roleid)
        isnotmodrole = True
        if role is None:
            print("No role found.")
            return
        if role.id == self.cfg.get("puppetrole") or role.id == self.cfg.get("handrole"):
            isnotmodrole = False
        if self.pm.hasrole(target, role.id):
            await target.remove_roles(role, reason = sanitizereason(context.author.name, reason = isemptyreason(reason), removedrolename = role.name))
            await context.respond("Removed " + role.name + " role from <@" + str(target.id) + ">.", ephemeral = isnotmodrole)
            await self.logm.sendlog(self.logm.roles, context, mode = self.logm.removerole, target = target, role = role, reason = isemptyreason(reason))
        else:
            await target.add_roles(role, reason = sanitizereason(context.author.name, reason = isemptyreason(reason), addedrolename = role.name))
            await context.respond("Added " + role.name + " role to <@" + str(target.id) + ">.", ephemeral = isnotmodrole)
            await self.logm.sendlog(self.logm.roles, context, mode = self.logm.addrole, target = target, role = role, reason = isemptyreason(reason))
        return