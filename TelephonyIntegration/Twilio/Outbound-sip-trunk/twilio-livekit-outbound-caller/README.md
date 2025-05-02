# 📞 Twilio–LiveKit Outbound SIP Trunk Voice Agent

In this article, I’ll walk you through how to build an AI-powered outbound voice agent that can call patients, confirm appointments, and transfer calls to a human agent-all using Twilio, LiveKit, and modern AI tools. This project is perfect for automating appointment confirmations in healthcare, but the architecture is flexible enough for many outbound calling scenarios.

# **Key Features**

- **Automated Outbound Calling**: The agent dials patients using Twilio’s SIP trunk.
- **Conversational AI**: Uses GPT-4o for natural, context-aware dialogue.
- **Speech Recognition & Synthesis**: Integrates Deepgram for speech-to-text and Cartesia for text-to-speech.
- **Call Transfers**: Seamlessly hands off to a human agent when needed.
- **Appointment Management**: Confirms, reschedules, or cancels appointments by voice.

---

## 📥 Download the Project

Run the following commands:

```bash
# Clone the repository:
git clone https://github.com/ICubeSystems/ai-playground.git
# Change directory to `twilio-livekit-outbound-caller`:
cd TelephonyIntegration/Twilio/Outbound-sip-trunk/twilio-livekit-outbound-caller/twilio-livekit-outbound-caller
```

(Optional) Create and activate a virtual environment:

```bash
python -m venv lkvenv

# For Linux/macOS:
source lkvenv/bin/activate

# For Windows:
lkvenv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Download additional files:

```bash
python agent.py download-files
```

---

## ☎️ Create Twilio SIP Outbound Trunk

1. Create a [Twilio](https://www.twilio.com/) account if you haven't already.
2. Get a Twilio phone number.
3. In the Twilio Console:
   - Navigate to **Elastic SIP Trunking > Manage > Trunks > Create a SIP Trunk**
   - Enter a trunk name and save.

4. Configure SIP Termination:
   - Go to Termination, Set a unique **Termination SIP URI** 
   - Select the plus(+) icon for **Credential Lists**, Provide a friendly name, username and password and save

---

## 🔧 Create LiveKit SIP Outbound Trunk

1. Copy and rename `outbound-trunk-example.json` to `outbound-trunk.json`, then update it with your SIP credentials.

```bash
cp outbound-trunk-example.json outbound-trunk.json
```

   **Field Descriptions:**
   - `name`: Friendly name (Can be anything)
   - `address`: Twilio Termination SIP URI
   - `numbers`: Your Twilio number(s)
   - `auth_username`: Your username created in previous step in Twilio console.
   - `auth_password`: Your password created in previous step in Twilio console.

2. **Install LiveKit CLI if you haven't already**

- **Windows**:
  ```bash
  winget install LiveKit.LiveKitCLI
  ```
- **Linux**:
  ```bash
  curl -sSL https://get.livekit.io/cli | bash
  ```
- **macOS**:
  ```bash
  brew update && brew install livekit-cli
  ```

3. **Register the Trunk with LiveKit**

✅ If you have a global LiveKit CLI config set:
```bash
lk sip outbound create outbound-trunk.json
```

If you're not using a global Livekit CLI config, provide your credentials inline:
- Generate your API keys: [livekit](https://docs.livekit.io/home/cloud/keys-and-tokens/) 
- Then add keys and run:
```bash
lk --api-key <api-key> --api-secret <api-secret> --url <url> sip outbound create outbound-trunk.json
```

Save the returned `SIPTrunkID` — it will be required later.

---

## ⚙️ Environment Configuration

Copy the env template and fill in your values:

```bash
cp .env.example .env.local
```

Update the following in `.env.local`:

- `LIVEKIT_URL`
- `LIVEKIT_API_KEY`
- `LIVEKIT_API_SECRET`
- `OPENAI_API_KEY`
- `DEEPGRAM_API_KEY` *(Optional) only needed when using pipelined models (Fetch from [Deepgram](https://console.deepgram.com) )*
- `CARTESIA_API_KEY` *(Optional) only needed when using pipelined models (Fetch from [Cartesia](https://play.cartesia.ai/keys) )*
- `SIP_OUTBOUND_TRUNK_ID` *(Returned from trunk creation)*

---

## ▶️ Run the LiveKit Outbound Caller Voice Agent

Start the agent with:

```bash
python agent.py dev
```

The agent is now listening for dispatches to make outbound calls.

---

## 📲 Make a Call via LiveKit CLI

In a new terminal, use the following:

```bash
lk dispatch create \
  --new-room \
  --agent-name outbound-caller \
  --metadata '{"phone_number": "+1234567890", "transfer_to": "+9876543210"}'
```

If you're not using a global Livekit CLI config: [livekit](https://docs.livekit.io/home/cloud/keys-and-tokens/)

```bash
lk --api-key <api-key> --api-secret <api-secret> --url <url> \
dispatch create --new-room --agent-name outbound-caller \
--metadata '{"phone_number": "+1234567890"}'
```

---

## 🧰 Helpful LiveKit CLI Commands

```bash
lk project list           # List LiveKit projects
lk sip outbound list      # List configured SIP trunks
lk sip dispatch list      # View past call dispatch logs
```
