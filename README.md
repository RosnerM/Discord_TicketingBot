# Ticketing bot for Discord

## Description
This discord bot allows the users of a discord server (250,000+ users) to send anonymous/non-anonymous complaint tickets to a discord server's admins. The ticket will create a private text channel for the user and admins to resolve/discuss the issue (other users will not be able to see this channel). The admins can also respond anonymously. Tickets are stored in a JSON dataset.

## Requirements
1. You must register a discord developer account on https://discord.com/developers/ and make a 'New Application'
2. You must create a **.env** file with the following variables for this program to work:
```
DISCORD_TOKEN= <YOUR_TOKEN_HERE>
GUILD_ID= <YOUR_GUILD_ID_HERE> 
ROLE_ID= <ADMIN_ROLE_ID>
```
3. You must have Docker or Docker Desktop (Windows, Linux or Mac)

## Installation
```
git clone https://github.com/RosnerM/Discord_TicketingBot.git
cd Discord_TicketingBot/
docker compose build
docker compose up -d
```


## List of commands:

- Send a DM to this bot - (user) allows a discord user to create a ANONYMOUS ticket with the message that was sent to this bot, which will be analyzed by the admins
- /ticket 'msg' - (user) allows a discord user to create a ticket with 'msg' as the reason
- /respond - (admin) allows admin to respond to a ticket
- /close - (admin) close a ticket. This deletes the channel it was invoked in after 5 seconds