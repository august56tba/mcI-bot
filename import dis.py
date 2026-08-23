import discord
from discord import app_commands
from discord.ui import Button, View
import uuid
import os
from typing import Optional

# Configuração do bot
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

class MCLBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
    
    # ===== CORREÇÃO: setup_hook DENTRO da classe =====
    async def setup_hook(self):
        guild = discord.Object(id=1496579366677909704)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        print("✅ Comandos sincronizados no servidor!")

bot = MCLBot()

# IDs dos canais
LOG_CHANNEL_ID = 1510486940833812670
SCOUTING_CHANNEL_ID = 1520619945526825070
FREE_AGENCY_CHANNEL_ID = 1496579368493777097

# Cargos permitidos
MANAGER_ROLE_ID = 1496579366765723720
VICE_MANAGER_ROLE_ID = 1496579366736625723
PLAYER_ROLE_ID = 1496579366698750185

# Dicionário com os IDs dos times e seus emojis
TEAM_ROLES = {
    1536899006397939802: {
        "name": "França",
        "emoji_id": 1529940051574788226,
        "emoji_name": "FRA",
        "role_id": 1536899006397939802
    },
    1531762164619018340: {
        "name": "ESPANHA",
        "emoji_id": 1529940469839298622,
        "emoji_name": "ESP",
        "role_id": 1531762164619018340
    },
    1536898498971045999: {
        "name": "Inglaterra",
        "emoji_id": 1529943945491120178,
        "emoji_name": "ENG",
        "role_id": 1536898498971045999
    },
    1520779736408653914: {
        "name": "BraziI",
        "emoji_id": 1529941002104602786,
        "emoji_name": "BRA",
        "role_id": 1520779736408653914
    },
    1520780175590031481: {
        "name": "CABO VERDE",
        "emoji_id": 1529939732287590572,
        "emoji_name": "CBV",
        "role_id": 1520780175590031481
    },
    1520780363712954428: {
        "name": "PortugaI",
        "emoji_id": 1534588893456891975,
        "emoji_name": "POR",
        "role_id": 1520780363712954428
    },
    1520620774564827176: {
        "name": "Argentina",
        "emoji_id": 1540742657788215396,
        "emoji_name": "ARG",
        "role_id": 1520620774564827176
    },
    1520779908660596836: {
        "name": "Uruguai",
        "emoji_id": 1512649773948080189,
        "emoji_name": "URG",
        "role_id": 1520779908660596836
    },
    1520785259866886195: {
        "name": "MARROCOS",
        "emoji_id": 1512649740670603425,
        "emoji_name": "MAR",
        "role_id": 1520785259866886195
    }
}

def get_user_team(member: discord.Member) -> Optional[dict]:
    """Retorna as informações do time do usuário baseado nos cargos"""
    for role in member.roles:
        if role.id in TEAM_ROLES:
            return TEAM_ROLES[role.id]
    return None

def get_team_emoji(team_info: dict) -> str:
    """Retorna o emoji formatado corretamente"""
    return f"<:{team_info['emoji_name']}:{team_info['emoji_id']}>"

