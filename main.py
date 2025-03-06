import discord
import aiomysql as sql
import configparse
import datetime
import permmanager

cfg = configparse.parseconfig("config.cfg")
cfg.load()
token = cfg.loadtoken()

# cfg.set(key, value)

bot = discord.Bot()
pm = permmanager.permmanager(cfg)

def isvalidtime(time):
    try:
        timeunit = time[-1:]
        timeduration = time[:-1]
        timeduration = int(timeduration)
        if timeunit not in ["m", "h", "d"]:
            raise InvalidTimeoutUnit
        if timeduration <= 0:
            raise InvalidTimeoutDuration
    # returns a datetime object if time is valid
        date = datetime.datetime.now(datetime.UTC)
        if timeunit == "m":
            date = date + datetime.timedelta(minutes = timeduration)
        elif timeunit == "h":
            date = date + datetime.timedelta(hours = timeduration)
        elif timeunit == "d":
            date = date + datetime.timedelta(days = timeduration)
        return date
    except:
        return False
    return False


    
@bot.slash_command(description = "Time-out a user for any duration.")
async def timeout(context, target: discord.Option(
    discord.SlashCommandOptionType.user,
    required = True,
    description = "User to issue a time-out to."),
    duration: discord.Option(discord.SlashCommandOptionType.string,
    required = True,
    description = "The duration of a timeout. Examples: 2d - 2 days, 7m - 7 minutes, 3h - 3 hours."),
    reason: discord.Option(discord.SlashCommandOptionType.string,
    required = True,
    description = "Reason for the timeout.")
    ):
        reason = "Responsible user: " + context.author.name + ", reason:" + reason
        reason = reason[:450]
        commandpermissionlevel = 1
        canrun = await pm.canrun(context, context.author, target, commandpermissionlevel)
        if not canrun:
            return
        time = isvalidtime(duration)
        if not time:
            await context.respond("Invalid timeout duration.", ephemeral = True)
            return
        
        await target.timeout(time, reason)
        await context.respond("Timed out.")
        return
        

@bot.slash_command(description = "Toggles Puppet role for a user.")
async def puppet(context, target: discord.Option(
    discord.SlashCommandOptionType.user,
    required = True,
    description = "User to toggle a Puppet role for.")
    ):
        inituser = context.author
        commandpermissionlevel = 2
        canrun = await pm.canrun(context, context.author, target, commandpermissionlevel)
        if not canrun:
            return
       
        if hasrole(target, cfg.get("puppetrole")):
            await target.remove_roles(inituser.guild.get_role(cfg.get("puppetrole")), reason = "Responsible user: " + str(inituser.name))
            await context.respond("Removed Puppet role from " + target.name + ".")
        else:
            await target.add_roles(inituser.guild.get_role(cfg.get("puppetrole")), reason = "Responsible user: " + str(inituser.name))
            await context.respond("Added Puppet role to " + target.name + ".")
        return
            
@bot.slash_command(description = "Toggles Hand role for a user.")
async def hand(context, target: discord.Option(
    discord.SlashCommandOptionType.user,
    required = True,
    description = "User to toggle a Hand role for.")
    ):
        inituser = context.author
        commandpermissionlevel = 3
        canrun = await pm.canrun(context, context.author, target, commandpermissionlevel)
        if not canrun:
            return
       
        if hasrole(targetuser, cfg.get("puppetrole")):
            await target.remove_roles(inituser.guild.get_role(cfg.get("handrole")), reason = "Responsible user: " + str(inituser.name))
            await context.respond("Removed Hand role from " + target.name + ".")
        else:
            await target.add_roles(inituser.guild.get_role(cfg.get("handrole")), reason = "Responsible user: " + str(inituser.name))
            await context.respond("Added Hand role to " + target.name + ".")
        

        
@bot.slash_command(description = "Mark role as Puppet.")
async def setpuppetrole(context, roleid: discord.Option(
    discord.SlashCommandOptionType.role,
    required = True,
    description = "Role to be marked as a Puppet role.")
    ):
        commandpermissionlevel = 4
        canrun = await pm.canrun(context, context.author, target, commandpermissionlevel)
        if not canrun:
            return
        try:
            cfg.set("puppetrole", roleid.id)
            await context.respond("Marked " + roleid.name + " as Puppet.")
        except:
            await context.respond("Error setting Puppet role.")
            
@bot.slash_command(description = "Mark role as Hand.")
async def sethandrole(context, roleid: discord.Option(
    discord.SlashCommandOptionType.role,
    required = True,
    description = "Role to be marked as a Hand role.")
    ):
        commandpermissionlevel = 4
        canrun = await pm.canrun(context, context.author, target, commandpermissionlevel)
        if not canrun:
            return
        try:
            cfg.set("handrole", roleid.id)
            await context.respond("Marked " + roleid.name + " as Hand.")
        except:
            await context.respond("Error setting Hand role.")
            
@bot.slash_command(description = "Mark role as Arm.")
async def setarmrole(context, roleid: discord.Option(
    discord.SlashCommandOptionType.role,
    required = True,
    description = "Role to be marked as an Arm role.")
    ):
        commandpermissionlevel = 4
        canrun = await pm.canrun(context, context.author, target, commandpermissionlevel)
        if not canrun:
            return
        try:
            cfg.set("armrole", roleid.id)
            await context.respond("Marked " + roleid.name + " as Arm.")
        except:
            await context.respond("Error setting Arm role.")
            
@bot.slash_command(description = "Get user's permission level.")
async def getperms(context):
    await context.respond("Your permission level is: " + str(pm.getpermissionlevel(context.author)))
            
bot.run(token)