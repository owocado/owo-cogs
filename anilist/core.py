import logging
import random
from typing import Literal

from redbot.core import commands
from redbot.core.commands import Context
from redbot.core.utils.dpy2_menus import BaseMenu, ListPages

from .api.base import GenreCollection, NotFound
from .api.character import CharacterData
from .api.media import MediaData
from .api.schedule import ScheduleData
from .api.staff import StaffData
from .api.studio import StudioData
from .api.user import UserData
from .embed_maker import (
    do_character_embed,
    do_media_embed,
    do_schedule_embed,
    do_staff_embed,
    do_studio_embed,
    do_user_embed,
)
from .schemas import (
    CHARACTER_SCHEMA,
    GENRE_SCHEMA,
    MEDIA_SCHEMA,
    SCHEDULE_SCHEMA,
    STAFF_SCHEMA,
    STUDIO_SCHEMA,
    TAG_SCHEMA,
    USER_SCHEMA,
)

log = logging.getLogger("red.owo.anilist")


class Anilist(commands.GroupCog, group_name="anilist"):
    """Fetch info on anime, manga, character, studio and more from Anilist!"""

    __authors__ = ["<@306810730055729152>"]
    __version__ = "2.0.0"

    def format_help_for_context(self, ctx: Context) -> str:  # Thanks Sinbad!
        return (
            f"{super().format_help_for_context(ctx)}\n\n"
            f"**Authors:**  {', '.join(self.__authors__)}\n"
            f"**Cog version:**  {self.__version__}"
        )

    async def cog_check(self, ctx: Context) -> bool:
        if ctx.guild:
            my_perms = ctx.channel.permissions_for(ctx.guild.me)
            return my_perms.read_message_history and my_perms.send_messages
        return True

    @commands.bot_has_permissions(embed_links=True)
    @commands.hybrid_command()
    async def anime(self, ctx: Context, *, query: str):
        """Fetch info on any anime from given query!"""
        async with ctx.typing():
            results = await MediaData.request(
                ctx.bot.session,
                query=MEDIA_SCHEMA,
                search=query,
                type="ANIME",
            )
            if isinstance(results, NotFound):
                return await ctx.send(str(results), ephemeral=True)

            pages = []
            for i, page in enumerate(results, start=1):
                emb = do_media_embed(page, getattr(ctx.channel, "is_nsfw", False))
                text = f"{emb.footer.text} • Page {i} of {len(results)}"
                emb.set_footer(text=text)
                pages.append(emb)

        await BaseMenu(ListPages(pages), timeout=120, ctx=ctx).start(ctx)

    @commands.bot_has_permissions(embed_links=True)
    @commands.hybrid_command(aliases=["manhwa"])
    async def manga(self, ctx: Context, *, query: str):
        """Fetch info on any manga from given query!"""
        async with ctx.typing():
            results = await MediaData.request(
                ctx.bot.session,
                query=MEDIA_SCHEMA,
                search=query,
                type="MANGA",
            )
            if isinstance(results, NotFound):
                return await ctx.send(str(results), ephemeral=True)

            pages = []
            for i, page in enumerate(results, start=1):
                emb = do_media_embed(page, getattr(ctx.channel, "is_nsfw", False))
                emb.set_footer(text=f"{emb.footer.text} • Page {i} of {len(results)}")
                pages.append(emb)

        await BaseMenu(ListPages(pages), timeout=120, ctx=ctx).start(ctx)

    @commands.bot_has_permissions(embed_links=True)
    @commands.hybrid_command()
    async def trending(self, ctx: Context, media_type: Literal["anime", "manga"]):
        """Fetch currently trending animes or manga from AniList!"""
        async with ctx.typing():
            results = await MediaData.request(
                ctx.bot.session, query=MEDIA_SCHEMA, type=media_type.upper(), sort="TRENDING_DESC"
            )
            if isinstance(results, NotFound):
                return await ctx.send(str(results), ephemeral=True)

            pages = []
            for i, page in enumerate(results, start=1):
                emb = do_media_embed(page, getattr(ctx.channel, "is_nsfw", False))
                emb.set_footer(text=f"{emb.footer.text} • Page {i} of {len(results)}")
                pages.append(emb)

        await BaseMenu(ListPages(pages), timeout=120, ctx=ctx).start(ctx)

    @commands.bot_has_permissions(embed_links=True)
    @commands.hybrid_command()
    async def random(
        self,
        ctx: Context,
        media_type: Literal["anime", "manga"],
        *,
        genre_or_tag: str = ""
    ):
        """Fetch a random anime or manga based on provided genre or tag!

        **Supported Genres:**
            - Action, Adventure, Comedy, Drama, Ecchi
            - Fantasy, Hentai, Horror, Mahou Shoujo, Mecha
            - Music, Mystery, Psychological, Romance, Schi-Fi
            - Slice of Life, Sports, Supernatural, Thriller

        You can also use any of the search tags supported on Anilist instead of any of above genres!
        """
        all_genres = list(map(str.lower, GenreCollection))
        async with ctx.typing():
            if not genre_or_tag:
                genre_or_tag = random.choice(GenreCollection)
                await ctx.send(
                    f"No genre or tag provided, so I chose random genre: **{genre_or_tag}**"
                )

            get_format = {
                "anime": ["TV", "TV_SHORT", "MOVIE", "OVA", "ONA"],
                "manga": ["MANGA", "NOVEL", "ONE_SHOT"],
            }
            results = await MediaData.request(
                ctx.bot.session,
                query=GENRE_SCHEMA if genre_or_tag.lower() in all_genres else TAG_SCHEMA,
                perPage=1,
                type=media_type.upper(),
                genre=genre_or_tag,
                format_in=get_format[media_type.lower()],
            )

            if isinstance(results, NotFound):
                return await ctx.send(
                    f"Could not find a random {media_type} from the given genre or tag.\n"
                    "See if its valid as per AniList or try again with different genre/tag.",
                    ephemeral=True,
                )

            emb = do_media_embed(results[0], getattr(ctx.channel, "is_nsfw", False))
            await ctx.send(embed=emb, ephemeral=True)

    @commands.bot_has_permissions(embed_links=True)
    @commands.hybrid_command()
    async def character(self, ctx: Context, *, query: str) -> None:
        """Fetch info on a anime/manga character from given query!"""
        async with ctx.typing():
            results = await CharacterData.request(
                ctx.bot.session, query=CHARACTER_SCHEMA, search=query, sort="SEARCH_MATCH"
            )
            if isinstance(results, NotFound):
                return await ctx.send(str(results), ephemeral=True)

            pages = []
            for i, page in enumerate(results, start=1):
                emb = do_character_embed(page)
                emb.set_footer(text=f"Powered by AniList • Page {i} of {len(results)}")
                pages.append(emb)

        await BaseMenu(ListPages(pages), timeout=120, ctx=ctx).start(ctx)

    @commands.bot_has_permissions(embed_links=True)
    @commands.hybrid_command()
    async def studio(self, ctx: Context, *, name: str) -> None:
        """Fetch info on an animation studio from given name query!"""
        async with ctx.typing():
            results = await StudioData.request(ctx.bot.session, query=STUDIO_SCHEMA, search=name)
            if isinstance(results, NotFound):
                return await ctx.send(str(results), ephemeral=True)

            pages = []
            for i, page in enumerate(results, start=1):
                emb = do_studio_embed(page)
                emb.set_footer(text=f"Powered by AniList • Page {i} of {len(results)}")
                pages.append(emb)

        await BaseMenu(ListPages(pages), timeout=120, ctx=ctx).start(ctx)

    @commands.hybrid_command()
    async def upcoming(self, ctx: Context, summary_version: bool = False):
        """Fetch list of upcoming animes airing within a day."""
        async with ctx.typing():
            results = await ScheduleData.request(
                ctx.bot.session, query=SCHEDULE_SCHEMA, perPage=20, notYetAired=True, sort="TIME"
            )
            if isinstance(results, NotFound):
                return await ctx.send(str(results), ephemeral=True)

            if not ctx.channel.permissions_for(ctx.me).embed_links or summary_version:
                airing = "\n".join(
                    f"<t:{media.airingAt}:R> • {media.media.title}" for media in results
                )
                return await ctx.send(
                    f"Upcoming animes in next **24 to 48 hours**:\n\n{airing}",
                    ephemeral=True,
                )

            pages = []
            for i, page in enumerate(results, start=1):
                emb = do_schedule_embed(page, upcoming=True)
                emb.set_footer(text=f"Powered by AniList • Page {i} of {len(results)}")
                pages.append(emb)

        await BaseMenu(ListPages(pages), timeout=120, ctx=ctx).start(ctx)

    @commands.hybrid_command()
    async def lastaired(self, ctx: Context, summary_version: bool = False):
        """Fetch list of upcoming animes airing within a day."""
        async with ctx.typing():
            results = await ScheduleData.request(
                ctx.bot.session,
                query=SCHEDULE_SCHEMA,
                perPage=20,
                notYetAired=False,
                sort="TIME_DESC",
            )
            if isinstance(results, NotFound):
                return await ctx.send(str(results), ephemeral=True)

            if not ctx.channel.permissions_for(ctx.me).embed_links or summary_version:
                airing = "\n".join(
                    f"<t:{media.airingAt}:R> • {media.media.title}" for media in results
                )
                return await ctx.send(
                    f"Recently aired animes in past **24 to 48 hours**:\n\n{airing}",
                    ephemeral=True,
                )

            pages = []
            for i, page in enumerate(results, start=1):
                emb = do_schedule_embed(page, upcoming=False)
                emb.set_footer(text=f"Powered by AniList • Page {i} of {len(results)}")
                pages.append(emb)

        await BaseMenu(ListPages(pages), timeout=120, ctx=ctx).start(ctx)

    @commands.bot_has_permissions(embed_links=True)
    @commands.hybrid_command(aliases=("mangaka", "seiyuu"))
    async def anistaff(self, ctx: Context, *, name: str):
        """Get info on any manga or anime staff, seiyuu etc."""
        async with ctx.typing():
            results = await StaffData.request(ctx.bot.session, query=STAFF_SCHEMA, search=name)
            if isinstance(results, NotFound):
                return await ctx.send(str(results), ephemeral=True)

            pages = []
            for i, page in enumerate(results, start=1):
                emb = do_staff_embed(page)
                emb.set_footer(text=f"Powered by AniList • Page {i} of {len(results)}")
                pages.append(emb)

        await BaseMenu(ListPages(pages), timeout=120, ctx=ctx).start(ctx)

    @commands.bot_has_permissions(embed_links=True)
    @commands.hybrid_command(aliases=["anilistuser"])
    async def aniuser(self, ctx: Context, username: str):
        """Get info on AniList user account."""
        async with ctx.typing():
            results = await UserData.request(ctx.bot.session, query=USER_SCHEMA, search=username)
            if isinstance(results, NotFound):
                return await ctx.send(str(results), ephemeral=True)

            pages = []
            for i, page in enumerate(results, start=1):
                emb = do_user_embed(page)
                emb.set_footer(text=f"Page {i} of {len(results)}")
                pages.append(emb)

        await BaseMenu(ListPages(pages), timeout=120, ctx=ctx).start(ctx)
