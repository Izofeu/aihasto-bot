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

@bot.slash_command(description = "testt")
async def hello(context, name: discord.Option(str, description = "test2")):
    name = name or context.author.name
    text = "Hello, " + name + "!"
    await context.respond(text)

@bot.slash_command(description = "Toggle puppet")
async def puppet(context, username: discord.Option(
    discord.SlashCommandOptionType.user,
    required = True,
    description = "User to toggle a puppet role for.")
    ):
        #await context.defer()
        inituser = context.author
        targetuser = username
        
        inituser_roles = inituser.roles
        #print(inituser_roles)
        #role = username.guild.get_role(1346996001801506936)
        targetuser_roles = targetuser.roles
        guild_roles = context.author.guild.roles
        for roles in inituser_roles:
            print(roles.id)
            #print("\n")
       # await username.add_roles(role)
       
        if hasrole(targetuser, 1346996001801506936):
            await targetuser.remove_roles(inituser.guild.get_role(1346996001801506936))
        else:
            await targetuser.add_roles(inituser.guild.get_role(1346996001801506936), reason = "Responsible user: " + str(inituser.name))
        await context.respond("Toggled role.")
        
@bot.slash_command(description = "Mark role as Puppet.")
async def setpuppetrole(context, roleid: discord.Option(
    discord.SlashCommandOptionType.role,
    required = True,
    description = "Role to be marked as a Puppet role.")
    ):
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