import os
import asyncio
import discord
from discord.ext import commands, tasks


VOICE_CHANNEL_ID = int(os.getenv("VOICE_CHANNEL_ID", 0))


class Voice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.lock = asyncio.Lock()
        self.voice_check.start()

    def cog_unload(self):
        self.voice_check.cancel()

    async def get_channel(self):
        channel = self.bot.get_channel(VOICE_CHANNEL_ID)

        if channel is None:
            channel = await self.bot.fetch_channel(VOICE_CHANNEL_ID)

        return channel

    async def ensure_connected(self):
        async with self.lock:
            await self.bot.wait_until_ready()

            if not VOICE_CHANNEL_ID:
                print("❌ VOICE_CHANNEL_ID não configurado.")
                return

            try:
                channel = await self.get_channel()
            except Exception as e:
                print(f"❌ Canal de voz não encontrado: {repr(e)}")
                return

            if not isinstance(channel, (discord.VoiceChannel, discord.StageChannel)):
                print("❌ O ID informado não é de canal de voz.")
                return

            voice_client = discord.utils.get(
                self.bot.voice_clients,
                guild=channel.guild
            )

            if voice_client and voice_client.is_connected():
                if voice_client.channel and voice_client.channel.id == channel.id:
                    return

                await voice_client.move_to(channel)
                print(f"✅ Bot movido para: {channel.name}")
                return

            if voice_client:
                try:
                    await voice_client.disconnect(force=True)
                    await asyncio.sleep(2)
                except Exception:
                    pass

            try:
                await channel.connect(
                    reconnect=True,
                    self_deaf=True,
                    self_mute=True,
                    timeout=30
                )

                print(f"✅ Bot conectado ao canal de voz: {channel.name}")

            except Exception as e:
                print(f"❌ Erro ao conectar no canal de voz: {repr(e)}")

    @tasks.loop(minutes=2)
    async def voice_check(self):
        await self.ensure_connected()

    @voice_check.before_loop
    async def before_voice_check(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(5)

    @commands.Cog.listener()
    async def on_ready(self):
        print("✅ [Voice] Sistema de presença em voz carregado.")


async def setup(bot):
    await bot.add_cog(Voice(bot))