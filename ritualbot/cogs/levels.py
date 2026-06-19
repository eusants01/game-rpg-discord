# cogs/levels.py

import os
import random
import asyncpg
import discord
from discord.ext import commands
from datetime import datetime, timezone, timedelta

EMBED_BANNER_URL = "https://cdn.discordapp.com/attachments/961677475191078992/1517576185658478612/content.png?ex=6a36c875&is=6a3576f5&hm=2de37c97024ba5d82284d80f2686fbbe8bc029b45f1ce99b9f4db24bdfb45d9b&"

COR_PRINCIPAL = discord.Color.from_rgb(123, 47, 247)
COR_RANK      = discord.Color.from_rgb(76, 201, 240)

LEVEL_TITLES = [
    (85, "🌌 Entidade Cósmica de Nebularis"),
    (65, "🪐 Guardião da Nebulosa"),
    (45, "☄️ Comandante Estelar"),
    (25, "🛰️ Explorador Estelar"),
    (10, "🚀 Piloto Novato"),
    (1,  "✨ Poeira Estelar"),
]
ROLE_REWARDS = {
    10: 1489690725246308473,  
    25: 1489690908797567197,  
    45: 1489691028536557620, 
    65: 1489691179963388206,  
    85: 1489691407840055450,  
}

XP_BONUS_ROLES: dict[int, float] = {
    123456789012345678: 1.5,
    1480334522053558465: 2.0,
    1486411238513836052: 3.0,
}

LEVELUP_CHANNEL_ID = int(os.getenv("LEVELUP_CHANNEL_ID", 0))


