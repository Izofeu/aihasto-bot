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
        #await interaction.response.send_message(message, ephemeral = True)
        return