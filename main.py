import discord
from discord.ext import tasks
from discord import guild_only
from discord.ext import commands
import re
import configparse
import datetime
import permmanager
import sqlmanager
import logmanager
import commandmanager
import rolemanager
import c_ui
import responsemanager
from extrafunctions import getutctimestamp

messagecache = []
recentunbans = []
recenttimeouts = []

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
intents.members = True
intents.moderation = True
intents.guilds = True

nocachemembers = discord.MemberCacheFlags.none()

bot = discord.Bot(intents = intents, chunk_guilds_at_startup = False, max_messages = 10000)
cfg = configparse.parseconfig("config.cfg")
cfg.load()
# Load bot token
token = cfg.loadtoken()
responsem = responsemanager.responsemanager(cfg)
# Load up sql manager and permissions manager
pm = permmanager.permmanager(cfg, responsem)
sqlm = sqlmanager.sqlmanager(cfg)
logm = logmanager.logmanager(cfg, bot, sqlm)
rolem = rolemanager.rolemanager(cfg, pm, bot, sqlm, logm, responsem)
cmdm = commandmanager.cmdmanager(cfg, bot, pm, sqlm, rolem, logm, responsem)

def isemptyreason(reason):
    if not reason:
        reason = "No reason provided."
    return reason[:511]

def sanitizereason(author, reason = False, addedrolename = False, removedrolename = False, duration = False, unban = False):
    finalreason = "Responsible user: " + author
    if addedrolename:
        finalreason += ", Added role: " + addedrolename
    if removedrolename:
        finalreason += ", Removed role: " + removedrolename
    if unban:
        finalreason += ", Action: Unban"
    if duration:
        finalreason += ", Duration: " + duration
    if reason:
        finalreason = finalreason + ", Reason: " + reason
    finalreason = finalreason[:511]
    return finalreason

# Check if duration inputted by user in commands is valid
def isvalidtime(time, maxduration = 14):
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
        if (timeunit == "d" and timeduration > maxduration) or (
        timeunit == "h" and timeduration > (maxduration * 24)) or (
        timeunit == "m" and timeduration > (maxduration * 24 * 60)):
            raise Exception("Invalid duration.")
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
async def on_raw_audit_log_entry(entry):
    await logm.parserawauditlogentry(entry, recentunbans, recenttimeouts)
    return
        
@bot.event
async def on_member_join(member):
    isflooder = await sqlm.isflooder(member.id)
    if isflooder > 0:
        flooderrole = member.guild.get_role(cfg.get("flooderrole"))
        await member.add_roles(flooderrole, reason = "Added a Flooder role due to user rejoining the server while having an active Flooder punishment.")
    return

@bot.event
async def on_message_edit(before, after):
    if before.author.bot:
        return
    if after.channel.id == cfg.get("greatmitaid"):
        if not cfg.get("automessagecuration"):
            return
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
            await logm.sendlog(category = logm.timeouts, mode = logm.selfissuedwarn, context = bot, target = after.author.id, duration = untiltimestamp, reason = reason)
            await after.author.send(content = "You have been timed out by " + bot.user.name + " for " + reason + " until <t:" + str(untiltimestamp) + ":F>.")
    elif after.channel.id == cfg.get("gifpartyid"):
        if not cfg.get("automessagecuration"):
            return
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
    elif before.content == after.content and before.attachments == after.attachments:
        return
    else:
        if pm.getpermissionlevel(after.author) == 4:
            return
        if str(before.channel.id) in cfg.get("nologs").split(","):
            return
        embed = discord.Embed()
        embed.title="Message edited"
        embed.color = discord.Colour.orange()
        embed.description = "Message author: <@" + str(before.author.id) + ">, at https://discord.com/channels/" + str(cfg.get("guild")) + "/" + str(before.channel.id) + "/" + str(before.id)
        oldmessage = before.content
        oldmessagetitle = "Old message:"
        newmessagetitle = "New message:"
        if len(oldmessage) > 1023:
            oldmessage = oldmessage[:1023]
            oldmessagetitle += " (trimmed)"
        newmessage = after.content
        if len(newmessage) > 1023:
            newmessage = newmessage[:1023]
            newmessagetitle += " (trimmed)"
        embed.add_field(name = oldmessagetitle, value = oldmessage, inline = False)
        embed.add_field(name = newmessagetitle, value = newmessage, inline = False)
        attachmentlinks = ""
        for x in before.attachments:
            attachmentlinks += x.proxy_url + "\n"
        if attachmentlinks:
            embed.add_field(name = "Attachments:", value = attachmentlinks, inline = False)
        #embed.add_field(name = "Date:", value = "<t:" + getutctimestamp() + ":f>", inline = False)
        await logm.uploadembed(embed, ismessagelog = True)
    return
    
