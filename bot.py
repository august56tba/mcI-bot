import discord
from discord import app_commands
from discord.ui import Button, View
import uuid
import os
from typing import Optional

# ============================================
# CONFIGURAÇÃO DO BOT
# ============================================

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

class MCLBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # Sincroniza os comandos no servidor específico
        guild = discord.Object(id=1496579366677909704)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        print("✅ Comandos sincronizados no servidor (setup_hook)")

bot = MCLBot()

# ============================================
# IDs DE CANAIS E CARGOS
# ============================================

LOG_CHANNEL_ID = 1510486940833812670
SCOUTING_CHANNEL_ID = 1520619945526825070
FREE_AGENCY_CHANNEL_ID = 1496579368493777097

MANAGER_ROLE_ID = 1496579366765723720
VICE_MANAGER_ROLE_ID = 1496579366736625723
PLAYER_ROLE_ID = 1496579366698750185

# ============================================
# TIMES E EMOJIS
# ============================================

TEAM_ROLES = {
    1536899006397939802: {"name": "França", "emoji_id": 1529940051574788226, "emoji_name": "FRA", "role_id": 1536899006397939802},
    1531762164619018340: {"name": "ESPANHA", "emoji_id": 1529940469839298622, "emoji_name": "ESP", "role_id": 1531762164619018340},
    1536898498971045999: {"name": "Inglaterra", "emoji_id": 1529943945491120178, "emoji_name": "ENG", "role_id": 1536898498971045999},
    1520779736408653914: {"name": "BraziI", "emoji_id": 1529941002104602786, "emoji_name": "BRA", "role_id": 1520779736408653914},
    1520780175590031481: {"name": "CABO VERDE", "emoji_id": 1529939732287590572, "emoji_name": "CBV", "role_id": 1520780175590031481},
    1520780363712954428: {"name": "PortugaI", "emoji_id": 1534588893456891975, "emoji_name": "POR", "role_id": 1520780363712954428},
    1520620774564827176: {"name": "Argentina", "emoji_id": 1540742657788215396, "emoji_name": "ARG", "role_id": 1520620774564827176},
    1520779908660596836: {"name": "Uruguai", "emoji_id": 1512649773948080189, "emoji_name": "URG", "role_id": 1520779908660596836},
    1520785259866886195: {"name": "MARROCOS", "emoji_id": 1512649740670603425, "emoji_name": "MAR", "role_id": 1520785259866886195}
}

def get_user_team(member: discord.Member) -> Optional[dict]:
    for role in member.roles:
        if role.id in TEAM_ROLES:
            return TEAM_ROLES[role.id]
    return None

def get_team_emoji(team_info: dict) -> str:
    return f"<:{team_info['emoji_name']}:{team_info['emoji_id']}>"

# ============================================
# BOTÕES PARA OFERTAS
# ============================================

