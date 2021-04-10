# imports
# standard library imports
import asyncio
import io
import json
import random
import re
import string
import time

# third-part imports
import discord
import nacl
import psycopg2
import requests
from discord.ext import commands
from PIL import Image, ImageDraw, ImageEnhance, ImageFont
from pretty_help import PrettyHelp
from discord_slash import SlashCommand


def rounded_rectangle(self: ImageDraw, xy, corner_radius, fill=None, outline=None):
    upper_left_point = xy[0]
    bottom_right_point = xy[1]
    self.rectangle(
        [
            (upper_left_point[0], upper_left_point[1] + corner_radius),
            (bottom_right_point[0], bottom_right_point[1] - corner_radius),
        ],
        fill=fill,
        outline=outline,
    )
    self.rectangle(
        [
            (upper_left_point[0] + corner_radius, upper_left_point[1]),
            (bottom_right_point[0] - corner_radius, bottom_right_point[1]),
        ],
        fill=fill,
        outline=outline,
    )
    self.pieslice(
        [
            upper_left_point,
            (
                upper_left_point[0] + corner_radius * 2,
                upper_left_point[1] + corner_radius * 2,
            ),
        ],
        180,
        270,
        fill=fill,
        outline=outline,
    )
    self.pieslice(
        [
            (
                bottom_right_point[0] - corner_radius * 2,
                bottom_right_point[1] - corner_radius * 2,
            ),
            bottom_right_point,
        ],
        0,
        90,
        fill=fill,
        outline=outline,
    )
    self.pieslice(
        [
            (upper_left_point[0], bottom_right_point[1] - corner_radius * 2),
            (upper_left_point[0] + corner_radius * 2, bottom_right_point[1]),
        ],
        90,
        180,
        fill=fill,
        outline=outline,
    )
    self.pieslice(
        [
            (bottom_right_point[0] - corner_radius * 2, upper_left_point[1]),
            (bottom_right_point[0], upper_left_point[1] + corner_radius * 2),
        ],
        270,
        360,
        fill=fill,
        outline=outline,
    )


ImageDraw.rounded_rectangle = rounded_rectangle


def draw(icon, xp, level, name, avt_size=1, avatar_x=600, avatar_y=745):
    image = (
        ImageEnhance.Brightness(
            Image.open(
                io.BytesIO(
                    requests.get(
                        # "http://picsum.photos/5000/1500?grayscale&&blur=4"
                        "https://picsum.photos/id/1045/5000/1500?blur=5"
                    ).content
                )
            )
        )
        .enhance(0.5)
        .convert("RGB")
    )
    draw = ImageDraw.Draw(image)
    draw.ellipse(
        (
            avatar_x - 445 * avt_size - 50,
            avatar_y - 445 * avt_size - 50,
            avatar_x + 445 * avt_size + 50,
            avatar_y + 445 * avt_size + 50,
        ),
        (0, 0, 0),
    )
    mask = Image.new("L", image.size)
    draw = ImageDraw.Draw(mask)
    draw.ellipse(
        (
            int(avatar_x - 445 * avt_size),
            int(avatar_y - 445 * avt_size),
            int(avatar_x + 445 * avt_size),
            int(avatar_y + 445 * avt_size),
        ),
        255,
    )
    pasted = Image.new("RGB", image.size)
    avatar = Image.open(io.BytesIO(requests.get(icon).content)).resize(
        (int(890 * avt_size), int(890 * avt_size))
    )
    pasted.paste(
        avatar, (int(avatar_x - 445 * avt_size),
                 int(avatar_y - 445 * avt_size))
    )
    composite = Image.composite(pasted, image, mask)
    draw = ImageDraw.Draw(composite)
    rounded_rectangle(draw, ((1150, 1150), (4850, 1350)), 100, (255, 255, 255))
    rounded_rectangle(
        draw, ((1200, 1200), (1300 + (4700 - 1200)
                              * xp / 100, 1300)), 50, (0, 0, 0)
    )

    try:
        draw.text(
            (1200, 100),
            name,
            font=ImageFont.truetype("Arial", 400),
            fill=(255, 255, 255),
        )
        draw.text(
            (1200, 600),
            f"lvl #{level}, {xp} xp",
            font=ImageFont.truetype("Arial", 300),
            fill=(255, 255, 255),
        )
    except OSError:
        draw.text(
            (1200, 100),
            name,
            font=ImageFont.truetype("arial.ttf", 400),
            fill=(255, 255, 255),
        )
        draw.text(
            (1200, 600),
            f"lvl #{level}, {xp} xp",
            font=ImageFont.truetype("arial.ttf", 300),
            fill=(255, 255, 255),
        )

    result = composite.resize((500, 150), Image.ANTIALIAS)

    return result


