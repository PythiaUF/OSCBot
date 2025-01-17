import importlib
import io
import typing

import aiohttp
import humanize
import interactions as ipy
import orjson
from interactions.ext import prefixed_commands as prefixed

import common.utils as utils


class SayCMDs(utils.Extension):
    def __init__(self, bot: utils.OSCBotBase) -> None:
        self.bot: utils.OSCBotBase = bot
        self.name = "Say"
        self.add_ext_auto_defer(enabled=False)

    @ipy.slash_command(
        "say",
        description="Allows you to send a message as the bot",
        default_member_permissions=ipy.Permissions.MANAGE_MESSAGES,
    )
    @ipy.slash_option(
        "channel",
        "The channel to send the message in.",
        ipy.OptionType.CHANNEL,
        required=False,
        channel_types=[ipy.ChannelType.GUILD_TEXT],
    )
    async def say(
        self, ctx: ipy.SlashContext, channel: ipy.GuildText | None = None
    ) -> None:
        if channel is None:
            channel = ctx.channel  # type: ignore
            if typing.TYPE_CHECKING:
                assert channel is not None

        modal = ipy.Modal(
            ipy.InputText(
                label="Enter the content you want to send:",
                style=ipy.TextStyles.PARAGRAPH,
                custom_id="say-content",
            ),
            title="Say Command",
            custom_id=f"say-cmd|{channel.id}",
        )
        await ctx.send_modal(modal)

    @prefixed.prefixed_command(name="say")
    @utils.proper_permissions()
    async def say_cmd(
        self,
        ctx: prefixed.PrefixedContext,
        channel: typing.Optional[ipy.GuildText],
        *,
        content: typing.Optional[str] = None,
    ) -> None:
        if channel is None:
            channel = ctx.channel  # type: ignore
            if typing.TYPE_CHECKING:
                assert channel is not None

        files_to_upload: list[ipy.File] = []

        if ctx.message.attachments:
            for attachment in ctx.message.attachments:
                if attachment.size > ctx.guild.filesize_limit:
                    raise ipy.errors.BadArgument(
                        "Attachments must be less than"
                        f" {humanize.naturalsize(attachment.size, binary=True)} in"
                        " size."
                    )

                async with aiohttp.ClientSession() as session:
                    async with session.get(attachment.url) as resp:
                        if resp.status == 200:
                            data = io.BytesIO(await resp.read())
                            files_to_upload.append(ipy.File(data, attachment.filename))
        elif not content:
            raise ipy.errors.BadArgument("You must provide content or files.")

        try:
            msg = await channel.send(content, files=files_to_upload)
            if channel != ctx.channel:
                await ctx.reply(f"Sent. See it at: {msg.jump_url}")
        finally:
            for ipy_file in files_to_upload:
                ipy_file.file.close()

    @ipy.slash_command(
        "raw-embed-say",
        description="Allows you to send an embed from the raw embed JSON format.",
        default_member_permissions=ipy.Permissions.MANAGE_MESSAGES,
    )
    @ipy.slash_option(
        "channel",
        "The channel to send the embed in.",
        ipy.OptionType.CHANNEL,
        required=False,
        channel_types=[ipy.ChannelType.GUILD_TEXT],
    )
    async def raw_embed_say(
        self, ctx: ipy.SlashContext, channel: ipy.GuildText | None = None
    ) -> None:
        if channel is None:
            channel = ctx.channel  # type: ignore
            if typing.TYPE_CHECKING:
                assert channel is not None

        modal = ipy.Modal(
            ipy.InputText(
                label="Enter the embed you want to send:",
                style=ipy.TextStyles.PARAGRAPH,
                custom_id="embed-say",
            ),
            title="Raw Embed Say",
            custom_id=f"raw-embed-say|{channel.id}",
        )
        await ctx.send_modal(modal)

    @ipy.context_menu(
        "Edit Embed (Raw)",
        context_type=ipy.CommandType.MESSAGE,
        default_member_permissions=ipy.Permissions.MANAGE_MESSAGES,
        dm_permission=False,
    )
    async def raw_embed_edit(self, ctx: ipy.ContextMenuContext) -> None:
        msg: ipy.Message = ctx.target  # type: ignore

        if not msg.embeds:
            await ctx.send("No embeds found.", ephemeral=True)
            return

        if msg.author.id != self.bot.user.id:
            await ctx.send("You can only edit embeds sent by the bot.", ephemeral=True)
            return

        modal = ipy.Modal(
            ipy.InputText(
                label="Enter the embed you want to edit:",
                style=ipy.TextStyles.PARAGRAPH,
                value=orjson.dumps(
                    msg.embeds[0].to_dict(), option=orjson.OPT_INDENT_2
                ).decode(),
                custom_id="embed-edit",
            ),
            title="Raw Embed Edit",
            custom_id=f"raw-embed-edit|{msg.id}",
        )
        await ctx.send_modal(modal)

    @ipy.context_menu(
        "Edit Message",
        context_type=ipy.CommandType.MESSAGE,
        default_member_permissions=ipy.Permissions.MANAGE_MESSAGES,
        dm_permission=False,
    )
    async def edit_message(self, ctx: ipy.ContextMenuContext) -> None:
        msg: ipy.Message = ctx.target  # type: ignore

        if msg.author.id != self.bot.user.id:
            await ctx.send(
                "You can only edit messages sent by the bot.", ephemeral=True
            )
            return

        modal = ipy.Modal(
            ipy.InputText(
                label="Enter what you want to edit the message to:",
                style=ipy.TextStyles.PARAGRAPH,
                value=msg.content or "N/A",
                custom_id="edit-content",
            ),
            title="Edit Message",
            custom_id=f"edit-message|{msg.id}",
        )
        await ctx.send_modal(modal)

    @prefixed.prefixed_command(name="edit-message")
    @utils.proper_permissions()
    async def edit_message_prefixed(
        self,
        ctx: prefixed.PrefixedContext,
        message: ipy.Message,
        *,
        content: typing.Optional[str] = None,
    ) -> None:
        files_to_upload: list[ipy.File] | None = []

        if ctx.message.attachments:
            for attachment in ctx.message.attachments:
                if attachment.size > ctx.guild.filesize_limit:
                    raise ipy.errors.BadArgument(
                        "Attachments must be less than"
                        f" {humanize.naturalsize(attachment.size, binary=True)} in"
                        " size."
                    )

                async with aiohttp.ClientSession() as session:
                    async with session.get(attachment.url) as resp:
                        if resp.status == 200:
                            data = io.BytesIO(await resp.read())
                            files_to_upload.append(ipy.File(data, attachment.filename))
        elif not content:
            raise ipy.errors.BadArgument("You must provide content or files.")
        else:
            files_to_upload = None

        try:
            msg = await message.edit(content=content, files=files_to_upload)
            if msg.channel != ctx.channel:
                await ctx.reply(f"Edited. See it at: {msg.jump_url}")
        finally:
            if files_to_upload:
                for ipy_file in files_to_upload:
                    ipy_file.file.close()

    @ipy.listen(ipy.events.ModalCompletion)  # type: ignore
    async def on_modal_completion(self, event: ipy.events.ModalCompletion) -> None:
        ctx = event.ctx

        if ctx.custom_id.startswith("raw-embed-say"):
            channel_id = int(ctx.custom_id.split("|")[1])
            channel = await self.bot.fetch_channel(channel_id)
            if not channel:
                await ctx.send("Could not get channel.", ephemeral=True)
                return

            try:
                embed_dict: dict = orjson.loads(ctx.responses["embed-say"])
            except orjson.JSONDecodeError:
                await ctx.send("Could not parse the raw embed.", ephemeral=True)
                return

            if embeds := embed_dict.get("embeds"):
                embed_dict = embeds[0]

            msg = await channel.send(embed=embed_dict)
            await ctx.send(f"Sent. See it at: {msg.jump_url}", ephemeral=True)

        elif ctx.custom_id.startswith("raw-embed-edit"):
            msg_id = int(ctx.custom_id.split("|")[1])

            try:
                embed_dict: dict = orjson.loads(ctx.responses["embed-edit"])
            except orjson.JSONDecodeError:
                await ctx.send("Could not parse the raw embed.", ephemeral=True)
                return

            if embeds := embed_dict.get("embeds"):
                embed_dict = embeds[0]

            message = await ctx.channel.fetch_message(msg_id)
            if message:
                await message.edit(embed=embed_dict)
                await ctx.send("Edited.", ephemeral=True)
            else:
                await ctx.send("Could not get message.", ephemeral=True)

        elif ctx.custom_id.startswith("say-cmd"):
            channel_id = int(ctx.custom_id.split("|")[1])
            channel = await self.bot.fetch_channel(channel_id)
            if not channel:
                await ctx.send("Could not get channel.", ephemeral=True)
                return

            msg = await channel.send(content=ctx.responses["say-content"])
            await ctx.send(f"Sent. See it at: {msg.jump_url}", ephemeral=True)

        elif ctx.custom_id.startswith("edit-message"):
            msg_id = int(ctx.custom_id.split("|")[1])
            message = await ctx.channel.fetch_message(msg_id)
            if not message:
                await ctx.send("Could not get message.", ephemeral=True)
                return

            await message.edit(content=ctx.responses["edit-content"])
            await ctx.send("Edited.", ephemeral=True)


def setup(bot: utils.OSCBotBase) -> None:
    importlib.reload(utils)
    SayCMDs(bot)
