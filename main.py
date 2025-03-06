import discord
import aiomysql as sql
import configparse
import datetime

cfg = configparse.parseconfig("config.cfg")
cfg.load()
token = cfg.loadtoken()
# cfg.set(key, value)

bot = discord.Bot()

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

def hasrole(member, role):
    memberroles = member.roles
    for roles in memberroles:
        if role == roles.id:
            return True
    return False
    
def getpermissionlevel(member):
    #if member.guild_permissions.manage_guild or member.id == cfg.get("master"):
    #    return 4
    if hasrole(member, cfg.get("armrole")):
        return 3
    if hasrole(member, cfg.get("handrole")):
        return 2
    if hasrole(member, cfg.get("puppetrole")):
        return 1
    return 0
    
@bot.slash_command(description = "Time-out a user for any duration.")
async def timeout(context, username: discord.Option(
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
        commandpermissionlevel = 1
        inituser = context.author
        targetuser = username
        reason = "Responsible user: " + inituser.name + ", reason:" + reason
        reason = reason[:450]
        inituser_permlevel = getpermissionlevel(inituser)
        targetuser_permlevel = getpermissionlevel(targetuser)
        if getpermissionlevel(context.author) < commandpermissionlevel:
            await context.respond("You do not have enough permissions. Your permission level: "
                + str(getpermissionlevel(context.author)) + ", required permission level: " + str(commandpermissionlevel) + ".",
                ephemeral = True)
            return
        if targetuser_permlevel >= inituser_permlevel:
            await context.respond("The permission level of target user (" + str(targetuser_permlevel)
                + ") needs to be smaller than yours (" + str(inituser_permlevel) + ").",
                ephemeral = True)
            return
        time = isvalidtime(duration)
        if not time:
            await context.respond("Invalid timeout duration.", ephemeral = True)
            return
        
        await username.timeout(time, reason)
        await context.respond("Timed out.")
        

@bot.slash_command(description = "Toggles Puppet role for a user.")
async def puppet(context, username: discord.Option(
    discord.SlashCommandOptionType.user,
    required = True,
    description = "User to toggle a Puppet role for.")
    ):
        inituser = context.author
        targetuser = username
        
        inituser_permlevel = getpermissionlevel(inituser)
        targetuser_permlevel = getpermissionlevel(targetuser)
        commandpermissionlevel = 2
        if getpermissionlevel(context.author) < commandpermissionlevel:
            await context.respond("You do not have enough permissions. Your permission level: "
                + str(getpermissionlevel(context.author)) + ", required permission level: " + str(commandpermissionlevel) + ".",
                ephemeral = True)
            return
        if targetuser_permlevel >= inituser_permlevel:
            await context.respond("The permission level of target user (" + str(targetuser_permlevel)
                + ") needs to be smaller than yours (" + str(inituser_permlevel) + ").",
                ephemeral = True)
            return
       
        if hasrole(targetuser, cfg.get("puppetrole")):
            await targetuser.remove_roles(inituser.guild.get_role(cfg.get("puppetrole")), reason = "Responsible user: " + str(inituser.name))
            await context.respond("Removed Puppet role from " + targetuser.name + ".")
        else:
            await targetuser.add_roles(inituser.guild.get_role(cfg.get("puppetrole")), reason = "Responsible user: " + str(inituser.name))
            await context.respond("Added Puppet role to " + targetuser.name + ".")
            
@bot.slash_command(description = "Toggles Hand role for a user.")
async def hand(context, username: discord.Option(
    discord.SlashCommandOptionType.user,
    required = True,
    description = "User to toggle a Hand role for.")
    ):
        inituser = context.author
        targetuser = username
        
        inituser_permlevel = getpermissionlevel(inituser)
        targetuser_permlevel = getpermissionlevel(targetuser)
        commandpermissionlevel = 3
        if getpermissionlevel(context.author) < commandpermissionlevel:
            await context.respond("You do not have enough permissions. Your permission level: "
                + str(getpermissionlevel(context.author)) + ", required permission level: " + str(commandpermissionlevel) + ".",
                ephemeral = True)
            return
        if targetuser_permlevel >= inituser_permlevel:
            await context.respond("The permission level of target user (" + str(targetuser_permlevel)
                + ") needs to be smaller than yours (" + str(inituser_permlevel) + ").",
                ephemeral = True)
            return
       
        if hasrole(targetuser, cfg.get("puppetrole")):
            await targetuser.remove_roles(inituser.guild.get_role(cfg.get("handrole")), reason = "Responsible user: " + str(inituser.name))
            await context.respond("Removed Hand role from " + targetuser.name + ".")
        else:
            await targetuser.add_roles(inituser.guild.get_role(cfg.get("handrole")), reason = "Responsible user: " + str(inituser.name))
            await context.respond("Added Hand role to " + targetuser.name + ".")
        

        
@bot.slash_command(description = "Mark role as Puppet.")
async def setpuppetrole(context, roleid: discord.Option(
    discord.SlashCommandOptionType.role,
    required = True,
    description = "Role to be marked as a Puppet role.")
    ):
        commandpermissionlevel = 4
        if getpermissionlevel(context.author) < commandpermissionlevel:
            await context.respond("You do not have enough permissions. Your permission level: "
                + str(getpermissionlevel(context.author)) + ", required permission level: " + str(commandpermissionlevel) + ".",
                ephemeral = True)
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
        if getpermissionlevel(context.author) < commandpermissionlevel:
            await context.respond("You do not have enough permissions. Your permission level: "
                + str(getpermissionlevel(context.author)) + ", required permission level: " + str(commandpermissionlevel) + ".",
                ephemeral = True)
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
        if getpermissionlevel(context.author) < commandpermissionlevel:
            await context.respond("You do not have enough permissions. Your permission level: "
                + str(getpermissionlevel(context.author)) + ", required permission level: " + str(commandpermissionlevel) + ".",
                ephemeral = True)
            return
        try:
            cfg.set("armrole", roleid.id)
            await context.respond("Marked " + roleid.name + " as Arm.")
        except:
            await context.respond("Error setting Arm role.")
            
@bot.slash_command(description = "Get user's permission level.")
async def getperms(context):
    await context.respond("Your permission level is: " + str(getpermissionlevel(context.author)))
            
bot.run(token)