@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return
    if pm.getpermissionlevel(message.author) == 4:
        return
    if str(message.channel.id) in cfg.get("nologs").split(","):
        return
    embed = discord.Embed()
    embed.title = "Message deleted"
    embed.color = discord.Colour.red()
    embed.description = "Message author: <@" + str(message.author.id) + ">, at <#" + str(message.channel.id) + ">"
    embed.add_field(name = "Old message:", value = message.content, inline = False)
    attachmentlinks = ""
    for x in message.attachments:
        attachmentlinks += x.proxy_url + "\n"
    if attachmentlinks:
        embed.add_field(name = "Attachments:", value = attachmentlinks, inline = False)
    stickers = ""
    for x in message.stickers:
        stickers += x.url + "\n"
    if stickers:
        embed.add_field(name = "Stickers:", value = stickers, inline = False)
    #embed.add_field(name = "Date:", value = "<t:" + getutctimestamp() + ":f>", inline = False)
    await logm.uploadembed(embed, ismessagelog = True)
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
        if message.channel.id == cfg.get("logchannelid"):
            await message.delete()
        elif message.channel.id == cfg.get("greatmitaid"):
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
    # Start periodic task for checking expired temproles
    logm.ready()
    checkmodactions.start()
    
@tasks.loop(seconds=60)
async def checkmodactions():
    await checkwarnings()
    await checktemproles()
    return
