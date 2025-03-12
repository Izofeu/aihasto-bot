from extrafunctions import isemptyreason, isvalidtime
import datetime
import discord

class warns:
    def __init__(self, cfg, bot, permmanager, log, sql):
        self.cfg = cfg
        self.bot = bot
        self.pm = permmanager
        self.logm = log
        self.sqlm = sql
    
    async def addwarn(self, context, target, reason):
        expirydate = isvalidtime("3d")[0].strftime("%Y-%m-%d %H:%M:%S")
        warncount = await self.sqlm.getwarncount(target.id)
        message = "User <@" + str(target.id) + "> has been issued a warning for " + isemptyreason(reason) + "."
        if warncount > 0:
            message += " They have " + str(warncount) + " other warning(s) on account."
            class showwarnsbutton(discord.ui.View):
                @discord.ui.button(label = "Show all warns", style = discord.ButtonStyle.primary)
                async def button_callback(self, button, interaction):
                    # Command permission level
                    commandpermissionlevel = 1
                    # Permission check
                    canrun = await self.pm.canrun(context = interaction, member = interaction.user, commandpermissionlevel = commandpermissionlevel, interaction = True)
                    if not canrun:
                        return
                    await interaction.response.send_message(await self.getwarningmessage(target), ephemeral = True)
                def __init__(self, pm, getwarningmessage):
                    # Run init function of discord.ui.View before initializing our variables
                    super().__init__()
                    self.pm = pm
                    self.getwarningmessage = getwarningmessage
        else:
            message += " This is their first warning."
        modreason = "<@" + str(context.author.id) + "> - " + isemptyreason(reason)
        await self.sqlm.addwarning(target.id, expirydate, modreason)
        if warncount > 0:
            # Delete the message after 1 minute to prevent a memory leak with too many buttons
            await context.respond(message, view = showwarnsbutton(self.pm, self.getwarningmessage), ephemeral = True, delete_after = 120)
        else:
            await context.respond(message, ephemeral = True)
        
        await self.logm.sendlog(self.logm.warns, context, mode = self.logm.addwarn, target = target, reason = isemptyreason(reason))
        try:
            await target.send("You have been issued a warning by <@" + str(context.author.id) + "> for " + isemptyreason(reason) + ".")
        except:
            pass
        return
        
    async def clearwarns(self, context, target, reason):
        try:
            await self.sqlm.removewarnings(target.id)
            await context.respond("Warnings for user <@" + str(target.id) + "> have been removed.", ephemeral = True)
            await self.logm.sendlog(self.logm.warns, context, target = target, mode = self.logm.clearwarns, reason = isemptyreason(reason))
        except:
            await self.pm.throwerror(context, "Error removing warnings.")
        return
        
    async def getwarningmessage(self, member):
        warningscount, warnings = await self.sqlm.getwarnings(member.id)
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
        return message
        
    async def showwarnings(self, context, member):
        message = await self.getwarningmessage(member)
        await context.respond(message, ephemeral = True)
        return