class OfferButtons(View):
    def __init__(self, user_id: int, log_channel_id: int, team_info: dict, guild_id: int):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.log_channel_id = log_channel_id
        self.team_info = team_info
        self.guild_id = guild_id

        accept_button = Button(label="✅ Aceitar", style=discord.ButtonStyle.success, custom_id=f"accept_{uuid.uuid4()}")
        accept_button.callback = self.accept_callback
        self.add_item(accept_button)

        decline_button = Button(label="❌ Recusar", style=discord.ButtonStyle.danger, custom_id=f"decline_{uuid.uuid4()}")
        decline_button.callback = self.decline_callback
        self.add_item(decline_button)

    async def accept_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Esta oferta não é para você!", ephemeral=True)
            return

        for item in self.children:
            item.disabled = True

        team_role_id = self.team_info["role_id"]
        team_name = self.team_info["name"]
        team_emoji = get_team_emoji(self.team_info)

        try:
            guild = bot.get_guild(self.guild_id)
            if not guild:
                await interaction.response.send_message("❌ Servidor não encontrado!", ephemeral=True)
                return

            role = guild.get_role(team_role_id)
            if not role:
                await interaction.response.send_message("❌ Cargo não encontrado!", ephemeral=True)
                return

            member = guild.get_member(interaction.user.id)
            if not member:
                await interaction.response.send_message("❌ Usuário não encontrado!", ephemeral=True)
                return

            await member.add_roles(role)

            embed = discord.Embed(
                title=f"{team_emoji} ✅ Oferta Aceita!",
                description=f"Parabéns! Você agora faz parte do **{team_name}**!",
                color=discord.Color.green()
            )
            embed.add_field(name="🎉 Bem-vindo ao time!", value=f"Você recebeu o cargo {role.mention}.", inline=False)
            embed.set_footer(text="Aguardando instruções do Manager")

            await interaction.response.edit_message(embed=embed, view=self)

            log_channel = guild.get_channel(self.log_channel_id)
            if log_channel:
                embed_log = discord.Embed(
                    title="📋 Oferta Aceita",
                    description=f"**Jogador:** {interaction.user.mention}\n**Time:** {team_emoji} {team_name}\n**Status:** ✅ Aceita\n**Cargo:** {role.mention}",
                    color=discord.Color.green()
                )
                await log_channel.send(embed=embed_log)

        except discord.Forbidden:
            await interaction.response.send_message("❌ Sem permissão para adicionar cargo!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erro: {e}", ephemeral=True)

    async def decline_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Esta oferta não é para você!", ephemeral=True)
            return

        for item in self.children:
            item.disabled = True

        embed = discord.Embed(title="❌ Oferta Recusada", description="Você recusou a oferta.", color=discord.Color.red())
        embed.set_footer(text="Oferta encerrada")
        await interaction.response.edit_message(embed=embed, view=self)

        guild = bot.get_guild(self.guild_id)
        if guild:
            log_channel = guild.get_channel(self.log_channel_id)
            if log_channel:
                embed_log = discord.Embed(
                    title="📋 Oferta Recusada",
                    description=f"**Jogador:** {interaction.user.mention}\n**Time:** {get_team_emoji(self.team_info)} {self.team_info['name']}\n**Status:** ❌ Recusada",
                    color=discord.Color.red()
                )
                await log_channel.send(embed=embed_log)

# ============================================
# VIEW DA FREE AGENCY
# ============================================

class FreeAgencyView(View):
    def __init__(self, player_id: int, guild_id: int):
        super().__init__(timeout=None)
        self.player_id = player_id
        self.guild_id = guild_id
        self.finished = False

        hire_button = Button(label="Contratar", emoji="✅", style=discord.ButtonStyle.success, custom_id=f"hire_{player_id}")
        hire_button.callback = self.hire_callback
        self.add_item(hire_button)

        reject_button = Button(label="Recusar", emoji="❌", style=discord.ButtonStyle.danger, custom_id=f"reject_{player_id}")
        reject_button.callback = self.reject_callback
        self.add_item(reject_button)

    def is_manager(self, member: discord.Member) -> bool:
        return any(role.id in (MANAGER_ROLE_ID, VICE_MANAGER_ROLE_ID) for role in member.roles)

    async def hire_callback(self, interaction: discord.Interaction):
        if self.finished:
            await interaction.response.send_message("❌ Esta Free Agency já foi encerrada.", ephemeral=True)
            return
        if not interaction.guild:
            await interaction.response.send_message("❌ Use dentro do servidor.", ephemeral=True)
            return

        member = interaction.guild.get_member(interaction.user.id)
        if not member or not self.is_manager(member):
            await interaction.response.send_message("❌ Apenas Managers podem contratar.", ephemeral=True)
            return

        if interaction.user.id == self.player_id:
            await interaction.response.send_message("❌ Não pode contratar a si mesmo.", ephemeral=True)
            return

        team_info = get_user_team(member)
        if not team_info:
            await interaction.response.send_message("❌ Você não tem um time.", ephemeral=True)
            return

        player = interaction.guild.get_member(self.player_id)
        if not player:
            await interaction.response.send_message("❌ Jogador não encontrado.", ephemeral=True)
            return

        if get_user_team(player):
            await interaction.response.send_message(f"❌ Jogador já tem time.", ephemeral=True)
            return

        team_role = interaction.guild.get_role(team_info["role_id"])
        if not team_role:
            await interaction.response.send_message("❌ Cargo do time não encontrado.", ephemeral=True)
            return

        try:
            await player.add_roles(team_role)
            self.finished = True
            for item in self.children:
                item.disabled = True

            embed = interaction.message.embeds[0]
            embed.color = discord.Color.green()
            embed.add_field(
                name="Status",
                value=f"✅ **CONTRATADO por {interaction.user.mention}**\n{get_team_emoji(team_info)} **{team_info['name']}**",
                inline=False
            )
            await interaction.response.edit_message(embed=embed, view=self)

            try:
                await player.send(f"🎉 Você foi contratado por {interaction.user.mention} para o time {get_team_emoji(team_info)} **{team_info['name']}**!")
            except:
                pass

            log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                log_embed = discord.Embed(
                    title="📋 Free Agency — Contratação",
                    description=f"**Jogador:** {player.mention}\n**Manager:** {interaction.user.mention}\n**Time:** {get_team_emoji(team_info)} {team_info['name']}\n**Status:** ✅ Contratado",
                    color=discord.Color.green()
                )
                await log_channel.send(embed=log_embed)

        except discord.Forbidden:
            await interaction.response.send_message("❌ Sem permissão para adicionar cargo.", ephemeral=True)

    async def reject_callback(self, interaction: discord.Interaction):
        if self.finished:
            await interaction.response.send_message("❌ Já encerrada.", ephemeral=True)
            return
        if not interaction.guild:
            return

        member = interaction.guild.get_member(interaction.user.id)
        if not member or not self.is_manager(member):
            await interaction.response.send_message("❌ Apenas Managers podem recusar.", ephemeral=True)
            return

        if interaction.user.id == self.player_id:
            await interaction.response.send_message("❌ Não pode recusar a própria.", ephemeral=True)
            return

        self.finished = True
        for item in self.children:
            item.disabled = True

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.red()
        embed.add_field(name="Status", value=f"❌ **Recusado por {interaction.user.mention}**", inline=False)
        await interaction.response.edit_message(embed=embed, view=self)

        player = interaction.guild.get_member(self.player_id)
        if player:
            try:
                await player.send(f"❌ Sua Free Agency foi recusada por {interaction.user.mention}.")
            except:
                pass

        log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            log_embed = discord.Embed(
                title="📋 Free Agency — Recusada",
                description=f"**Jogador:** {player.mention if player else self.player_id}\n**Manager:** {interaction.user.mention}\n**Status:** ❌ Recusado",
                color=discord.Color.red()
            )
            await log_channel.send(embed=log_embed)

