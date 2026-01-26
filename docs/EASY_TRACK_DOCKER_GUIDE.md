# Easy Track Validator Exit Guide (Docker)

This guide shows how to generate validator exit calldata for Easy Track governance using **Docker** or **Poetry**.

## Prerequisites

- Docker installed ([Get Docker](https://docs.docker.com/get-docker/)) OR Poetry installed
- Access to a Consensus Layer (Beacon Chain) node
- Validator index(es) you want to exit

---

## Option A: Using Poetry

### 1. Install Dependencies

```bash
cd validator-exit-bot
poetry install --with dev
```

### 2. Generate Easy Track Hash Calldata

```bash
poetry run python -m scripts.generate \
  --kapi-url https://keys-api.lido.fi \
  --cl-url CL_NODE_URL \
  et-hash \
  --vi <CL_VALIDATOR_INDEX>
```

**Example:**
```bash
poetry run python -m scripts.generate \
  --kapi-url https://keys-api.lido.fi \
  --cl-url CL_NODE_URL \
  et-hash \
  --vi 123456
```

**Multiple validators:**
```bash
poetry run python -m scripts.generate \
  --kapi-url https://keys-api.lido.fi \
  --cl-url CL_NODE_URL \
  et-hash \
  --vi 123456 \
  --vi 123457 \
  --vi 123458
```

### 3. Submit to Easy Track

1. Go to **Easy Track UI**: https://easytrack.lido.fi/
2. Connect your wallet
3. Click **"Start motion"**
4. Select motion type: **"[Curated] Submit Exit hashes"**
5. Paste the hex calldata from step 2
6. Review and confirm the transaction

### 4. Wait for Easy Track Approval

After the Easy Track motion passes (can take days), proceed to reveal the validator data.

### 5. Generate VEB Data Reveal Calldata

```bash
poetry run python -m scripts.generate \
  --kapi-url https://keys-api.lido.fi \
  --cl-url CL_NODE_URL \
  veb-data \
  --vi <CL_VALIDATOR_INDEX>
```

**Example:**
```bash
poetry run python -m scripts.generate \
  --kapi-url https://keys-api.lido.fi \
  --cl-url CL_NODE_URL \
  veb-data \
  --vi 123456
```

### 6. Submit Data to VEBO Contract

1. Go to **Validator Exit Bus Oracle**: https://etherscan.io/address/0x0De4Ea0184c2ad0BacA7183356Aea5B8d5Bf5c6e#writeProxyContract#F15
2. Connect your wallet
3. Find function **`submitExitRequestsData`** (function #15)
4. Fill in:
   - `data`: Paste the hex calldata from step 5
   - `dataFormat`: `1`
5. Click "Write" and confirm the transaction

---

## Option B: Using Docker

### 1. Build the Docker Image

```bash
cd validator-exit-bot
docker build -t validator-exit-bot .
```

### 2. Generate Easy Track Hash Calldata

```bash
docker run --rm --entrypoint python3 validator-exit-bot \
  -m scripts.generate \
  --kapi-url https://keys-api.lido.fi \
  --cl-url CL_NODE_URL \
  et-hash \
  --vi <CL_VALIDATOR_INDEX>
```

**Example:**
```bash
docker run --rm --entrypoint python3 validator-exit-bot \
  -m scripts.generate \
  --kapi-url https://keys-api.lido.fi \
  --cl-url CL_NODE_URL \
  et-hash \
  --vi 123456
```

**Multiple validators:**
```bash
docker run --rm --entrypoint python3 validator-exit-bot \
  -m scripts.generate \
  --kapi-url https://keys-api.lido.fi \
  --cl-url CL_NODE_URL \
  et-hash \
  --vi 123456 \
  --vi 123457 \
  --vi 123458
```

### 3. Submit to Easy Track

1. Go to **Easy Track UI**: https://easytrack.lido.fi/
2. Connect your wallet
3. Click **"Start motion"**
4. Select motion type: **"[Curated] Submit Exit hashes"**
5. Paste the hex calldata from step 2
6. Review and confirm the transaction

### 4. Wait for Easy Track Approval

After the Easy Track motion passes (can take days), proceed to reveal the validator data.

### 5. Generate VEB Data Reveal Calldata

```bash
docker run --rm --entrypoint python3 validator-exit-bot \
  -m scripts.generate \
  --kapi-url https://keys-api.lido.fi \
  --cl-url http://host.docker.internal:5052 \
  veb-data \
  --vi <CL_VALIDATOR_INDEX>
```

**Example:**
```bash
docker run --rm --entrypoint python3 validator-exit-bot \
  -m scripts.generate \
  --kapi-url https://keys-api.lido.fi \
  --cl-url CL_NODE_URL \
  veb-data \
  --vi 123456
```

### 6. Submit Data to VEBO Contract

1. Go to **Validator Exit Bus Oracle**: https://etherscan.io/address/0x0De4Ea0184c2ad0BacA7183356Aea5B8d5Bf5c6e#writeProxyContract#F15
2. Connect your wallet
3. Find function **`submitExitRequestsData`** (function #15)
4. Fill in:
   - `data`: Paste the hex calldata from step 5
   - `dataFormat`: `1`
5. Click "Write" and confirm the transaction

---

## Network Configuration

### Mainnet
```bash
--kapi-url https://keys-api.lido.fi
--cl-url CL_NODE_URL
```

### Holesky Testnet
```bash
--kapi-url https://keys-api-holesky.testnet.fi
--cl-url CL_NODE_URL
```

---

## Important Notes

### Docker-Specific

- **`--entrypoint python3`**: Required to override the bot's default entrypoint
- **`host.docker.internal`**: Use this instead of `localhost` to access your host machine's services from inside Docker

### General

- **Same validator indexes**: Use the same `--vi` values for both `et-hash` and `veb-data` commands
- **Order doesn't matter**: The script automatically sorts validators by `(module_id, operator_id, validator_index)`
- **Debug mode**: Add `--debug` after `scripts.generate` to see detailed execution logs

---

## Troubleshooting

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

**Solution:**
```bash
git pull
docker system prune -a  # Clean old images
docker build -t validator-exit-bot .
```

---

## Save Output to File

### Linux/Mac
```bash
# Poetry
poetry run python -m scripts.generate \
  --kapi-url https://keys-api.lido.fi \
  --cl-url CL_NODE_URL \
  et-hash \
  --vi 123456 > et_calldata.txt

# Docker
docker run --rm --entrypoint python3 validator-exit-bot \
  -m scripts.generate \
  --kapi-url https://keys-api.lido.fi \
  --cl-url CL_NODE_URL \
  et-hash \
  --vi 123456 > et_calldata.txt
```

### Windows (PowerShell)
```powershell
# Docker
docker run --rm --entrypoint python3 validator-exit-bot -m scripts.generate --kapi-url https://keys-api.lido.fi --cl-url CL_NODE_URL et-hash --vi 123456 | Out-File -Encoding utf8 et_calldata.txt
```

---

## Complete Workflow Example

### Using Poetry

```bash
# Step 1: Generate ET hash calldata
poetry run python -m scripts.generate \
  --kapi-url https://keys-api.lido.fi \
  --cl-url CL_NODE_URL \
  et-hash \
  --vi 123456 > et_calldata.txt

# Step 2: Submit to Easy Track UI
# → Go to https://easytrack.lido.fi/
# → Start motion: "[Curated] Submit Exit hashes"
# → Paste calldata from et_calldata.txt

# Step 3: Wait for Easy Track approval (can take days)

# Step 4: Generate VEB data calldata
poetry run python -m scripts.generate \
  --kapi-url https://keys-api.lido.fi \
  --cl-url CL_NODE_URL \
  veb-data \
  --vi 123456 > veb_calldata.txt

# Step 5: Submit to VEBO contract
# → Go to https://etherscan.io/address/0x0De4Ea0184c2ad0BacA7183356Aea5B8d5Bf5c6e#writeProxyContract#F15
# → Call submitExitRequestsData with calldata from veb_calldata.txt
# → Set dataFormat = 1
```

### Using Docker

```bash
# Step 1: Build image (one-time)
docker build -t validator-exit-bot .

# Step 2: Generate ET hash calldata
docker run --rm --entrypoint python3 validator-exit-bot \
  -m scripts.generate \
  --kapi-url https://keys-api.lido.fi \
  --cl-url CL_NODE_URL \
  et-hash \
  --vi 123456 > et_calldata.txt

# Step 3: Submit to Easy Track UI
# → Go to https://easytrack.lido.fi/
# → Start motion: "[Curated] Submit Exit hashes"
# → Paste calldata from et_calldata.txt

# Step 4: Wait for Easy Track approval (can take days)

# Step 5: Generate VEB data calldata
docker run --rm --entrypoint python3 validator-exit-bot \
  -m scripts.generate \
  --kapi-url https://keys-api.lido.fi \
  --cl-url CL_NODE_URL \
  veb-data \
  --vi 123456 > veb_calldata.txt

# Step 6: Submit to VEBO contract
# → Go to https://etherscan.io/address/0x0De4Ea0184c2ad0BacA7183356Aea5B8d5Bf5c6e#writeProxyContract#F15
# → Call submitExitRequestsData with calldata from veb_calldata.txt
# → Set dataFormat = 1
```

---

## Additional Resources

- [Easy Track UI](https://easytrack.lido.fi/) - Submit motions here
- [Easy Track Documentation](https://docs.lido.fi/guides/easy-track-guide/)
- [Docker Documentation](https://docs.docker.com/)
