#!/usr/bin/python3

'''
Reece Williams (Reecepbcups | PBCUPS Validator)
February 9th, 2022
- Twitter bot to monitor and report on COSMOS governance proposals

apt install pip
pip install requests tweepy schedule

*Get REST lcd's in chain.json from https://github.com/cosmos/chain-registry
'''

import tweepy
import requests
import os
import schedule
import time

IN_PRODUCTION = True

chainAPIs = {
    "dig": 
        [ 
        'https://api-1-dig.notional.ventures/cosmos/gov/v1beta1/proposals',
        'https://ping.pub/dig/gov'
        ],
    'juno': [
        'https://lcd-juno.itastakers.com/cosmos/gov/v1beta1/proposals',
        'https://ping.pub/juno/gov'
        ],
    'huahua': [
        'https://api.chihuahua.wtf/cosmos/gov/v1beta1/proposals',
        'https://ping.pub/chihuahua/gov'
        ],
    'osmo': [
        'https://lcd-osmosis.blockapsis.com/cosmos/gov/v1beta1/proposals',
        'https://ping.pub/osmosis/gov'
        ],
    'atom': [
        'https://lcd-cosmoshub.blockapsis.com/cosmos/gov/v1beta1/proposals',
        'https://ping.pub/cosmos/gov'
        ],
    'akt': [
        'https://akash.api.ping.pub/cosmos/gov/v1beta1/proposals',
        'https://ping.pub/akash-network/gov'
        ],
    'stars': [
        "https://rest.stargaze-apis.com/cosmos/gov/v1beta1/proposals",
        'https://ping.pub/stargaze/gov'
        ],
    'kava': [
        'https://api.data.kava.io/cosmos/gov/v1beta1/proposals',
        'https://ping.pub/kava/gov'
        ],
    'like': [
        'https://mainnet-node.like.co/cosmos/gov/v1beta1/proposals',
        'https://ping.pub/likecoin/gov'
        ],
    'xprt': [
        'https://rest.core.persistence.one/cosmos/gov/v1beta1/proposals',
        'https://ping.pub/persistence/gov'
        ],
    'cmdx': [
        'https://rest.comdex.one/cosmos/gov/v1beta1/proposals',
        'https://ping.pub/comdex/gov'
        ],
}


with open("secrets.prop", "r") as f:
    secrets = f.read().splitlines()
    APIKEY = secrets[0]
    APIKEYSECRET = secrets[1]
    ACCESS_TOKEN = secrets[2]
    ACCESS_TOKEN_SECRET = secrets[3]
    f.close()

# Authenticate to Twitter & Get API
auth = tweepy.OAuth1UserHandler(APIKEY, APIKEYSECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth, wait_on_rate_limit=True)


def tweet(ticker, propID, title, voteEndTime=""):
    message = f"${str(ticker).upper()} | Proposal #{propID} | VOTING_PERIOD | {title} | {chainAPIs[ticker][1]}/{propID}"
    print(message)

    if IN_PRODUCTION:
        try:
            tweet = api.update_status(message)
            print(f"Tweet sent for {tweet.id}: {message}")
            # api.update_status(in_reply_to_status_id=tweet.id, status=f"Voting Ends: {voteEndTime}")
        except:
            print("Tweet failed due to being duplicate")
        

def betterTimeFormat(ISO8061) -> str:
    # Improve in future to be Jan-01-2022
    return ISO8061.replace("T", " ").split(".")[0]

def getAllProposals(ticker) -> list:
    # Makes request to API & gets JSON reply in form of a list
    props = []
    
    try:
        link = chainAPIs[ticker][0]
        response = requests.get(link, headers={
            'accept': 'application/json', 
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36'}, 
            params={'proposal_status': '2'})
        # print(response.url)
        props = response.json()['proposals']
    except Exception as e:
        print(f"Issue with request to {ticker}: {e}")
    return props

def getLatestProposalIDChecked(ticker, fileName) -> int:
    # returns the last proposal ID we checked, or 0 if none tweeted yet
    lastPropID = 0

    # open text file (means we have already tweeted about this chain)
    if os.path.exists(fileName):
        with open(fileName, "r") as f:
            # update to last checked proposal ID
            lastPropID = int(f.read())
            f.close()
            
    print(f"{ticker} last voting prop id: {lastPropID}")

    return lastPropID

def checkIfNewestProposalIDIsGreaterThanLastTweet(ticker):
    fileName = f"{ticker}.txt"

    # get our last tweeted proposal ID (that was in voting period), found in file
    lastPropID = getLatestProposalIDChecked(ticker, fileName)

    # gets JSON list of all proposals
    props = getAllProposals(ticker)

    if len(props) == 0:
        return

    # loop through out last stored voted prop ID & newest proposal ID
    for prop in props:
        current_prop_id = int(prop['proposal_id'])

        # If this is a new proposal which is not the last one we tweeted for
        if current_prop_id > lastPropID:   
            print(f"Newest prop ID {current_prop_id} is greater than last prop ID {lastPropID}")

            # save newest prop ID to file so we don't double tweet it
            if IN_PRODUCTION:
                with open(fileName, "w") as f:
                    f.write(str(current_prop_id))
                    f.close()
            else:
                print("Not in production, not writing to file.")
                    
            # Tweet that bitch
            tweet(
                ticker=ticker,
                propID=current_prop_id, 
                title=prop['content']['title'], 
                # votePeriodEnd=betterTimeFormat(prop['voting_end_time'])
            )


def runChecks():
    for chain in chainAPIs.keys():
        try:
            checkIfNewestProposalIDIsGreaterThanLastTweet(chain)
        except Exception as e:
            print(f"{chain} checkProp failed: {e}")
            
    print("All chains checked, waiting")


SCHEDULE_SECONDS = 1 # 1 second for testing
output = "Bot is in test mode..."

if IN_PRODUCTION:  
    SCHEDULE_SECONDS = 20*60
    output = "[!] BOT IS RUNNING IN PRODUCTION MODE!!!!!!!!!!!!!!!!!!"
    print(output)
    time.sleep(5) # Extra wait to ensure we want to run
    runChecks() # Runs 1st time to update, then does runnable


print(output)
schedule.every(SCHEDULE_SECONDS).seconds.do(runChecks)    
while True:
    schedule.run_pending()
    time.sleep(SCHEDULE_SECONDS)