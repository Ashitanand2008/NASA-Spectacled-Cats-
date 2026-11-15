# NASA Earth Information Jukebox — Vercel Deployment Guide

This guide provides step-by-step instructions to deploy the repaired **NASA Earth Information Jukebox** project to Vercel.

---

## 1. Quick Overview

The project is structured with **dual-root Vercel compatibility**:
- **Option A (Recommended — Direct Root)**: Deploy from the repository root `./`.
- **Option B (Subfolder Root)**: Deploy with Root Directory set to `Member_5`.

Both options work out-of-the-box because configuration, entrypoints, and assets are synchronized at both levels.

---

## 2. Vercel Project Settings

### A. General Settings
| Setting | Recommended Value | Alternative Value | Notes |
|---|---|---|---|
| **Framework Preset** | **Other** | **Flask** | Do NOT use Next.js or Vite presets. |
| **Root Directory** | `./` (leave blank / root) | `Member_5` | Both roots are fully configured. |
| **Build Command** | *(leave empty)* | *(leave empty)* | Vercel's `@vercel/python` builder installs dependencies automatically. |
| **Output Directory** | *(leave empty)* | *(leave empty)* | Static files are served directly from `public/`. |
| **Install Command** | `pip install -r requirements.txt` | *(leave empty / auto)* | Vercel automatically runs this when Python is detected. |

### B. Python Runtime
- Dependencies are defined in `requirements.txt`:
  ```text
  Flask
  numpy
  scipy
  Pillow
  ```
- Python version is set via `.python-version` (Python `3.12` or `3.11`).

### C. Deployment Protection (Authentication)
If your deployment URL asks for a Vercel login:
1. In your Vercel Dashboard, go to your project.
2. Navigate to **Settings** > **Deployment Protection**.
3. Under **Vercel Authentication**, toggle it to **Disabled** (or configure password protection if desired).
4. Save changes.

---

## 3. How to Deploy

### Method 1: Deploying via GitHub (Recommended)
1. Push the contents of this archive (`ready_fr.zip`) to your GitHub repository:
   ```bash
   git add .
   git commit -m "Fix Vercel serverless routing, API endpoints, and ephemeral storage"
   git push origin main
   ```
2. In the Vercel Dashboard:
   - If already connected: Vercel will trigger a new deployment automatically.
   - If creating a new project: Click **Add New...** > **Project**, select your repository, verify **Framework Preset: Other**, and click **Deploy**.

### Method 2: Deploying via Vercel CLI
1. Open PowerShell or Terminal in the project directory.
2. Run:
   ```bash
   npx vercel --prod
   ```
3. Follow the CLI prompts to deploy directly to production.

---

## 4. Verification Checklist After Deployment

Once deployed, verify the endpoints on your public Vercel URL (e.g. `https://your-app.vercel.app`):

1. **Frontend Home Page**:
   - Visit `https://your-app.vercel.app/`
   - Confirm the Earth Jukebox page loads with styles, starfield background, and navigation.

2. **Backend Health Check**:
   - Visit `https://your-app.vercel.app/api/health`
   - Expected JSON response:
     ```json
     {
       "modules": {
         "integration_adapter": true,
         "member4_adapter": true,
         "nasa2py": true,
         "sonification": true,
         "windspeed_mapper": true
       },
       "status": "running"
     }
     ```

3. **Image Upload & Sonification**:
   - In the web browser, click **"Explore Wind Speed"**.
   - Upload any NASA wind speed image or the included `Member_2/wind_grid_overlay.png`.
   - Click **"Generate Sound"**.
   - Confirm:
     - Progress message appears: *"Processing your wind speed image..."*.
     - 25 data bars appear displaying wind speed values in m/s.
     - Playable `<audio>` player appears with the sonification.
     - Click **Play** to listen to the generated wind tones.
     - Click **Download Audio ↓** to download `earth-jukebox-wind-speed.wav`.

---

## 5. Troubleshooting & FAQ

- **Q: I get "Image is too large" error.**
  - Vercel Serverless Functions have a maximum payload limit of 4.5 MB. Please upload images under 4 MB.
- **Q: Why does the URL redirect to a login screen?**
  - This is Vercel Deployment Protection. Turn off "Vercel Authentication" in your project settings.
- **Q: How long does processing take?**
  - The complete 25-cell grid extraction, color mapping, and 44.1 kHz audio synthesis takes under 0.1 seconds.