class OfferButtons(View):
    def __init__(self, user_id: int, log_channel_id: int, team_info: dict, guild_id: int):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.log_channel_id = log_channel_id
        self.team_info = team_info
        self.guild_id = guild_id
        
        accept_button = Button(
            label="✅ Aceitar",
            style=discord.ButtonStyle.success,
            custom_id=f"accept_{uuid.uuid4()}"
        )
        accept_button.callback = self.accept_callback
        self.add_item(accept_button)
        
        decline_button = Button(
            label="❌ Recusar",
            style=discord.ButtonStyle.danger,
            custom_id=f"decline_{uuid.uuid4()}"
        )
        decline_button.callback = self.decline_callback
        self.add_item(decline_button)
    
    async def accept_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ Esta oferta não é para você!",
                ephemeral=True
            )
            return
        
        # Desativa os botões
        for item in self.children:
            item.disabled = True
        
        # Adiciona o cargo do time ao jogador
        team_role_id = self.team_info["role_id"]
        team_name = self.team_info["name"]
        team_emoji = get_team_emoji(self.team_info)
        
        try:
            # Pega o servidor
            guild = bot.get_guild(self.guild_id)
            if not guild:
                await interaction.response.send_message(
                    "❌ Erro: Servidor não encontrado!",
                    ephemeral=True
                )
                return
            
            # Pega o cargo do time
            role = guild.get_role(team_role_id)
            if not role:
                await interaction.response.send_message(
                    "❌ Erro: Cargo do time não encontrado!",
                    ephemeral=True
                )
                return
            
            # Pega o membro atualizado
            member = guild.get_member(interaction.user.id)
            if not member:
                await interaction.response.send_message(
                    "❌ Erro: Usuário não encontrado no servidor!",
                    ephemeral=True
                )
                return
            
            # Adiciona o cargo ao jogador
            await member.add_roles(role)
            
            # Mensagem de confirmação estilizada
            embed = discord.Embed(
                title=f"{team_emoji} ✅ Oferta Aceita!",
                description=f"Parabéns! Você agora faz parte do **{team_name}**!",
                color=discord.Color.green()
            )
            embed.add_field(
                name="🎉 Bem-vindo ao time!",
                value=f"Você recebeu o cargo {role.mention} com sucesso.",
                inline=False
            )
            embed.set_footer(text="Aguardando instruções do Manager")
            
            await interaction.response.edit_message(
                embed=embed,
                view=self
            )
            
            # Log de aceitação com informações do cargo
            log_channel = guild.get_channel(self.log_channel_id)
            if log_channel:
                embed_log = discord.Embed(
                    title="📋 Oferta Aceita",
                    description=f"**Jogador:** {interaction.user.mention}\n"
                               f"**Time:** {team_emoji} {team_name}\n"
                               f"**Status:** ✅ Aceita\n"
                               f"**Cargo Atribuído:** {role.mention}",
                    color=discord.Color.green()
                )
                embed_log.set_footer(text=f"Jogador ID: {interaction.user.id}")
                await log_channel.send(embed=embed_log)
            
            print(f"Oferta aceita por {interaction.user.name} - Time: {team_name}")
            
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Não tenho permissão para adicionar cargos! Verifique minhas permissões.",
                ephemeral=True
            )
        except discord.HTTPException as e:
            await interaction.response.send_message(
                f"❌ Erro ao adicionar cargo: {str(e)}",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Erro inesperado: {str(e)}",
                ephemeral=True
            )
    
    async def decline_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ Esta oferta não é para você!",
                ephemeral=True
            )
            return
        
        # Desativa os botões
        for item in self.children:
            item.disabled = True
        
        # Mensagem de confirmação estilizada
        embed = discord.Embed(
            title="❌ Oferta Recusada",
            description="Você recusou a oferta.",
            color=discord.Color.red()
        )
        embed.set_footer(text="Oferta encerrada")
        
        await interaction.response.edit_message(
            embed=embed,
            view=self
        )
        
        # Log de recusa
        guild = bot.get_guild(self.guild_id)
        if guild:
            log_channel = guild.get_channel(self.log_channel_id)
            if log_channel:
                team_name = self.team_info["name"]
                team_emoji = get_team_emoji(self.team_info)
                embed_log = discord.Embed(
                    title="📋 Oferta Recusada",
                    description=f"**Jogador:** {interaction.user.mention}\n"
                               f"**Time:** {team_emoji} {team_name}\n"
                               f"**Status:** ❌ Recusada",
                    color=discord.Color.red()
                )
                embed_log.set_footer(text=f"Jogador ID: {interaction.user.id}")
                await log_channel.send(embed=embed_log)
        
        print(f"Oferta recusada por {interaction.user.name}")