# ============================================
# BOTÃO DE SCOUTING
# ============================================

class ScoutingSendButton(View):
    def __init__(self, message_content: str, manager_id: int, team_info: dict):
        super().__init__(timeout=300)
        self.message_content = message_content
        self.manager_id = manager_id
        self.team_info = team_info

        send_button = Button(label="📤 Enviar Mensagem", style=discord.ButtonStyle.primary, custom_id=f"scouting_send_{uuid.uuid4()}")
        send_button.callback = self.send_callback
        self.add_item(send_button)

    async def send_callback(self, interaction: discord.Interaction):
        scouting_channel = interaction.guild.get_channel(SCOUTING_CHANNEL_ID)
        if not scouting_channel:
            await interaction.response.send_message("❌ Canal de scouting não encontrado!", ephemeral=True)
            return

        team_emoji = get_team_emoji(self.team_info)
        embed = discord.Embed(
            title="🔍 Scouting",
            description=f"{team_emoji} **{self.team_info['name']}** está procurando jogadores!",
            color=discord.Color.blue()
        )
        embed.add_field(name="📝 Mensagem:", value=self.message_content, inline=False)
        embed.set_footer(text=f"Enviado por: {interaction.user.name}")

        contact_view = View()
        contact_button = Button(label="📩 Contatar Manager", style=discord.ButtonStyle.secondary, custom_id=f"contact_{uuid.uuid4()}")

        async def contact_callback(interact: discord.Interaction):
            manager = interact.guild.get_member(self.manager_id)
            if manager:
                try:
                    await manager.send(f"📩 **{interact.user.name}** entrou em contato sobre scouting do **{self.team_info['name']}**.\nMensagem original: {self.message_content}\nJogador: {interact.user.mention}")
                    await interact.response.send_message("✅ Mensagem enviada ao Manager!", ephemeral=True)
                except:
                    await interact.response.send_message("❌ Manager com DMs desativadas.", ephemeral=True)
            else:
                await interact.response.send_message("❌ Manager não encontrado.", ephemeral=True)

        contact_button.callback = contact_callback
        contact_view.add_item(contact_button)

        await scouting_channel.send(embed=embed, view=contact_view)
        await interaction.response.send_message("✅ Mensagem enviada para o canal de scouting!", ephemeral=True)

# ============================================
# VERIFICAÇÃO DE CARGO MANAGER
# ============================================

