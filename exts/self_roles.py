import importlib

import interactions as ipy
import interactions.ext.prefixed_commands as prefixed

import common.utils as utils


class SelfRoles(utils.Extension):
    def __init__(self, bot: utils.OSCBotBase) -> None:
        self.bot: utils.OSCBotBase = bot
        self.name = "Self Role"

        self.project_roles: dict[str, tuple[int, str]] = {
            "Jukebox": (1153816806654492672, "🎶"),
            "OSC Workout": (1417623455443980439, "💪"),
            "Studygachi": (1417623653344084060, "👾"),
            "Terminal Casino": (1417623539355484223, "🎰"),
            "Terminal Monopoly": (1283182183816892579, "💰"),
            "UF r/place": (1417623564894343370, "🖼️"),
        }

        self.ping_roles_rows = ipy.spread_to_rows(
            *(
                ipy.Button(
                    label=k,
                    custom_id=f"rolebutton|{v[0]}",
                    emoji=v[1],
                    style=ipy.ButtonStyle.PRIMARY,
                )
                for k, v in sorted(self.project_roles.items(), key=lambda x: x[0])
            )
        )

        self.other_roles: dict[str, tuple[int, str]] = {
            "Archive Viewer": (1235104106855665716, "📜"),
            "Soccer": (1205300430335115285, "⚽️"),
            "Bowling": (1357090384018276452, "🎳"),
        }

        self.other_roles_rows = ipy.spread_to_rows(
            *(
                ipy.Button(
                    label=k,
                    custom_id=f"rolebutton|{v[0]}",
                    emoji=v[1],
                    style=ipy.ButtonStyle.PRIMARY,
                )
                for k, v in sorted(self.other_roles.items(), key=lambda x: x[0])
            )
        )

    @prefixed.prefixed_command()
    @utils.proper_permissions()
    async def send_project_roles(self, ctx: prefixed.PrefixedContext) -> None:
        embed = ipy.Embed(
            title="Project Roles",
            description="Click on the buttons below to toggle project roles.",
            color=self.bot.color,
        )

        await ctx.send(
            embed=embed,
            components=self.ping_roles_rows,
        )
        await ctx.message.delete()

    @prefixed.prefixed_command()
    @utils.proper_permissions()
    async def edit_project_roles(
        self, ctx: prefixed.PrefixedContext, msg: ipy.Message
    ) -> None:
        embed = ipy.Embed(
            title="Project Roles",
            description="Click on the buttons below to toggle project roles.",
            color=self.bot.color,
        )

        await msg.edit(
            embed=embed,
            components=self.ping_roles_rows,
        )
        await ctx.reply(embeds=utils.make_embed("Done!"))

    @prefixed.prefixed_command()
    @utils.proper_permissions()
    async def send_other_roles(self, ctx: prefixed.PrefixedContext) -> None:
        embed = ipy.Embed(
            title="Other Roles",
            description="Click on the buttons below to toggle the roles you want.",
            color=ipy.RoleColors.DARK_GRAY,
        )

        await ctx.send(
            embed=embed,
            components=self.other_roles_rows,
        )
        await ctx.message.delete()

    @prefixed.prefixed_command()
    @utils.proper_permissions()
    async def edit_other_roles(
        self, ctx: prefixed.PrefixedContext, msg: ipy.Message
    ) -> None:
        embed = ipy.Embed(
            title="Other Roles",
            description="Click on the buttons below to toggle the roles you want.",
            color=ipy.RoleColors.DARK_GRAY,
        )

        await msg.edit(
            embed=embed,
            components=self.other_roles_rows,
        )
        await ctx.reply(embeds=utils.make_embed("Done!"))

    @ipy.listen(ipy.events.ButtonPressed)
    async def button_handle(self, event: ipy.events.ButtonPressed) -> None:
        ctx = event.ctx

        if ctx.custom_id.startswith("rolebutton|"):
            await ctx.defer(ephemeral=True)

            member = ctx.author
            if not isinstance(member, ipy.Member):
                await ctx.send(
                    embeds=utils.error_embed_generate(
                        "An error occured. Please try again."
                    ),
                    ephemeral=True,
                )
                return

            role_id = int(ctx.custom_id.removeprefix("rolebutton|"))
            role = await ctx.guild.fetch_role(role_id)
            if not role:
                await ctx.send(
                    embeds=utils.error_embed_generate(
                        "An error occured. Please try again."
                    ),
                    ephemeral=True,
                )
                return

            if member.has_role(role):
                await member.remove_role(role)
                await ctx.send(
                    embeds=utils.make_embed(f"Removed `{role.name}`."),
                    ephemeral=True,
                )
            else:
                await member.add_role(role)
                await ctx.send(
                    embeds=utils.make_embed(f"Added `{role.name}`."), ephemeral=True
                )


def setup(bot: utils.OSCBotBase) -> None:
    importlib.reload(utils)
    SelfRoles(bot)