class FreeAgencyView(View):
    def __init__(self, player_id: int, guild_id: int):
        super().__init__(timeout=None)

        self.player_id = player_id
        self.guild_id = guild_id
        self.finished = False

        hire_button = Button(
            label="Contratar",
            emoji="✅",
            style=discord.ButtonStyle.success,
            custom_id=f"freeagency_hire_{player_id}"
        )
        hire_button.callback = self.hire_callback

        reject_button = Button(
            label="Recusar",
            emoji="❌",
            style=discord.ButtonStyle.danger,
            custom_id=f"freeagency_reject_{player_id}"
        )
        reject_button.callback = self.reject_callback

        self.add_item(hire_button)
        self.add_item(reject_button)

    def is_manager(self, member: discord.Member) -> bool:
        return any(
            role.id in (MANAGER_ROLE_ID, VICE_MANAGER_ROLE_ID)
            for role in member.roles
        )

    async def hire_callback(self, interaction: discord.Interaction):

        if self.finished:
            await interaction.response.send_message(
                "❌ Esta Free Agency já foi encerrada.",
                ephemeral=True
            )
            return

        if not interaction.guild:
            await interaction.response.send_message(
                "❌ Este botão só pode ser usado dentro do servidor.",
                ephemeral=True
            )
            return

        member = interaction.guild.get_member(interaction.user.id)

        if not member or not self.is_manager(member):
            await interaction.response.send_message(
                "❌ Apenas Managers e Vice Managers podem contratar jogadores.",
                ephemeral=True
            )
            return

        if interaction.user.id == self.player_id:
            await interaction.response.send_message(
                "❌ Você não pode contratar a si mesmo!",
                ephemeral=True
            )
            return

        team_info = get_user_team(member)

        if not team_info:
            await interaction.response.send_message(
                "❌ Você não possui um cargo de time.",
                ephemeral=True
            )
            return

        player = interaction.guild.get_member(self.player_id)

        if not player:
            await interaction.response.send_message(
                "❌ Jogador não encontrado no servidor.",
                ephemeral=True
            )
            return

        # Verifica se o jogador já possui algum time
        current_team = get_user_team(player)

        if current_team:
            await interaction.response.send_message(
                f"❌ Este jogador já está no time **{current_team['name']}**.",
                ephemeral=True
            )
            return

        team_role = interaction.guild.get_role(team_info["role_id"])

        if not team_role:
            await interaction.response.send_message(
                "❌ Cargo do time não encontrado.",
                ephemeral=True
            )
            return

        try:
            await player.add_roles(team_role)

            self.finished = True

            for item in self.children:
                item.disabled = True

            team_name = team_info["name"]
            team_emoji = get_team_emoji(team_info)

            embed = interaction.message.embeds[0]

            embed.color = discord.Color.green()

            embed.add_field(
                name="Status",
                value=f"✅ **CONTRATADO por {interaction.user.mention}**\n"
                      f"{team_emoji} **{team_name}**",
                inline=False
            )

            await interaction.response.edit_message(
                embed=embed,
                view=self
            )

            # DM para o jogador
            try:
                await player.send(
                    f"🎉 **Você foi contratado!**\n\n"
                    f"Você foi contratado por {interaction.user.mention} "
                    f"para o time {team_emoji} **{team_name}**."
                )
            except discord.Forbidden:
                pass

            # Log
            log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)

            if log_channel:
                log_embed = discord.Embed(
                    title="📋 Free Agency — Contratação",
                    description=(
                        f"**Jogador:** {player.mention}\n"
                        f"**Manager:** {interaction.user.mention}\n"
                        f"**Time:** {team_emoji} {team_name}\n"
                        f"**Status:** ✅ Contratado"
                    ),
                    color=discord.Color.green()
                )

                await log_channel.send(embed=log_embed)

        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Não tenho permissão para adicionar o cargo do time.",
                ephemeral=True
            )

        except discord.HTTPException as e:
            await interaction.response.send_message(
                f"❌ Erro ao contratar o jogador: {e}",
                ephemeral=True
            )

    async def reject_callback(self, interaction: discord.Interaction):

        if self.finished:
            await interaction.response.send_message(
                "❌ Esta Free Agency já foi encerrada.",
                ephemeral=True
            )
            return

        if not interaction.guild:
            await interaction.response.send_message(
                "❌ Este botão só pode ser usado dentro do servidor.",
                ephemeral=True
            )
            return

        member = interaction.guild.get_member(interaction.user.id)

        if not member or not self.is_manager(member):
            await interaction.response.send_message(
                "❌ Apenas Managers e Vice Managers podem recusar jogadores.",
                ephemeral=True
            )
            return

        if interaction.user.id == self.player_id:
            await interaction.response.send_message(
                "❌ Você não pode recusar a própria Free Agency.",
                ephemeral=True
            )
            return

        player = interaction.guild.get_member(self.player_id)

        self.finished = True

        for item in self.children:
            item.disabled = True

        embed = interaction.message.embeds[0]

        embed.color = discord.Color.red()

        embed.add_field(
            name="Status",
            value=f"❌ **Recusado por {interaction.user.mention}**",
            inline=False
        )

        await interaction.response.edit_message(
            embed=embed,
            view=self
        )

        # DM para o jogador
        if player:
            try:
                await player.send(
                    f"❌ Sua Free Agency foi recusada por "
                    f"{interaction.user.mention}."
                )
            except discord.Forbidden:
                pass

        # Log
        log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)

        if log_channel:
            log_embed = discord.Embed(
                title="📋 Free Agency — Recusada",
                description=(
                    f"**Jogador:** {player.mention if player else self.player_id}\n"
                    f"**Manager:** {interaction.user.mention}\n"
                    f"**Status:** ❌ Recusado"
                ),
                color=discord.Color.red()
            )

            await log_channel.send(embed=log_embed)

