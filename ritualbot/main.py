import os
import asyncio
import discord

from discord.ext import commands, tasks
from dotenv import load_dotenv

from utils.db import criar_tabelas
from utils.cassino_db import criar_tabelas_cassino


load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", "0"))


intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.voice_states = True
intents.message_content = True


bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


status_list = [
    "🌌 Um universo. Infinitas histórias.",
    "🪐 a comunidade orbitando",
    "✨ novas experiências surgindo",
    "📡 sinais da galáxia",
    "⚡ o Núcleo Nebularis",
    "🌠 o universo se expandir",
    "🚀 novas funções chegando",
    "💜 Desenvolvido por Sant's",
]


@tasks.loop(seconds=30)
async def trocar_status():
    status_atual = status_list[
        trocar_status.current_loop % len(status_list)
    ]

    try:
        await bot.change_presence(
            status=discord.Status.online,
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=status_atual
            )
        )

        print(f"🔄 Status atualizado: {status_atual}")

    except Exception as e:
        print(f"❌ Erro ao atualizar status: {e}")


@trocar_status.before_loop
async def before_trocar_status():
    await bot.wait_until_ready()


@bot.event
async def on_ready():
    print(f"🌌 Nebularis online como {bot.user}")

    try:
        criar_tabelas()
        criar_tabelas_cassino()
        print("✅ Banco de dados verificado.")
    except Exception as e:
        print(f"❌ Erro ao criar/verificar tabelas: {e}")

    if not trocar_status.is_running():
        trocar_status.start()
        print("✅ Sistema de status iniciado.")

    try:
        if GUILD_ID:
            guild = discord.Object(id=GUILD_ID)
            synced = await bot.tree.sync(guild=guild)
            print(f"✅ {len(synced)} comandos sincronizados no servidor.")
        else:
            synced = await bot.tree.sync()
            print(f"✅ {len(synced)} comandos sincronizados globalmente.")

    except Exception as e:
        print(f"❌ Erro ao sincronizar comandos: {e}")


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    await bot.process_commands(message)


async def carregar_cogs():
    cogs = [
        "cogs.abate",
        "cogs.maldicoes",
        "cogs.pactos",
        "cogs.mercado_amaldicoado",
        "cogs.loja_maldicoes",
        "cogs.levels",
        "cogs.boas_vindas",
        "cogs.loja_feiticeiros",

        # Sistemas Nebularis
        "cogs.painel_cassino",
        "cogs.economia",
        "cogs.roleta",
        "cogs.leilao",
    ]

    for cog in cogs:
        try:
            if cog in bot.extensions:
                print(f"⚠️ Cog já carregado, ignorando: {cog}")
                continue

            await bot.load_extension(cog)
            print(f"✅ Cog carregado: {cog}")

        except commands.ExtensionAlreadyLoaded:
            print(f"⚠️ Extensão já estava carregada, ignorando: {cog}")

        except commands.ExtensionNotFound:
            print(f"❌ Extensão não encontrada: {cog}")

        except commands.NoEntryPointError:
            print(f"❌ O cog {cog} não possui função setup(bot).")

        except commands.ExtensionFailed as e:
            erro = str(e)

            if "already loaded" in erro or "already registered" in erro:
                print(f"⚠️ Cog duplicado detectado em {cog}, ignorando.")
                continue

            print(f"❌ Erro ao carregar {cog}: {repr(e)}")

        except Exception as e:
            print(f"❌ Erro inesperado ao carregar {cog}: {repr(e)}")


async def main():
    if not TOKEN:
        raise RuntimeError(
            "Token não encontrado. Configure DISCORD_TOKEN no Railway."
        )

    async with bot:
        await carregar_cogs()
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())