def has_manager_role():
    async def predicate(interaction: discord.Interaction) -> bool:
        if not interaction.guild:
            return False
        member = interaction.guild.get_member(interaction.user.id)
        if not member:
            return False
        return any(role.id in (MANAGER_ROLE_ID, VICE_MANAGER_ROLE_ID) for role in member.roles)
    return app_commands.check(predicate)

# ============================================
# COMANDOS SLASH
# ============================================

# --- Comandos de teste ---
@bot.tree.command(name="ping", description="🏓 Teste simples")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!", ephemeral=True)

@bot.tree.command(name="oi", description="👋 Teste simples 2")
async def oi(interaction: discord.Interaction):
    await interaction.response.send_message("Olá!", ephemeral=True)

@bot.tree.command(name="teste", description="🧪 Teste simples 3")
async def teste(interaction: discord.Interaction):
    await interaction.response.send_message("Teste funcionou!", ephemeral=True)

# --- Free Agency ---
@bot.tree.command(name="freeagency", description="⚽ Coloca você na Free Agency")
@app_commands.describe(mensagem="Informação adicional")
async def freeagency(interaction: discord.Interaction, mensagem: str = "Estou disponível!"):
    if not interaction.guild:
        await interaction.response.send_message("❌ Use no servidor.", ephemeral=True)
        return

    player = interaction.guild.get_member(interaction.user.id)
    if not player:
        await interaction.response.send_message("❌ Usuário não encontrado.", ephemeral=True)
        return

    if not any(role.id == PLAYER_ROLE_ID for role in player.roles):
        await interaction.response.send_message("❌ Você precisa do cargo Player.", ephemeral=True)
        return

    if get_user_team(player):
        await interaction.response.send_message("❌ Você já tem um time.", ephemeral=True)
        return

    channel = interaction.guild.get_channel(FREE_AGENCY_CHANNEL_ID)
    if not channel:
        await interaction.response.send_message("❌ Canal não encontrado.", ephemeral=True)
        return

    embed = discord.Embed(title="⚽ FREE AGENCY", description=mensagem, color=discord.Color.blue())
    embed.set_author(name=f"{player.display_name} está disponível!", icon_url=player.display_avatar.url)
    embed.add_field(name="👤 Jogador", value=player.mention, inline=True)
    embed.add_field(name="📋 Status", value="🟢 Disponível", inline=True)
    embed.set_footer(text=f"ID: {player.id}")

    view = FreeAgencyView(player.id, interaction.guild.id)
    await channel.send(embed=embed, view=view)
    await interaction.response.send_message(f"✅ Publicado em {channel.mention}!", ephemeral=True)

# --- Offer ---
@bot.tree.command(name="offer", description="📩 Envia oferta para um jogador")
@app_commands.describe(user="Jogador")
@has_manager_role()
async def offer(interaction: discord.Interaction, user: discord.Member):
    if user.bot or user.id == interaction.user.id:
        await interaction.response.send_message("❌ Inválido.", ephemeral=True)
        return

    member = interaction.guild.get_member(interaction.user.id)
    team_info = get_user_team(member)
    if not team_info:
        await interaction.response.send_message("❌ Você não tem time.", ephemeral=True)
        return

    try:
        embed = discord.Embed(
            title=f"{get_team_emoji(team_info)} OFERTA DO {team_info['name'].upper()}",
            description="📋 **CONTRATO DE OFERTA**",
            color=discord.Color.gold()
        )
        embed.add_field(name="Caro jogador,", value="Gostaríamos de formalizar uma oferta para você fazer parte do nosso time.", inline=False)
        embed.add_field(name="📌 Termos:", value="• Treinos e jogos\n• Comprometimento\n• Seguir regras", inline=False)
        embed.add_field(name="⚠️", value="Selecione uma opção abaixo:", inline=False)
        embed.set_footer(text=f"Oferta por: {interaction.user.name}", icon_url=interaction.user.display_avatar.url)

        view = OfferButtons(user.id, LOG_CHANNEL_ID, team_info, interaction.guild.id)
        await user.send(embed=embed, view=view)
        await interaction.response.send_message(f"✅ Oferta enviada para {user.mention}!", ephemeral=True)

        log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            log_embed = discord.Embed(
                title="📤 Oferta Enviada",
                description=f"**Manager:** {interaction.user.mention}\n**Jogador:** {user.mention}\n**Time:** {get_team_emoji(team_info)} {team_info['name']}\n**Status:** ⏳ Pendente",
                color=discord.Color.blue()
            )
            await log_channel.send(embed=log_embed)

    except discord.Forbidden:
        await interaction.response.send_message("❌ Usuário com DMs desativadas.", ephemeral=True)

