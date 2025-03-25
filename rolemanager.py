from extrafunctions import isemptyreason, sanitizereason, isvalidtime

class rolemanager:
    def __init__(self, cfg, pm, bot, sql, log):
        self.cfg = cfg
        self.pm = pm
        self.bot = bot
        self.sqlm = sql
        self.logm = log
        self.addtemprole = 1
        self.removetemprole = 2
        self.flooderrole = 1
        self.gladiatorrole = 2
        self.mrmustardrole = 3
        
    def getroleid(self, rolemode):
        if rolemode == self.sqlm.flooderrole:
            roleid = self.cfg.get("flooderrole")
        elif rolemode == self.sqlm.gladiatorrole:
            roleid = self.cfg.get("gladiatorid")
        elif rolemode == self.sqlm.mrmustardrole:
            roleid = self.cfg.get("mustardid")
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
        
    async def temprole(self, context, target, mode, role_type, duration = False, reason = False, interaction = False):
        roleid = self.getroleid(role_type)
        guild = self.bot.get_guild(self.cfg.get("guild"))
        role = guild.get_role(roleid)
        maxduration = 365
        if mode == self.addtemprole:
            modreason = sanitizereason(context.author.name, reason = reason, addedrolename = role.name, duration = duration)
            reason = isemptyreason(reason)
            if role_type == self.flooderrole:
                if self.pm.hasrole(target, role.id):
                    await self.pm.respond(context, "User has " + role.name + " role already!", interaction = interaction)
                    return False, False, False
            date, timestamp = isvalidtime(duration, maxduration = maxduration)
            if not date:
                await self.pm.respond(context, "Invalid time duration.", interaction = interaction)
                return False, False, False
            date = date.strftime("%Y-%m-%d %H:%M:%S")
            await target.add_roles(role, reason = modreason)
            await self.sqlm.addtemprole(target.id, context.author.id, date, role_type, reason)
            await self.pm.respond(context, "Added " + role.name + " to <@" + str(target.id) + "> until <t:" + str(timestamp) + ":F> for " + reason + ".", interaction = interaction)
            await self.logm.sendlog(self.logm.temproles, context, mode = self.logm.addrole, target = target, duration = timestamp, reason = reason, role = role)
            return role, timestamp, reason
        else:
            modreason = sanitizereason(context.author.name, reason = reason, removedrolename = role.name, duration = duration)
            reason = isemptyreason(reason)
            if not self.pm.hasrole(target, role.id):
                await self.pm.respond(context, "User doesn't have " + role.name + " role!", interaction = interaction)
                return False, False, False
            await target.remove_roles(role, reason = modreason)
            await self.sqlm.removetemprole(target.id, role_type)
            await self.pm.respond(context, "Removed " + role.name + " from <@" + str(target.id) + "> for " + reason + ".", interaction = interaction)
            await self.logm.sendlog(self.logm.temproles, context, mode = self.logm.removerole, target = target, reason = reason, role = role)
            return role, False, reason