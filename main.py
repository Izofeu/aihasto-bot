import discord
from discord.ext import tasks
from discord import guild_only
import re
import configparse
import datetime
import permmanager
import sqlmanager
import logmanager

messagecache = []

# Load up config
intents = discord.Intents.default()
intents.guild_messages = True
intents.dm_messages = False
intents.invites = False
intents.integrations = False
intents.webhooks = False
intents.emojis = False
intents.emojis_and_stickers = False
intents.auto_moderation_configuration = False
intents.auto_moderation_execution = False
intents.message_content = True
intents.typing = False
intents.presences = False
intents.polls = False
intents.dm_reactions = False
intents.members = False

nocachemembers = discord.MemberCacheFlags.none()

#bot = discord.Bot(intents = intents, member_cache_flags = nocachemembers, chunk_guilds_at_startup = False)
bot = discord.Bot(intents = intents)
cfg = configparse.parseconfig("config.cfg")
cfg.load()
# Load bot token
token = cfg.loadtoken()

# Load up sql manager and permissions manager
pm = permmanager.permmanager(cfg)
sqlm = sqlmanager.sqlmanager(cfg)
logm = logmanager.logmanager(cfg, bot)

def isemptyreason(reason):
    if not reason:
        reason = "No reason provided."
    return reason

def sanitizereason(author, reason = False, addedrolename = False, removedrolename = False, duration = False):
    finalreason = "Responsible user: " + author
    if addedrolename:
        finalreason += ", Added role: " + addedrolename
    if removedrolename:
        finalreason += ", Removed role: " + removedrolename
    if duration:
        finalreason += ", Duration: " + duration
    if reason:
        finalreason = finalreason + ", Reason: " + reason
    finalreason = finalreason[:511]
    return finalreason

# Check if duration inputted by user in commands is valid
def isvalidtime(time):
    try:
        # Time format should be a number followed by a letter like minute, hour, day
        timeunit = time[-1:]
        timeduration = time[:-1]
        timeduration = int(timeduration)
        if timeunit not in ["m", "h", "d"]:
            raise InvalidUnit
        # Duration cannot be negative
        if timeduration <= 0:
            raise InvalidDuration
        # Maximum of 14 days allowed, Discord's limitation for timeouts is 28 days
        if (timeunit == "d" and timeduration >= 14) or (
        timeunit == "h" and timeduration >= 336) or (
        timeunit == "m" and timeduration >= 20160):
            raise InvalidDuration
        # Returns a datetime object if time is valid
        date = datetime.datetime.now(datetime.UTC)
        # Calculate the time when a punishment should end
        if timeunit == "m":
            date = date + datetime.timedelta(minutes = timeduration)
        elif timeunit == "h":
            date = date + datetime.timedelta(hours = timeduration)
        elif timeunit == "d":
            date = date + datetime.timedelta(days = timeduration)
        return date
    # If anything went wrong, report an incorrect date
    except:
        return False
    return False

@bot.event
async def on_message_edit(before, after):
    if not cfg.get("automessagecuration"):
        return
    if after.channel.id == cfg.get("greatmitaid"):
        try:
            await after.delete(reason = "Edited a message in miside-great-mita.")
        except:
            pass
        time = isvalidtime("1d")
        untiltimestamp = int(time.timestamp())
        permlevel = pm.getpermissionlevel(after.author)
        if permlevel == 0:
            reason = "Edited a message in miside-great-mita."
            await after.author.timeout(time, reason = reason)
            await logm.sendlog(category = logm.timeouts, mode = logm.selfissuedwarn, context = bot, target = after.author, duration = untiltimestamp, reason = reason)
            await after.author.send(content = "You have been timed out by " + bot.user.name + " for " + reason + " until <t:" + str(untiltimestamp) + ":F>.")
    elif after.channel.id == cfg.get("gifpartyid"):
        if before.content == after.content:
            try:
                messagecache.remove(str(after.id))
            except:
                pass
            return
        try:
            await after.delete(reason = "Edited a message in gif-party.")
        except:
            pass
    return
    
