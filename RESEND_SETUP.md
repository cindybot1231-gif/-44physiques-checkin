# 44 Physiques - Resend Email Setup

## Environment Variables (Render Dashboard)

Make sure these are set in your Render dashboard:

| Variable | Value | Status |
|----------|-------|--------|
| `RESEND_API_KEY` | Your Resend API key (starts with `re_`) | ✅ You added this |
| `FROM_EMAIL` | `onboarding@resend.dev` (Resend's test domain) | ✅ Pre-configured |
| `COACH_EMAIL` | David's email (where check-ins are sent) | ⬜ Needs setup |
| `DATABASE_URL` | Auto-set by Render PostgreSQL | ✅ Auto-configured |
| `SECRET_KEY` | Any random string for Flask sessions | ⬜ Optional but recommended |

## Steps to Complete

### 1. Set COACH_EMAIL on Render (Required)

Go to your Render dashboard → Service → Environment → Add:

```
COACH_EMAIL=david@44physiques.com
```

(Replace with David's actual email address)

### 2. Deploy

The code is ready. Just push to GitHub and Render will auto-deploy.

## Testing

After deployment, submit a test check-in. You should see in the logs:
```
Starting email send process via Resend...
FROM_EMAIL: onboarding@resend.dev
COACH_EMAIL: david@44physiques.com
RESEND_API_KEY set: Yes
Email sent successfully to david@44physiques.com via Resend
```

## Using Your Own Domain Later (Optional)

When you're ready to use your own domain (e.g., `checkins@44physiques.com`):

1. Go to https://resend.com/domains
2. Add your domain
3. Add DNS records to your domain registrar
4. Wait for verification
5. Update `FROM_EMAIL` environment variable in Render

## Changes Made

1. ✅ Updated `app.py` - Replaced Outlook SMTP with Resend
2. ✅ Updated `requirements.txt` - Added `resend==2.6.0`
3. ✅ Default `FROM_EMAIL` set to `onboarding@resend.dev`
4. ⬜ You need to add `COACH_EMAIL` environment variable on Render

## Troubleshooting

**"RESEND_API_KEY not configured"**
→ Check the env var is set in Render dashboard

**Emails not received**
→ Check spam folder, verify `COACH_EMAIL` is correct
→ Resend test domain emails sometimes go to spam initially
