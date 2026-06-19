import os
import random
from datetime import datetime, timezone

import discord
from discord.ext import commands


CHANNEL_ID = int(os.getenv("CANAL_BOAS_VINDAS_ID", 1511581802991452311))

EMBED_COLOR = 0x7B4DFF

BANNER_URL = os.getenv(
    "BANNER_BOAS_VINDAS_URL",
    "https://cdn.discordapp.com/attachments/1498137107997130855/1517423859689717852/content.png?ex=6a363a98&is=6a34e918&hm=efc765d5c0e9d1c9a887d684a8e746f961c49a6ce3aad506f14f6613ed0be53f&"
)

FOOTER_ICON_URL = os.getenv(
    "LOGO_NEBULARIS_URL",
    ""
)


HEADLINES = [
    "UMA NOVA ESTRELA SURGIU NA NEBULARIS",
    "UM EXPLORADOR ATRAVESSOU O HORIZONTE",
    "SINAL DETECTADO: NOVO MEMBRO LOCALIZADO",
    "UMA NOVA PRESENÇA ENTROU EM ÓRBITA",
    "O UNIVERSO DA NEBULARIS ACABA DE EXPANDIR",
    "NOVO EXPLORADOR CONECTADO À CONSTELAÇÃO",
]


WELCOME_MESSAGES = [
    "Que sua jornada por aqui seja incrível.",
    "Prepare-se para explorar novos momentos conosco.",
    "Você agora faz parte de uma comunidade em expansão.",
    "Entre, participe e faça parte dessa história.",
    "A Nebularis acaba de ganhar uma nova estrela.",
]


def account_age(created: datetime) -> str:
    now = datetime.now(timezone.utc)
    delta = now - created

    years = delta.days // 365
    months = (delta.days % 365) // 30
    days = delta.days % 30

    if years:
        return f"{years} ano{'s' if years > 1 else ''} e {months} {'meses' if months != 1 else 'mês'}"

    if months:
        return f"{months} {'meses' if months != 1 else 'mês'} e {days} dia{'s' if days != 1 else ''}"

    return f"{days} dia{'s' if days != 1 else ''}"


def build_embed(
    member: discord.Member,
    inviter: discord.Member | discord.User | None,
    inv_total: int,
    member_count: int
) -> discord.Embed:

    now = datetime.now(timezone.utc)
    created_at = int(member.created_at.timestamp())
    acc_days = (now - member.created_at).days
    acc_age = account_age(member.created_at)

    headline = random.choice(HEADLINES)
    welcome = random.choice(WELCOME_MESSAGES)

    embed = discord.Embed(
        title=f"🌌 {headline}",
        description=(
            f"Bem-vindo(a), {member.mention}.\n\n"
            f"{welcome}\n\n"
            f"Você é o **{member_count}º explorador** a entrar na Nebularis."
        ),
        color=EMBED_COLOR,
        timestamp=now
    )

    embed.set_author(
        name="Nebularis • Entrada Detectada",
        icon_url=member.display_avatar.url
    )

    embed.set_thumbnail(url=member.display_avatar.url)

    account_status = "⚠️ Conta recente" if acc_days < 30 else "✅ Conta verificada"

    embed.add_field(
        name="👤 Explorador",
        value=(
            f"**Nome:** {member.mention}\n"
            f"**ID:** `{member.id}`\n"
            f"**Conta criada:** <t:{created_at}:D>\n"
            f"**Idade da conta:** `{acc_age}`\n"
            f"**Status:** {account_status}"
        ),
        inline=False
    )

    if inviter:
        invite_text = "1 convite" if inv_total == 1 else f"{inv_total} convites"

        embed.add_field(
            name="🛰️ Convidado por",
            value=(
                f"{inviter.mention}\n"
                f"**Usuário:** `{inviter.name}`\n"
                f"**Total registrado:** `{invite_text}`"
            ),
            inline=False
        )
    else:
        embed.add_field(
            name="🛰️ Convidado por",
            value="Não foi possível identificar o convite utilizado.",
            inline=False
        )

    embed.add_field(
        name="🚀 Primeiros passos",
        value=(
            "Leia as regras, escolha seus cargos e participe dos canais da comunidade.\n"
            "A Nebularis é construída por pessoas, histórias e grandes momentos."
        ),
        inline=False
    )

    if BANNER_URL:
        embed.set_image(url=BANNER_URL)

    footer_kwargs = {
        "text": "Nebularis • Entre horizontes infinitos."
    }

    if FOOTER_ICON_URL:
        footer_kwargs["icon_url"] = FOOTER_ICON_URL

    embed.set_footer(**footer_kwargs)

    return embed


invite_cache: dict[int, dict[str, discord.Invite]] = {}


async def refresh_invites(guild: discord.Guild) -> None:
    try:
        invites = await guild.invites()
        invite_cache[guild.id] = {invite.code: invite for invite in invites}

    except discord.Forbidden:
        print(f"[BoasVindas] Sem permissão para ver convites em {guild.name}.")

    except discord.HTTPException as error:
        print(f"[BoasVindas] Erro ao atualizar convites: {error}")


class BoasVindas(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.invite_counts: dict[int, int] = {}

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            await refresh_invites(guild)

        print("✅ [BoasVindas] Sistema carregado com sucesso.")

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        await refresh_invites(guild)

    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        if invite.guild:
            await refresh_invites(invite.guild)

    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite):
        if invite.guild:
            await refresh_invites(invite.guild)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        channel = guild.get_channel(CHANNEL_ID)

        if not channel:
            print(f"[BoasVindas] Canal {CHANNEL_ID} não encontrado em {guild.name}.")
            return

        old_invites = invite_cache.get(guild.id, {})

        await refresh_invites(guild)

        new_invites = invite_cache.get(guild.id, {})

        used_invite: discord.Invite | None = None

        for code, new_invite in new_invites.items():
            old_invite = old_invites.get(code)

            if old_invite and new_invite.uses > old_invite.uses:
                used_invite = new_invite
                break

        inviter = None
        inv_total = 0

        if used_invite and used_invite.inviter:
            inviter = guild.get_member(used_invite.inviter.id) or used_invite.inviter

            inviter_id = used_invite.inviter.id
            self.invite_counts[inviter_id] = self.invite_counts.get(inviter_id, 0) + 1
            inv_total = self.invite_counts[inviter_id]

        embed = build_embed(
            member=member,
            inviter=inviter,
            inv_total=inv_total,
            member_count=guild.member_count or 0
        )

        await channel.send(
            content=f"🌌 Bem-vindo(a), {member.mention}.",
            embed=embed
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(BoasVindas(bot))