async def checkwarnings():
    await sqlm.deleteexpiredwarns(datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M:%S"))
    return
async def checktemproles():
    await rolem.removeexpiredroles(datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M:%S"))
    return
    
@bot.message_command(name = "Edit mod reason")
@guild_only()
async def editmodreason(context, message):
    # Command permission level
    commandpermissionlevel = 1
    # Permission check
    canrun = await pm.canrun(context, context.author, commandpermissionlevel = commandpermissionlevel)
    if not canrun:
        return
    await cmdm.openeditreasonmenu(context, message)
    return
    
@bot.user_command(name = "Show punishments")
@guild_only()
async def showpunishments(context, member: discord.Member):
    # Command permission level
    commandpermissionlevel = 1
    # Permission check
    canrun = await pm.canrun(context, context.author, target = member, commandpermissionlevel = commandpermissionlevel)
    if not canrun:
        return
    await cmdm.showpunishmenthistory(context, member)
    return
    
@bot.slash_command(description = "Adds Mr Mustard to a user for 24 hours.")
@guild_only()
async def addmustard(context, target: discord.Option(
    discord.SlashCommandOptionType.user,
    required = True,
    description = "User to add a Mr Mustard role.")
    ):
        # Command permission level
        commandpermissionlevel = 2
        # Permission check
        canrun = await pm.canrun(context, context.author, commandpermissionlevel = commandpermissionlevel)
        if not canrun:
            return
        await context.defer(ephemeral = True)
        await cmdm.temprole(context, target, rolem.addtemprole, rolem.mrmustardrole, duration = "24h")
        return
        
@bot.slash_command(description = "Removes Mr Mustard from a user.")
@guild_only()
async def removemustard(context, target: discord.Option(
    discord.SlashCommandOptionType.user,
    required = True,
    description = "User to remove a Mr Mustard role from.")
    ):
         # Command permission level
        commandpermissionlevel = 2
        # Permission check
        canrun = await pm.canrun(context, context.author, commandpermissionlevel = commandpermissionlevel)
        if not canrun:
            return
        await context.defer(ephemeral = True)
        await cmdm.temprole(context, target, rolem.removetemprole, rolem.mrmustardrole)
        return
    
@bot.slash_command(description = "Adds Mita's Gladiators to a user.")
@guild_only()
async def addgladiator(context, target: discord.Option(
    discord.SlashCommandOptionType.user,
    required = True,
    description = "Who to add the Gladiator role to."),
    duration: discord.Option(
    discord.SlashCommandOptionType.string,
    required = True,
    description = "The duration of the Gladiator. Examples: 30d - 30 days, 24h - 24 hours."),
    reason: discord.Option(
    discord.SlashCommandOptionType.string,
    required = False,
    description = "Reason for issuing the Gladiator role.")
    ):
        try:
            eventmanagerrole = context.author.guild.get_role(cfg.get("eventmanagerid"))
            gladiatorrole = context.author.guild.get_role(cfg.get("gladiatorid"))
            if eventmanagerrole is None or gladiatorrole is None:
                raise Exception()
        except:
            await pm.throwerror(context, "Gladiator / Event manager roles are not set!")
            return
        if not pm.hasrole(context.author, eventmanagerrole.id) and pm.getpermissionlevel(context.author) < 4:
            await pm.throwerror(context, "You do not have Event Manager role.")
            return
        await context.defer(ephemeral = True)
        await cmdm.temprole(context, target, rolem.addtemprole, rolem.gladiatorrole, duration = duration, reason = reason)
        return
        
@bot.slash_command(description = "Removes Mita's Gladiators from a user.")
@guild_only()
async def removegladiator(context, target: discord.Option(
    discord.SlashCommandOptionType.user,
    required = True,
    description = "Who to remove the Gladiator role from."),
    reason: discord.Option(
    discord.SlashCommandOptionType.string,
    required = False,
    description = "Reason for removing the Gladiator role.")
    ):
        try:
            eventmanagerrole = context.author.guild.get_role(cfg.get("eventmanagerid"))
            gladiatorrole = context.author.guild.get_role(cfg.get("gladiatorid"))
        except:
            await pm.throwerror(context, "Gladiator / Event manager roles are not set!")
            return
        if not pm.hasrole(context.author, eventmanagerrole.id) and pm.getpermissionlevel(context.author) < 4:
            await pm.throwerror(context, "You do not have Event Manager role.")
            return
        await context.defer(ephemeral = True)
        await cmdm.temprole(context, target, rolem.removetemprole, rolem.gladiatorrole, reason = reason)
        return

@bot.slash_command(description = "Unbans a user with a reason.")
@guild_only()
async def unban(context, target: discord.Option(
    discord.SlashCommandOptionType.user,
    required = True,
    description = "ID of a user to unban."),
    reason: discord.Option(
    discord.SlashCommandOptionType.string,
    required = True,
    description = "Reason for the unban.")
    ):
        # Command permission level
        commandpermissionlevel = 2
        # Permission check
        canrun = await pm.canrun(context, context.author, commandpermissionlevel = commandpermissionlevel)
        if not canrun:
            return
        await context.defer(ephemeral = True)
        try:
            modreason = sanitizereason(context.author.name, reason = reason, unban = True)
            recentunbans.append(target.id)
            await context.author.guild.unban(target, reason = modreason)
            await context.respond("User with id " + str(target.id) + " (<@" + str(target.id) + ">) has been unbanned.")
            await logm.sendlog(logm.unbans, context = context.author, target = target.id, reason = isemptyreason(reason))
            sec10 = datetime.datetime.now() + datetime.timedelta(seconds = 10)
            await discord.utils.sleep_until(sec10)
            try:
                recentunbans.remove(target.id)
            except:
                pass
        except:
            try:
                recentunbans.remove(target.id)
            except:
                pass
            await pm.throwerror(context, "Couldn't unban the user with id " + str(target.id) + ". User may be unbanned already.")
        return

@bot.slash_command(description = "Toggles auto message curation of gif-party and miside-great-mita.")
@guild_only()
async def autopunishtoggle(context):
    # Command permission level
    commandpermissionlevel = 4
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
        await context.defer(ephemeral = True)
        await cmdm.warn(context, target, reason, True)
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
        await context.defer(ephemeral = True)
        await cmdm.warn(context, target, reason, False)
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
        await context.defer(ephemeral = True)
        await cmdm.temprole(context, target, mode = rolem.removetemprole, roletype = rolem.flooderrole, reason = reason)
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
        await context.defer(ephemeral = True)
        await cmdm.temprole(context, target, mode = rolem.addtemprole, roletype = rolem.flooderrole, duration = duration, reason = reason)
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
        await context.defer(ephemeral = True)
        await cmdm.setslowmode(context, target, delay)
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
        await context.defer(ephemeral = True)
        await cmdm.timeout(context, target, duration, reason)
        return
        
@bot.slash_command(description = "Removes a user from a time-out with a reason.")
@guild_only()
async def untimeout(context, target: discord.Option(
    discord.SlashCommandOptionType.user,
    required = True,
    description = "User to issue a time-out to."),
    reason: discord.Option(
    discord.SlashCommandOptionType.string,
    required = False,
    description = "Reason for the timeout.")
    ):
        # Command permission level
        commandpermissionlevel = 1
        # Permission check
        canrun = await pm.canrun(context, context.author, target=target, commandpermissionlevel=commandpermissionlevel)
        if not canrun:
            return
        await context.defer(ephemeral = True)
        await cmdm.timeout(context, target, duration = False, reason = reason, untimeout = True)
        return
        
@bot.slash_command(description = "Toggles Content creator for a user.")
@guild_only()
async def creator(context, target: discord.Option(
    discord.SlashCommandOptionType.user,
    required = True,
    description = "User to toggle a Content creator role for."),
    reason: discord.Option(
    discord.SlashCommandOptionType.string,
    required = False,
    description = "Reason for toggling the Content creator role.")
    ):
        # Command permission level
        if not pm.hasrole(context.author, cfg.get("contentcreatormanagerrole")) and pm.getpermissionlevel(context.author) < 4:
            await pm.throwerror(context, "Only Content creator managers can run this command.")
            return
        await cmdm.role(context = context, target = target, role = rolem.contentcreatorrole, reason = reason)
        return

@bot.slash_command(description = "Toggles Puppet role for a user.")
@guild_only()
async def puppet(context, target: discord.Option(
    discord.SlashCommandOptionType.user,
    required = True,
    description = "User to toggle a Puppet role for."),
    reason: discord.Option(
    discord.SlashCommandOptionType.string,
    required = False,
    description = "Reason for toggling the Puppet role.")
    ):
        # Command permission level
        commandpermissionlevel = 2
        # Permission check
        canrun = await pm.canrun(context, context.author, target = target, commandpermissionlevel = commandpermissionlevel)
        if not canrun:
            return
        await cmdm.role(context = context, target = target, role = rolem.puppetrole, reason = reason)
        return
            
@bot.slash_command(description = "Toggles Hand role for a user.")
@guild_only()
async def hand(context, target: discord.Option(
    discord.SlashCommandOptionType.user,
    required = True,
    description = "User to toggle a Hand role for."),
    reason: discord.Option(
    discord.SlashCommandOptionType.string,
    required = False,
    description = "Reason for toggling the Hand role.")
    ):
        # Command permission level
        commandpermissionlevel = 3
        # Permission check
        canrun = await pm.canrun(context, context.author, target = target, commandpermissionlevel = commandpermissionlevel)
        if not canrun:
            return
        await cmdm.role(context = context, target = target, role = rolem.handrole, reason = reason)
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
        
@bot.slash_command(description = "Mark which roles are content creator roles.")
@guild_only()
async def setcreatorroles(context, contentcreatormanager: discord.Option(
    discord.SlashCommandOptionType.role,
    required = True,
    description = "Role to be marked as a Content Creator Manager role."),
    contentcreator: discord.Option(
    discord.SlashCommandOptionType.role,
    required = True,
    description = "Role to be marked as a Content Creator role.")
    ):
        # Command permission level
        commandpermissionlevel = 4
        # Permission check
        canrun = await pm.canrun(context, context.author, commandpermissionlevel=commandpermissionlevel)
        if not canrun:
            return
        try:
            cfg.set("contentcreatormanagerrole", contentcreatormanager.id)
            cfg.set("contentcreatorrole", contentcreator.id)
            await context.respond("Marked " + contentcreatormanager.name + " as Content creator manager and " + contentcreator.name + " as Content creator.")
        except:
            await pm.throwerror(context, "Error setting roles.")
        return
        
@bot.slash_command(description = "Mark which roles are event roles.")
@guild_only()
async def seteventroles(context, eventmanager: discord.Option(
    discord.SlashCommandOptionType.role,
    required = True,
    description = "Role to be marked as an Event manager role."),
    gladiator: discord.Option(
    discord.SlashCommandOptionType.role,
    required = True,
    description = "Role to be marked as a Gladiator role.")
    ):
        # Command permission level
        commandpermissionlevel = 4
        # Permission check
        canrun = await pm.canrun(context, context.author, commandpermissionlevel=commandpermissionlevel)
        if not canrun:
            return
        try:
            # Write new ids to config
            cfg.set("eventmanagerid", eventmanager.id)
            cfg.set("gladiatorid", gladiator.id)
            await context.respond("Marked " + eventmanager.name + " as Event manager and " + gladiator.name + " as Gladiator.")
        except:
            await pm.throwerror(context, "Error setting roles.")
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

@bot.slash_command(description = "Enable permission debug mode. Developer only.")
@guild_only()
async def permdebug(context):
    if str(context.author.id) not in cfg.get("masters").split(","):
        await context.respond("This command can only be toggled by the bot developer.", ephemeral = True)
        return
    if cfg.get("permdebug") == 1:
        cfg.set("permdebug", 0)
        await context.respond("Disabled permission debug mode.", ephemeral = True)
    else:
        cfg.set("permdebug", 1)
        await context.respond("Enabled permission debug mode.", ephemeral = True)
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