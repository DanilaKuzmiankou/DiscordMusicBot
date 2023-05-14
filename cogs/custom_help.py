import os

import discord
from discord.ext import commands
from discord.errors import Forbidden

from dotenv import load_dotenv

load_dotenv()
COMMAND_PREFIX = os.getenv('COMMAND_PREFIX')
BOT_VERSION = os.getenv('BOT_VERSION')

BOT_OWNER = os.getenv('BOT_OWNER')

async def send_embed(ctx, embed):
    """
    Function that handles the sending of embeds
    -> Takes context and embed to send
    - tries to send embed in channel
    - tries to send normal message when that fails
    - tries to send embed private with information abot missing permissions
    If this all fails: https://youtu.be/dQw4w9WgXcQ
    """
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
    """
    Sends this help message
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    # @commands.bot_has_permissions(add_reactions=True,embed_links=True)
    async def help(self, ctx, *input):
        """Shows all modules of that bot"""

        # checks if cog parameter was given
        # if not: sending all modules and commands not associated with a cog
        if not input:

            # starting to build embed
            emb = discord.Embed(title='Commands and modules', color=discord.Color.blue(),
                                description=f'Use `{COMMAND_PREFIX}help <module>` to gain more information about that module '
                                            f':smiley:\n')

            # iterating trough cogs, gathering descriptions
            cogs_desc = ''
            for cog in self.bot.cogs:
                cogs_desc += f'`{cog}` {self.bot.cogs[cog].__doc__}\n'

            # adding 'list' of cogs to embed
            emb.add_field(name='Modules', value=cogs_desc, inline=False)

            # integrating trough uncategorized commands
            commands_desc = ''
            for command in self.bot.walk_commands():
                # if cog not in a cog
                # listing command if cog name is None and command isn't hidden
                if not command.cog_name and not command.hidden:
                    commands_desc += f'{command.name} - {command.help}\n'



            # adding those commands to embed
            if commands_desc:
                emb.add_field(name='Main bot commands', value=commands_desc, inline=False)

            # setting information about author
            emb.add_field(name="About", value=f"The Bot is developed by {BOT_OWNER}, based on discord.py.")
            emb.set_footer(text=f"Bot is running {BOT_VERSION}")

        # block called when one cog-name is given
        # trying to find matching cog and it's commands
        elif len(input) == 1:

            # iterating trough cogs
            for cog in self.bot.cogs:
                # check if cog is the matching one
                if cog.lower() == input[0].lower():

                    # making title - getting description from doc-string below class
                    emb = discord.Embed(title=f'{cog} - Commands', description=self.bot.cogs[cog].__doc__,
                                        color=discord.Color.green())

                    # getting commands from cog
                    for command in self.bot.get_cog(cog).get_commands():
                        # if cog is not hidden
                        if not command.hidden:
                            emb.add_field(name=f"`{COMMAND_PREFIX}{command.name}`", value=command.help, inline=False)
                            for sub_command in command.walk_commands():
                                # if cog not in a cog
                                # listing command if cog name is None and command isn't hidden
                                if not sub_command.hidden:
                                    print('aha', sub_command)
                                    emb.add_field(name=f"`{COMMAND_PREFIX}{sub_command.name}`", value=sub_command.help, inline=False)
                    # found cog - breaking loop
                    break

            # if input not found
            # yes, for-loops have an else statement, it's called when no 'break' was issued
            else:
                emb = discord.Embed(title="What's that?!",
                                    description=f"I've never heard from a module called `{input[0]}` before :scream:",
                                    color=discord.Color.orange())

        # too many cogs requested - only one at a time allowed
        elif len(input) > 1:
            emb = discord.Embed(title="That's too much.",
                                description="Please request only one module at once :sweat_smile:",
                                color=discord.Color.orange())

        else:
            emb = discord.Embed(title="It's a magical place.",
                                description="I don't know how you got here. But I didn't see this coming at all.",
                                color=discord.Color.red())

        # sending reply embed using our own function defined above
        await send_embed(ctx, emb)


async def setup(bot):
    await bot.add_cog(Help(bot))
