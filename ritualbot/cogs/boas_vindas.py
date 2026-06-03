import discord
from discord.ext import commands
from datetime import datetime, timezone
import random


CHANNEL_ID  = 1511581802991452311
EMBED_COLOR = 0x1a1008
BANNER_URL  = "https://cdn.discordapp.com/attachments/961677475191078992/1511588427877842944/content.png?ex=6a20ffed&is=6a1fae6d&hm=5566f784d522dcae8e8c53f104a5cf26c8fbadccc3a2c8ae0142b41cddcbc4c8&"


HEADLINES = [
    "RECÉM-CHEGADO CAUSA ALVOROÇO NO GRAND LINE!",
    "NOVO PIRATA AVISTADO NAS ÁGUAS DO SERVIDOR!",
    "LENDÁRIO RECRUTA ABORDA NOSSA EMBARCAÇÃO!",
    "MISTERIOSO NAVEGANTE ENTRA EM NOSSO PORTO!",
    "MAIS UM FORAGIDO SE JUNTA À NOSSA TRIPULAÇÃO!",
    "RECRUTA DESAFIA O DESTINO AO ENTRAR AQUI!",
]


def _account_age(created: datetime) -> str:
    delta  = datetime.now(timezone.utc) - created
    years  = delta.days // 365
    months = (delta.days % 365) // 30
    days   = delta.days % 30
    if years:
        return f"{years} ano{'s' if years > 1 else ''} e {months} {'meses' if months != 1 else 'mês'}"
    if months:
        return f"{months} {'meses' if months != 1 else 'mês'} e {days} dia{'s' if days != 1 else ''}"
    return f"{delta.days} dia{'s' if delta.days != 1 else ''}"


def build_embed(
    member:    discord.Member,
    inviter:   discord.Member | discord.User | None,
    inv_total: int,
) -> discord.Embed:

    now      = datetime.now(timezone.utc)
    acc_age  = _account_age(member.created_at)
    acc_days = (now - member.created_at).days
    edition  = random.randint(4000, 9999)
    headline = random.choice(HEADLINES)

    embed = discord.Embed(color=EMBED_COLOR)

    
    embed.set_author(
        name=f"☠  USOPP NEWS  ·  Edição Nº {edition:,}  ·  {now.strftime('%d/%m/%Y')}",
        icon_url=member.display_avatar.url,
    )

    # Manchete
    embed.title = f"📰  {headline}"

  
    embed.set_thumbnail(url=member.display_avatar.url)

    new_tag = "  ⚠️ conta nova!" if acc_days < 30 else ""
    embed.add_field(
        name=f"⚓  {member.display_name}",
        value=(
            f"**Conta criada:** <t:{int(member.created_at.timestamp())}:D>\n"
            f"**Idade da conta:** `{acc_age}`{new_tag}"
        ),
        inline=False,
    )

    if inviter:
        inv_txt = "1 convite" if inv_total == 1 else f"{inv_total} convites"
        embed.add_field(
            name="⚔️  Recrutado por",
            value=f"{inviter.mention} — `{inviter.name}` · {inv_txt}",
            inline=False,
        )
    else:
        embed.add_field(
            name="⚔️  Recrutado por",
            value="_Recrutador desconhecido — veio pelo próprio poder do destino_",
            inline=False,
        )

    embed.set_image(url=BANNER_URL)

    embed.set_footer(
        text="Família Sant's - Todos os direitos reservados bb ❤️",
        icon_url="https://cdn.discordapp.com/attachments/961677475191078992/1511590833646731326/e.gif?ex=6a21022a&is=6a1fb0aa&hm=93e668f7b70b4bab195cd01d6ac9097457aecacad5ad847eea99cd17ab66564e&",
    )

    return embed


invite_cache: dict[int, dict[str, discord.Invite]] = {}


async def _refresh(guild: discord.Guild) -> None:
    try:
        invites = await guild.invites()
        invite_cache[guild.id] = {i.code: i for i in invites}
    except discord.Forbidden:
        pass



class BoasVindas(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._inv_counts: dict[str, int] = {}

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            await _refresh(guild)
        print("[BoasVindas] cache de invites pronto.")

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        await _refresh(guild)

    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        await _refresh(invite.guild)

    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite):
        await _refresh(invite.guild)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild   = member.guild
        channel = guild.get_channel(CHANNEL_ID)

        if not channel:
            print(f"[BoasVindas] Canal {CHANNEL_ID} não encontrado em '{guild.name}'.")
            return

        old = invite_cache.get(guild.id, {})
        await _refresh(guild)
        new = invite_cache.get(guild.id, {})

        used: discord.Invite | None = None
        for code, inv in new.items():
            prev = old.get(code)
            if prev is None or inv.uses > prev.uses:
                used = inv
                break

        inviter   = None
        inv_total = 0

        if used and used.inviter:
            raw     = used.inviter
            inviter = guild.get_member(raw.id) or raw
            key     = str(raw.id)
            self._inv_counts[key] = self._inv_counts.get(key, 0) + 1
            inv_total = self._inv_counts[key]

        embed = build_embed(member=member, inviter=inviter, inv_total=inv_total)
        await channel.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(BoasVindas(bot))