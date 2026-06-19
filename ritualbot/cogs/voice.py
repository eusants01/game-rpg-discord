import os
import discord
from discord.ext import commands


def get_voice_channel_id():
    value = os.getenv("VOICE_CHANNEL_ID", "0").strip()
    return int(value) if value.isdigit() else 0


VOICE_CHANNEL_ID = get_voice_channel_id()


class Voice(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.connected = False

    async def conectar_voz(self):
        await self.bot.wait_until_ready()

        if not VOICE_CHANNEL_ID:
            print("❌ VOICE_CHANNEL_ID não configurado.")
            return

        channel = self.bot.get_channel(VOICE_CHANNEL_ID)

        if channel is None:
            try:
                channel = await self.bot.fetch_channel(VOICE_CHANNEL_ID)
            except Exception as e:
                print(f"❌ Canal de voz não encontrado: {e}")
                return

        if not isinstance(channel, (discord.VoiceChannel, discord.StageChannel)):
            print("❌ O ID informado não é de um canal de voz.")
            return

        guild = channel.guild

        voice_client = discord.utils.get(
            self.bot.voice_clients,
            guild=guild
        )

        if voice_client and voice_client.is_connected():
            print("✅ Bot já está conectado ao canal de voz.")
            return

        try:
            await channel.connect(
                reconnect=True,
                self_deaf=True
            )

            print(f"✅ Bot conectado ao canal de voz: {channel.name}")

        except Exception as e:
            print(f"❌ Erro ao conectar no canal de voz: {e}")

    @commands.Cog.listener()
    async def on_ready(self):
        if self.connected:
            return

        self.connected = True
        await self.conectar_voz()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not self.bot.user:
            return

        if member.id != self.bot.user.id:
            return

        if after.channel is None:
            print("⚠️ Bot saiu do canal de voz. Tentando reconectar...")
            await self.conectar_voz()


async def setup(bot: commands.Bot):
    await bot.add_cog(Voice(bot))