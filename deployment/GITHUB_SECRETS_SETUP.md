# GitHub Secrets Setup for Auto-Deployment

To enable automatic backend deployment to Oracle Cloud when you push to `main`, you need to add your SSH private key as a GitHub Secret.

## Steps:

### 1. Get Your SSH Private Key

Your SSH private key is the file you use to connect to your Oracle Cloud instance (the `.key` file you downloaded when creating the instance).

**Location:** Probably in `~/Downloads/` or `~/.ssh/`

### 2. Copy the Private Key Content

```bash
# Display the content of your private key
cat ~/path/to/your-oracle-key.key

# Or copy it to clipboard (macOS)
cat ~/path/to/your-oracle-key.key | pbcopy
```

The key should look like:
```
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA...
...
-----END RSA PRIVATE KEY-----
```

### 3. Add to GitHub Secrets

1. Go to your GitHub repository: https://github.com/tommylowry/patriot-center
2. Click: **Settings** (top menu)
3. Left sidebar: Click **Secrets and variables** → **Actions**
4. Click: **New repository secret**
5. Fill in:
   - **Name:** `ORACLE_SSH_KEY`
   - **Secret:** Paste your entire private key (including the `-----BEGIN` and `-----END` lines)
6. Click: **Add secret**

### 4. Test Auto-Deployment

Once the secret is added, any push to `main` that changes backend files will automatically:
1. SSH into your Oracle Cloud instance
2. Pull the latest code
3. Install any new dependencies
4. Restart the backend service

**View deployment status:**
- Go to: **Actions** tab in your GitHub repo
- You'll see "Deploy to Oracle Cloud" runs for each push to main

### 5. Verify It's Working

After pushing to `main`, you can:
- Check the Actions tab for deployment status
- Or manually verify: `ssh ubuntu@129.80.188.14 "sudo systemctl status patriot-center"`

---

## Troubleshooting

**If deployment fails:**
1. Check the Actions tab for error logs
2. Verify the SSH key was copied correctly (no extra spaces/newlines)
3. Test SSH connection manually: `ssh -i ~/path/to/key.key ubuntu@129.80.188.14`

**To manually deploy:**
```bash
ssh ubuntu@129.80.188.14
cd /opt/patriot-center
git pull
sudo systemctl restart patriot-center
```
