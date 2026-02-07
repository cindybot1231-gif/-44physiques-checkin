# 44 Physiques - Athlete Check-In System

Complete athlete check-in system for 44 Physiques bodybuilding coaching.

## What This Is

A mobile-friendly web form where athletes can submit:
- Weekly progress photos (Front, Left, Right, Back poses)
- Weight tracking with automatic change calculation
- Nutrition & meal compliance
- Training & cardio logs
- Recovery & energy levels (slider 1-10)
- Digestion feedback
- Coach notes
- Optional posing videos

**Tech Stack:** Flask (Python) + HTML/CSS/JS (no database needed - files stored on disk)

---

## Deployment Instructions for Railway

### Step 1: Create Railway Account (2 minutes)

1. Go to https://railway.app
2. Click "Get Started"
3. Sign up with your Google account or email
4. Verify your email if needed

### Step 2: Create New Project

1. Click "New Project"
2. Click "Deploy from GitHub repo"
3. If prompted, connect your GitHub account
4. **IMPORTANT:** You'll need to upload these files to GitHub first (see Step 3)

### Step 3: Upload to GitHub (5 minutes)

**Option A - Easy way:**
1. Go to https://github.com/new
2. Repository name: `44physiques-checkin`
3. Make it "Public"
4. Click "Create repository"
5. Click "uploading an existing file"
6. Upload these 4 files from the `44physiques-railway` folder:
   - `app.py`
   - `index.html`
   - `requirements.txt`
   - `nixpacks.toml`
7. Click "Commit changes"

### Step 4: Deploy to Railway (2 minutes)

1. Back in Railway, click your project
2. Click "Add a Service"
3. Click "GitHub Repo"
4. Select `44physiques-checkin`
5. Railway will automatically detect Python and deploy
6. Wait 2-3 minutes for deployment
7. Click the URL Railway gives you (looks like `44physiques-checkin.up.railway.app`)

### Step 5: Test It

1. Open the URL on your phone
2. Fill out the form
3. Submit a test check-in
4. Files will be saved in the `uploads/` folder on Railway's server

---

## Free Tier Limits (Railway)

- 500 hours/month (about 21 days continuous)
- If you need 24/7: $5/month
- Bandwidth: 100GB/month
- Perfect for 15 athletes

---

## File Structure After Upload

```
44physiques-checkin/
├── app.py              # Flask backend
├── index.html          # Athlete form
├── requirements.txt    # Python packages
└── nixpacks.toml      # Railway config
```

---

## Common Issues

**Issue:** "Build failed"
- **Fix:** Make sure `requirements.txt` is uploaded

**Issue:** "App crashed"
- **Fix:** Check Railway logs (click "View Logs" in Railway dashboard)

**Issue:** "Can't upload files"
- **Fix:** Normal - files are stored on Railway's server, not locally

---

## Support

If deployment fails:
1. Check Railway dashboard for error messages
2. Make sure all 4 files are uploaded to GitHub
3. Try redeploying in Railway

---

## Backup Important Data

Files uploaded by athletes are stored on Railway's server. To download them:
1. Go to Railway dashboard
2. Click your service
3. Click "Shell" tab
4. Run: `ls uploads/` to see files
5. Use Railway's file explorer to download

---

**You're done!** The form will be live at your Railway URL.