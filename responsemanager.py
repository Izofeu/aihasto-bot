from discord.ext import commands

class responsemanager:
    def __init__(self, cfg):
        self.cfg = cfg
        # We use payloads for big / multiple messages created in different files like punishment history
        self.payload = 1
        self.e_messageauthornotbot = 2
        self.e_messagenoembeds = 3
        self.e_messagenotauthorandnothand = 4
        self.e_nopermissionembededit = 5
        self.e_noissuerfield = 6
        self.s_editedembed = 7
        self.s_addedwarning = 8
        self.e_leftserver = 9
        
    async def respond(self, context, type, target = None, reason = None, payload = None):
        if isinstance(context, commands.Context):
            author = context.author
        else:
            author = context.user
        message = "Error getting an interaction response. Contact the bot developer."
        if type == self.payload:
            message = payload
        elif type == self.e_messageauthornotbot:
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
        elif type == self.s_addedwarning:
            message = "User <@" + str(target) + "> has been issued a warning for " + reason + "."
        elif type == self.e_leftserver:
            message = "User <@" + str(target.id) + "> has left the server."
        if isinstance(context, commands.Context):
            await context.respond(message, ephemeral = True)
        else:
            if context.response.is_done():
                await context.followup.send(message, ephemeral = True)
            else:
                await context.response.send_message(message, ephemeral = True)
        return