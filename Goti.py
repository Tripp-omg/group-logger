import asyncio
import json
import requests
from datetime import datetime, timedelta
import pytz



# Track last time ROBLOX was reported down
last_roblox_down_notification_time = None
roblox_down_cooldown = timedelta(hours=1)

# Track recent declines for bulk notifications
recent_declines = []
bulk_decline_threshold = 5  # Number of declines before bulk notification

# FUNCTIONS FOR ENSURING BOT HASN'T BEEN MESSED WITH
def get_membership_info():
    session = requests.Session()
    session.cookies.set(".ROBLOSECURITY", cookie)

    try:
        url = f"https://groups.roblox.com/v1/groups/{group_id}/membership?includeNotificationPreferences=true"
        r = session.get(url)

        if r.status_code == 200:
            return r.json()
        else:
            print(f"Couldn't fetch membership info ({r.status_code} : {r.reason})")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching membership info: {e}")
        return None

def get_authenticated_user():
    session = requests.Session()
    session.cookies.set(".ROBLOSECURITY", cookie)

    try:
        response = session.get("https://users.roblox.com/v1/users/authenticated")

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            global cookiegood
            cookiegood = False
        else:
            print(f"Error: {response.status_code} - {response.reason}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching authenticated user: {e}")
        return None

async def check_bot_rank():
    global notification_spam
    while True:
        membership_info = get_membership_info()
        if membership_info:
            current_username = membership_info['userRole']['user']['displayName']
            current_rank_id = membership_info['userRole']['role']['id']
            current_rank_name = membership_info['userRole']['role']['name']

            # Check if the bot is exiled (rank is Guest)
            if current_rank_name == "Guest":
                print("Bot has been exiled (rank is Guest), notifying.")
                await spam_exiled_notification()  # Call the spam function
            elif (current_username != desired_username or
                  current_rank_id != desired_rank_id or
                  current_rank_name != desired_rank_name):
                notification_spam = True
                print("Bot's rank is incorrect, notifying.")
                notify_discord(f"<@1145012840533610556> The bot's rank is incorrect! Current: {current_rank_name}, Expected: {desired_rank_name}")
            else:
                notification_spam = False  # Reset if everything is correct

        await asyncio.sleep(300)  # Check every 5 minutes

async def check_authenticated_user():
    global incorrect_username
    session = requests.Session()
    session.cookies.set(".ROBLOSECURITY", cookie)

    while True:
        response = session.get("https://users.roblox.com/v1/users/authenticated")

        if response.status_code == 200:
            user_info = response.json()
            current_username = user_info['name']
            if current_username != desired_username:
                incorrect_username = True
                print("Authenticated user is incorrect, notifying.")
                notify_discord(f"<@1145012840533610556> The authenticated user is incorrect! Current: {current_username}, Expected: {desired_username}")
            else:
                incorrect_username = False  # Reset if everything is correct
        elif response.status_code == 401:
            incorrect_username = True
            print("Authenticated user is not logged in, notifying.")
            notify_discord(f"<@1145012840533610556> The bot's cookie has expired!")
        await asyncio.sleep(300)  # Check every 5 minutes

## DISCORD MESSAGES 
def notify_discord(message):
    content = {
        "content": message
    }
    for webhook_url in WEBHOOK_URLS:
        requests.post(webhook_url, data=json.dumps(content), headers={'Content-Type': 'application/json'})

def send_to_discord(embed):
    content = {
        "embeds": [embed]
    }
    for webhook_url in WEBHOOK_URLS:
        requests.post(webhook_url, data=json.dumps(content), headers={'Content-Type': 'application/json'})

def notify_roblox_down():
    global last_roblox_down_notification_time
    now = datetime.now()

    if last_roblox_down_notification_time is None or (now - last_roblox_down_notification_time) >= roblox_down_cooldown:
        embed_content = {
            "title": "ROBLOX IS DOWN",
            "description": "**LOGGING WILL NOT WORK AS NORMAL TIL API IS BACK TO NORMAL**",
            "color": 16711680,  # Red color for visibility
        }
        send_to_discord(embed_content)
        last_roblox_down_notification_time = now  # Update last notification time

def send_startup_message():
    startup_message = {
        "content": "Starting GOTI GROUP logger"
    }
    for webhook_url in WEBHOOK_URLS:
        requests.post(webhook_url, data=json.dumps(startup_message), headers={'Content-Type': 'application/json'})

async def spam_notification():
    while True:
        if notification_spam:
            notify_discord(f"<@1145012840533610556> The bot's rank is still incorrect!")
        await asyncio.sleep(60)  # Spam every minute if there's an issue

async def spam_dev():
    while True:
        if incorrect_username:
            notify_discord(f"<@1145012840533610556> The bot's cookie has expired!")
        await asyncio.sleep(60)  # Check every minute

async def spam_exiled_notification():
    """Spams a notification if the bot is exiled."""
    while True:
        notify_discord(f"<@1145012840533610556> <@&1293321707691704401> The bot has been exiled ( Goti group )! An ongoing nuke is likely happening!")
        await asyncio.sleep(60)  # Spam every 60 seconds

