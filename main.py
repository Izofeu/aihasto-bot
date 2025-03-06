import discord
import aiomysql as sql
import configparse

cfg = configparse.parseconfig("config.cfg")
cfg.load()
token = cfg.loadtoken()

bot = discord.Bot()

def hasrole(member, role):
    memberroles = member.roles
    for roles in memberroles:
        if role == roles.id:
            return True
    return False

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
    
bot.run(token)