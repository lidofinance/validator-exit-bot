# Easy Track Validator Exit Guide (Docker)

This guide shows how to generate validator exit calldata for Easy Track governance **using Docker only** - no Python or Poetry installation required!

## Prerequisites

- Docker installed ([Get Docker](https://docs.docker.com/get-docker/))
- Access to a Consensus Layer (Beacon Chain) node
- Validator index(es) you want to exit

## Quick Start

### Option A: Using Makefile (Easiest!)

```bash
# Generate Easy Track hash
make generate-et-hash VI=123456

# Generate VEB data
make generate-veb-data VI=123456

# Multiple validators
make generate-et-hash VI=123456 VI2=123457 VI3=123458
```

**That's it!** The Makefile handles building the image and running the command. ✨

### Option B: Using Docker Directly

### 1. Build the Docker Image

```bash
git clone <your-repo-url>
cd validator-exit-bot
docker build -t validator-exit-bot .
```

### 2. Generate Easy Track Hash Calldata

```bash
docker run --rm validator-exit-bot \
  python3 -m scripts.generate \
  --kapi-url https://keys-api.lido.fi \
  --cl-url http://host.docker.internal:5052 \
  et-hash \
  --vi <VALIDATOR_INDEX>
```

**Example:**
```bash
docker run --rm validator-exit-bot \
  python3 -m scripts.generate \
  --kapi-url https://keys-api.lido.fi \
  --cl-url http://host.docker.internal:5052 \
  et-hash \
  --vi 123456
```

**Output:** Hex-encoded calldata (copy this entire string)

### 3. Submit to Easy Track

1. Go to **Easy Track UI**: https://easytrack.lido.fi/
2. Connect your wallet
3. Click **"Start motion"**
4. Select motion type: **"[Curated] Submit Exit hashes"**
5. Paste the hex calldata from step 2 into the data field
6. Review and confirm the transaction

### 4. Wait for Easy Track Approval

After the Easy Track motion passes, you'll need to reveal the validator data.

### 5. Generate VEB Data Reveal Calldata

```bash
docker run --rm validator-exit-bot \
  python3 -m scripts.generate \
  --kapi-url https://keys-api.lido.fi \
  --cl-url http://host.docker.internal:5052 \
  veb-data \
  --vi <VALIDATOR_INDEX>
```

**Example:**
```bash
docker run --rm validator-exit-bot \
  python3 -m scripts.generate \
  --kapi-url https://keys-api.lido.fi \
  --cl-url http://host.docker.internal:5052 \
  veb-data \
  --vi 123456
```

### 6. Submit Data to VEBO Contract

1. Go to Validator Exit Bus Oracle: https://etherscan.io/address/0x0De4Ea0184c2ad0BacA7183356Aea5B8d5Bf5c6e#writeProxyContract#F15
2. Connect your wallet
3. Find function **`submitExitRequestsData`** (function #15)
4. Fill in:
   - `data`: Paste the hex calldata from step 5
   - `dataFormat`: `1`
5. Click "Write" and confirm the transaction

---

## Multiple Validators

To exit multiple validators, add multiple `--vi` parameters:

```bash
docker run --rm validator-exit-bot \
  python3 -m scripts.generate \
  --kapi-url https://keys-api.lido.fi \
  --cl-url http://host.docker.internal:5052 \
  et-hash \
  --vi 123456 \
  --vi 123457 \
  --vi 123458
```

**Important:** Use the **same validator indexes** for both `et-hash` and `veb-data` commands!

---

## Network Configuration

### Mainnet (default)
```bash
--kapi-url https://keys-api.lido.fi
--cl-url http://host.docker.internal:5052
```

### Holesky Testnet
```bash
--kapi-url https://keys-api-holesky.testnet.fi
--cl-url https://holesky.beaconcha.in
```

### Custom Node
If you're running a local Beacon node, use:
- **Linux/Mac:** `http://host.docker.internal:5052`
- **Windows:** `http://host.docker.internal:5052`

This special hostname allows Docker to access your host machine's localhost.

---

## Debug Mode

To see detailed execution steps, add `--debug`:

```bash
docker run --rm validator-exit-bot \
  python3 -m scripts.generate \
  --debug \
  --kapi-url https://keys-api.lido.fi \
  --cl-url http://host.docker.internal:5052 \
  et-hash \
  --vi 123456
```

---

## Save Output to File

### Linux/Mac
```bash
docker run --rm validator-exit-bot \
  python3 -m scripts.generate \
  --kapi-url https://keys-api.lido.fi \
  --cl-url http://host.docker.internal:5052 \
  et-hash \
  --vi 123456 > calldata.txt
```

### Windows (PowerShell)
```powershell
docker run --rm validator-exit-bot python3 -m scripts.generate --kapi-url https://keys-api.lido.fi --cl-url http://host.docker.internal:5052 et-hash --vi 123456 | Out-File -Encoding utf8 calldata.txt
```

---

## Troubleshooting

### Error: "Connection refused"

**Problem:** Docker can't reach your local Beacon node.

**Solution:** Use `http://host.docker.internal:5052` instead of `http://localhost:5052`

### Error: "Validator index not found"

**Problem:** The validator index doesn't exist on the Consensus Layer.

**Solutions:**
- Double-check the validator index
- Verify you're using the correct network (mainnet vs. testnet)
- Check your CL node is synced

### Error: "Validator pubkey not found in KAPI"

**Problem:** The validator is not part of Lido's staking modules.

**Solution:** Verify the validator is actually a Lido validator using [beaconcha.in](https://beaconcha.in)

### Docker Build Fails

**Problem:** Build errors during `docker build`.

**Solution:** Ensure you have the latest code and Docker version:
```bash
git pull
docker system prune -a  # Clean old images
docker build -t validator-exit-bot .
```

---

## Using Pre-built Docker Image (Optional)

If your team publishes Docker images to a registry, users can skip the build step:

```bash
# Pull the image
docker pull ghcr.io/your-org/validator-exit-bot:latest

# Run directly
docker run --rm ghcr.io/your-org/validator-exit-bot:latest \
  python3 -m scripts.generate \
  --kapi-url https://keys-api.lido.fi \
  --cl-url http://host.docker.internal:5052 \
  et-hash \
  --vi 123456
```

---

## Complete Workflow Example

Here's a complete example for exiting validator `123456`:

### Using Makefile (Recommended)

```bash
# Step 1: Generate ET hash calldata
make generate-et-hash VI=123456 > et_calldata.txt

# Step 2: Submit to Easy Track (manual - use Easy Track UI)
# → Go to https://easytrack.lido.fi/
# → Start motion: "[Curated] Submit Exit hashes"
# → Paste the calldata from et_calldata.txt

# Step 3: Wait for Easy Track approval (can take days)

# Step 4: Generate VEB data calldata
make generate-veb-data VI=123456 > veb_calldata.txt

# Step 5: Submit to VEBO (manual - use Etherscan)
# → Go to VEBO contract
# → Call submitExitRequestsData with the calldata from veb_calldata.txt
# → Set dataFormat = 1
```

### Using Docker Directly

```bash
# Step 1: Build image (one-time)
docker build -t validator-exit-bot .

# Step 2: Generate ET hash calldata
docker run --rm validator-exit-bot \
  python3 -m scripts.generate \
  --kapi-url https://keys-api.lido.fi \
  --cl-url http://host.docker.internal:5052 \
  et-hash \
  --vi 123456 > et_calldata.txt

# Step 3: Submit to Easy Track (manual - use Easy Track UI)
# → Go to https://easytrack.lido.fi/
# → Start motion: "[Curated] Submit Exit hashes"
# → Paste the calldata from et_calldata.txt

# Step 4: Wait for Easy Track approval (can take days)

# Step 5: Generate VEB data calldata
docker run --rm validator-exit-bot \
  python3 -m scripts.generate \
  --kapi-url https://keys-api.lido.fi \
  --cl-url http://host.docker.internal:5052 \
  veb-data \
  --vi 123456 > veb_calldata.txt

# Step 6: Submit to VEBO (manual - use Etherscan)
# → Go to VEBO contract
# → Call submitExitRequestsData with the calldata from veb_calldata.txt
# → Set dataFormat = 1
```

---

## Makefile Commands Reference

The project includes convenient Makefile targets for easier usage:

```bash
# Generate Easy Track hash calldata
make generate-et-hash VI=123456

# Generate VEB data calldata
make generate-veb-data VI=123456

# Multiple validators (up to 5 via VI, VI2, VI3, VI4, VI5)
make generate-et-hash VI=123456 VI2=123457 VI3=123458

# Custom endpoints
make generate-et-hash VI=123456 \
  KAPI_URL=https://keys-api-holesky.testnet.fi \
  CL_URL=https://holesky-beacon.example.com
```

---

## Additional Resources

- [Easy Track UI](https://easytrack.lido.fi/) - Submit motions here
- [Easy Track Documentation](https://docs.lido.fi/guides/easy-track-guide/)
- [Validator Exit Bus Oracle](https://docs.lido.fi/contracts/validator-exit-bus-oracle/)
- [Docker Documentation](https://docs.docker.com/)
