# 44 Physiques - Resend Email Setup

## Environment Variables (Render Dashboard)

Make sure these are set in your Render dashboard:

| Variable | Value | Status |
|----------|-------|--------|
| `RESEND_API_KEY` | Your Resend API key (starts with `re_`) | ✅ You added this |
| `FROM_EMAIL` | Your verified sender email (e.g., `checkins@44physiques.com`) | ⬜ Needs setup |
| `COACH_EMAIL` | David's email (where check-ins are sent) | ⬜ Needs setup |
| `DATABASE_URL` | Auto-set by Render PostgreSQL | ✅ Auto-configured |
| `SECRET_KEY` | Any random string for Flask sessions | ⬜ Optional but recommended |

## Steps to Complete

### 1. Verify Sender Domain in Resend

1. Go to https://resend.com/domains
2. Add your domain (e.g., `44physiques.com`)
3. Add the DNS records shown to your domain registrar
4. Wait for verification (usually instant to a few minutes)

### 2. Set Remaining Environment Variables on Render

Go to your Render dashboard → Service → Environment → Add:

```
FROM_EMAIL=checkins@44physiques.com
COACH_EMAIL=david@44physiques.com
SECRET_KEY=any-random-string-here
```

### 3. Deploy

The code is ready. Just push to GitHub and Render will auto-deploy.

## Testing

After deployment, submit a test check-in. You should see in the logs:
```
Starting email send process via Resend...
FROM_EMAIL: checkins@44physiques.com
COACH_EMAIL: david@44physiques.com
RESEND_API_KEY set: Yes
Email sent successfully to david@44physiques.com via Resend
```

## Changes Made

1. ✅ Updated `app.py` - Replaced Outlook SMTP with Resend
2. ✅ Updated `requirements.txt` - Added `resend==2.6.0`
3. ⬜ You need to verify domain in Resend
4. ⬜ You need to add environment variables on Render

## Troubleshooting

**"RESEND_API_KEY not configured"**
→ Check the env var is set in Render dashboard

**"Domain not verified"**
→ Complete domain verification in Resend dashboard first

**Emails not received**
→ Check spam folder, verify `COACH_EMAIL` is correct
