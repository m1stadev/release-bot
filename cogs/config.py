from discord import Option

from views.selects import DropdownView
from views.buttons import PaginatorView

import discord
import json


class ConfigCog(discord.Cog, name='Configuration'):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

        self.utils = self.bot.get_cog('Utilities')

    config = discord.SlashCommandGroup('config', 'Configuration commands')

    @config.command(name='help', description='View all configuration commands.')
    async def _help(self, ctx: discord.ApplicationContext) -> None:
        cmd_embeds = [await self.utils.cmd_help_embed(ctx, _) for _ in self.config.subcommands]

        paginator = PaginatorView(cmd_embeds, ctx, timeout=180)
        await ctx.respond(embed=cmd_embeds[paginator.embed_num], view=paginator, ephemeral=True)

    @config.command(name='setchannel', description='Set a channel for *OS releases to be announced in.') #TODO: Implement setting announcement channels on a per-role basis
    async def set_channel(self, ctx: discord.ApplicationContext, channel: Option(discord.TextChannel, 'Channel to send OS releases in')):
        timeout_embed = discord.Embed(title='Add Device', description='No response given in 5 minutes, cancelling.')
        cancelled_embed = discord.Embed(title='Add Device', description='Cancelled.')
        invalid_embed = discord.Embed(title='Error')

        for x in (timeout_embed, cancelled_embed):
            x.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar.with_static_format('png').url)

        if not ctx.author.guild_permissions.administrator:
            invalid_embed.description = 'You do not have permission to use this command.'
            await ctx.respond(embed=invalid_embed, ephemeral=True)
            return

        if not channel.can_send():
            invalid_embed.description = "I don't have permission to send OS releases into that channel."
            await ctx.respond(embed=invalid_embed, ephemeral=True)
            return

        async with self.bot.db.execute('SELECT data FROM roles WHERE guild = ?', (ctx.guild.id,)) as cursor:
            roles = json.loads((await cursor.fetchone())[0])

        options = [
            discord.SelectOption(
                label='All',
                description='All OS releases'
            )

        ]
        for os in roles.keys():
            options.append(discord.SelectOption(
                label=os,
                description=f'All {os} releases'
            ))

        options.append(discord.SelectOption(
            label='Cancel',
            emoji='❌'
        ))

        embed = discord.Embed(title='Configuration', description=f"Choose which OS you'd like to send new releases to {channel.mention} for.")
        embed.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar.with_static_format('png').url)

        dropdown = DropdownView(options, ctx, 'OS Type')
        await ctx.respond(embed=embed, view=dropdown, ephemeral=True)
        await dropdown.wait()
        if dropdown.answer is None:
            await ctx.edit(embed=timeout_embed)
            return

        elif dropdown.answer == 'Cancel':
            await ctx.edit(embed=cancelled_embed)
            return

        if dropdown.answer == 'All':
            for os in roles.keys():
                roles[os].update({'channel': channel.id})

        else:
            roles[dropdown.answer].update({'channel': channel.id})

        await self.bot.db.execute('UPDATE roles SET data = ? WHERE guild = ?', (json.dumps(roles), ctx.guild.id))
        await self.bot.db.commit()

        embed = discord.Embed(title='Configuration', description=f"{'*OS' if dropdown.answer == 'All' else dropdown.answer} releases will now be sent to: {channel.mention}")
        embed.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar.with_static_format('png').url)

        await ctx.edit(embed=embed)
        

def setup(bot):
    bot.add_cog(ConfigCog(bot))