class Levels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pool = None
        self.cooldowns: dict[str, datetime] = {}

    async def cog_load(self):
        self.pool = await asyncpg.create_pool(os.getenv("DATABASE_URL"))
        await self.criar_tabela()

        if not LEVELUP_CHANNEL_ID:
            print(
                "[LEVELS] ⚠️ A variável de ambiente LEVELUP_CHANNEL_ID não está "
                "definida. Os anúncios de level-up serão enviados no mesmo canal "
                "onde a pessoa mandou a mensagem. Configure LEVELUP_CHANNEL_ID "
                "no Railway para fixar um canal único."
            )

    async def criar_tabela(self):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS levels (
                    guild_id   BIGINT  NOT NULL,
                    user_id    BIGINT  NOT NULL,
                    xp         BIGINT  NOT NULL DEFAULT 0,
                    level      INTEGER NOT NULL DEFAULT 1,
                    updated_at TIMESTAMP DEFAULT NOW(),
                    PRIMARY KEY (guild_id, user_id)
                );
            """)

    def xp_necessario(self, level: int) -> int:
        return 100 + (level * level * 85)

    def titulo_por_level(self, level: int) -> str:
        for required_level, title in LEVEL_TITLES:
            if level >= required_level:
                return title
        return LEVEL_TITLES[-1][1]

    def calcular_level(self, xp: int) -> int:
        level = 1
        while xp >= self.xp_necessario(level + 1):
            level += 1
        return level

    def xp_para_proximo(self, xp_total: int, level_atual: int) -> tuple[int, int, int]:
        xp_inicio_level     = self.xp_necessario(level_atual)
        xp_inicio_proximo   = self.xp_necessario(level_atual + 1)
        xp_atual_no_level   = xp_total - xp_inicio_level
        xp_necessario_level = max(1, xp_inicio_proximo - xp_inicio_level)
        falta               = max(0, xp_inicio_proximo - xp_total)
        return xp_atual_no_level, xp_necessario_level, falta

    def montar_barra(self, atual: int, necessario: int, tamanho: int = 12) -> str:
        necessario = max(1, necessario)
        proporcao  = max(0.0, min(1.0, atual / necessario))
        cheios     = int(proporcao * tamanho)
        return "▰" * cheios + "▱" * (tamanho - cheios)

    def calcular_multiplicador(self, member: discord.Member) -> float:
        ids_do_membro = {role.id for role in member.roles}
        multiplicadores = [
            mult for role_id, mult in XP_BONUS_ROLES.items()
            if role_id in ids_do_membro
        ]
        return max(multiplicadores, default=1.0)

    async def aplicar_cargos(self, member: discord.Member, level_antigo: int, level_novo: int):
        """Concede TODOS os cargos de recompensa entre level_antigo e level_novo
        (importante quando alguém pula vários níveis de uma vez, ex: via !addxp)."""
        cargos_a_conceder = [
            threshold for threshold in ROLE_REWARDS
            if level_antigo < threshold <= level_novo
        ]
        for threshold in sorted(cargos_a_conceder):
            role = member.guild.get_role(ROLE_REWARDS[threshold])
            if role and role not in member.roles:
                try:
                    await member.add_roles(role, reason=f"Recompensa de nível {threshold}")
                except discord.Forbidden:
                    print(f"[LEVELS] Sem permissão para aplicar o cargo de nível {threshold}.")

    def montar_embed_levelup(
        self,
        member: discord.Member,
        level_novo: int,
        xp_total: int,
        xp_ganho: int,
        multiplicador: float,
    ) -> discord.Embed:
        titulo = self.titulo_por_level(level_novo)
        xp_atual_no_level, xp_necessario_level, falta = self.xp_para_proximo(xp_total, level_novo)
        barra = self.montar_barra(xp_atual_no_level, xp_necessario_level)

        bonus_linha = ""
        if multiplicador > 1.0:
            xp_base_estimado = round(xp_ganho / multiplicador)
            bonus_linha = (
                f"**✦ Bônus de XP:** `x{multiplicador}` "
                f"(+{xp_ganho - xp_base_estimado} XP extras)\n"
            )

        embed = discord.Embed(
            title="🌌  Novo Nível Alcançado!",
            description=(
                f"### {member.mention} avançou pela imensidão de Nebularis!\n\n"
                f"**✦ Nível:** `{level_novo}`\n"
                f"**✦ Título:** {titulo}\n"
                f"{bonus_linha}"
                f"\n──────────────────────\n"
                f"**Progresso para o Nível {level_novo + 1}**\n"
                f"`{barra}` `{xp_atual_no_level}/{xp_necessario_level} XP`\n\n"
                f"> 📡 Faltam **{falta} XP** para alcançar o **Nível {level_novo + 1}**!\n"
                f"──────────────────────"
            ),
            color=COR_PRINCIPAL,
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"🌠  Nebularis • XP Total: {xp_total}")
        if EMBED_BANNER_URL:
            embed.set_image(url=EMBED_BANNER_URL)
        return embed

    def montar_embed_rank(self, member: discord.Member, xp: int, level: int, posicao: int) -> discord.Embed:
        titulo = self.titulo_por_level(level)
        xp_atual_no_level, xp_necessario_level, falta = self.xp_para_proximo(xp, level)
        barra = self.montar_barra(xp_atual_no_level, xp_necessario_level)

        mult = self.calcular_multiplicador(member)
        mult_linha = f"**✦ Bônus de XP:** `x{mult}`\n" if mult > 1.0 else ""

        embed = discord.Embed(
            title="🛰️  Registro de Exploração",
            description=(
                f"{member.mention}\n\n"
                f"**✦ Título:** {titulo}\n"
                f"**✦ Nível:** `{level}`\n"
                f"**✦ Ranking:** `#{posicao}`\n"
                f"{mult_linha}"
                f"\n──────────────────────\n"
                f"**Progresso para o Nível {level + 1}**\n"
                f"`{barra}` `{xp_atual_no_level}/{xp_necessario_level} XP`\n\n"
                f"> 📡 Faltam **{falta} XP** para o próximo nível!\n"
                f"──────────────────────\n"
                f"**XP Total acumulado:** `{xp}`"
            ),
            color=COR_RANK,
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        if EMBED_BANNER_URL:
            embed.set_image(url=EMBED_BANNER_URL)
        embed.set_footer(text="Continue explorando o cosmos de Nebularis.")
        return embed

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        user_id  = message.author.id
        guild_id = message.guild.id
        key      = f"{guild_id}:{user_id}"
        now      = datetime.now(timezone.utc)

        if (last := self.cooldowns.get(key)) and now - last < timedelta(seconds=60):
            return

        self.cooldowns[key] = now

        xp_base  = random.randint(15, 35)
        mult     = self.calcular_multiplicador(message.author)
        xp_ganho = round(xp_base * mult)

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO levels (guild_id, user_id, xp, level, updated_at)
                VALUES ($1, $2, $3, 1, NOW())
                ON CONFLICT (guild_id, user_id)
                DO UPDATE SET
                    xp         = levels.xp + EXCLUDED.xp,
                    updated_at = NOW()
                RETURNING xp, level;
            """, guild_id, user_id, xp_ganho)

            xp_total     = row["xp"]
            level_antigo = row["level"]
            level_novo   = self.calcular_level(xp_total)

            if level_novo > level_antigo:
                await conn.execute("""
                    UPDATE levels SET level = $1
                    WHERE guild_id = $2 AND user_id = $3
                """, level_novo, guild_id, user_id)

                await self.aplicar_cargos(message.author, level_antigo, level_novo)

                embed = self.montar_embed_levelup(
                    message.author, level_novo, xp_total, xp_ganho, mult
                )

                canal_destino = None
                if LEVELUP_CHANNEL_ID:
                    canal_destino = self.bot.get_channel(LEVELUP_CHANNEL_ID)
                    if canal_destino is None:
                        try:
                            canal_destino = await self.bot.fetch_channel(LEVELUP_CHANNEL_ID)
                        except discord.NotFound:
                            print(f"[LEVELS] ⚠️ Canal {LEVELUP_CHANNEL_ID} não encontrado. "
                                  "Verifique se o ID em LEVELUP_CHANNEL_ID está correto.")
                        except discord.Forbidden:
                            print(f"[LEVELS] ⚠️ Sem permissão para ver/enviar no canal "
                                  f"{LEVELUP_CHANNEL_ID}.")

                if canal_destino is None:
                    canal_destino = message.channel
                    if LEVELUP_CHANNEL_ID:
                        print(f"[LEVELS] ⚠️ Falha ao acessar o canal configurado "
                              f"({LEVELUP_CHANNEL_ID}). Anúncio enviado em "
                              f"#{message.channel} como alternativa.")

                try:
                    await canal_destino.send(embed=embed)
                except discord.Forbidden:
                    print(f"[LEVELS] ⚠️ Sem permissão para enviar mensagens em #{canal_destino}.")


    @commands.command(name="rank")
    async def rank(self, ctx, member: discord.Member = None):
        member = member or ctx.author

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT xp, level FROM levels
                WHERE guild_id = $1 AND user_id = $2
            """, ctx.guild.id, member.id)

            if not row:
                return await ctx.reply(
                    f"{member.mention} ainda não iniciou sua jornada pelo cosmos. "
                    "Mande uma mensagem para começar a ganhar XP!"
                )

            posicao = await conn.fetchval("""
                SELECT posicao FROM (
                    SELECT user_id, RANK() OVER (ORDER BY xp DESC) AS posicao
                    FROM levels WHERE guild_id = $1
                ) ranking WHERE user_id = $2
            """, ctx.guild.id, member.id)

        embed = self.montar_embed_rank(member, row["xp"], row["level"], posicao)
        await ctx.reply(embed=embed)

    @commands.command(name="top")
    async def top(self, ctx):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT user_id, xp, level FROM levels
                WHERE guild_id = $1
                ORDER BY xp DESC LIMIT 10
            """, ctx.guild.id)

        if not rows:
            return await ctx.reply("Ainda não há exploradores registrados em Nebularis.")

        descricao = ""
        medals = {1: "🥇", 2: "🥈", 3: "🥉"}

        for index, row in enumerate(rows, start=1):
            titulo  = self.titulo_por_level(row["level"])
            medalha = medals.get(index, f"**{index}.**")
            descricao += (
                f"{medalha} <@{row['user_id']}>\n"
                f"╰ `Nível {row['level']}` · `{row['xp']} XP` · {titulo}\n\n"
            )

        embed = discord.Embed(
            title="🌌  Ranking Estelar de Nebularis",
            description=descricao,
            color=COR_PRINCIPAL,
        )
        if EMBED_BANNER_URL:
            embed.set_thumbnail(url=EMBED_BANNER_URL)
        embed.set_footer(text="Os exploradores mais lendários do servidor.")
        await ctx.reply(embed=embed)

    @commands.command(name="levelroles", aliases=["cargosdenivel"])
    async def levelroles(self, ctx):
        """Mostra todos os cargos de recompensa e em qual nível são liberados."""
        linhas = []
        for threshold in sorted(ROLE_REWARDS):
            role = ctx.guild.get_role(ROLE_REWARDS[threshold])
            titulo = self.titulo_por_level(threshold)
            nome_cargo = role.mention if role else "*(cargo não configurado)*"
            linhas.append(f"**Nível {threshold}** — {titulo}\n╰ {nome_cargo}\n")

        embed = discord.Embed(
            title="🪐  Cargos de Recompensa",
            description="\n".join(linhas) or "Nenhum cargo configurado ainda.",
            color=COR_PRINCIPAL,
        )
        await ctx.reply(embed=embed)

    @commands.command(name="setxp")
    @commands.has_permissions(administrator=True)
    async def setxp(self, ctx, member: discord.Member, xp: int):
        if xp < 0:
            return await ctx.reply("O XP não pode ser negativo.")

        async with self.pool.acquire() as conn:
            row_anterior = await conn.fetchrow("""
                SELECT level FROM levels WHERE guild_id = $1 AND user_id = $2
            """, ctx.guild.id, member.id)
            level_antigo = row_anterior["level"] if row_anterior else 1

            level_novo = self.calcular_level(xp)
            await conn.execute("""
                INSERT INTO levels (guild_id, user_id, xp, level, updated_at)
                VALUES ($1, $2, $3, $4, NOW())
                ON CONFLICT (guild_id, user_id)
                DO UPDATE SET xp = $3, level = $4, updated_at = NOW()
            """, ctx.guild.id, member.id, xp, level_novo)

        if level_novo > level_antigo:
            await self.aplicar_cargos(member, level_antigo, level_novo)

        await ctx.reply(
            f"✅ XP de {member.mention} definido para **{xp}** (Nível `{level_novo}`)."
        )

    @commands.command(name="addxp")
    @commands.has_permissions(administrator=True)
    async def addxp(self, ctx, member: discord.Member, xp: int):
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO levels (guild_id, user_id, xp, level, updated_at)
                VALUES ($1, $2, GREATEST(0, $3), 1, NOW())
                ON CONFLICT (guild_id, user_id)
                DO UPDATE SET
                    xp         = GREATEST(0, levels.xp + $3),
                    updated_at = NOW()
                RETURNING xp, level;
            """, ctx.guild.id, member.id, xp)

            xp_total     = row["xp"]
            level_antigo = row["level"]
            level_novo   = self.calcular_level(xp_total)

            await conn.execute("""
                UPDATE levels SET level = $1
                WHERE guild_id = $2 AND user_id = $3
            """, level_novo, ctx.guild.id, member.id)

        if level_novo > level_antigo:
            await self.aplicar_cargos(member, level_antigo, level_novo)

        sinal = "+" if xp >= 0 else ""
        await ctx.reply(
            f"✅ {sinal}{xp} XP aplicado a {member.mention}. "
            f"Total: **{xp_total} XP** · Nível `{level_novo}`."
        )

    @commands.command(name="testlevel")
    @commands.has_permissions(administrator=True)
    async def testlevel(self, ctx, member: discord.Member = None):
        """[ADMIN] Força o anúncio de level-up para testar o embed."""
        member = member or ctx.author

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT xp, level FROM levels
                WHERE guild_id = $1 AND user_id = $2
            """, ctx.guild.id, member.id)

        if not row:
            return await ctx.reply("Usuário sem XP registrado. Use `!setxp` primeiro.")

        mult = self.calcular_multiplicador(member)
        embed = self.montar_embed_levelup(member, row["level"], row["xp"], 25, mult)

        canal_destino = None
        if LEVELUP_CHANNEL_ID:
            canal_destino = ctx.guild.get_channel(LEVELUP_CHANNEL_ID)
        canal_destino = canal_destino or ctx.channel
        await canal_destino.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Levels(bot))