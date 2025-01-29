import disnake
from disnake.ext import commands
import os
from dotenv import load_dotenv
from datetime import datetime, timezone
import random
import string
import asyncio
import pytz

from save_load_files import save_dict_to_file, load_dict_lst_or_str__from_jsonfile





#-------------------------------------------------Do not change
folder_path = "databases/"
MAP_INT_USERID_FILENAME = 'RANDOMINT_TO_USERID.json'
if os.path.exists(folder_path+MAP_INT_USERID_FILENAME):
    MAP_INT_USERID = load_dict_lst_or_str__from_jsonfile(folder_path+MAP_INT_USERID_FILENAME)
    print(f'>Found pre-existing {MAP_INT_USERID_FILENAME} + loaded successfully')
else:
    print(f'>Could not find {MAP_INT_USERID_FILENAME}. Putting variable to empty dict')
    MAP_INT_USERID= {}



#Env variables
#--------------------------------- CHANGE THESE
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = os.getenv('GUILD_ID') #TODO 
ROLE_ID = int(os.getenv('ROLE_ID'))


#-----------------------------------------------------------------------------------
guild_ids = [int(GUILD_ID)]

# Create an instance of Bot with a command prefix
bot = commands.Bot(intents = disnake.Intents.all(),command_prefix='!', test_guilds=guild_ids )
bot.guildid_global = guild_ids[0]



# Event when the bot is ready
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')



#DECORATOR
# Checks if admin or has roleid, to run the command
def has_role_or_admin():
    async def predicate(inter: disnake.ApplicationCommandInteraction):
        """My custom decorator I created that only makes a command run if it returns TRUE. If FALSE, then function does not have permission to run"""
        # print('>Checking for admin or role<')
        if inter.author.guild_permissions.administrator:
            # print('--User has admin role case')
            return True
        role = disnake.utils.get(inter.author.roles, id=ROLE_ID)
        # print('--User has role case')
        # print('Role extracted:', role)
        return role is not None
    return commands.check(predicate)


# Command to submit a ticket
@bot.slash_command(description="Submit a ticket")
async def ticket(inter: disnake.ApplicationCommandInteraction, message: str = commands.Param(max_length=1024)):
    """Allows users to submit tickets."""
    guild = inter.guild
    now = datetime.now(timezone.utc)

    # Create a timezone object for CST
    cst_timezone = pytz.timezone('US/Central')
    # Convert the UTC datetime to CST
    now = now.astimezone(cst_timezone)


    formatted_time = now.strftime("%I:%M:%p") #Formatted PM/AM time
    hour, minute, period = formatted_time.split(':')

    if guild is None:
        await inter.response.send_message("This command can only be used in a server.", ephemeral=True)
        return

    # Create a new channel for the ticket
    channel_name = f"ticket-{inter.author.display_name}-{hour}-{minute}-{period}-on-{now.month}-{now.day}-{now.year}"
    overwrites = {
        guild.default_role: disnake.PermissionOverwrite(view_channel=False),
        inter.author: disnake.PermissionOverwrite(view_channel=True, send_messages=True),
        guild.me: disnake.PermissionOverwrite(view_channel=True, send_messages=True)
    }

    # Add admin roles to the overwrites
    for role in guild.roles:
        if role.permissions.administrator:
            overwrites[role] = disnake.PermissionOverwrite(view_channel=True, send_messages=True)

    ticket_channel = await guild.create_text_channel(channel_name, overwrites=overwrites)

    # Create an embed for the ticket
    embed = disnake.Embed(title="New Ticket", description='Admins may respond to this ticket using **/respond**. Close this ticket and delete channel using **/close**' , color=0x00ff00)
    embed.add_field(name="User", value=f"{inter.author.mention} ({inter.author.id})", inline=False)
    embed.add_field(name="Roles", value=f"{' '.join([role.mention for role in inter.author.roles])}", inline=False)
    
    embed.add_field(name="Message", value=message, inline=False)
    embed.set_footer(text=f"{inter.author.display_name} | {inter.author.id} | {now.month}/{now.day} at {hour}:{minute} {period} CST")

    
    # Send the embed to the new ticket channel
    await ticket_channel.send(embed=embed)
    await inter.response.send_message(f"Your ticket has been submitted successfully for admin review! Admin(s) will respond to your ticket at the private text channel: {ticket_channel.mention}", ephemeral=True)
    print(">Unanonymous ticket submitted!")


