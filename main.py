import discord
import configparse
import datetime
import permmanager
import sqlmanager

cfg = configparse.parseconfig("config.cfg")
cfg.load()
token = cfg.loadtoken()

bot = discord.Bot()
pm = permmanager.permmanager(cfg)
sqlm = sqlmanager.sqlmanager(cfg)

def isvalidtime(time):
    try:
        timeunit = time[-1:]
        timeduration = time[:-1]
        timeduration = int(timeduration)
        if timeunit not in ["m", "h", "d"]:
            raise InvalidUnit
        if timeduration <= 0:
            raise InvalidDuration
        if (timeunit == "d" and timeduration >= 14) or (
        timeunit == "h" and timeduration >= 336) or (
        timeunit == "m" and timeduration >= 20160):
            raise InvalidDuration
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
    
    
@bot.slash_command(description = "Issue a flooder to a user for a certain duration.")
async def flooder(context, target: discord.Option(
    discord.SlashCommandOptionType.user,
    required = True,
    description = "User to issue a flooder role to."),
    duration: discord.Option(
    discord.SlashCommandOptionType.string,
    required = True,
    description = "The duration of a flooder. Examples: 2d - 2 days, 7m - 7 minutes, 3h - 3 hours."),
    reason: discord.Option(
    discord.SlashCommandOptionType.string,
    required = False,
    description = "Reason for issuing the flooder (shows up in audit log).")
    ):
        commandpermissionlevel = 1
        canrun = await pm.canrun(context, context.author, target=target, commandpermissionlevel=commandpermissionlevel)
        if not canrun:
            return
        time = isvalidtime(duration)
        if not time:
            await pm.throwerror(context, "Invalid flooder duration.")
            return
        try:
            await sqlm.addflooder(target.id, duration)
        except:
            await pm.throwerror(context, "Failure inserting a record into the database. Flooder has not been issued.")
            return
        # todo add flooder here
        await context.respond("Success.")
        return


@bot.slash_command(description = "Edit slow mode for a general channel.")
async def slowmode(context, target: discord.Option(
    discord.SlashCommandOptionType.channel,
    required = True,
    description = "Channel to set slow mode for."),
    delay: discord.Option(
    discord.SlashCommandOptionType.integer,
    required = True,
    description = "The value of slow mode.")
    ):
        commandpermissionlevel = 2
        canrun = await pm.canrun(context, context.author, commandpermissionlevel=commandpermissionlevel)
        if not canrun:
            return
        if not str(target.type) == "text":
            await pm.throwerror(context, "The channel you've selected is not a text channel.")
            return
        if "general" not in str(target.name):
            await pm.throwerror(context, "You can only edit slow mode for general channels.")
            return
        if delay < 0 or delay > 21600:
            await pm.throwerror(context, "Invalid slow mode duration. Allowed values: 0 - 21600 seconds.")
            return
        await target.edit(reason = "Responsible user: " + context.author.name, slowmode_delay = delay)
        await context.respond("Slow mode for channel " + target.name + " set to " + str(delay) + " seconds.")
        return
    
@bot.slash_command(description = "Time-out a user for any duration.")
async def timeout(context, target: discord.Option(
    discord.SlashCommandOptionType.user,
    required = True,
    description = "User to issue a time-out to."),
    duration: discord.Option(
    discord.SlashCommandOptionType.string,
    required = True,
    description = "The duration of a timeout. Examples: 2d - 2 days, 7m - 7 minutes, 3h - 3 hours."),
    reason: discord.Option(
    discord.SlashCommandOptionType.string,
    required = True,
    description = "Reason for the timeout.")
    ):
        reason = "Responsible user: " + context.author.name + ", reason: " + reason
        reason = reason[:511]
        commandpermissionlevel = 1
        canrun = await pm.canrun(context, context.author, target=target, commandpermissionlevel=commandpermissionlevel)
        if not canrun:
            return
        time = isvalidtime(duration)
        if not time:
            await context.respond("Invalid timeout duration.", ephemeral = True)
            return
        try:
            await target.timeout(time, reason=reason)
            await context.respond("User " + target.name + " has been timed out for " + duration + ".")
        except:
            await context.respond("Error issuing a timeout. Check bot permissions.")
        return
        

@bot.slash_command(description = "Toggles Puppet role for a user.")
async def puppet(context, target: discord.Option(
    discord.SlashCommandOptionType.user,
    required = True,
    description = "User to toggle a Puppet role for.")
    ):
        inituser = context.author
        commandpermissionlevel = 2
        canrun = await pm.canrun(context, context.author, target=target, commandpermissionlevel=commandpermissionlevel)
        if not canrun:
            return
       
        if pm.hasrole(target, cfg.get("puppetrole")):
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
        canrun = await pm.canrun(context, context.author, target=target, commandpermissionlevel=commandpermissionlevel)
        if not canrun:
            return
       
        if pm.hasrole(target, cfg.get("handrole")):
            await target.remove_roles(inituser.guild.get_role(cfg.get("handrole")), reason = "Responsible user: " + str(inituser.name))
            await context.respond("Removed Hand role from " + target.name + ".")
        else:
            await target.add_roles(inituser.guild.get_role(cfg.get("handrole")), reason = "Responsible user: " + str(inituser.name))
            await context.respond("Added Hand role to " + target.name + ".")
        return
        

        
@bot.slash_command(description = "Mark which roles are moderation roles.")
async def setmodroles(context, puppet: discord.Option(
    discord.SlashCommandOptionType.role,
    required = True,
    description = "Role to be marked as a Puppet role."),
    hand: discord.Option(
    discord.SlashCommandOptionType.role,
    required = True,
    description = "Role to be marked as a Hand role."),
    arm: discord.Option(
    discord.SlashCommandOptionType.role,
    required = True,
    description = "Role to be marked as an Arm role."),
    ):
        commandpermissionlevel = 4
        canrun = await pm.canrun(context, context.author, commandpermissionlevel=commandpermissionlevel)
        if not canrun:
            return
        try:
            cfg.set("puppetrole", puppet.id)
            cfg.set("handrole", hand.id)
            cfg.set("armrole", arm.id)
            await context.respond("Marked " + puppet.name + " as Puppet, " + hand.name + " as Hand and " + arm.name + " as Arm.")
        except:
            await context.respond("Error setting roles.")
        return
            
@bot.slash_command(description = "Get user's permission level.")
async def getperms(context):
    permlevel = pm.getpermissionlevel(context.author)
    if permlevel == 4:
        permmessage = "Shoulder / Bot Administrator (4)."
    elif permlevel == 3:
        permmessage = "Mita's Arms (3)."
    elif permlevel == 2:
        permmessage = "Mita's Hands (2)."
    elif permlevel == 1:
        permmessage = "Mita's Puppets (1)."
    else:
        permmessage = "No permissions (0)."
    await context.respond("Your permission level is: " + permmessage, ephemeral = True)
            
bot.run(token)