import os
import asyncio
import discord

from discord.ext import commands


VOICE_CHANNEL_ID = int(os.getenv("VOICE_CHANNEL_ID", 0))


class SilenceSource(discord.AudioSource):
    def read(self):
        return b"\xF8\xFF\xFE" * 960

    def is_opus(self):
        return True


class Voice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_client = None
        self.reconnect_task = None

    async def connect(self):
        await self.bot.wait_until_ready()

        channel = self.bot.get_channel(VOICE_CHANNEL_ID)

        if channel is None:
            channel = await self.bot.fetch_channel(VOICE_CHANNEL_ID)

        if not isinstance(channel, discord.VoiceChannel):
            print("❌ O ID informado não é de um canal de voz.")
            return

        vc = discord.utils.get(
            self.bot.voice_clients,
            guild=channel.guild
        )

        if vc and vc.is_connected():
            self.voice_client = vc

            if vc.channel.id != channel.id:
                await vc.move_to(channel)

            if not vc.is_playing():
                vc.play(SilenceSource())

            print(f"✅ Bot já está no canal de voz: {channel.name}")
            return

        self.voice_client = await channel.connect(
            reconnect=True,
            self_deaf=True,
            self_mute=False,
            timeout=60
        )

        self.voice_client.play(SilenceSource())

        print(f"✅ Bot conectado ao canal de voz: {channel.name}")

    async def reconnect_later(self):
        await asyncio.sleep(10)

        try:
            await self.connect()
        except Exception as e:
            print(f"❌ Erro ao reconectar voz: {repr(e)}")

        self.reconnect_task = None

    @commands.Cog.listener()
    async def on_ready(self):
        print("✅ [Voice] Presença em voz carregada.")

        try:
            await self.connect()
        except Exception as e:
            print(f"❌ Erro inicial na voz: {repr(e)}")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not self.bot.user or member.id != self.bot.user.id:
            return

        if after.channel is None and self.reconnect_task is None:
            print("⚠️ Bot saiu do canal. Tentando voltar em 10s...")
            self.reconnect_task = asyncio.create_task(self.reconnect_later())


async def setup(bot):
    await bot.add_cog(Voice(bot))