conn = psycopg2.connect(user="",
                        password="",
                        host="",
                        port="",
                        database=""
                        )

cursor = conn.cursor()

cursor.execute(
    "CREATE TABLE IF NOT EXISTS list (server_id text, user_id text, xp integer, lvl integer)"
)


# add user
def add_user(server_id, user_id, xp, level):
    command = f"INSERT INTO list VALUES ('{server_id}','{user_id}','{xp}','{level}')"
    cursor.execute(command)
    conn.commit()
    print(
        f"Added User with id '{user_id}' from server with id '{server_id}' with {xp}xp and {level}level")


# set xp for a user
def set_xp(server_id, user_id, xp):
    command = "SELECT * FROM list"
    cursor.execute(command)

    command = f"UPDATE list SET xp = {xp} WHERE user_id = '{user_id}' AND server_id = '{server_id}'"
    cursor.execute(command)
    conn.commit()
    print(f"XP set to '{user_id}' in '{server_id}' to {xp}")


# set level for user
def set_lvl(server_id, user_id, lvl, calc_lvl):
    command = "SELECT * FROM list"
    conn.commit()
    cursor.execute(command)

    command = f"UPDATE list SET lvl = {lvl} WHERE user_id = '{user_id}' AND server_id = '{server_id}'"
    conn.commit()
    cursor.execute(command)
    conn.commit()
    print(f"Level set to {user_id} in {server_id} to {lvl}")

    if calc_lvl >= 1:
        command = f"UPDATE list SET xp = 0 WHERE user_id = '{user_id}' AND server_id = '{server_id}'"
        conn.commit()
        cursor.execute(command)
        conn.commit()
        print(f"XP set to '{user_id}' in '{server_id}' to 0")


# get info about xp for a user
def get_xp_info(server_id, user_id):
    command = f"SELECT * FROM list WHERE user_id = '{user_id}' AND server_id = '{server_id}'"
    conn.commit()
    cursor.execute(command)
    info = cursor.fetchall()
    infos = []
    for item in info:
        for i in item:
            infos.append(i)
    try:
        infos = infos[2]
    except IndexError:
        return 'e'
    print(infos)
    return infos


# get info about lvl for a user
def get_lvl_info(server_id, user_id):
    conn.commit()
    command = f"SELECT * FROM list WHERE user_id = '{user_id}' AND server_id = '{server_id}'"
    cursor.execute(command)
    info = cursor.fetchall()
    print(info)
    return info


# get all info
def get_all(server_id):
    command = f"SELECT * FROM list WHERE server_id = '{server_id}'"
    conn.commit()
    cursor.execute(command)
    info = cursor.fetchall()
    return info


# get all info no server_id
def get_all_no_server():
    command = f"SELECT * FROM list"
    conn.commit()
    cursor.execute(command)
    infos = cursor.fetchall()
    return infos


client = discord.Client(intents=discord.Intents.all())
slash = SlashCommand(client, sync_commands=True) 

guild_ids = [802032452109467658, 812355361473691658, 789171959858462731]

@client.event
async def on_ready():
    print("Slasher Ready!")

# avatar
@slash.slash(name="mypfp", description="Displays your pfp", guild_ids=guild_ids)
async def pfp(ctx):

    embed = discord.Embed(
        title=f"Avatar of {ctx.author.display_name}",
        color=discord.Color.teal()
    ).set_image(url=ctx.author.avatar_url)

    await ctx.send(embed=embed)