class ScoutingSendButton(View):
    def __init__(self, message_content: str, manager_id: int, team_info: dict):
        super().__init__(timeout=300)
        self.message_content = message_content
        self.manager_id = manager_id
        self.team_info = team_info
        
        send_button = Button(
            label="📤 Enviar Mensagem",
            style=discord.ButtonStyle.primary,
            custom_id=f"scouting_send_{uuid.uuid4()}"
        )
        send_button.callback = self.send_callback
        self.add_item(send_button)
    
    async def send_callback(self, interaction: discord.Interaction):
        scouting_channel = interaction.guild.get_channel(SCOUTING_CHANNEL_ID)
        
        if not scouting_channel:
            await interaction.response.send_message(
                "❌ Canal de scouting não encontrado!",
                ephemeral=True
            )
            return
        
        # Cria a mensagem com o nome do time e o emoji
        team_name = self.team_info["name"]
        team_emoji = get_team_emoji(self.team_info)
        
        embed = discord.Embed(
            title="🔍 Scouting",
            description=f"{team_emoji} **{team_name}** está procurando jogadores!",
            color=discord.Color.blue()
        )
        embed.add_field(name="📝 Mensagem do Manager:", value=self.message_content, inline=False)
        embed.set_footer(text=f"Enviado por: {interaction.user.name}")
        
        # Botão para contatar o manager
        contact_view = View()
        contact_button = Button(
            label="📩 Enviar mensagem para o Manager",
            style=discord.ButtonStyle.secondary,
            custom_id=f"contact_manager_{uuid.uuid4()}"
        )
        
        async def contact_callback(interaction: discord.Interaction):
            manager = interaction.guild.get_member(self.manager_id)
            if manager:
                try:
                    await manager.send(
                        f"📩 **{interaction.user.name}** entrou em contato sobre o scouting do **{team_name}**:\n\n"
                        f"**Mensagem original:** {self.message_content}\n"
                        f"**Jogador:** {interaction.user.mention}"
                    )
                    await interaction.response.send_message(
                        "✅ Mensagem enviada para o Manager!",
                        ephemeral=True
                    )
                except discord.Forbidden:
                    await interaction.response.send_message(
                        "❌ Não foi possível enviar mensagem para o Manager. Ele pode ter DMs desativadas.",
                        ephemeral=True
                    )
            else:
                await interaction.response.send_message(
                    "❌ Manager não encontrado.",
                    ephemeral=True
                )
        
        contact_button.callback = contact_callback
        contact_view.add_item(contact_button)
        
        await scouting_channel.send(embed=embed, view=contact_view)
        
        await interaction.response.send_message(
            "✅ Mensagem enviada com sucesso para o canal de scouting!",
            ephemeral=True
        )

def has_manager_role():
    async def predicate(interaction: discord.Interaction) -> bool:
        if not interaction.guild:
            return False
        
        member = interaction.guild.get_member(interaction.user.id)
        if not member:
            return False
        
        for role in member.roles:
            if role.id == MANAGER_ROLE_ID or role.id == VICE_MANAGER_ROLE_ID:
                return True
        return False
    return app_commands.check(predicate)

# ===== COMANDO DE TESTE =====
@bot.tree.command(name="ping", description="Testa se o bot está funcionando")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong! Bot está online!", ephemeral=True)

