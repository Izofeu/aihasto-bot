import discord
import aiomysql as sql
import configparse

cfg = configparse.parseconfig("config.cfg")
cfg.load()
token = cfg.loadtoken()
# cfg.set(key, value)

bot = discord.Bot()

def hasrole(member, role):
    memberroles = member.roles
    for roles in memberroles:
        if role == roles.id:
            return True
    return False
    
def getpermissionlevel(member):
    #if member.guild_permissions.manage_guild:
    #    return 4
    if hasrole(member, cfg.get("armrole")):
        return 3
    if hasrole(member, cfg.get("handrole")):
        return 2
    if hasrole(member, cfg.get("puppetrole")):
        return 1
    return 0

@bot.slash_command(description = "Toggles Puppet role for a user.")
async def puppet(context, username: discord.Option(
    discord.SlashCommandOptionType.user,
    required = True,
    description = "User to toggle a Puppet role for.")
    ):
        #await context.defer()
        inituser = context.author
        targetuser = username
        
        inituser_permlevel = getpermissionlevel(inituser)
        targetuser_permlevel = getpermissionlevel(targetuser)
        if inituser_permlevel < 2:
            await context.respond("You do not have enough permissions. Your permission level: "
                + str(inituser_permlevel) + ", required permission level: 2.",
                ephemeral = True)
            return
        if targetuser_permlevel >= inituser_permlevel:
            await context.respond("The permission level of target user (" + str(targetuser_permlevel)
                + ") needs to be smaller than yours (" + str(inituser_permlevel) + ").",
                ephemeral = True)
            return
       
        if hasrole(targetuser, cfg.get("puppetrole")):
            await targetuser.remove_roles(inituser.guild.get_role(cfg.get("puppetrole")), reason = "Responsible user: " + str(inituser.name))
            await context.respond("Removed Puppet role from " + targetuser.name + ".")
        else:
            await targetuser.add_roles(inituser.guild.get_role(cfg.get("puppetrole")), reason = "Responsible user: " + str(inituser.name))
            await context.respond("Added Puppet role to " + targetuser.name + ".")
        

        
@bot.slash_command(description = "Mark role as Puppet.")
async def setpuppetrole(context, roleid: discord.Option(
    discord.SlashCommandOptionType.role,
    required = True,
    description = "Role to be marked as a Puppet role.")
    ):
        if getpermissionlevel(context.author) < 4:
            await context.respond("You do not have enough permissions. Your permission level: "
                + str(getpermissionlevel(context.author)) + ", required permission level: 4.",
                ephemeral = True)
            return
        try:
            cfg.set("puppetrole", roleid.id)
            await context.respond("Marked " + roleid.name + " as Puppet.")
        except:
            await context.respond("Error setting Puppet role.")
            
@bot.slash_command(description = "Mark role as Hand.")
async def sethandrole(context, roleid: discord.Option(
    discord.SlashCommandOptionType.role,
    required = True,
    description = "Role to be marked as a Hand role.")
    ):
        try:
            cfg.set("handrole", roleid.id)
            await context.respond("Marked " + roleid.name + " as Hand.")
        except:
            await context.respond("Error setting Hand role.")
            
@bot.slash_command(description = "Mark role as Arm.")
async def setarmrole(context, roleid: discord.Option(
    discord.SlashCommandOptionType.role,
    required = True,
    description = "Role to be marked as an Arm role.")
    ):
        print(getpermissionlevel(context.author))
        try:
            cfg.set("armrole", roleid.id)
            await context.respond("Marked " + roleid.name + " as Arm.")
        except:
            await context.respond("Error setting Arm role.")
            
@bot.slash_command(description = "Get user's permission level.")
async def getperms(context):
    await context.respond("Your permission level is: " + str(getpermissionlevel(context.author)))
            
bot.run(token)