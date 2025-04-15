import discord

class issueflooderbutton(discord.ui.View):
    @discord.ui.button(label = "Issue flooder", style = discord.ButtonStyle.primary)
    async def button_callback(self, button, interaction):
        self.disable_all_items()
        # Command permission level
        commandpermissionlevel = 1
        # Permission check
        canrun = await self.pm.canrun(context = interaction, member = self.context.author, target = self.target, commandpermissionlevel = commandpermissionlevel, interaction = True)
        if not canrun:
            return
        
        flooderui = self.flooderui(context = self.context, target = self.target, rolem = self.rolem, temprole = self.temprole)
        await interaction.response.send_modal(flooderui)
        await self.hook.edit(view = self)
    def __init__(self, pm, context, target, flooderui, rolem, temprole):
        # Run init function of discord.ui.View before initializing our variables
        super().__init__()
        self.pm = pm
        self.context = context
        self.target = target
        self.flooderui = flooderui
        self.rolem = rolem
        self.temprole = temprole
        
    def setwebhook(self, hook):
        self.hook = hook
        return
        
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
        
class flooderui(discord.ui.Modal):
    def __init__(self, context, target, rolem, temprole, title = "Issue flooder role"):
        super().__init__(title = title)
        self.add_item(discord.ui.InputText(label = "Duration", required = True, placeholder = "2d, 48h, etc.", max_length = 5, value = "2d"))
        self.add_item(discord.ui.InputText(label = "Reason", required = False, max_length = 511))
        self.target = target
        self.context = context
        self.rolem = rolem
        self.temprole = temprole
        
    async def callback(self, interaction: discord.Interaction):
        duration = self.children[0].value
        reason = self.children[1].value
        await self.temprole(self.context, self.target, mode = self.rolem.addtemprole, roletype = self.rolem.flooderrole, duration = duration, reason = reason, interaction = interaction)
        #await interaction.response.send_message(message, ephemeral = True)
        return
        
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
        
class warnui(discord.ui.Modal):
    def __init__(self, context, target, addwarn, title = "Issue warn"):
        super().__init__(title = title)
        self.add_item(discord.ui.InputText(label = "Reason", required = False, max_length = 511))
        self.target = target
        self.context = context
        self.addwarn = addwarn
        
    async def callback(self, interaction: discord.Interaction):
        reason = self.children[0].value
        await self.addwarn(self.context, self.target, reason = reason, interaction = interaction)
        return
        
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
        duration = self.children[0].value
        reason = self.children[1].value
        await self.rolem.temprole(interaction, self.target, self.rolem.addtemprole, self.rolem.flooderrole, duration = duration, reason = reason)
        
    def __init__(self, member, rolemanager):
        super().__init__(title = "Issue flooder")
        self.target = member
        self.rolem = rolemanager
        self.add_item(discord.ui.InputText(label = "Duration", value = "2d", required = True, max_length = 4))
        self.add_item(discord.ui.InputText(label = "Reason", required = False, max_length = 511))
        
class newwarnui(discord.ui.Modal):
    async def callback(self, interaction):
        reason = self.children[0].value
        await self.addwarn(interaction, self.target, reason = reason)
        
    def __init__(self, member, addwarn):
        super().__init__(title = "Issue warn")
        self.target = member
        self.addwarn = addwarn
        self.add_item(discord.ui.InputText(label = "Reason", required = False, max_length = 511))
        
class newtimeoutui(discord.ui.Modal):
    async def callback(self, interaction):
        duration = self.children[0].value
        reason = self.children[1].value
        await self.addtimeout(interaction, self.target, duration = duration, reason = reason)
        
    def setdefaultduration(self, duration):
        self.add_item(discord.ui.InputText(label = "Duration", value = duration, required = True, max_length = 4))
        self.add_item(discord.ui.InputText(label = "Reason", required = True, max_length = 511))
        
    def __init__(self, target, addtimeout):
        super().__init__(title = "Issue timeout")
        self.target = target
        self.addtimeout = addtimeout
        
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
        
    async def disableallbuttons(self, interaction):
        self.disable_all_items()
        await self.hook.edit(view = self)
        return
    
    def sethook(self, hook):
        self.hook = hook
        
    def __init__(self, target, warnui, timeoutui, flooderui):
        super().__init__()
        self.target = target
        self.warnui = warnui
        self.timeoutui = timeoutui
        self.flooderui = flooderui
        self.hook = None