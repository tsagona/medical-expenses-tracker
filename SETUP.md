# Quick Setup Guide

Follow these steps in order to get your Medical Expenses Tracker up and running.

---

## Part 1: Create Your Google Sheet (5 minutes)

1. Go to [Google Sheets](https://sheets.google.com) and create a new spreadsheet
2. Name it **"Medical Expenses"**
3. In **Row 1** (the header row), type these column names in order:

   ```
   Provider | In Portal | Patient | Amount | Date of Service | Bill Received | Notes | Photo
   ```

4. Format the columns:
   - **Column B (In Portal)**: Select the entire column → Insert menu → Checkbox
   - **Column D (Amount)**: Select the entire column → Format menu → Number → Currency
   - **Column E (Date of Service)**: Select the entire column → Format menu → Number → Date
   - **Column F (Bill Received)**: Select the entire column → Format menu → Number → Date

5. **Save the Sheet URL** - copy it from your browser (you'll need it later)

✅ Your sheet is ready!

---

## Part 2: Create Google Form for Mobile Entry (10 minutes)

1. Go to [Google Forms](https://forms.google.com) and create a new form
2. Name it **"Log Medical Expense"**
3. Add these 8 questions **in exact order**:

### Question 1: Provider
- Type: **Short answer**
- Make required

### Question 2: In Portal
- Type: **Checkboxes**
- Add one option: "Yes"
- Leave optional

### Question 3: Patient
- Type: **Multiple choice**
- Options: Tim, Amber, Scarlett, Layla
- Make required

### Question 4: Amount
- Type: **Short answer**
- Click the ⋮ menu → Response validation
- Set to: Number → Greater than → 0
- Make required

### Question 5: Date of Service
- Type: **Date**
- Make required

### Question 6: Bill Received
- Type: **Date**
- Make required

### Question 7: Notes
- Type: **Paragraph**
- Leave optional

### Question 8: Photo
- Type: **File upload**
- Allow: Images only
- Max size: 10 MB
- When prompted, save files to Google Drive folder "Medical Bills"
- Leave optional

4. **Link Form to Sheet:**
   - Click the "Responses" tab
   - Click the green Sheets icon
   - Select "Select existing spreadsheet"
   - Choose your "Medical Expenses" sheet
   - Click "Select"

5. **Important:** The form creates a tab called "Form Responses 1". You need to:
   - Either rename it to "Sheet1", OR
   - Add `sheet_name = "Form Responses 1"` to your Streamlit secrets later

6. **Save the form URL**

### Add to iPhone:
1. Open the form URL in Safari on your iPhone
2. Tap Share button → "Add to Home Screen"
3. Name it "Medical Expense" → Add

✅ Your mobile entry form is ready!

---

## Part 3: Set Up Google Cloud & Service Account (15 minutes)

### 3.1 Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Click the project dropdown (top bar) → "New Project"
3. Name: **"Medical Expenses"**
4. Click "Create"

### 3.2 Enable Required APIs

1. Make sure your new project is selected
2. Go to **"APIs & Services"** → **"Library"**
3. Search for **"Google Sheets API"** → Click it → Click "Enable"
4. Search for **"Google Drive API"** → Click it → Click "Enable"

### 3.3 Create Service Account

1. Go to **"IAM & Admin"** → **"Service Accounts"**
2. Click **"Create Service Account"**
3. Name: **"medical-expenses-app"**
4. Description: "Service account for medical expenses tracker"
5. Click **"Create and Continue"**
6. Skip the permissions step → Click "Continue"
7. Skip the grant access step → Click "Done"

### 3.4 Create Service Account Key

1. Click on the service account you just created
2. Go to the **"Keys"** tab
3. Click **"Add Key"** → **"Create new key"**
4. Choose **"JSON"**
5. Click "Create"
6. A JSON file will download - **save this file safely!**

### 3.5 Share Google Sheet with Service Account

1. Open the JSON file you just downloaded
2. Find the line that says `"client_email"` - copy that email address
   (It looks like: `medical-expenses-app@project-name.iam.gserviceaccount.com`)
3. Go to your Google Sheet
4. Click the **Share** button
5. Paste the service account email
6. Give it **"Editor"** access
7. **Uncheck** "Notify people"
8. Click "Share"

✅ Google Cloud setup complete!

---

## Part 4: Deploy to Streamlit Cloud (10 minutes)

### 4.1 Push Code to GitHub

1. Open Terminal and navigate to this project folder
2. Run these commands:

   ```bash
   git init
   git add .
   git commit -m "Initial medical expenses tracker"
   ```

3. Create a GitHub repository:
   - Option A: Using GitHub CLI:
     ```bash
     gh repo create medical-expenses-tracker --private --source=. --remote=origin --push
     ```
   - Option B: Manually:
     - Go to GitHub → Create new repository → Name it "medical-expenses-tracker" → Create
     - Follow the instructions to push existing repository

### 4.2 Deploy to Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click **"New app"**
4. Repository: Select "medical-expenses-tracker"
5. Branch: main
6. Main file path: `app.py`
7. Click **"Deploy"** (don't worry about it failing - we need to add secrets first)

### 4.3 Add Secrets

1. While your app is deploying, click **Settings** (⚙️ icon)
2. Click **"Secrets"** in the left sidebar
3. Open the JSON file you downloaded from Google Cloud
4. Copy the **entire contents** of that JSON file
5. In the Streamlit secrets editor, paste this (replacing with your actual values):

   ```toml
   [gcp_service_account]
   type = "service_account"
   project_id = "your-project-id"
   private_key_id = "abc123..."
   private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
   client_email = "medical-expenses-app@your-project.iam.gserviceaccount.com"
   client_id = "123456789"
   auth_uri = "https://accounts.google.com/o/oauth2/auth"
   token_uri = "https://oauth2.googleapis.com/token"
   auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
   client_x509_cert_url = "..."

   sheet_url = "YOUR_GOOGLE_SHEET_URL_HERE"
   ```

   **Important:**
   - Replace all the values with the actual values from your JSON file
   - For `sheet_url`, paste the URL of your Google Sheet
   - If you're using "Form Responses 1" sheet, add: `sheet_name = "Form Responses 1"`

6. Click **"Save"**
7. Your app will automatically redeploy with the secrets

### 4.4 Restrict Access (Recommended)

1. Still in Settings, click **"Sharing"**
2. Toggle on **"Restrict viewer access"**
3. Add your email address
4. Click "Save"

Now only you can access the app!

✅ Your app is live!

---

## Part 5: Start Using It!

### On iPhone:
1. Tap the "Medical Expense" icon on your home screen
2. Fill out the form when you get a bill
3. Upload a photo of the receipt
4. Submit!

### On Desktop:
1. Go to your Streamlit app URL (e.g., `https://your-app.streamlit.app`)
2. View your FSA summary
3. Browse all expenses
4. Edit or delete entries
5. Add expenses directly (if not on phone)

---

## Troubleshooting

### "Error connecting to Google Sheets"
- Make sure you shared the sheet with the service account email
- Verify the `sheet_url` in Streamlit secrets is correct
- Check that both APIs are enabled in Google Cloud

### Form submissions not showing up
- Check that the form is linked to your sheet
- Make sure you're using the correct sheet name in secrets
- Look in the "Form Responses 1" tab in your Google Sheet

### Can't access the app
- Check Streamlit Cloud sharing settings
- Make sure your email is whitelisted
- Try opening in an incognito window

---

## What's Next?

- Test the form by adding a test expense on your phone
- Check that it appears in the Google Sheet
- Verify it shows up in the Streamlit dashboard
- Delete the test expense

**You're all set! Happy tracking! 🏥**
