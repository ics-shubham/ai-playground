

### This is documentation for the twilio sip trunking set up, below mentioned steps will be taken in order to achieve  configuration successfully.

# For Inbound calls

### 📦 Prerequisites
- ##### Twilio Account
- ##### LiveKit Account
- ##### API Keys for:
  - ##### Deepgram (DEEPGRAM_API_KEY)
  - ##### OpenAI (OPENAI_API_KEY)
  - ##### Cartesia (CARTESIA_API_KEY)


## Install twilio cli

### Using apt 

      wget -qO- https://twilio-cli-prod.s3.amazonaws.com/twilio_pub.asc \
        | sudo apt-key add -
      sudo touch /etc/apt/sources.list.d/twilio.list
      echo 'deb https://twilio-cli-prod.s3.amazonaws.com/apt/ /' \
        | sudo tee /etc/apt/sources.list.d/twilio.list
      sudo apt update
      sudo apt install -y twilio

## Now in order to use twilio cli
- Create an account in twilio (Skip this step in case you already have an account)
- buy a number run:

    ```
    twilio login
    
### Create a SIP trunk using twilio cli
  #### Make sure domain name of your SIP trunk must end with (pstn.twilio.com) 

        twilio api trunking v1 trunks create \
        --friendly-name "My test trunk" \
        --domain-name "my-test-trunk.pstn.twilio.com"

### After running above command you will recieve TWILIO-TRUNK-ID , Copy your TWILIO-TRUNK-ID and save it

## Now you have to configure your trunk for inbound calls:

#### Configure an origination URI AKA your SIP host
Go to liveKit. Create an account in case you dont have one.
Navigate to Setting and Copy your SIP-URI

    twilio api trunking v1 trunks origination-urls create \
        --trunk-sid <TWILIO-TRUNK-ID> \
        --friendly-name "LiveKit SIP URI" \
        --sip-url <SIP-URI> \
        --weight 1 --priority 1 --enabled

## Associate phone Number and trunk
#### For this you need Twilio-Trunk-SID and Twilio-Phone-Number-SID If you have them saved than you can use them else you can get them  by following ways. 
  - To list phone numbers:
 
        twilio phone-numbers list
    
  - To list trunks:

        twilio api trunking v1 trunks list
    

##### Then to associate both
    twilio api trunking v1 trunks phone-numbers create \
    --trunk-sid <twilio_trunk_sid> \
    --phone-number-sid <twilio_phone_number_sid>

#### OR Configure a SIP trunk using the TWILIO UI
- Search Elastic SIP OR 
- Select Elastic SIP Trunking >> Manage >> Trunks.
- Create SIP trunk.

#### For Inbound SIP
- Navigate to Voice >> Manage >> Origination connection policy.
- Select created origination policy.
- Add the SIP-URI, weight, and priority as was done earlier during trunk configuration via the CLI.

#### Livekit cli set up
   Install livekit cli

#### Linux :
    curl -sSL https://get.livekit.io/cli | bash

#### Optionally authentication with cloud
- This is in order to avoid adding api-key and api-secret in each request manually

        lk cloud auth

- You'll be prompted to set the current project as default, select Yes. This can be changed later by editing the config.yaml file (the path to which will be logged after running the above commands)

#### Create inbound trunk using inbound-trunk.json , make sure to update numbers in inbound-trunk.json :
      lk sip inbound create inbound-trunk.json

#### Create dispatcher rule 
- As atleast one is required to accept incoming calls into livekit rooms:

      lk sip dispatch create dispatch-rule.json

#### Installing Dependencies for AI Agent


      pip install \
        "livekit-agents[deepgram,openai,cartesia,silero,turn-detector]~=1.0" \
        "livekit-plugins-noise-cancellation~=0.2" \
        "python-dotenv"

#### Your agent strings together three specialized providers into a high-performance voice pipeline. You need accounts and API keys for each.

- Deepgram  , DEEPGRAM_API_KEY
- OpenAI , OPENAI_API_KEY
- Cartesia , CARTESIA_API_KEY


#### Download model files
##### To use the turn-detector, silero, or noise-cancellation plugins, you first need to download the model files:

      python main.py download-files

#### Speak to your agent
##### Start your agent in console mode to run inside your terminal:

      python main.py console

#### Connect to playground
##### Start your agent in **dev** mode to connect it to LiveKit and make it available from anywhere on the internet:

      python main.py dev

#### Now test connection from twilio UI

Select Elastic SIP trunk >> select Your trunk >> Origination >> Make test call.

You will be able to see session being created with livekit on your dev terminal.
