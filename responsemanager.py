from discord.ext import commands

class responsemanager:
    def __init__(self, cfg):
        self.cfg = cfg
        
    async def respond(self, context, message = None, view = None, dmsuccess = True):
        if isinstance(context, commands.Context):
            author = context.author
        else:
            author = context.user
        
        if not dmsuccess:
            message += "\n:warning: Target has Direct messages disabled. They have not received info about this punishment."
        
        if isinstance(context, commands.Context):
            if view is not None:
                response = await context.respond(message, view = view, ephemeral = True)
            else:
                response = await context.respond(message, ephemeral = True)
        else:
            if context.response.is_done():
                if view is not None:
                    response = await context.followup.send(message, view = view, ephemeral = True)
                else:
                    response = await context.followup.send(message, ephemeral = True)
            else:
                if view is not None:
                    response = await context.response.send_message(message, view = view, ephemeral = True)
                else:
                    response = await context.response.send_message(message, ephemeral = True)
        return response
        
    async def dm(self, target, message = None, embed = None):
        try:
            await target.send(message, embed = embed)
            return True
        except Exception as e:
            print(e)
            return False