@bot.tree.command(
    name="freeagency",
    description="Coloca você na Free Agency para ser contratado"
)
@app_commands.describe(
    mensagem="Informação adicional sobre sua Free Agency"
)
@app_commands.checks.cooldown(1, 60.0)
async def freeagency(
    interaction: discord.Interaction,
    mensagem: str = "Estou disponível para receber propostas!"
):
    if not interaction.guild:
        await interaction.response.send_message(
            "❌ Este comando só pode ser usado dentro de um servidor.",
            ephemeral=True
        )
        return

    if interaction.user.bot:
        await interaction.response.send_message(
            "❌ Bots não podem entrar na Free Agency.",
            ephemeral=True
        )
        return

    player = interaction.guild.get_member(interaction.user.id)

    if not player:
        await interaction.response.send_message(
            "❌ Não consegui encontrar seu usuário no servidor.",
            ephemeral=True
        )
        return

    # Verifica se o usuário possui o cargo de Player
    if not any(role.id == PLAYER_ROLE_ID for role in player.roles):
        await interaction.response.send_message(
            "❌ Apenas jogadores com o cargo de Player podem usar a Free Agency.",
            ephemeral=True
        )
        return

    # Verifica se o jogador já possui algum time
    current_team = get_user_team(player)

    if current_team:
        await interaction.response.send_message(
            f"❌ Este jogador já está no time **{current_team['name']}**.",
            ephemeral=True
        )
        return

    if len(mensagem) > 1024:
        await interaction.response.send_message(
            "❌ Sua mensagem pode ter no máximo 1024 caracteres.",
            ephemeral=True
        )
        return

    channel = interaction.guild.get_channel(FREE_AGENCY_CHANNEL_ID)

    if not channel:
        await interaction.response.send_message(
            "❌ Canal de Free Agency não encontrado.",
            ephemeral=True
        )
        return

    # Embed
    embed = discord.Embed(
        title="⚽ FREE AGENCY",
        description=mensagem,
        color=discord.Color.blue()
    )

    # Avatar circular à esquerda
    embed.set_author(
        name=f"{player.display_name} está disponível!",
        icon_url=player.display_avatar.url
    )

    embed.add_field(
        name="👤 Jogador",
        value=player.mention,
        inline=True
    )

    embed.add_field(
        name="📋 Status",
        value="🟢 Disponível",
        inline=True
    )

    embed.set_footer(
        text=f"Player ID: {player.id}"
    )

    # Botões
    view = FreeAgencyView(
        player_id=player.id,
        guild_id=interaction.guild.id
    )

    await channel.send(
        embed=embed,
        view=view
    )

    await interaction.response.send_message(
        f"✅ Sua Free Agency foi publicada em {channel.mention}!",
        ephemeral=True
    )

