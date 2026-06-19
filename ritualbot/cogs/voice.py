import os
import discord

from discord.ext import commands


VOICE_CHANNEL_ID = int(
    os.getenv("VOICE_CHANNEL_ID", 0)
)


class Voice(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):

        channel = self.bot.get_channel(
            VOICE_CHANNEL_ID
        )

        if channel is None:
            print("❌ Canal de voz não encontrado.")
            return

        try:

            if self.bot.voice_clients:
                return

            await channel.connect(
                reconnect=True
            )

            print(
                "🎙️ Bot conectado ao canal de voz."
            )

        except Exception as e:

            print(
                f"Erro: {e}"
            )


async def setup(bot):

    await bot.add_cog(
        Voice(bot)
    )