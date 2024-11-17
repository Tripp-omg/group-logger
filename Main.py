import asyncio
import json
import requests
from datetime import datetime, timedelta
import pytz

# Constants
group_id = 34681400
limit = 10  # Set to the desired limit
sort_order = "Desc"
WEBHOOK_URLS = [
    'https://discord.com/api/webhooks/1293320270743867474/augwcixQQ6y4xWV47ubKnGHL5o_mkelQ0I6nqJCJLt3VGH_H47g8OcYOPsKOjOfvHcxg',
    'https://discord.com/api/webhooks/1292960319613702276/vBnxtbu9QtpPtJUgoHmw2Hpn2jfrY6bJOHK4rjOY2j7Z0UdiVoi4WZUimkFRVbkHz9Qw'  # Replace with your second webhook URL
]
ROBLOX_COOKIE = '_|WARNING:-DO-NOT-SHARE-THIS.--Sharing-this-will-allow-someone-to-log-in-as-you-and-to-steal-your-ROBUX-and-items.|_2C6601CCB677D4FEEBF2E3D814E44A3E3EE31DFF68B8DA23A3D53A31750ADA79F63DF05F39EDB98D128B2FFA1D84FD1104DEFE0EF10FB69B5E857A2551FF068CB787A2E0F97FECED2EB33A53A7C612CD293DA94B179B28F1B4D26C0B8DDA5F23ACFDC98CA2B35EAA9BD73E3DB671084E7744021663E53980E0EED5812F6A82ECFCD0A70893F5BFCE7DAAFD517F8FA3904F6B14D02E90E5A6B631A4403E39887B819E354970FA1C889BB3D061D5038E6358C01F910DBB275103C0B2E6896DB19EF9FDA3B676C5FA0B155B087C70D0239CED1D6F210AD51B44BB967CCD3F16999B02FA162B7D9F1C7FE1C88A855E907FDF26F037F1BA661C9A8ED4F36B02BEBD772EB1068203D639317E439E20AB99FA45EF925DD364C573F169042AAF3FE1329D36920327EDF90B9D9713944E79CA3C69ED78FE1EEDF398AAAF7C2C2F41C57D2DF07D2FECC0B6DC8DAAB46C58B9E7E8AFDD43D83B9BE0B1648CDC725BD073035195098E646F56FC0BA7A0F993E1FDD0B55BEF2489BDD10D2374C912FD7973DB3B5325ADDE1518E384DF0A2E5F62DF26F34BFBB5477C6EBDDCC8F8DC68D5454E5BCB3C28CBD7CDC378CCC9599DFD013610E28C088694B352269E8EE98F690B12161F5C15387DC46EB6FACD53B488F21CB5B4FCFD9318EA15B1B53B9B5602765FCA58B3D892B30AEE74BC5D8F92D266B4AD7D238347EDD50BCB740C2FA7C1ECB2A8EA8EB809C7395B8B9ADD9656790B73B5158F5935B50444BBF8CE4412C9FEA0547AB445F232317CD752EC8C74985EEB7EF7B3EDE5E4814690DAB6D765F850976BEA0CD017DB3E19B90A18CCD98361450CEB11154896BFC60B1B7535EA78389502D243748F27D61CDBAB67308D486AB561958307A8908F98E4801CE4034E1996A3A371EF28D959112C78D611922794C3F153901A9C9FDD37ECA1B08B2322D09EA427984CCB589C3E3E9FC3DDE8148481C4F6EEF9BD16926A8C931809EADE26DB5BF138FBF6B60DA4587E3B8B98807B19A257FFA701FF4DC3AB0462150B5F664B390A9CBA89890F7711C32052A6BB2735DB66251619C5056464A18056B6541969DF0F943064C402FD1B25E1EE012B88FCA434266679'  # Place your cookie here
cookie = ROBLOX_COOKIE

# State Variables
last_seen_log_timestamp = None  # Store the timestamp of the last seen log
desired_username = "TrippomgApi"
desired_rank_id = 111240490  # Replace with the actual desired rank ID
desired_rank_name = "."
notification_spam = False
incorrect_username = False

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
        "content": "Starting KC GROUP logger"
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
        notify_discord(f"<@1145012840533610556> <@&1293321707691704401> The bot has been exiled ( KC GROUP )! An ongoing nuke is likely happening!")
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
        "color": 7506394,  # Example color: cyan
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