## FORMATTING
def format_time(timestamp):
    """Convert UTC timestamp to EST in 12-hour format."""
    utc_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))  # Convert to datetime
    est_timezone = pytz.timezone('America/New_York')  # EST timezone
    est_time = utc_time.astimezone(est_timezone)  # Convert to EST
    return est_time.strftime("%Y-%m-%d %I:%M:%S %p")  # Format in 12-hour format

def format_log(log):
    global recent_declines
    timestamp = log['created']
    formatted_time = format_time(timestamp)  # Convert to EST
    action = log['actionType']
    user = log['actor']['user']['displayName']
    user_id = log['actor']['user']['userId']
    roblox_profile_url = f"https://www.roblox.com/users/{user_id}/profile"

    embed_content = {
        "title": "New Log Detected!",
        "color": int("575656", 16),  # Example color: cyan
        "fields": [],
        "footer": {
            "text": "The time for logs is in EST."
        }
    }

    if action == "Post Status":
        message = log['description']['Text']
        embed_content['fields'].append({
            "name": "Log Details",
            "value": f"**Action:** {action}\n**User:** [{user}]({roblox_profile_url}) (ID: {user_id})\n**Time:** {formatted_time}\n**Shout Message:** {message}",
            "inline": False
        })

    elif action == "Change Rank":
        target_user = log['description']['TargetName']
        old_rank = log['description']['OldRoleSetName']
        new_rank = log['description']['NewRoleSetName']
        embed_content['fields'].append({
            "name": "Log Details",
            "value": f"**Action:** {action}\n**User:** [{user}]({roblox_profile_url}) (ID: {user_id})\n**Time:** {formatted_time}\n**Target User:** {target_user}\n**Old Rank:** {old_rank}\n**New Rank:** {new_rank}",
            "inline": False
        })

    elif action == "Accept Join Request":
        target_user = log['description']['TargetName']
        embed_content['fields'].append({
            "name": "Log Details",
            "value": f"**Action:** {action}\n**User:** [{user}]({roblox_profile_url}) (ID: {user_id})\n**Time:** {formatted_time}\n**Accepted User:** {target_user}",
            "inline": False
        })

    elif action == "Remove Member":
        target_user = log['description']['TargetName']
        embed_content['fields'].append({
            "name": "Log Details",
            "value": f"**Action:** {action}\n**User:** [{user}]({roblox_profile_url}) (ID: {user_id})\n**Time:** {formatted_time}\n**Exiled User:** {target_user}",
            "inline": False
        })
    
    elif action == "Decline Join Request":  # New case for declined members
        target_user = log['description']['TargetName']
        recent_declines.append(target_user)  # Track recent declines
        embed_content['fields'].append({
            "name": "Log Details",
            "value": f"**Action:** {action}\n**User:** [{user}]({roblox_profile_url}) (ID: {user_id})\n**Time:** {formatted_time}\n**Declined User:** {target_user}",
            "inline": False
        })
        # Send bulk notification if threshold is reached
        if len(recent_declines) >= bulk_decline_threshold:
            notify_discord(f"<@1145012840533610556> There have been multiple declines: {', '.join(recent_declines)}")
            recent_declines.clear()  # Clear the list after notification

    return embed_content

## Audit Log check
def get_audit_log():
    session = requests.Session()
    session.cookies.set(".ROBLOSECURITY", cookie)

    try:
        url = f"https://groups.roblox.com/v1/groups/{group_id}/audit-log"
        params = {
            "limit": limit,
            "sortOrder": sort_order
        }

        r = session.get(url, params=params)

        if r.status_code == 200:
            return r.json()
        else:
            print(f"Couldn't fetch Audit Log ({r.status_code} : {r.reason})")
            notify_roblox_down()  # Notify if Roblox is down
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching audit log: {e}")
        notify_roblox_down()  # Notify if there's a request exception
        return None

## main
async def main():
    global last_seen_log_timestamp
    send_startup_message()

    # Start the bot rank check and authenticated user check in the background
    asyncio.create_task(check_bot_rank())
    asyncio.create_task(spam_notification())
    asyncio.create_task(check_authenticated_user())
    asyncio.create_task(spam_dev())  # Start spam_dev as well

    # Initial fetch to process logs but not send to Discord
    logs = get_audit_log()
    if isinstance(logs, dict) and 'data' in logs:
        logs['data'].reverse()  # Reverse to process older logs first
        if logs['data']:
            last_seen_log_timestamp = logs['data'][-1]['created']  # Set the last seen log timestamp from the most recent log

    while True:
        await asyncio.sleep(60)  # Check every minute
        new_logs = get_audit_log()

        if isinstance(new_logs, dict) and 'data' in new_logs:
            new_logs['data'].reverse()  # Reverse to process older logs first
            timestamp_groups = {}  # Dictionary to group logs by their timestamps

            for log in new_logs['data']:
                if log['created'] <= last_seen_log_timestamp:
                    continue  # Skip logs that have already been processed
                
                # Group logs by their timestamps
                timestamp = log['created']
                if timestamp not in timestamp_groups:
                    timestamp_groups[timestamp] = []
                timestamp_groups[timestamp].append(log)

            # Process each group of logs
            for timestamp, logs in timestamp_groups.items():
                for log in logs:
                    formatted_embed = format_log(log)
                    send_to_discord(formatted_embed)  # Send each log's details
                last_seen_log_timestamp = timestamp  # Update to the most recent log timestamp

# Run the bot
asyncio.run(main())

