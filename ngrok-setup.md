# Setting up ngrok for Local Misinfo Detector Access

Since your misinfo detector runs locally on `localhost:8000`, Railway needs a public URL to reach it. ngrok creates a secure tunnel to your local machine.

## 1. Install ngrok

### macOS
```bash
brew install ngrok
```

### Windows/Linux
Download from https://ngrok.com/download

## 2. Start ngrok

```bash
# Expose your local misinfo detector
ngrok http 8000
```

You'll get output like:
```
Session Status                online
Account                       Your Name (Plan: Free)
Version                       3.x.x
Region                        United States (us-cal-1)
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://random-string.ngrok-free.app -> http://localhost:8000
```

## 3. Update Railway Environment

In Railway dashboard, set:
```
MISINFO_DETECTOR_URL=https://random-string.ngrok-free.app
```

## 4. Keep ngrok Running

- Keep the ngrok command running while testing
- The URL changes each time you restart ngrok (unless you have a paid account)
- For production, consider running your misinfo detector on a cloud service

## 5. Alternative: Run Misinfo Detector on Railway

For a fully cloud solution, you could also deploy your misinfo detector to Railway and update the OCR service to use the Railway URL.
