import os
import asyncio
import discord

from discord.ext import commands, tasks


VOICE_CHANNEL_ID = int(os.getenv("VOICE_CHANNEL_ID", 0))


class SilenceSource(discord.AudioSource):
    def read(self):
        return b"\x00" * 3840

    def is_opus(self):
        return False


class Voice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.lock = asyncio.Lock()
        self.voice_task.start()

    def cog_unload(self):
        self.voice_task.cancel()

    async def get_voice_channel(self):
        channel = self.bot.get_channel(VOICE_CHANNEL_ID)

        if channel is None:
            channel = await self.bot.fetch_channel(VOICE_CHANNEL_ID)

        return channel

    async def connect_voice(self):
        async with self.lock:
            await self.bot.wait_until_ready()

            if not VOICE_CHANNEL_ID:
                print("❌ VOICE_CHANNEL_ID não configurado.")
                return

            try:
                channel = await self.get_voice_channel()
            except Exception as e:
                print(f"❌ Canal de voz não encontrado: {repr(e)}")
                return

            if not isinstance(channel, discord.VoiceChannel):
                print("❌ O ID informado não é de um canal de voz.")
                return

            voice_client = discord.utils.get(
                self.bot.voice_clients,
                guild=channel.guild
            )

            if voice_client and voice_client.is_connected():
                if voice_client.channel.id != channel.id:
                    await voice_client.move_to(channel)
                    print(f"✅ Bot movido para: {channel.name}")

                if not voice_client.is_playing():
                    voice_client.play(SilenceSource())

                return

            if voice_client:
                try:
                    await voice_client.disconnect(force=True)
                    await asyncio.sleep(3)
                except Exception:
                    pass

            try:
                voice_client = await channel.connect(
                    reconnect=True,
                    self_deaf=True,
                    self_mute=True,
                    timeout=60
                )

                voice_client.play(SilenceSource())

                print(f"✅ Bot conectado 24h ao canal de voz: {channel.name}")

            except discord.ClientException:
                pass

            except Exception as e:
                print(f"❌ Erro ao conectar no canal de voz: {repr(e)}")

    @tasks.loop(minutes=5)
    async def voice_task(self):
        await self.connect_voice()

    @voice_task.before_loop
    async def before_voice_task(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(10)

    @commands.Cog.listener()
    async def on_ready(self):
        print("✅ [Voice] Sistema de presença 24h carregado.")


async def setup(bot):
    await bot.add_cog(Voice(bot))