@bot.event
async def on_message(message):
    if not cfg.get("automessagecuration"):
        return
    if message.author.bot:
        return
    reasonmita = "Incorrect message in miside-great-mita."
    reasongif = "Incorrect message in gif-party."
    try:
        if message.channel.id == cfg.get("greatmitaid"):
            if message.content != "Praying for you 🕯️ O Great Mita 💝" or str(message.type) == "MessageType.reply":
                await message.delete(reason = reasonmita)
        elif message.channel.id == cfg.get("gifpartyid"):
            if " " in message.content or "\n" in message.content:
                await message.delete(reason = reasongif)
                return
            elif "gif" in message.content:
                if (message.content.startswith("https://tenor.com/") or message.content.startswith("https://cdn.discordapp.com/attachments/")
                or message.content.startswith("https://media.discordapp.net/attachments/") or message.content.startswith("https://giphy.com/gifs/")):
                    try:
                        embed = message.embeds[0]
                    except:
                        messagecache.append(str(message.id))
                        sec5 = datetime.datetime.now() + datetime.timedelta(seconds = 5)
                        await discord.utils.sleep_until(sec5)
                        try:
                            messagecache.remove(str(message.id))
                            await message.delete(reason = reasongif)
                        except:
                            pass
                    return
            await message.delete(reason = reasongif)
    except:
        pass
    return

@bot.event
async def on_ready():
    print("Logged in to Discord.")
    print("successfully finished startup")
    # Start periodic task for checking expired flooders
    logm.ready()
    checkflooders.start()
    