# help-needed-dev
@slash.slash(name="dev-help", description='Get help from an active programmer', guild_ids=guild_ids)
async def dev_h(ctx):
    basic = discord.utils.get(ctx.guild.roles, name="Puppy")
    medium = discord.utils.get(ctx.guild.roles, name="Woof")
    loud = discord.utils.get(ctx.guild.roles, name="Loud Woof")
    programmer = discord.utils.get(ctx.guild.roles, name="Programmer")

    members_basic = []
    members_medium = []
    members_loud = []

    active_members_list = []

    for member in ctx.guild.members:
        if loud in member.roles:
            members_loud.append(member)

        elif basic in member.roles:
            members_basic.append(member)

        elif medium in member.roles:
            members_medium.append(member)

    for mem in members_loud:
        if programmer in mem.roles:
            active_members_list.append(mem)
    for mem in members_medium:
        if programmer in mem.roles:
            active_members_list.append(mem)

    if active_members_list == []:
        for mem in members_basic:
            if programmer in mem.roles:
                active_members_list.append(mem)
    try:
        choosen_dev = random.choice(active_members_list)
        await ctx.send(f'Hey {choosen_dev.mention} {ctx.author.mention} needs dev help!')
    except IndexError:
        await ctx.send('No active members :frowning:')

# poll command
@ slash.slash(name="poll", description="Create a poll", guild_ids=guild_ids)
async def poll(ctx, title: str, *, o_r_in):
    embed = discord.Embed(title=title)

    t_l = o_r_in.split(";")

    for item in t_l:
        stuff = item.split()
        option = stuff[0]
        reaction = stuff[1]
        embed.add_field(name=option, value=f'- {reaction}')

    msg = await ctx.send(embed=embed)

    for item in t_l:
        stuff = item.split()
        reaction = stuff[1]
        await msg.add_reaction(reaction)

# Display level and Xp of a user in a server
@ slash.slash(name="lvl", description="Display your level and xp", guild_ids=guild_ids)
async def lvl(ctx, user: discord.Member):
    await ctx.defer()
    xp = get_xp_info(ctx.guild.id, user.id)
    lvl_in = get_lvl_info(ctx.guild.id, user.id)
    lvl = []

    for i in lvl_in:
        for item in i:
            lvl.append(item)

    lvl = lvl[3]

    if xp == 'e':
        ctx.send("Chat before you can get levels.")

    # embed = discord.Embed(
    #     title=f"Level and xp information about {ctx.author.display_name}"
    # )
    # value_xp_rem = ":white_large_square:" * int(10 - int((xp / 100)))
    # value_xp_emoji_in = ":blue_square:" * int((xp / 100))
    # value_xp_emoji = "*" + str(value_xp_emoji_in) + str(value_xp_rem) + "*"
    #
    # embed.add_field(name="XP", value=xp, inline=True)
    # embed.add_field(name="Level", value=f"**{lvl}**")
    # embed.add_field(name="Progress Bar", value=value_xp_emoji)

    img = draw(str(user.avatar_url), xp,
                lvl, str(user.display_name))

    arr = io.BytesIO()
    img.save(arr, format='PNG')
    arr.seek(0)
    file = discord.File(
        arr, filename=f"rank requested by {ctx.author.display_name!r}.png")
    await ctx.send(file=file)
    # await ctx.send(embed=embed)

# Create simple react command
@ slash.slash(name="react", description="Add a reaction to a given message id if possible", guild_ids=guild_ids)
async def react(ctx, message_given=0, reaction=""):
    await ctx.send("This command does not work with slash interactions as of now. Please try using `$react`")

# server info
@ slash.slash(name="sinf", description="Displays server info", guild_ids=guild_ids)
async def sinf(ctx):
    embed = discord.Embed(title="Server Info",
                        color=discord.Color.teal())

    info_title = [
        "Server Name",
        "Server ID",
        "Server Owner",
        "Member Count",
        "Channel Count",
        "Role Count",
        "Region",
    ]

    infos = [
        str(ctx.guild.name),
        str(ctx.guild.id),
        str(ctx.guild.owner),
        str(len(ctx.guild.members)),
        f"{len(ctx.guild.channels)} \n _includes categories and staff channels_",
        str(len(ctx.guild.roles)),
        str(ctx.guild.region),
    ]

    i = 0
    for i in range(len(infos)):
        embed.add_field(name=info_title[i], value=infos[i])

    embed.set_thumbnail(url=ctx.guild.icon_url)

    await ctx.send(embed=embed)


client.run("ODAzMzA5ODM0MjkxMzgwMjc1.YA76lQ.KnVsTO3zdY-u36Hkv_LvslNLPDs")