from extrafunctions import isvalidtime, isemptyreason, sanitizereason

class flooders:
    def __init__(self, cfg, bot, permmanager, log, sql):
        self.cfg = cfg
        self.bot = bot
        self.pm = permmanager
        self.logm = log
        self.sqlm = sql
    async def issueflooder(self, context, target, duration, reason, isslash = True, unflooder = False):
        if not unflooder:
             # Check if time inputted by user is valid
            time, untiltimestamp = isvalidtime(duration)
            if not time:
                await self.pm.throwerror(context, "Invalid flooder duration.")
                return
            
            flooderrole = context.author.guild.get_role(self.cfg.get("flooderrole"))
            if self.pm.hasrole(target, flooderrole.id):
                await self.pm.throwerror(context, "User has flooder role already!")
                return
            modreason = sanitizereason(context.author.name, reason = reason, duration = duration, addedrolename = flooderrole.name)
            # Add flooder role
            try:
                await target.add_roles(flooderrole, reason = modreason)
                try:
                    await target.send(content = "You have been issued a flooder role by <@" + str(context.author.id) + "> until <t:" + str(untiltimestamp) + ":F> for " + isemptyreason(reason) + ".")
                except:
                    pass
                await context.respond("User <@" + str(target.id) + "> has been issued a Flooder role for " + duration + " (until <t:" + str(untiltimestamp) + ":F>).", ephemeral = True)
                await self.logm.sendlog(self.logm.flooders, context, mode = self.logm.addrole, target = target, duration = untiltimestamp, reason = isemptyreason(reason))
            except:
                await self.pm.throwerror(context, "Couldn't mark user as flooder. User may already be a flooder.")
                return
            try:
                # Convert the time to SQL datetime format
                time = time.strftime("%Y-%m-%d %H:%M:%S")
                # If user has any pending flooders in the database for whatever reason, mark them as removed
                await self.sqlm.markflooderasremoved(target.id)
                # Add flooder record to database
                await self.sqlm.addflooder(target.id, time)
            except:
                await self.pm.throwerror(context, "Failure inserting a record into the database. Issued flooder may not be autoremoved.")
            return
            
        else:
            try:
                await self.sqlm.removeflooder(target.id)
                flooderrole = context.author.guild.get_role(self.cfg.get("flooderrole"))
                if not self.pm.hasrole(target, flooderrole.id):
                    await self.pm.throwerror(context, "User doesn't have a flooder role!")
                    return
                modreason = sanitizereason(context.author.name, reason = reason, removedrolename = flooderrole.name)
                await target.remove_roles(flooderrole, reason = modreason)
                await context.respond("Removed flooder from <@" + str(target.id) + ">.")
                await self.logm.sendlog(self.logm.flooders, context, target = target, mode = self.logm.removerole, reason = isemptyreason(reason))
            except:
                await self.pm.throwerror(context, "Couldn't remove flooder from <@" + str(target.id) + ">.")
            return