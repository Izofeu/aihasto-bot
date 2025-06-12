import datetime
from discord.ext import commands
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
        untiltimestamp = int(date.timestamp())
        return date, untiltimestamp
    # If anything went wrong, report an incorrect date
    except:
        return False, False
    
def isemptyreason(reason):
    if not reason:
        reason = "No reason provided."
    return reason[:511]
    
def sanitizereason(author, reason = False, addedrolename = False, removedrolename = False, duration = False, unban = False, kick = False, ban = False):
    finalreason = "Responsible user: " + author
    if addedrolename:
        finalreason += ", Added role: " + addedrolename
    if removedrolename:
        finalreason += ", Removed role: " + removedrolename
    if unban:
        finalreason += ", Action: Unban"
    if kick:
        finalreason += ", Action: Kick"
    if ban:
        finalreason += ", Action: Ban"
    if duration:
        finalreason += ", Duration: " + duration
    if reason:
        finalreason = finalreason + ", Reason: " + reason
    finalreason = finalreason[:511]
    return finalreason
    
def discorddatetodateobject(date):
    date_date = date[:10]
    date_time = date[11:19]
    date = date_date + " " + date_time + " +0000"
    format = "%Y-%m-%d %H:%M:%S %z"
    date = datetime.datetime.strptime(date, format)
    timestamp = int(date.timestamp())
    return date, timestamp
    
def sqldatetodateobject(date):
    format = "%Y-%m-%d %H:%M:%S %z"
    date = str(date)
    date += " +0000"
    date = datetime.datetime.strptime(date, format)
    timestamp = int(date.timestamp())
    return date, timestamp
    
def datetotimestamp(date):
    return int(date.timestamp())
    
def getutctimestamp():
    return str(int(datetime.datetime.now(datetime.UTC).timestamp()))
    
def amiauthor(message, botid):
    if message.author.id != botid:
        return False
    return True
    
def getauthor(context):
    if isinstance(context, commands.Context):
        return context.author
    return context.user
    
def gettimedifferencestr(date2, date1):
    timedifference = date2 - date1
    timedifference = int(timedifference.total_seconds())
    # Account for potential clock desync of 1 minute
    timedifference += 60
    hours = timedifference // 3600
    timediff = str(hours) + " hour(s)"
    if hours == 0:
        timediff = "<1 hour"
    elif hours > 24:
        hours = hours // 24
        timediff = str(hours) + " day(s)"
    return timediff
    
def getdatefordb():
    return datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M:%S")
    
def datetosqlformat(date):
    return date.strftime("%Y-%m-%d %H:%M:%S")
    
def preparemessagelog(cfg, message):
    attachmentlinks = stickers = preparedtitle = ""
    prepareddescription = "Message author: <@" + str(message.author.id) + ">, at https://discord.com/channels/" + str(cfg.get("guild")) + "/" + str(message.channel.id) + "/" + str(message.id)
    preparedmessage = message.content
    if len(preparedmessage) > 1023:
        preparedtitle = " (trimmed)"
        preparedmessage = preparedmessage[:1023]
    
    for x in message.attachments:
        attachmentlinks += x.proxy_url + "\n"
    for x in message.stickers:
        stickers += x.url + "\n"
        attachmentlinks = attachmentlinks[:1023]
    return preparedmessage, prepareddescription, preparedtitle, attachmentlinks, stickers
    
def getguild(cfg, bot):
    return bot.get_guild(cfg.get("guild"))