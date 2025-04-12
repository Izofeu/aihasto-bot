from discord.ext import commands

class responsemanager:
    def __init__(self, cfg):
        self.cfg = cfg
        
        self.e_messageauthornotbot = 1
        self.e_messagenoembeds = 2
        self.e_messagenotauthorandnothand = 3
        self.e_nopermissionembededit = 4
        self.e_noissuerfield = 5
        self.s_editedembed = 6
        
    async def respond(self, context, type):
        message = "Error getting an interaction response. Contact the bot developer."
        if type == self.e_messageauthornotbot:
            message = "Only messages sent by me can be edited."
        elif type == self.e_messagenoembeds:
            message = "This message doesn't have embeds."
        elif type == self.e_messagenotauthorandnothand:
            message = "You are not the author of this punishment. Ask Mita's Arms for assistance."
        elif type == self.e_nopermissionembededit:
            message = "Couldn't fetch permissions for embed edit."
        elif type == self.e_noissuerfield:
            message = "This message doesn't have an Issuer field so its reason cannot be edited."
        elif type == self.s_editedembed:
            message = "Successfully edited the embed."
        if isinstance(context, commands.Context):
            await context.respond(message, ephemeral = True)
        else:
            await context.response.send_message(message, ephemeral = True)
        return