@bot.tree.command(name="offer", description="Envia uma oferta para um jogador via DM")
@app_commands.describe(user="Usuário para enviar a oferta")
@has_manager_role()
async def offer(interaction: discord.Interaction, user: discord.Member):
    if user.bot:
        await interaction.response.send_message(
            "❌ Não é possível enviar ofertas para bots!",
            ephemeral=True
        )
        return
    
    if user.id == interaction.user.id:
        await interaction.response.send_message(
            "❌ Você não pode enviar uma oferta para si mesmo!",
            ephemeral=True
        )
        return
    
    try:
        # Pega o time do manager
        member = interaction.guild.get_member(interaction.user.id)
        team_info = get_user_team(member)
        
        if not team_info:
            await interaction.response.send_message(
                "❌ Você não possui um cargo de time!",
                ephemeral=True
            )
            return
        
        team_name = team_info["name"]
        team_emoji = get_team_emoji(team_info)
        
        # Cria a mensagem estilizada com embed
        embed = discord.Embed(
            title=f"{team_emoji} OFERTA DO {team_name.upper()}",
            description="📋 **CONTRATO DE OFERTA**",
            color=discord.Color.gold()
        )
        embed.add_field(
            name="Caro jogador,",
            value="Gostaríamos de formalizar uma oferta para você fazer parte do nosso time.",
            inline=False
        )
        embed.add_field(
            name="📌 Termos da Oferta:",
            value="• Participação em treinos e jogos\n• Comprometimento com a equipe\n• Seguir as regras do clube",
            inline=False
        )
        embed.add_field(
            name="⚠️ Atenção:",
            value="Por favor, selecione uma das opções abaixo para aceitar ou recusar esta oferta.",
            inline=False
        )
        embed.set_footer(text=f"Oferta enviada por: {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
        
        # Envia a mensagem para o usuário
        view = OfferButtons(user.id, LOG_CHANNEL_ID, team_info, interaction.guild.id)
        await user.send(embed=embed, view=view)
        
        await interaction.response.send_message(
            f"✅ Oferta enviada com sucesso para {user.mention}!",
            ephemeral=True
        )
        
        log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            embed_log = discord.Embed(
                title="📤 Oferta Enviada",
                description=f"**Manager:** {interaction.user.mention}\n"
                           f"**Jogador:** {user.mention}\n"
                           f"**Time:** {team_emoji} {team_name}\n"
                           f"**Status:** ⏳ Pendente",
                color=discord.Color.blue()
            )
            embed_log.set_footer(text=f"Manager ID: {interaction.user.id} | Jogador ID: {user.id}")
            await log_channel.send(embed=embed_log)
        
        print(f"Oferta enviada por {interaction.user.name} para {user.name} - Time: {team_name}")
        
    except discord.Forbidden:
        await interaction.response.send_message(
            f"❌ Não foi possível enviar mensagem para {user.mention}. O usuário pode ter DMs desativadas.",
            ephemeral=True
        )
    except Exception as e:
        await interaction.response.send_message(
            f"❌ Ocorreu um erro ao enviar a oferta: {str(e)}",
            ephemeral=True
        )

@bot.tree.command(name="scouting", description="Envia uma mensagem de scouting para o canal")
@app_commands.describe(mensagem="Mensagem personalizada para o scouting")
@has_manager_role()
async def scouting(interaction: discord.Interaction, mensagem: str):
    if len(mensagem) > 1024:
        await interaction.response.send_message(
            "❌ A mensagem é muito longa! Máximo de 1024 caracteres.",
            ephemeral=True
        )
        return
    
    # Verifica o time do manager
    member = interaction.guild.get_member(interaction.user.id)
    team_info = get_user_team(member)
    
    if not team_info:
        await interaction.response.send_message(
            "❌ Você não possui um cargo de time! Para usar este comando, você precisa ter um cargo de time (Fortaleza, Boca Juniors, etc.).",
            ephemeral=True
        )
        return
    
    # Cria a view com o botão para enviar
    view = ScoutingSendButton(mensagem, interaction.user.id, team_info)
    
    team_name = team_info["name"]
    team_emoji = get_team_emoji(team_info)
    
    embed = discord.Embed(
        title="📢 Scouting",
        description=f"**Sua mensagem:**\n{mensagem}\n\n**Time:** {team_emoji} {team_name}",
        color=discord.Color.purple()
    )
    embed.set_footer(text="Clique no botão abaixo para enviar ao canal de scouting")
    
    await interaction.response.send_message(
        embed=embed,
        view=view,
        ephemeral=True
    )

@bot.event
@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError
):

    if isinstance(error, app_commands.CommandOnCooldown):

        remaining = int(error.retry_after)

        if remaining < 60:
            tempo = f"{remaining} segundos"
        else:
            tempo = f"{remaining // 60} minuto(s)"

        await interaction.response.send_message(
            f"⏳ Você precisa esperar **{tempo}** antes de usar `/freeagency` novamente.",
            ephemeral=True
        )
        return

    print(f"Erro em slash command: {error}")
@bot.event
async def on_ready():
    print(f'✅ {bot.user.name} está online!')
    print(f'📡 Conectado como: {bot.user.id}')
    print(f'📡 Conectado a {len(bot.guilds)} servidores')
    print(f'🏆 Times configurados: {len(TEAM_ROLES)}')
    
    # Sincronizar comandos novamente (garantia)
    try:
        guild = discord.Object(id=1496579366677909704)
        await bot.tree.sync(guild=guild)
        print("✅ Comandos sincronizados!")
    except Exception as e:
        print(f"❌ Erro ao sincronizar: {e}")

# ===== INICIALIZAÇÃO =====
if __name__ == "__main__":
    token = os.getenv('DISCORD_TOKEN')  # Mude para DISCORD_TOKEN
    if not token:
        print("❌ Token não encontrado!")
        exit(1)
    
    try:
        bot.run(token)
    except Exception as e:
        print(f"❌ Erro: {e}")

