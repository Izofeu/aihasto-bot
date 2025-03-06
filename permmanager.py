class permmanager:
    def __init__(self, cfg):
        self.cfg = cfg
        
    async def canrun(self, context, member, commandpermissionlevel):
        try:
            if not commandpermissionlevel:
                raise PermissionException
            inituser_permissionlevel = self.getpermissionlevel(member)
            if inituser_permissionlevel < commandpermissionlevel:
                await self.throwerror(context, "You do not have enough permissions to run this command.")
                return False
        except:
            return False
        return True
        
    async def canrun(self, context, member, target, commandpermissionlevel):
        try:
            if not commandpermissionlevel:
                raise PermissionException
            inituser_permissionlevel = self.getpermissionlevel(member)
            targetuser_permissionlevel = self.getpermissionlevel(target)
            
            if inituser_permissionlevel < commandpermissionlevel:
                await self.throwerror(context, "You do not have enough permissions to run this command.")
                return False
            
            if targetuser_permissionlevel >= inituser_permissionlevel:
                await self.throwerror(context, "The target user needs to be lower than your highest role.")
                return False
        except:
            return False
        return True
        
    def getpermissionlevel(self, member):
        #if member.guild_permissions.manage_guild or member.id == cfg.get("master"):
        #    return 4
        if self.hasrole(member, self.cfg.get("armrole")):
            return 3
        if self.hasrole(member, self.cfg.get("handrole")):
            return 2
        if self.hasrole(member, self.cfg.get("puppetrole")):
            return 1
        return 0
        
    def hasrole(self, member, role):
        memberroles = member.roles
        for roles in memberroles:
            if role == roles.id:
                return True
        return False
    
    async def throwerror(self, context, reason):
        await context.respond(reason)
        return