# Command for admins to respond to tickets
@bot.slash_command(description="Respond to a ticket (Admins only)")
@has_role_or_admin()
async def respond(
    inter: disnake.ApplicationCommandInteraction,
    response: str = commands.Param(max_length=1024),
    responder_name: str = commands.Param(choices=["Your Name","Admins", "Anonymous"])
):
    """Allows admins to respond to tickets with different identity options."""
    guild = bot.get_guild(bot.guildid_global)
    if inter.channel.name.startswith("ticket-") or inter.channel.name.startswith("anonymous-ticket-"):
        # Determine the responder identity
        if responder_name == "Your Name":
            responder = inter.author.display_name
        elif responder_name == "Admins":
            responder = "Admins"
        else:
            responder = "Anonymous"

        # Create an embed for the response
        embed = disnake.Embed(title=f"Admin Response | {responder}", description=response, color=0xff0000)
        #embed.add_field(name="Response", value=response, inline=False)

        # Send the embed to the current channel if in 'ticket-' channel:
        if inter.channel.name.startswith("ticket-"):
            await inter.channel.send(embed=embed)
            await inter.response.send_message("Your response has been sent.", ephemeral=True)
            print("<Unanonymous ticket responded to by admins!")

        # Check if this is an anonymous ticket
        elif inter.channel.name.startswith("anonymous-ticket-"):
            # Extract user discriminator from the channel name
            random_id = inter.channel.name.split('-')[-1]
            if random_id in MAP_INT_USERID:
                user = guild.get_member(MAP_INT_USERID[random_id])
            else:
                return await inter.send('Message to anonymous user could not be delivered. User is no longer in the discord server.')
            if user:
                try:
                    # Send the response to the user via DM
                    await user.send(embed=embed)
                    await inter.send('Admin DM was sent to anonymous user.')
                    print("<Anonymous ticket responded to by admins!")
                except disnake.Forbidden:
                    await inter.channel.send("Failed to send DM to the user.")



    else:
        await inter.response.send_message("This command can only be used in a ticket channel.", ephemeral=True)



@bot.slash_command(description="Close a ticket (Admins only)")
@has_role_or_admin()
async def close(inter: disnake.ApplicationCommandInteraction):
    global MAP_INT_USERID
    guild = bot.get_guild(bot.guildid_global)
    if inter.channel.name.startswith("ticket-") or inter.channel.name.startswith("anonymous-ticket-"):
        if inter.channel.name.startswith("anonymous-ticket-"): #FOR Anonymous channel, we must delete from global MAP
            random_id = inter.channel.name.split('-')[-1]
            if random_id in MAP_INT_USERID:
                del MAP_INT_USERID[random_id] #delete from global MAP + save changes
                save_dict_to_file(MAP_INT_USERID, folder_path+MAP_INT_USERID_FILENAME)

        channel = inter.channel
        await inter.response.send_message("Ticket has been closed. Deleting the channel in 5 seconds.")
        await asyncio.sleep(5)
        await channel.delete()
        print("<>Discord channel deleted!")
    else:
        return await inter.send('This command may only be used in a ticket channel')



# Event to handle DMs to the bot
@bot.event
async def on_message(message: disnake.Message):
    global MAP_INT_USERID
    if message.guild is None and not message.author.bot:
        # This is a DM
        guild = bot.get_guild(bot.guildid_global)  # Replace with your guild ID
        if guild is None:
            return

        # Create a new anonymous ticket channel + Generate a unique ticket ID
        ticket_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))

        #Add ticket id to global dict (in case power goes out) + save changes
        MAP_INT_USERID[ticket_id] = message.author.id
        save_dict_to_file(MAP_INT_USERID, folder_path+MAP_INT_USERID_FILENAME)
        

        # Create a new channel for the ticket
        channel_name = f"anonymous-ticket-{ticket_id}"
        overwrites = {
            guild.default_role: disnake.PermissionOverwrite(view_channel=False),
        }

        # Add admin roles to the overwrites
        for role in guild.roles:
            if role.permissions.administrator:
                overwrites[role] = disnake.PermissionOverwrite(view_channel=True, send_messages=True)

        ticket_channel = await guild.create_text_channel(channel_name, overwrites=overwrites)

        # Create an embed for the anonymous ticket
        embed = disnake.Embed(title="New Anonymous Ticket", description='Admins may respond to this ticket using **/respond**. Close this ticket and delete channel using **/close**. Note: The anonymous user may not send another message to this channel, since when they DM the bot they automatically create another ticket.', color=0x00ff00)
        embed.add_field(name="Message", value=message.content, inline=False)
        embed.set_footer(text="From anonymous")

        # Send the embed to the new ticket channel
        await ticket_channel.send(embed=embed)

        # Send a confirmation to the user
        await message.author.send("Your anonymous ticket has been submitted successfully! Please allow the admins time to respond to your ticket, which response you will see receive in this DM.")
        print(">Anonymous ticket submitted!")




# Run the bot with your token
bot.run(DISCORD_TOKEN)