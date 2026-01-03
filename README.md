# Medical Expenses Tracker

A simple web application to track medical expenses for FSA reimbursement. Uses Google Forms for mobile entry and Streamlit for desktop management and analytics.

## Features

- **Mobile Entry:** Google Form optimized for iPhone (quick expense logging with photo upload)
- **Desktop Dashboard:** Streamlit app for viewing, editing, and analyzing expenses
- **FSA Tracking:** Real-time tracking of spending against $3,400 FSA budget
- **Analytics:** Breakdown by patient, date range, and provider
- **Secure:** Service account authentication

## Architecture

- **Backend:** Google Sheets (single spreadsheet)
- **Mobile Entry:** Google Forms
- **Desktop Dashboard:** Streamlit (Python)
- **Authentication:** Google Service Account
- **Hosting:** Streamlit Cloud (free)
- **Cost:** $0/month

## Quick Start

**👉 See [SETUP.md](SETUP.md) for complete step-by-step setup instructions.**

The setup takes about 40 minutes total and includes:
1. Creating your Google Sheet (5 min)
2. Creating a Google Form for mobile (10 min)
3. Setting up Google Cloud & Service Account (15 min)
4. Deploying to Streamlit Cloud (10 min)

---

## Project Structure

```
medical-expenses-tracker/
├── app.py                          # Main Streamlit application
├── requirements.txt                # Python dependencies
├── SETUP.md                        # Step-by-step setup guide
├── README.md                       # This file
├── .streamlit/
│   ├── config.toml                # Streamlit configuration
│   └── secrets.toml.example       # Example secrets file
└── .gitignore
```

---

## Local Development

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create `.streamlit/secrets.toml` based on `secrets.toml.example`
4. Add your Google service account credentials and sheet URL
5. Run the app:
   ```bash
   streamlit run app.py
   ```

---

## Usage

### Mobile (iPhone)
- Tap the "Medical Expense" icon on your home screen
- Fill out the form and upload receipt photo
- Submit

### Desktop (Streamlit Dashboard)
- View FSA summary and spending analytics
- Browse, search, and filter all expenses
- Add, edit, or delete expenses
- Track spending by patient

---

## Technical Details

### Google Sheet Schema

| Column | Type | Description |
|--------|------|-------------|
| Provider | String | Medical provider name |
| In Portal | Boolean | Whether bill is in provider's portal |
| Patient | Enum | One of: Tim, Amber, Scarlett, Layla |
| Amount | Currency | Dollar amount of expense |
| Date of Service | Date | When service was provided |
| Bill Received | Date | When bill was received |
| Notes | String | Additional notes |
| Photo | String | Google Drive link to receipt photo |

### Python Dependencies

- `streamlit`: Web application framework
- `gspread`: Google Sheets API client
- `google-auth`: Google authentication
- `pandas`: Data manipulation

---

## Detailed Setup Instructions (Reference)

### Step 1: Create Google Sheet

