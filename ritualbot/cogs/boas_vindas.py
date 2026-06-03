import discord
from discord.ext import commands
from datetime import datetime, timezone
import random


CHANNEL_ID = 1511581802991452311 # Só coloque o id do canal ai
EMBED_COLOR   = 0x1a1008  


# ── Manchetes aleatórias estilo Usopp News ────────────────────────────────────

HEADLINES = [
    ("NOVO PIRATA AVISTADO NAS ÁGUAS DO SERVIDOR!", "Forajido confirmado — nenhum tesouro está seguro"),
    ("RECÉM-CHEGADO CAUSA ALVOROÇO NO GRAND LINE!", "Membros veteranos pedem calma; situação sob controle"),
    ("LENDÁRIO RECRUTA ABORDA NOSSA EMBARCAÇÃO!", "Fontes afirmam que o novo membro é 'absolutamente aterrorizante'"),
    ("MISTERIOSO NAVEGANTE ENTRA EM NOSSO PORTO!", "Marinha Mundial ainda não sabe de nada — por enquanto"),
    ("MAIS UM FORAGIDO SE JUNTA À NOSSA TRIPULAÇÃO!", "Especialistas divergem: ameaça ou bênção para os mares?"),
    ("RECRUTA DESAFIA O DESTINO AO ENTRAR AQUI!", "Dizem os sábios: 'Este servidor nunca mais será o mesmo'"),
]

BYLINES = [
    "\"Os mares tremem com esta chegada. Ou talvez seja só o vento.\"",
    "\"Usopp pessoalmente confirma: este pirata é digno da tripulação.\"",
    "\"Bem-vindo ao Grand Line. Tente não morrer logo de cara.\"",
    "\"Nossa fonte exclusiva garante: este tripulante vai mudar tudo.\"",
    "\"Robin leu as Poneglyphs. Nenhuma palavra sobre este recruta. Suspeito.\"",
    "\"Nami já calculou a cota de impostos do novo membro. Bem-vindo.\"",
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _account_age(created: datetime) -> str:
    delta = datetime.now(timezone.utc) - created
    years  = delta.days // 365
    months = (delta.days % 365) // 30
    days   = delta.days % 30
    if years:
        return f"{years} ano{'s' if years>1 else ''} e {months} {'meses' if months!=1 else 'mês'}"
    if months:
        return f"{months} {'meses' if months!=1 else 'mês'} e {days} dia{'s' if days!=1 else ''}"
    return f"{delta.days} dia{'s' if delta.days!=1 else ''}"


def _progress_bar(value: int, maximum: int, length: int = 15) -> str:
    filled = round((value / maximum) * length) if maximum else 0
    filled = max(0, min(filled, length))
    return "█" * filled + "░" * (length - filled)


# ── Embed estilo Usopp News ───────────────────────────────────────────────────

def build_embed(
    member:      discord.Member,
    inviter:     discord.Member | discord.User | None,
    inv_total:   int,
    guild_count: int,
) -> discord.Embed:

    now       = datetime.now(timezone.utc)
    acc_age   = _account_age(member.created_at)
    acc_days  = (now - member.created_at).days
    new_acct  = acc_days < 30

    top_role = next(
        (r for r in reversed(member.roles) if r.name != "@everyone"), None
    )
    role_txt = top_role.mention if top_role else "⚓ Marinheiro Novato"

    headline, sub = random.choice(HEADLINES)
    byline = random.choice(BYLINES)

    bar_max   = max(inv_total, 50)
    bar       = _progress_bar(inv_total, bar_max)
    ordinal   = f"{guild_count:,}".replace(",", ".")

    embed = discord.Embed(color=EMBED_COLOR)

    # Cabeçalho do jornal
    embed.set_author(
        name="☠  USOPP NEWS  ·  Grand Line Press  ·  \"A Verdade dos Mares, Com Algum Exagero\"  ☠",
        icon_url=member.display_avatar.url,
    )

    # Manchete como título
    embed.title = f"📰  {headline}"

    # Sub-manchete e byline
    embed.description = (
        f"*{sub}*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{byline}"
    )

    embed.set_thumbnail(url=member.display_avatar.url)

    # Coluna esquerda — identidade
    embed.add_field(
        name="📋  Identidade do Suspeito",
        value=(
            f"**Nome:** {member.mention}\n"
            f"**Usuário:** `{member.name}`\n"
            f"**ID:** `{member.id}`\n"
            f"**Cargo inicial:** {role_txt}"
        ),
        inline=True,
    )

    # Coluna direita — conta
    new_tag = "  ⚠️ *conta nova!*" if new_acct else ""
    embed.add_field(
        name="🗓️  Ficha Técnica",
        value=(
            f"**Conta criada:** <t:{int(member.created_at.timestamp())}:D>\n"
            f"**Idade da conta:** `{acc_age}`{new_tag}\n"
            f"**Entrou em:** <t:{int(now.timestamp())}:f>\n"
            f"**Membro nº:** `{ordinal}`"
        ),
        inline=True,
    )

    embed.add_field(name="\u200b", value="\u200b", inline=False)

    # Coluna do recrutador
    if inviter:
        embed.add_field(
            name="⚔️  Quem Trouxe Este Forajido?",
            value=(
                f"**{inviter.mention}** — `{inviter.name}`\n"
                f"Convites realizados: **{inv_total}**\n"
                f"`{bar}` `{inv_total}/{bar_max}`"
            ),
            inline=False,
        )
    else:
        embed.add_field(
            name="⚔️  Quem Trouxe Este Forajido?",
            value="_Recrutador desconhecido — veio pelo próprio poder do destino_",
            inline=False,
        )

    # Rodapé do jornal
    edition = random.randint(4000, 9999)
    embed.set_footer(
        text=(
            f"☠ Edição Nº {edition:,}  ·  Impresso nas Docas de Water Seven  "
            f"·  {now.strftime('%d/%m/%Y às %H:%M')} UTC  ·  Todos os direitos saqueados ☠"
        )
    )

    return embed


# ── Cog ───────────────────────────────────────────────────────────────────────

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
        guild = member.guild

        channel = guild.get_channel(CHANNEL_ID)
        if not channel:
            print(f"[BoasVindas] Canal '{CHANNEL_ID}' não encontrado em '{guild.name}'.")
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

        inviter = None
        inv_total = 0

        if used and used.inviter:
            raw = used.inviter
            inviter = guild.get_member(raw.id) or raw
            key = str(raw.id)
            self._inv_counts[key] = self._inv_counts.get(key, 0) + 1
            inv_total = self._inv_counts[key]

        embed = build_embed(
            member=member,
            inviter=inviter,
            inv_total=inv_total,
            guild_count=guild.member_count,
        )

        await channel.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(BoasVindas(bot))