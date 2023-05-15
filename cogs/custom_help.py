import os

import discord
from discord.ext import commands
from discord.errors import Forbidden

from dotenv import load_dotenv

load_dotenv()
COMMAND_PREFIX = os.getenv('COMMAND_PREFIX')
BOT_VERSION = os.getenv('BOT_VERSION')
BOT_OWNER_DESCRIPTION = os.getenv('BOT_OWNER_DESCRIPTION')
BOT_OWNER_ID = os.getenv('BOT_OWNER_ID')


async def send_embed(ctx, embed):
    try:
        await ctx.send(embed=embed)
    except Forbidden:
        try:
            await ctx.send("Hey, seems like I can't send embeds. Please check my permissions :)")
        except Forbidden:
            await ctx.author.send(
                f"Hey, seems like I can't send any message in {ctx.channel.name} on {ctx.guild.name}\n"
                f"May you inform the server team about this issue? :slight_smile: ", embed=embed)


class Help(commands.Cog):
    """Sends this help message"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx, *input):
        """Shows all modules of that bot"""

        if not input:

            emb = discord.Embed(title='Commands and modules', color=discord.Color.blue(),
                                description=f'Use `{COMMAND_PREFIX}help <module>` to gain more information about that module '
                                            f':smiley:\n')

            cogs_desc = ''
            for cog in self.bot.cogs:
                cogs_desc += f'`{cog}` {self.bot.cogs[cog].__doc__}\n'

            emb.add_field(name='Modules', value=cogs_desc, inline=False)

            commands_desc = ''
            for command in self.bot.walk_commands():
                if not command.cog_name and not command.hidden:
                    commands_desc += f'`{COMMAND_PREFIX}{command.name}'
                    if len(command.aliases) > 0:
                        commands_desc += f', aliases: {command.aliases}'
                    commands_desc += f'` - {command.help}\n'

            if commands_desc:
                emb.add_field(name='Main bot commands', value=commands_desc, inline=False)

            bot_owner_description = ''
            bot_owner = ctx.guild.get_member(int(BOT_OWNER_ID))
            if bot_owner is None:
                bot_owner_description = f"The Bot is developed by {BOT_OWNER_DESCRIPTION}, based on discord.py."
            else:
                bot_owner_description =f"The Bot is developed by {bot_owner.mention}, based on discord.py."

            emb.add_field(name="About", value=bot_owner_description)
            emb.set_footer(text=f"Bot is running {BOT_VERSION}")

        elif len(input) == 1:

            for cog in self.bot.cogs:
                if cog.lower() == input[0].lower():

                    emb = discord.Embed(title=f'{cog} - Commands', description=self.bot.cogs[cog].__doc__,
                                        color=discord.Color.green())

                    for command in self.bot.get_cog(cog).get_commands():
                        if not command.hidden:
                            emb.add_field(name=f"`{COMMAND_PREFIX}{command.name}, aliases: {command.aliases}`",
                                          value=command.help, inline=False)
                            for sub_command in command.walk_commands():
                                if not sub_command.hidden:
                                    emb.add_field(
                                        name=f"`{COMMAND_PREFIX}{sub_command.name}, aliases: {sub_command.aliases}`",
                                        value=sub_command.help, inline=False)
                    break

            else:
                emb = discord.Embed(title="What's that?!",
                                    description=f"I've never heard from a module called `{input[0]}` before :scream:",
                                    color=discord.Color.orange())

        elif len(input) > 1:
            emb = discord.Embed(title="That's too much.",
                                description="Please request only one module at once :sweat_smile:",
                                color=discord.Color.orange())

        else:
            emb = discord.Embed(title="It's a magical place.",
                                description="I don't know how you got here. But I didn't see this coming at all.",
                                color=discord.Color.red())

        await send_embed(ctx, emb)


async def setup(bot):
    await bot.add_cog(Help(bot))