1. Go to [Google Sheets](https://sheets.google.com)
2. Create a new spreadsheet
3. Name it "Medical Expenses Tracker"
4. In the first row (header), add these columns in this exact order:

   | Provider | In Portal | Patient | Amount | Date of Service | Bill Received | Notes | Photo |
   |----------|-----------|---------|--------|-----------------|---------------|-------|-------|

5. Format the columns:
   - **In Portal:** Select column B, go to Insert > Checkbox
   - **Amount:** Select column D, go to Format > Number > Currency
   - **Date of Service:** Select column E, go to Format > Number > Date
   - **Bill Received:** Select column F, go to Format > Number > Date

6. Copy the spreadsheet URL (you'll need this later)

---

### Step 2: Create Google Form

1. Go to [Google Forms](https://forms.google.com)
2. Create a new form
3. Name it "Log Medical Expense"
4. Add the following questions **in this order**:

#### Question 1: Provider
- Type: **Short answer**
- Required: **Yes**

#### Question 2: In Portal
- Type: **Checkboxes**
- Options: "Yes" (just one checkbox)
- Not required

#### Question 3: Patient
- Type: **Multiple choice**
- Options:
  - Tim
  - Amber
  - Scarlett
  - Layla
- Required: **Yes**

#### Question 4: Amount
- Type: **Short answer**
- Validation: **Number > Greater than 0**
- Required: **Yes**

#### Question 5: Date of Service
- Type: **Date**
- Required: **Yes**

#### Question 6: Bill Received
- Type: **Date**
- Required: **Yes**

#### Question 7: Notes
- Type: **Paragraph**
- Not required

#### Question 8: Photo
- Type: **File upload**
- Settings:
  - File types: Images only
  - Maximum file size: 10 MB
  - Maximum files: 1
- Not required

**Important:** When you add file upload, Google will ask you to configure file collection. Choose:
- Collect files in: Your Google Drive
- Folder name: "Medical Bills" (or any name you prefer)

5. Click on the **Responses** tab
6. Click the Google Sheets icon (green icon) to link to a spreadsheet
7. Select **"Select existing spreadsheet"**
8. Choose the "Medical Expenses Tracker" sheet you created in Step 1
9. Click **Select**

**Note:** The form will create a new sheet tab called "Form Responses 1". You'll need to either:
- Use this sheet (recommended for simplicity), OR
- Set up a script to copy data to your formatted sheet

For simplicity, I recommend using "Form Responses 1" and updating the column headers to match the required format.

10. Copy the form URL and save it (you'll access this on your phone)

#### Add Form to iPhone Home Screen

1. Open the form URL in Safari on your iPhone
2. Tap the Share button (square with arrow)
3. Scroll down and tap "Add to Home Screen"
4. Name it "Medical Expense"
5. Tap "Add"

Now you have a one-tap shortcut to log expenses!

---

### Step 3: Set Up Google Cloud Project & OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project (or select existing)
   - Click "Select a project" → "New Project"
   - Name: "Medical Expenses Tracker"
   - Click "Create"

3. Enable Google Sheets and Drive APIs:
   - Go to "APIs & Services" → "Enable APIs and Services"
   - Search for "Google Sheets API" → Click → Enable
   - Search for "Google Drive API" → Click → Enable

4. Create OAuth 2.0 Credentials:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - If prompted, configure OAuth consent screen first:
     - User Type: **External**
     - App name: "Medical Expenses Tracker"
     - User support email: Your email
     - Developer contact: Your email
     - Scopes: Add `../auth/spreadsheets` and `../auth/drive.readonly`
     - Test users: Add your email
     - Click "Save and Continue"
   - Back to Create OAuth client ID:
     - Application type: **Web application**
     - Name: "Medical Expenses Tracker"
     - Authorized redirect URIs: (add these)
       - `http://localhost:8501` (for local development)
       - `https://your-app-name.streamlit.app` (will update after deployment)
     - Click "Create"

5. Download the credentials:
   - Click the download button (⬇️) next to your OAuth 2.0 Client ID
   - Save the JSON file

6. Note the Client ID and Client Secret (you'll need these for Streamlit secrets)

---

### Step 4: Deploy to Streamlit Cloud

1. **Push code to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   gh repo create medical-expenses-tracker --private --source=. --remote=origin --push
   ```
   (Or create a GitHub repo manually and push)

2. **Deploy to Streamlit Cloud:**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with GitHub
   - Click "New app"
   - Select your repository: `medical-expenses-tracker`
   - Main file path: `app.py`
   - Click "Deploy"

3. **Add Secrets:**
   - In Streamlit Cloud, go to your app settings
   - Click "Secrets" in the left sidebar
   - Add the following (replace with your values):

   ```toml
   # Google OAuth credentials
   [google_oauth]
   client_id = "YOUR_CLIENT_ID.apps.googleusercontent.com"
   client_secret = "YOUR_CLIENT_SECRET"
   redirect_uris = ["https://your-app-name.streamlit.app"]

   # Your Google Sheet URL
   sheet_url = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"
   ```

4. **Update OAuth Redirect URI:**
   - Copy your Streamlit app URL (e.g., `https://your-app-name.streamlit.app`)
   - Go back to Google Cloud Console → Credentials
   - Edit your OAuth 2.0 Client ID
   - Add your Streamlit app URL to "Authorized redirect URIs"
   - Click "Save"

5. **Restrict Access (Recommended):**
   - In Streamlit Cloud app settings
   - Go to "Sharing"
   - Enable "Restrict access"
   - Add only your email address
   - This ensures only you can access the app

---

### Step 5: Authentication Flow (First Time Use)

The current app uses a simplified authentication approach. For production, you'll need to implement a full OAuth flow. Here are two options:

#### Option A: Service Account (Simpler, Recommended)

1. In Google Cloud Console, create a Service Account:
   - Go to "IAM & Admin" → "Service Accounts"
   - Click "Create Service Account"
   - Name: "medical-expenses-sa"
   - Click "Create and Continue"
   - Skip granting roles
   - Click "Done"

2. Create a key:
   - Click on the service account you just created
   - Go to "Keys" tab
   - Click "Add Key" → "Create new key"
   - Choose JSON
   - Download the key file

3. Share your Google Sheet with the service account:
   - Open your Google Sheet
   - Click "Share"
   - Paste the service account email (looks like `medical-expenses-sa@project-id.iam.gserviceaccount.com`)
   - Give it "Editor" access
   - Uncheck "Notify people"
   - Click "Share"

4. Update `app.py` to use service account:
   - Replace the OAuth flow with service account authentication
   - I can provide updated code if you choose this option

#### Option B: Full OAuth Flow (More Secure)

Requires implementing a proper OAuth callback handler. This is more complex but provides better security. Let me know if you want help implementing this.

**For now, I recommend Option A (Service Account)** for simplicity.

---

## Local Development

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create `.streamlit/secrets.toml`:
   ```toml
   [google_oauth]
   client_id = "YOUR_CLIENT_ID"
   client_secret = "YOUR_CLIENT_SECRET"
   redirect_uris = ["http://localhost:8501"]

   sheet_url = "YOUR_SHEET_URL"
   ```

4. Run the app:
   ```bash
   streamlit run app.py
   ```

---

## Usage

### Mobile (iPhone)
1. Tap the "Medical Expense" icon on your home screen
2. Fill out the form
3. Upload receipt photo from camera or photos
4. Submit

### Desktop (Streamlit Dashboard)
1. Go to your Streamlit app URL
2. View FSA summary and spending breakdown
3. Browse all expenses with filters
4. Add, edit, or delete expenses
5. Search by provider, patient, or date

---

## Troubleshooting

### "Error connecting to Google Sheets"
- Make sure your Google Sheet is shared with your Google account or service account
- Verify the sheet URL in secrets is correct
- Check that Google Sheets API is enabled

### "Authentication failed"
- Verify OAuth credentials in Streamlit secrets
- Make sure redirect URIs match exactly (http vs https, trailing slash)
- Check that your email is added as a test user in OAuth consent screen

### Form not populating sheet
- Check that form is linked to the correct sheet
- Verify column headers match exactly
- Make sure you're using the correct sheet tab

---

## Cost

- **Google Sheets:** Free (under 10 million cells)
- **Google Forms:** Free
- **Google Drive:** Free (15 GB storage)
- **Streamlit Cloud:** Free (1 private app, 1 GB resources)

**Total: $0/month**

---

## Next Steps

1. Complete Google Sheet setup
2. Create and test Google Form
3. Set up Google Cloud OAuth
4. Deploy to Streamlit Cloud
5. Add app to iPhone home screen

Let me know if you need help with any step!
