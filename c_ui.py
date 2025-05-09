import discord
from extrafunctions import getauthor, getutctimestamp
        
class issuewarnbutton(discord.ui.View):
    @discord.ui.button(label = "Issue warn", style = discord.ButtonStyle.primary)
    async def button_callback(self, button, interaction):
        self.disable_all_items()
        # Command permission level
        commandpermissionlevel = 1
        # Permission check
        canrun = await self.pm.canrun(context = interaction, member = self.context.author, target = self.target, commandpermissionlevel = commandpermissionlevel, interaction = True)
        if not canrun:
            return
        warnui = self.warnui(self.context, target = self.target, addwarn = self.addwarn)
        await interaction.response.send_modal(warnui)
        await self.hook.edit(view = self)
    def __init__(self, pm, warnui, context, target, addwarn):
        # Run init function of discord.ui.View before initializing our variables
        super().__init__()
        self.pm = pm
        self.warnui = warnui
        self.context = context
        self.target = target
        self.addwarn = addwarn
        
    def setwebhook(self, hook):
        self.hook = hook
        
class reportui(discord.ui.Modal):
    def __init__(self, message, modthread, submitreport, title = "Report message", minlength = 10):
        super().__init__(title = title)
        self.message = message
        self.modthread = modthread
        self.submitreport = submitreport
        self.add_item(discord.ui.InputText(label = "Reason", required = True, min_length = minlength, max_length = 256))
    async def callback(self, interaction: discord.Interaction):
        reason = self.children[0].value
        await self.submitreport(interaction, self.message, reason, self.modthread)
        return
        
class resolvereportbutton(discord.ui.View):
    def __init__(self, sqlm, responsem):
        super().__init__(timeout = None)
        self.sqlm = sqlm
        self.hook = None
        self.responsem = responsem
        
    @discord.ui.button(label = "Mark Resolved", emoji = "✅", custom_id = "resolvedbutton", style = discord.ButtonStyle.success)
    async def valid_callback(self, button, interaction):
        self.disable_all_items()
        author = getauthor(interaction)
        message = interaction.message
        try:
            embed = message.embeds[0]
            embed.insert_field_at(index = 0, name = "Resolved by", value = "<@" + str(author.id) + ">", inline = False)
            count = len(embed.fields)
            embed.insert_field_at(index = count, name = "Resolve date", value = "<t:" + getutctimestamp() + ":F>", inline = False)
            await message.edit(view = self, embed = embed)
            caseid = targetid = None
            for field in embed.fields:
                if field.name == "Case ID":
                    caseid = field.value
                elif field.name == "Reporter":
                    targetid = field.value[2:-1]
            try:
                if caseid and targetid:
                    guild = interaction.guild
                    member = await guild.fetch_member(targetid)
                    await self.responsem.dm(member, "Your report with Case ID " + str(caseid) + " has been marked as resolved.")
            except:
                pass
        except:
            await message.edit(view = self)
        await interaction.respond("Marked the report as resolved. Discord forces me to send this useless message else you get an error :slight_frown:.", ephemeral = True)
        await self.sqlm.subtractreport(author.id)
        return
        
    def sethook(self, hook):
        self.hook = hook
        
    #@discord.ui.button(label = "Mark Invalid", emoji = "❌", custom_id = "unresolvedbutton", style = discord.ButtonStyle.danger)
    #async def invalid_callback(self, button, interaction):
    #    author = getauthor(interaction)
    #    message = interaction.message
    #    await message.delete()
    #    return
        
class showwarnsbutton(discord.ui.View):
    @discord.ui.button(label = "Show all warns", style = discord.ButtonStyle.primary)
    async def button_callback(self, button, interaction):
        self.disable_all_items()
        await interaction.response.edit_message(view = self)
        # Command permission level
        commandpermissionlevel = 1
        # Permission check
        canrun = await self.pm.canrun(context = interaction, member = interaction.user, commandpermissionlevel = commandpermissionlevel, interaction = True)
        if not canrun:
            return
        await interaction.followup.send(await self.getwarningmessage(self.target), ephemeral = True)
    def __init__(self, pm, getwarningmessage, target):
        # Run init function of discord.ui.View before initializing our variables
        super().__init__()
        self.pm = pm
        self.getwarningmessage = getwarningmessage
        self.target = target
        
class editreasonui(discord.ui.Modal):
    def __init__(self, message, cmdm):
        super().__init__(title = "Edit mod reason")
        self.message = message
        self.cmdm = cmdm
        self.add_item(discord.ui.InputText(label = "Reason", required = True, max_length = 511))
    
    async def callback(self, interaction):
        reason = self.children[0].value
        await self.cmdm.editreason(interaction, self.message, reason)
        return
        