@tasks.loop(seconds=60)
async def checkflooders():
    await checkwarnings()
    # Get expired flooders as a tuple of user ids whose flooders have expired
    expiredflooders = await sqlm.getexpiredflooders(datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M:%S"))
    if not expiredflooders:
        await sqlm.removeoldflooders()
        return
    # Obtain guild object from guild id from config
    guild = bot.get_guild(cfg.get("guild"))
    # Obtain flooder role object from flooder role id from config
    flooderrole = guild.get_role(cfg.get("flooderrole"))
    # For each flooder, perform a flooder role removal and remove the database entry
    for flooderid in expiredflooders:
        # flooder is is a tuple, first result is a pure id
        id = int(flooderid[0])
        # Get member object
        try:
            flooder = await guild.fetch_member(id)
        except:
            await sqlm.markflooderasremoved(flooder.id)
            continue
        try:
            # Remove role
            await flooder.remove_roles(flooderrole, reason = "Expired flooder role.")
            await sqlm.markflooderasremoved(flooder.id)
        except:
            # If role removal goes wrong, for example the user got the role removed manually, then ignore the error
            print("Couldn't remove flooder role from " + str(flooder) + ".")
    return
async def checkwarnings():
    await sqlm.deleteexpiredwarns(datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M:%S"))
    return
    
@bot.user_command(name = "Show flooders")
@guild_only()
async def showflooders(context, member: discord.Member):
    commandpermissionlevel = 1
    # Permission check
    canrun = await pm.canrun(context, context.author, commandpermissionlevel = commandpermissionlevel)
    if not canrun:
        return
    floodercount = await sqlm.getfloodercount(member.id)
    if floodercount > 0:
        message = "<@" + str(member.id) + "> has received " + str(floodercount) + " flooders in last 30 days."
    else:
        message = "<@" + str(member.id) + "> has not received any flooders in last 30 days."
    await context.respond(message, ephemeral = True)
    return
    
@bot.user_command(name = "Show warnings")
@guild_only()
async def showwarnings(context, member: discord.Member):
    # Do not run the permission check if we only want the message for the button response
    # as we've already ran a permission check there
    if context != 27:
        # Command permission level
        commandpermissionlevel = 1
        # Permission check
        canrun = await pm.canrun(context, context.author, commandpermissionlevel = commandpermissionlevel)
        if not canrun:
            return
    warningscount, warnings = await sqlm.getwarnings(member.id)
    warningscount = warningscount[0][0]
    if warningscount == 0:
        message = member.name + " has not received any warnings."
    else:
        message = member.name + " has received " + str(warningscount) + " warnings. Here's the date and reason of the last three warnings:"
        #print(warnings)
        #print(len(warnings))
        format = "%Y-%m-%d %H:%M:%S %z"
        for warns in warnings:
            date = warns[1] - datetime.timedelta(days = 3)
            # datetime object assumes timezone of the machine
            # this part of code recreates the object with utc timezone
            date = str(date)
            date += " +0000"
            date = datetime.datetime.strptime(date, format)
            time = int(date.timestamp())
            message += "\n<t:" + str(time) + ":R> - " + str(warns[2])
    # We cannot add params to a command function
    # so we reuse one of arguments as a workaround
    if context == 27:
        return message
    else:
        await context.respond(message, ephemeral = True)
    return
    
@bot.slash_command(description = "Toggles auto message curation of gif-party and miside-great-mita.")
@guild_only()
async def autopunishtoggle(context):
    # Command permission level
    commandpermissionlevel = 3
    # Permission check
    canrun = await pm.canrun(context, context.author, commandpermissionlevel = commandpermissionlevel)
    if not canrun:
        return
    if cfg.get("automessagecuration") == 0:
        cfg.set("automessagecuration", 1)
        await context.respond("Enabled auto message curation of gif-party and miside-great-mita.")
    else:
        cfg.set("automessagecuration", 0)
        await context.respond("Disabled auto message curation of gif-party and miside-great-mita.")
    return

@bot.slash_command(description = "Removes all warnings from a user.")
@guild_only()
async def clearwarns(context, target: discord.Option(
    discord.SlashCommandOptionType.user,
    required = True,
    description = "User to remove warnings from."),
    reason: discord.Option(
    discord.SlashCommandOptionType.string,
    required = False,
    description = "Reason for removing the warnings.")
    ):
        # Command permission level
        commandpermissionlevel = 1
        # Permission check
        canrun = await pm.canrun(context, context.author, target = target, commandpermissionlevel = commandpermissionlevel)
        if not canrun:
            return
        try:
            await sqlm.removewarnings(target.id)
            await context.respond("Warnings for user " + target.name + " have been removed.")
            await logm.sendlog(logm.warns, context, target = target, mode = logm.clearwarns, reason = isemptyreason(reason))
        except:
            await pm.throwerror(context, "Error removing warnings.")
        return
    
@bot.slash_command(description = "Issue a warning to a user. Warnings auto-expire after 3 days.")
@guild_only()
async def warn(context, target: discord.Option(
    discord.SlashCommandOptionType.user,
    required = True,
    description = "User to issue a warning to."),
    reason: discord.Option(
    discord.SlashCommandOptionType.string,
    required = False,
    description = "Reason for the warning. Gets sent to the user.")
    ):
        # Command permission level
        commandpermissionlevel = 1
        # Permission check
        canrun = await pm.canrun(context, context.author, target = target, commandpermissionlevel = commandpermissionlevel)
        if not canrun:
            return
        expirydate = isvalidtime("3d").strftime("%Y-%m-%d %H:%M:%S")
        warncount = await sqlm.getwarncount(target.id)
        message = "User " + target.name + " has been issued a warning for " + isemptyreason(reason) + "."
        if warncount > 0:
            message += " They have " + str(warncount) + " other warning(s) on account."
            class showwarnsbutton(discord.ui.View):
                @discord.ui.button(label = "Show all warns", style = discord.ButtonStyle.primary)
                async def button_callback(self, button, interaction):
                    # Command permission level
                    commandpermissionlevel = 1
                    # Permission check
                    canrun = await pm.canrun(context = interaction, member = interaction.user, commandpermissionlevel = commandpermissionlevel, interaction = True)
                    if not canrun:
                        return
                    await interaction.response.send_message(await showwarnings(27, target), ephemeral = True)
        else:
            message += " This is their first warning."
        await sqlm.addwarning(target.id, expirydate, isemptyreason(reason))
        if warncount > 0:
            # Delete the message after 1 minute to prevent a memory leak with too many buttons
            await context.respond(message, view = showwarnsbutton(), ephemeral = True, delete_after = 120)
        else:
            await context.respond(message, ephemeral = True)
        await logm.sendlog(logm.warns, context, mode = logm.addwarn, target = target, reason = isemptyreason(reason))
        try:
            await target.send("You have been issued a warning by " + context.author.name + " for " + isemptyreason(reason) + ".")
        except:
            pass
        return
    
@bot.slash_command(description = "Remove a flooder from a user.")
@guild_only()
async def unflooder(context, target: discord.Option(
    discord.SlashCommandOptionType.user,
    required = True,
    description = "User to remove a flooder role from."),
    reason: discord.Option(
    discord.SlashCommandOptionType.string,
    required = False,
    description = "Reason for removing the flooder (shows up in audit log).")
    ):
        # Command permission level
        commandpermissionlevel = 1
        # Permission check
        canrun = await pm.canrun(context, context.author, target = target, commandpermissionlevel = commandpermissionlevel)
        if not canrun:
            return
        try:
            await sqlm.removeflooder(target.id)
            flooderrole = context.author.guild.get_role(cfg.get("flooderrole"))
            if not pm.hasrole(target, flooderrole.id):
                await pm.throwerror(context, "User doesn't have a flooder role!")
                return
            modreason = sanitizereason(context.author.name, reason = reason, removedrolename = flooderrole.name)
            await target.remove_roles(flooderrole, reason = modreason)
            await context.respond("Removed flooder from " + target.name + ".")
            await logm.sendlog(logm.flooders, context, target = target, mode = logm.removerole, reason = isemptyreason(reason))
        except:
            await pm.throwerror(context, "Couldn't remove flooder from " + target.name + ".")
        return
    
@bot.slash_command(description = "Issue a flooder to a user for a certain duration.")
@guild_only()
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
        # Command permission level
        commandpermissionlevel = 1
        # Permission check
        canrun = await pm.canrun(context, context.author, target=target, commandpermissionlevel=commandpermissionlevel)
        if not canrun:
            return
        # Check if time inputted by user is valid
        
        time = isvalidtime(duration)
        if not time:
            await pm.throwerror(context, "Invalid flooder duration.")
            return
        # Calculate the unix timestamp of end date of punishment to display it nicely to the user
        untiltimestamp = int(time.timestamp())
        
        flooderrole = context.author.guild.get_role(cfg.get("flooderrole"))
        if pm.hasrole(target, flooderrole.id):
            await pm.throwerror(context, "User has flooder role already!")
            return
        modreason = sanitizereason(context.author.name, reason = reason, duration = duration, addedrolename = flooderrole.name)
        # Add flooder role
        try:
            await target.add_roles(flooderrole, reason = modreason)
            try:
                await target.send(content = "You have been issued a flooder role by " + context.author.name + " until <t:" + str(untiltimestamp) + ":F> for " + isemptyreason(reason) + ".")
            except:
                pass
            await context.respond("User " + target.name + " has been issued a Flooder role for " + duration + " (until <t:" + str(untiltimestamp) + ":F>).", ephemeral = True)
            await logm.sendlog(logm.flooders, context, mode = logm.addrole, target = target, duration = untiltimestamp, reason = isemptyreason(reason))
        except:
            await pm.throwerror(context, "Couldn't mark user as flooder. User may already be a flooder.")
            return
        try:
            # Convert the time to SQL datetime format
            time = time.strftime("%Y-%m-%d %H:%M:%S")
            # If user has any pending flooders in the database for whatever reason, mark them as removed
            await sqlm.markflooderasremoved(target.id)
            # Add flooder record to database
            await sqlm.addflooder(target.id, time)
        except:
            await pm.throwerror(context, "Failure inserting a record into the database. Issued flooder may not be autoremoved.")
        return


@bot.slash_command(description = "Edit slow mode for a general channel.")
@guild_only()
async def slowmode(context, target: discord.Option(
    discord.SlashCommandOptionType.channel,
    required = True,
    description = "Channel to set slow mode for."),
    delay: discord.Option(
    discord.SlashCommandOptionType.integer,
    required = True,
    description = "The value of slow mode.")
    ):
        # Command permission level
        commandpermissionlevel = 2
        # Permission check
        canrun = await pm.canrun(context, context.author, commandpermissionlevel=commandpermissionlevel)
        if not canrun:
            return
        if not str(target.type) == "text":
            await pm.throwerror(context, "The channel you've selected is not a text channel.")
            return
        # Only channels with "general" in its name can have their slowmodes edited
        if "general" not in str(target.name):
            await pm.throwerror(context, "You can only edit slow mode for general channels.")
            return
        if delay < 5 or delay > 21600:
            await pm.throwerror(context, "Invalid slow mode duration. Allowed values: 5 - 21600 seconds.")
            return
        try:
            await target.edit(reason = sanitizereason(context.author.name), slowmode_delay = delay)
        except:
            await pm.throwerror(context, "Unable to edit the channel - I don't have permission.")
            return
        await context.respond("Slow mode for channel " + target.name + " set to " + str(delay) + " seconds.")
        await logm.sendlog(logm.slowmodes, context = context, duration = delay, channelid = target.id)
        return
    
@bot.slash_command(description = "Time-out a user for any duration.")
@guild_only()
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
        # Command permission level
        commandpermissionlevel = 1
        # Permission check
        canrun = await pm.canrun(context, context.author, target=target, commandpermissionlevel=commandpermissionlevel)
        if not canrun:
            return
        time = isvalidtime(duration)
        if not time:
            await context.respond("Invalid timeout duration.", ephemeral = True)
            return
        untiltimestamp = int(time.timestamp())
        try:
            # Issue timeout
            modreason = sanitizereason(context.author.name, reason = reason, duration = duration)
            await target.timeout(time, reason = modreason)
            try:
                await target.send(content = "You have been timed out by " + context.author.name + " for " + isemptyreason(reason) + " until <t:" + str(untiltimestamp) + ":F>.")
            except:
                pass
            await context.respond("User " + target.name + " has been timed out for " + duration + ".", ephemeral = True)
            await logm.sendlog(logm.timeouts, context, target = target, duration = untiltimestamp, reason = isemptyreason(reason))
        except:
            await context.respond("Error issuing a timeout. Check bot permissions.", ephemeral = True)
        return
        

@bot.slash_command(description = "Toggles Puppet role for a user.")
@guild_only()
async def puppet(context, target: discord.Option(
    discord.SlashCommandOptionType.user,
    required = True,
    description = "User to toggle a Puppet role for.")
    ):
        # Rename variable for easier use
        inituser = context.author
        # Command permission level
        commandpermissionlevel = 2
        # Permission check
        canrun = await pm.canrun(context, context.author, target = target, commandpermissionlevel = commandpermissionlevel)
        if not canrun:
            return
        # If user has role, then remove it
        puppetrole = inituser.guild.get_role(cfg.get("puppetrole"))
        if pm.hasrole(target, cfg.get("puppetrole")):
            await target.remove_roles(puppetrole, reason = sanitizereason(context.author.name, removedrolename = puppetrole.name))
            await context.respond("Removed Puppet role from " + target.name + ".")
            await logm.sendlog(logm.roles, context, mode = logm.removerole, target = target, role = puppetrole)
        # User doesn't have role, remove it
        else:
            await target.add_roles(puppetrole, reason = sanitizereason(context.author.name, addedrolename = puppetrole.name))
            await context.respond("Added Puppet role to " + target.name + ".")
            await logm.sendlog(logm.roles, context, mode = logm.addrole, target = target, role = puppetrole)
        return
            
@bot.slash_command(description = "Toggles Hand role for a user.")
@guild_only()
async def hand(context, target: discord.Option(
    discord.SlashCommandOptionType.user,
    required = True,
    description = "User to toggle a Hand role for.")
    ):
        # Rename variable for easier use
        inituser = context.author
        # Command permission level
        commandpermissionlevel = 3
        # Permission check
        canrun = await pm.canrun(context, context.author, target = target, commandpermissionlevel = commandpermissionlevel)
        if not canrun:
            return
        handrole = inituser.guild.get_role(cfg.get("handrole"))
        # If user has role, then remove it
        if pm.hasrole(target, cfg.get("handrole")):
            await target.remove_roles(handrole, reason = sanitizereason(context.author.name, removedrolename = handrole.name))
            await context.respond("Removed Hand role from " + target.name + ".")
            await logm.sendlog(logm.roles, context, mode = logm.removerole, target = target, role = handrole)
        # User doesn't have role, remove it
        else:
            await target.add_roles(handrole, reason = sanitizereason(context.author.name, addedrolename = handrole.name))
            await context.respond("Added Hand role to " + target.name + ".")
            await logm.sendlog(logm.roles, context, mode = logm.addrole, target = target, role = handrole)
        return
        

        
@bot.slash_command(description = "Mark which roles are moderation roles.")
@guild_only()
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
    flooder: discord.Option(
    discord.SlashCommandOptionType.role,
    required = True,
    description = "Role to be marked as a Flooder role.")
    ):
        # Command permission level
        commandpermissionlevel = 4
        # Permission check
        canrun = await pm.canrun(context, context.author, commandpermissionlevel=commandpermissionlevel)
        if not canrun:
            return
        try:
            # Write new ids to config
            cfg.set("puppetrole", puppet.id)
            cfg.set("handrole", hand.id)
            cfg.set("armrole", arm.id)
            cfg.set("flooderrole", flooder.id)
            await context.respond("Marked " + puppet.name + " as Puppet, " + hand.name + " as Hand, " + arm.name + " as Arm and " + flooder.name + " as Flooder.")
        except:
            await context.respond("Error setting roles.")
        return
        
@bot.slash_command(description = "Changes the channel of log messages.")
@guild_only()
async def setlogchannel(context, channel: discord.Option(
    discord.SlashCommandOptionType.channel,
    required = True,
    description = "Channel to send logs to.")
    ):
        # Command permission level
        commandpermissionlevel = 4
        # Permission check
        canrun = await pm.canrun(context, context.author, commandpermissionlevel=commandpermissionlevel)
        if not canrun:
            return
        if not str(channel.type) == "text":
            await pm.throwerror(context, "The channel you've selected is not a text channel.")
            return
        await context.respond("Set the log channel to <#" + str(channel.id) + ">.")
        cfg.set("logchannelid", channel.id)
        logm.loadlogchannelid()
        logm.ready()
        return
            
@bot.slash_command(description = "Get user's permission level.")
@guild_only()
async def getperms(context):
    # Debug command to return permission level
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