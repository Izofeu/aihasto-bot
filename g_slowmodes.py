from extrafunctions import isemptyreason, sanitizereason

class slowmodes:
    def __init__(self, cfg, bot, permmanager, log):
        self.cfg = cfg
        self.bot = bot
        self.pm = permmanager
        self.logm = log
    async def setslowmode(self, context, target, delay):
        if not str(target.type) == "text":
            await self.pm.throwerror(context, "The channel you've selected is not a text channel.")
            return
        # Only channels with "general" in its name can have their slowmodes edited
        if "general" not in str(target.name):
            await self.pm.throwerror(context, "You can only edit slow mode for general channels.")
            return
        if delay < 1 or delay > 21600:
            await self.pm.throwerror(context, "Invalid slow mode duration. Allowed values: 1 - 21600 seconds.")
            return
        try:
            await target.edit(reason = sanitizereason(context.author.name), slowmode_delay = delay)
        except:
            await self.pm.throwerror(context, "Unable to edit the channel - I don't have permission.")
            return
        await context.respond("Slow mode for channel " + target.name + " set to " + str(delay) + " seconds.")
        await self.logm.sendlog(self.logm.slowmodes, context = context, duration = delay, channelid = target.id)
        return