# --- Scouting ---
@bot.tree.command(name="scouting", description="🔍 Envia mensagem de scouting")
@app_commands.describe(mensagem="Mensagem personalizada")
@has_manager_role()
async def scouting(interaction: discord.Interaction, mensagem: str):
    if len(mensagem) > 1024:
        await interaction.response.send_message("❌ Máximo 1024 caracteres.", ephemeral=True)
        return

    member = interaction.guild.get_member(interaction.user.id)
    team_info = get_user_team(member)
    if not team_info:
        await interaction.response.send_message("❌ Você não tem time.", ephemeral=True)
        return

    view = ScoutingSendButton(mensagem, interaction.user.id, team_info)
    embed = discord.Embed(
        title="📢 Scouting",
        description=f"**Sua mensagem:**\n{mensagem}\n\n**Time:** {get_team_emoji(team_info)} {team_info['name']}",
        color=discord.Color.purple()
    )
    embed.set_footer(text="Clique em 'Enviar Mensagem' para publicar")
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# ============================================
# COMANDOS DE ADMINISTRAÇÃO (SYNC)
# ============================================

@bot.tree.command(name="sync", description="🔄 Forçar sincronização de comandos")
@app_commands.default_permissions(administrator=True)
async def sync_commands(interaction: discord.Interaction):
    await interaction.response.send_message("🔄 Sincronizando...", ephemeral=True)
    try:
        guild = discord.Object(id=1496579366677909704)
        await bot.tree.sync(guild=guild)
        commands = await bot.tree.fetch_commands(guild=guild)
        nomes = [cmd.name for cmd in commands]
        await interaction.edit_original_response(content=f"✅ Sincronizado!\n📌 Comandos: {', '.join(nomes)}")
    except Exception as e:
        await interaction.edit_original_response(content=f"❌ Erro: {e}")

@bot.tree.command(name="limpar", description="🧹 Limpar comandos do servidor")
@app_commands.default_permissions(administrator=True)
async def limpar_comandos(interaction: discord.Interaction):
    await interaction.response.send_message("🧹 Limpando...", ephemeral=True)
    try:
        guild = discord.Object(id=1496579366677909704)
        await bot.tree.sync(guild=guild)
        commands = await bot.tree.fetch_commands(guild=guild)
        await interaction.edit_original_response(content=f"✅ Limpo! {len(commands)} comandos restantes.")
    except Exception as e:
        await interaction.edit_original_response(content=f"❌ Erro: {e}")

@bot.tree.command(name="syncglobal", description="🌍 Sincronizar comandos globalmente")
@app_commands.default_permissions(administrator=True)
async def sync_global(interaction: discord.Interaction):
    await interaction.response.send_message("🌍 Sincronizando globalmente...", ephemeral=True)
    try:
        await bot.tree.sync()
        await interaction.edit_original_response(content="✅ Sincronização global concluída! Aguarde até 5 min.")
    except Exception as e:
        await interaction.edit_original_response(content=f"❌ Erro: {e}")

# ============================================
# EVENTOS
# ============================================

@bot.event
async def on_ready():
    import asyncio
    print(f'✅ {bot.user.name} está online!')
    print(f'📡 ID: {bot.user.id}')
    print(f'📡 Servidores: {len(bot.guilds)}')

    await asyncio.sleep(3)

    try:
        guild = discord.Object(id=1496579366677909704)
        await bot.tree.sync(guild=guild)
        commands = await bot.tree.fetch_commands(guild=guild)
        nomes = [cmd.name for cmd in commands]
        print(f"📌 Comandos ativos: {nomes}")

        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"{len(nomes)} comandos | MCL Bot"
            )
        )
        print("🚀 Bot pronto!")
    except Exception as e:
        print(f"❌ Erro no on_ready: {e}")

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(f"⏳ Aguarde {int(error.retry_after)}s.", ephemeral=True)
    else:
        await interaction.response.send_message(f"❌ Erro: {error}", ephemeral=True)
        print(f"Erro: {error}")

# ============================================
# INICIALIZAÇÃO
# ============================================

if __name__ == "__main__":
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("❌ Token não encontrado! Configure DISCORD_TOKEN")
        exit(1)

    try:
        bot.run(token)
    except Exception as e:
        print(f"❌ Erro ao iniciar: {e}")
