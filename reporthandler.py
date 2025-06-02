import c_ui
import asyncio
from extrafunctions import getauthor, getutctimestamp, isemptyreason

class reporthandler:
    def __init__(self, cfg, sqlm, responsem):
        self.cfg = cfg
        self.sqlm = sqlm
        self.responsem = responsem
        self.lock = asyncio.Lock()
        
    async def invalidreport(self, interaction, buttons):
        invalidreportreasonui = c_ui.invalidreportreasonui(buttons, isemptyreason, self.handlereport)
        await interaction.response.send_modal(invalidreportreasonui)
    
    async def handlereport(self, interaction, buttons, invalid = False):
        async with self.lock:
            channel = interaction.message.channel
            try:
                message = await channel.fetch_message(interaction.message.id)
            except:
                return
            resolved = False
            for field in message.embeds[0].fields:
                if field.name == "Resolve date":
                    resolved = True
            if resolved:
                await self.responsem.respond(interaction, ":x: This report has already been resolved!")
                return
            buttons.disable_all_items()
            author = getauthor(interaction)
            message = interaction.message
            try:
                embed = message.embeds[0]
                name = ":x: Marked Invalid by" if invalid else ":white_check_mark: Resolved by"
                embed.insert_field_at(index = 0, name = name, value = "<@" + str(author.id) + ">", inline = False)
                if invalid:
                    embed.insert_field_at(index = 1, name = "Reason", value = invalid, inline = False)
                count = len(embed.fields)
                embed.insert_field_at(index = count, name = "Resolve date", value = "<t:" + getutctimestamp() + ":F>", inline = False)
                await message.edit(view = buttons, embed = embed)
                caseid = targetid = None
                for field in embed.fields:
                    if field.name == "Case ID":
                        caseid = field.value
                    elif field.name == "Reporter":
                        targetid = field.value[2:-1]
                try:
                    if caseid and targetid:
                        guild = interaction.guild
                        member = await guild.fetch_member(targetid)
                        if invalid:
                            await self.responsem.dm(member, (":warning: Your report with Case ID " + str(caseid) + " has been marked as invalid for the following reason: " + invalid + ".\n" +
                            ":information_source: This notice serves as feedback to you, the Reporter. It isn't a punishment or a warning."))
                        else:
                            await self.responsem.dm(member, ":white_check_mark: Your report with Case ID " + str(caseid) + " has been marked as resolved.")
                except:
                    pass
            except Exception as e:
                print(e)
                await message.edit(view = buttons)
            marking = ":x: Invalid" if invalid else ":white_check_mark: Resolved"
            await interaction.respond((":white_check_mark: Marked the report as " + marking + ". Discord forces me to send this useless message else you get an error so have a kitty! " +
            ":cat:"), ephemeral = True)
            await self.sqlm.subtractreport(targetid)
            return