class newflooderui(discord.ui.Modal):
    async def callback(self, interaction):
        await interaction.response.defer()
        # Command permission level
        commandpermissionlevel = 1
        # Permission check
        canrun = await self.canrun(interaction, interaction.user, target = self.target, commandpermissionlevel = commandpermissionlevel)
        if not canrun:
            return
        duration = self.children[0].value
        reason = self.children[1].value
        await self.rolem.temprole(interaction, self.target, self.rolem.addtemprole, self.rolem.flooderrole, duration = duration, reason = reason)
        
    def __init__(self, member, rolemanager, canrun):
        super().__init__(title = "Issue flooder")
        self.canrun = canrun
        self.target = member
        self.rolem = rolemanager
        self.add_item(discord.ui.InputText(label = "Duration", value = "2d", required = True, max_length = 4))
        self.add_item(discord.ui.InputText(label = "Reason", required = False, max_length = 511))
        
class newwarnui(discord.ui.Modal):
    async def callback(self, interaction):
        await interaction.response.defer()
        # Command permission level
        commandpermissionlevel = 1
        # Permission check
        canrun = await self.canrun(interaction, interaction.user, target = self.target, commandpermissionlevel = commandpermissionlevel)
        if not canrun:
            return
        reason = self.children[0].value
        expiry = self.children[1].value
        await self.addwarn(interaction, self.target, reason = reason, until = expiry)
        
    def __init__(self, member, addwarn, canrun):
        super().__init__(title = "Issue warn")
        self.canrun = canrun
        self.target = member
        self.addwarn = addwarn
        self.add_item(discord.ui.InputText(label = "Reason", required = False, max_length = 511))
        self.add_item(discord.ui.InputText(label = "Expires in", required = True, value = "7d", max_length = 5))
        
class newtimeoutui(discord.ui.Modal):
    async def callback(self, interaction):
        await interaction.response.defer()
        # Command permission level
        commandpermissionlevel = 1
        # Permission check
        canrun = await self.canrun(interaction, interaction.user, target = self.target, commandpermissionlevel = commandpermissionlevel)
        if not canrun:
            return
        duration = self.children[0].value
        reason = self.children[1].value
        await self.addtimeout(interaction, self.target, duration = duration, reason = reason)
        
    def setdefaultduration(self, duration):
        self.add_item(discord.ui.InputText(label = "Duration", value = duration, required = True, max_length = 4))
        self.add_item(discord.ui.InputText(label = "Reason", required = True, max_length = 511))
        
    def __init__(self, target, addtimeout, canrun):
        super().__init__(title = "Issue timeout")
        self.canrun = canrun
        self.target = target
        self.addtimeout = addtimeout
        
class newkickui(discord.ui.Modal):
    async def callback(self, interaction):
        await interaction.response.defer()
        # Command permission level
        commandpermissionlevel = 2
        # Permission check
        canrun = await self.canrun(interaction, interaction.user, target = self.target, commandpermissionlevel = commandpermissionlevel)
        if not canrun:
            return
        reason = self.children[0].value
        await self.kick(interaction, self.target, reason)
            
    def __init__(self, target, canrun, kick):
        super().__init__(title = "Kick user")
        self.canrun = canrun
        self.target = target
        self.kick = kick
        self.add_item(discord.ui.InputText(label = "Reason", required = True, placeholder = "Bad name / bio / pronouns...", max_length = 511))
        
class punishmentbuttons(discord.ui.View):
    @discord.ui.button(label = "Warn", emoji = "⚠️", style = discord.ButtonStyle.primary)
    async def addwarn_callback(self, button, interaction):
        await self.disableallbuttons(interaction)
        warnui = self.warnui
        await interaction.response.send_modal(warnui)
        
    @discord.ui.button(label = "1h", emoji = "🔇", style = discord.ButtonStyle.primary)
    async def timeout1h_callback(self, button, interaction):
        await self.disableallbuttons(interaction)
        timeoutui = self.timeoutui
        timeoutui.setdefaultduration("1h")
        await interaction.response.send_modal(timeoutui)
        
    @discord.ui.button(label = "24h", emoji = "🔇", style = discord.ButtonStyle.primary)
    async def timeout24h_callback(self, button, interaction):
        await self.disableallbuttons(interaction)
        timeoutui = self.timeoutui
        timeoutui.setdefaultduration("24h")
        await interaction.response.send_modal(timeoutui)
        
    @discord.ui.button(label = "Flooder", emoji = "🌊", style = discord.ButtonStyle.primary)
    async def addflooder_callback(self, button, interaction):
        await self.disableallbuttons(interaction)
        flooderui = self.flooderui
        await interaction.response.send_modal(flooderui)
        
    @discord.ui.button(label = "Kick", emoji = "🥾", style = discord.ButtonStyle.danger, row = 1)
    async def kick_callback(self, button, interaction):
        await self.disableallbuttons(interaction)
        kickui = self.kickui
        await interaction.response.send_modal(kickui)
        
    async def disableallbuttons(self, interaction):
        self.disable_all_items()
        await self.hook.edit(view = self)
        return
    
    def sethook(self, hook):
        self.hook = hook
        
    def __init__(self, permmanager, target, warnui, timeoutui, flooderui, kickui):
        super().__init__(timeout = 60)
        self.target = target
        self.warnui = warnui
        self.timeoutui = timeoutui
        self.flooderui = flooderui
        self.kickui = kickui
        self.hook = None
        self.pm = permmanager