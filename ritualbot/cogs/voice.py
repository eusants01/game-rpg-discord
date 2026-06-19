import os
import asyncio
import discord
from discord.ext import commands


VOICE_CHANNEL_ID = int(os.getenv("VOICE_CHANNEL_ID", 0))


class Voice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reconnecting = False

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
            print("❌ O ID informado não é de canal de voz.")
            return

        voice_client = discord.utils.get(
            self.bot.voice_clients,
            guild=channel.guild
        )

        if voice_client:
            if voice_client.is_connected():
                if voice_client.channel.id == channel.id:
                    print("✅ Bot já está conectado no canal correto.")
                    return

                await voice_client.move_to(channel)
                print(f"✅ Bot movido para: {channel.name}")
                return

            try:
                await voice_client.disconnect(force=True)
            except:
                pass

        try:
            await channel.connect(
                reconnect=True,
                self_deaf=True,
                self_mute=True
            )

            print(f"✅ Bot conectado ao canal de voz: {channel.name}")

        except discord.ClientException as e:
            if "Already connected" in str(e):
                print("⚠️ Bot já estava conectado. Ignorando reconexão.")
                return

            print(f"❌ Erro ao conectar: {e}")

        except Exception as e:
            print(f"❌ Erro ao conectar no canal de voz: {e}")

    @commands.Cog.listener()
    async def on_ready(self):
        await asyncio.sleep(3)
        await self.conectar_voz()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not self.bot.user or member.id != self.bot.user.id:
            return

        if after.channel is None and not self.reconnecting:
            self.reconnecting = True

            print("⚠️ Bot saiu do canal de voz. Reconectando em 5 segundos...")

            await asyncio.sleep(5)
            await self.conectar_voz()

            self.reconnecting = False


async def setup(bot):
    await bot.add_cog(Voice(bot))