import logging
import os
import traceback
from pathlib import Path

import aiohttp
import interactions as ipy
import typing_extensions as typing
from interactions.ext import prefixed_commands as prefixed

logger = logging.getLogger("oscbot")

BOT_COLOR = ipy.Color(int(os.environ["BOT_COLOR"]))


def error_embed_generate(error_msg: str) -> ipy.Embed:
    return ipy.Embed(
        title="Error",
        description=error_msg,
        color=ipy.MaterialColors.ORANGE,
        timestamp=ipy.Timestamp.utcnow(),
    )


def make_embed(description: str) -> ipy.Embed:
    return ipy.Embed(
        description=description,
        color=BOT_COLOR,
        timestamp=ipy.Timestamp.utcnow(),
    )


CommandT = typing.TypeVar("CommandT", ipy.BaseCommand, ipy.const.AsyncCallable)


def proper_permissions() -> typing.Callable[[CommandT], CommandT]:
    async def predicate(ctx: ipy.BaseContext) -> bool:
        return (
            ipy.Permissions.ADMINISTRATOR in ctx.author.guild_permissions
            or ipy.Permissions.MANAGE_MESSAGES in ctx.author.guild_permissions
        )

    return ipy.check(predicate)


async def error_handle(
    error: Exception, *, ctx: typing.Optional[ipy.BaseContext] = None
) -> None:
    if not isinstance(error, aiohttp.ServerDisconnectedError):
        traceback.print_exception(error)
        logger.error("An error occured.", exc_info=error)

    if ctx:
        if isinstance(ctx, prefixed.PrefixedContext):
            await ctx.reply(
                embed=error_embed_generate(
                    "An internal error has occured. The bot owner has been notified "
                    "and will likely fix the issue soon."
                )
            )
        elif isinstance(ctx, ipy.InteractionContext):
            await ctx.send(
                embed=error_embed_generate(
                    "An internal error has occured. The bot owner has been notified "
                    "and will likely fix the issue soon."
                ),
                ephemeral=ctx.ephemeral,
            )


async def msg_to_owner(
    bot: ipy.Client,
    chunks: list[str] | list[ipy.Embed] | list[str | ipy.Embed] | str | ipy.Embed,
) -> None:
    if not isinstance(chunks, list):
        chunks = [chunks]

    # sends a message to the owner
    for chunk in chunks:
        if isinstance(chunk, ipy.Embed):
            await bot.owner.send(embeds=chunk)
        else:
            await bot.owner.send(chunk)


def line_split(content: str, split_by: int = 20) -> list[list[str]]:
    content_split = content.splitlines()
    return [
        content_split[x : x + split_by] for x in range(0, len(content_split), split_by)
    ]


def error_format(error: Exception) -> str:
    # simple function that formats an exception
    return "".join(
        traceback.format_exception(  # type: ignore
            type(error), value=error, tb=error.__traceback__
        )
    )


def file_to_ext(str_path: str, base_path: str) -> str:
    # changes a file to an import-like string
    str_path = str_path.replace(base_path, "")
    str_path = str_path.replace("/", ".")
    return str_path.replace(".py", "")


def get_all_extensions(str_path: str, folder: str = "exts") -> list[str]:
    # gets all extensions in a folder
    ext_files: list[str] = []
    location_split = str_path.split(folder)
    base_path = location_split[0]

    if base_path == str_path:
        base_path = base_path.replace("main.py", "")
    base_path = base_path.replace("\\", "/")

    if base_path[-1] != "/":
        base_path += "/"

    pathlist = Path(f"{base_path}/{folder}").glob("**/*.py")
    for path in pathlist:
        str_path = str(path.as_posix())
        str_path = file_to_ext(str_path, base_path)
        ext_files.append(str_path)

    return ext_files


class CustomCheckFailure(ipy.errors.BadArgument):
    # custom classs for custom prerequisite failures outside of normal command checks
    pass


async def _global_checks(ctx: ipy.BaseContext) -> bool:
    return bool(ctx.guild) if ctx.bot.is_ready else False


class Extension(ipy.Extension):
    def __new__(
        cls, bot: ipy.Client, *args: typing.Any, **kwargs: typing.Any
    ) -> "typing.Self":
        new_cls = super().__new__(cls, bot, *args, **kwargs)
        new_cls.add_ext_check(_global_checks)
        return new_cls


if typing.TYPE_CHECKING:
    import asyncio

    class OSCBotBase(prefixed.PrefixedInjectedClient):
        init_load: bool
        owner: ipy.User
        background_tasks: set[asyncio.Task]
        color: ipy.Color

        def create_task(self, coro: typing.Coroutine) -> asyncio.Task: ...

else:

    class OSCBotBase(ipy.Client):
        pass
