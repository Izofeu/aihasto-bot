import discord
# WARNING! These permission methods are sensitive as they safeguard the bot against misuse.
# Any changes here could result in unauthorized users being able to run forbidden commands!
class permmanager:
    def __init__(self, cfg, responsem):
        # Prepare cfg
        self.cfg = cfg
        self.responsem = responsem
        
    async def canrun(self, context, member, target=False, commandpermissionlevel=-1, interaction = False, useroverride = False, shoulderoverride = False):
        # This method checks if a member has permission to run a command.
        # The permissions involve two checks:
        # If a command is a general command that doesn't affect a specific user then
        # only check if the user has the required permission.
        # If a command affects another user, ensure that the user is below us
        # in the role hierarchy. This also prevents self removal of roles
        # because we are always equal in the role hierarchy.
        try:
            # If permission level isn't set by us, return false
            if commandpermissionlevel == -1:
                raise Exception("Command permission level not set.")
            # Check permission level of the user who ran the command
            inituser_permissionlevel = self.getpermissionlevel(member)
            if inituser_permissionlevel < commandpermissionlevel:
                await self.responsem.respond(context, "You do not have enough permissions to run this command.")
                return False
            # If a command affects another user, perform a hierarchy check
            if target:
                if not isinstance(target, discord.Member):
                    if useroverride:
                        return True
                    await self.responsem.respond(context, "User <@" + str(target.id) + "> has left the server.")
                    return False
                if target.bot:
                    await self.responsem.respond(context, "The target mustn't be a bot.")
                    return False
                targetuser_permissionlevel = self.getpermissionlevel(target)
                if targetuser_permissionlevel >= inituser_permissionlevel:
                    if shoulderoverride:
                        return True
                    await self.responsem.respond(context, "The target user needs to be lower than your highest role.")
                    return False
        except:
            return False
        return True
        
    def getpermissionlevel(self, member):
        # This method returns permission level based on what roles the user has.
        # Master is the bot coder who has the permission for debugging purposes.
        # Manage servers permission is considered a top level permission
        # that allows complete management over the bot.
        if not isinstance(member, discord.Member):
            return 0
        if (member.guild_permissions.manage_guild or str(member.id) in self.cfg.get("masters").split(",")) and self.cfg.get("permdebug") == 0:
            return 4
        if self.hasrole(member, self.cfg.get("armrole")) or memeber.guild_permissions.manage_roles:
            return 3
        if self.hasrole(member, self.cfg.get("handrole")) or member.guild_permissions.ban_members:
            return 2
        if self.hasrole(member, self.cfg.get("puppetrole")) or member.guild_permissions.manage_messages:
            return 1
        return 0
        
    def hasrole(self, member, role):
        # This method checks if a member has a role.
        memberroles = member.roles
        for roles in memberroles:
            if role == roles.id:
                return True
        return False
    
    async def respond(self, context, message, interaction, ephemeral = True):
        if not interaction:
            await context.respond(message, ephemeral = ephemeral)
        else:
            await interaction.response.send_message(message, ephemeral = ephemeral)
        return
    
    async def throwerror(self, context, reason):
        await context.respond(reason, ephemeral = True)
        return
    async def throwerrorinteraction(self, context, reason):
        await context.response.send_message(reason, ephemeral = True)
        return