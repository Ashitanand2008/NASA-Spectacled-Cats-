# NASA Earth Information Jukebox — Vercel Deployment Instructions

Follow these step-by-step instructions to deploy the NASA Earth Information Jukebox on Vercel with zero errors.

---

## 1. Prerequisites
- A free account on [Vercel](https://vercel.com).
- A GitHub account with access to your repository (or you can import this repository directly).

---

## 2. Step-by-Step Deployment Guide

### Step 1: Upload / Push the Repository to GitHub
If you are updating your existing repository (`Ashitanand2008/NASA-Spectacled-Cats-`):
1. Extract `ready.zip` onto your computer.
2. Commit and push the updated files to your GitHub repository `main` branch.

### Step 2: Import into Vercel
1. Open the [Vercel Dashboard](https://vercel.com/dashboard).
2. Click **Add New...** > **Project**.
3. Locate your repository (`NASA-Spectacled-Cats-`) and click **Import**.

### Step 3: CRITICAL PROJECT SETTING — Root Directory
Under the **Configure Project** screen:
1. Locate the **Root Directory** field.
2. Click **Edit** next to Root Directory.
3. Select or enter:
   ```
   Member_5
   ```
4. Click **Continue** / **Save**.
> **Why this is critical:** The deployable web application, static frontend, scientific mapping pipeline, and Vercel configuration live inside `Member_5`. Pointing Vercel's Root Directory to `Member_5` allows Vercel to discover `requirements.txt`, `vercel.json`, and `api/index.py` properly.

### Step 4: Build and Output Settings
- **Framework Preset**: Leave as **Other** (Vercel will automatically detect Python Serverless Functions from `api/index.py`).
- **Build Command**: Leave empty / default.
- **Output Directory**: Leave empty / default.
- **Install Command**: Leave empty / default (`pip install -r requirements.txt` runs automatically).

### Step 5: Environment Variables
- No external API keys or secret environment variables are required. All image processing, color matching, and sonification run locally inside the Python container.

### Step 6: Deploy
1. Click **Deploy**.
2. Wait 60–90 seconds for Vercel to build the container and deploy the static assets to Vercel's Edge CDN.

---

## 3. Disabling Deployment Protection (Public Access)
If visitors or team members see a Vercel login screen when visiting the site:
1. In the Vercel Dashboard, go to your project.
2. Click **Settings** (top navigation tab) > **Deployment Protection** (left sidebar).
3. Under **Vercel Authentication**:
   - Toggle it to **Disabled** (or select **Off** for Preview & Production Deployments).
4. Click **Save**.
5. Your deployment is now publicly accessible to anyone without requiring a Vercel account.

---

## 4. Production Domain Configuration
1. Go to **Settings** > **Domains**.
2. Verify your primary production domain (e.g. `nasa-spectacled-cats.vercel.app`).
3. Note: Individual preview deployment URLs (e.g., `nasa-spectacled-cats-gv7vqf7q4-...`) are temporary preview builds. For presentations and grading, always share the primary production domain:
   ```
   https://nasa-spectacled-cats.vercel.app
   ```

---

## 5. Verification & Testing After Deployment
Once deployed, test your live site with these quick checks:
1. **Homepage**: Visit `https://your-domain.vercel.app/` — The Earth Jukebox UI should load instantly with dark NASA theme, upload box, and controls.
2. **Backend Health Check**: Visit `https://your-domain.vercel.app/api/health` — Should return JSON:
   ```json
   {
     "status": "running",
     "modules": {
       "integration_adapter": true,
       "member4_adapter": true,
       "nasa2py": true,
       "sonification": true,
       "windspeed_mapper": true
     }
   }
   ```
3. **End-to-End Image Sonification**:
   - On the homepage, upload a NASA windspeed satellite image (PNG or JPG).
   - Click **Analyze & Sonify**.
   - The interactive 25-cell grid will display estimated windspeeds (m/s), and the audio player will play the synthesized musical tones.
