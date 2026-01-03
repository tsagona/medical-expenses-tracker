import streamlit as st
import gspread
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
import pandas as pd
from datetime import datetime
import os
import json

# Page configuration
st.set_page_config(
    page_title="Medical Expenses Tracker",
    page_icon="🏥",
    layout="wide"
)

# Constants
FSA_TOTAL = 3400.00
SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
          'https://www.googleapis.com/auth/drive.readonly']

# Column mapping for the Google Sheet
COLUMNS = [
    'Provider',
    'In Portal',
    'Patient',
    'Amount',
    'Date of Service',
    'Bill Received',
    'Notes',
    'Photo'
]

def init_google_auth():
    """Initialize Google OAuth flow"""
    if 'credentials' not in st.session_state:
        st.session_state.credentials = None

    # Check if we have credentials in secrets (for deployment)
    if 'google_oauth' in st.secrets:
        client_config = {
            "web": {
                "client_id": st.secrets["google_oauth"]["client_id"],
                "client_secret": st.secrets["google_oauth"]["client_secret"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": st.secrets["google_oauth"]["redirect_uris"]
            }
        }
        return client_config
    return None

def get_sheets_client():
    """Get authenticated gspread client"""
    if st.session_state.credentials is None:
        return None

    creds = Credentials(
        token=st.session_state.credentials['token'],
        refresh_token=st.session_state.credentials.get('refresh_token'),
        token_uri=st.session_state.credentials.get('token_uri'),
        client_id=st.session_state.credentials.get('client_id'),
        client_secret=st.session_state.credentials.get('client_secret'),
        scopes=SCOPES
    )

    return gspread.authorize(creds)

def get_expenses_data(sheet):
    """Fetch all expenses from Google Sheet"""
    try:
        # Get all values from the sheet
        data = sheet.get_all_records()
        if not data:
            return pd.DataFrame(columns=COLUMNS)

        df = pd.DataFrame(data)

        # Convert Amount to float
        if 'Amount' in df.columns:
            df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)

        # Convert dates
        for date_col in ['Date of Service', 'Bill Received']:
            if date_col in df.columns:
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

        return df
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        return pd.DataFrame(columns=COLUMNS)

def add_expense(sheet, expense_data):
    """Add a new expense to the sheet"""
    try:
        # Prepare row data in correct column order
        row = [
            expense_data.get('Provider', ''),
            'TRUE' if expense_data.get('In Portal', False) else 'FALSE',
            expense_data.get('Patient', ''),
            expense_data.get('Amount', 0),
            expense_data.get('Date of Service', ''),
            expense_data.get('Bill Received', ''),
            expense_data.get('Notes', ''),
            expense_data.get('Photo', '')
        ]
        sheet.append_row(row)
        return True
    except Exception as e:
        st.error(f"Error adding expense: {str(e)}")
        return False

def update_expense(sheet, row_index, expense_data):
    """Update an existing expense"""
    try:
        # row_index is 0-based from dataframe, sheet is 1-based, +2 for header
        sheet_row = row_index + 2

        row = [
            expense_data.get('Provider', ''),
            'TRUE' if expense_data.get('In Portal', False) else 'FALSE',
            expense_data.get('Patient', ''),
            expense_data.get('Amount', 0),
            expense_data.get('Date of Service', ''),
            expense_data.get('Bill Received', ''),
            expense_data.get('Notes', ''),
            expense_data.get('Photo', '')
        ]

        for col_idx, value in enumerate(row, start=1):
            sheet.update_cell(sheet_row, col_idx, value)

        return True
    except Exception as e:
        st.error(f"Error updating expense: {str(e)}")
        return False

def delete_expense(sheet, row_index):
    """Delete an expense from the sheet"""
    try:
        # row_index is 0-based from dataframe, sheet is 1-based, +2 for header
        sheet_row = row_index + 2
        sheet.delete_rows(sheet_row)
        return True
    except Exception as e:
        st.error(f"Error deleting expense: {str(e)}")
        return False

def show_analytics(df):
    """Display analytics and FSA tracking"""
    st.header("📊 FSA Summary")

    if df.empty:
        st.info("No expenses recorded yet.")
        return

    total_spent = df['Amount'].sum()
    remaining = FSA_TOTAL - total_spent
    percentage_used = (total_spent / FSA_TOTAL) * 100

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total FSA Budget", f"${FSA_TOTAL:,.2f}")

    with col2:
        st.metric("Total Spent", f"${total_spent:,.2f}")

    with col3:
        st.metric("Remaining", f"${remaining:,.2f}",
                 delta=f"{percentage_used:.1f}% used",
                 delta_color="inverse")

    with col4:
        st.metric("Total Expenses", len(df))

    # Progress bar
    st.progress(min(percentage_used / 100, 1.0))

    # Breakdown by patient
    st.subheader("Spending by Patient")
    patient_totals = df.groupby('Patient')['Amount'].sum().sort_values(ascending=False)

    col1, col2 = st.columns(2)
    with col1:
        for patient, amount in patient_totals.items():
            st.metric(patient, f"${amount:,.2f}")

    with col2:
        if not patient_totals.empty:
            st.bar_chart(patient_totals)

def show_expenses_table(df, sheet):
    """Display and manage expenses table"""
    st.header("📋 All Expenses")

    if df.empty:
        st.info("No expenses recorded yet. Add your first expense below!")
        return

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        patient_filter = st.multiselect(
            "Filter by Patient",
            options=df['Patient'].unique().tolist(),
            default=df['Patient'].unique().tolist()
        )

    with col2:
        provider_search = st.text_input("Search Provider")

    with col3:
        year_filter = st.selectbox(
            "Filter by Year",
            options=['All'] + sorted(df['Date of Service'].dt.year.dropna().unique().tolist(), reverse=True),
            index=0
        )

    # Apply filters
    filtered_df = df.copy()

    if patient_filter:
        filtered_df = filtered_df[filtered_df['Patient'].isin(patient_filter)]

    if provider_search:
        filtered_df = filtered_df[filtered_df['Provider'].str.contains(provider_search, case=False, na=False)]

    if year_filter != 'All':
        filtered_df = filtered_df[filtered_df['Date of Service'].dt.year == year_filter]

    # Display table
    if filtered_df.empty:
        st.warning("No expenses match your filters.")
        return

    # Format for display
    display_df = filtered_df.copy()
    display_df['Amount'] = display_df['Amount'].apply(lambda x: f"${x:,.2f}")
    display_df['Date of Service'] = display_df['Date of Service'].dt.strftime('%Y-%m-%d')
    display_df['Bill Received'] = display_df['Bill Received'].dt.strftime('%Y-%m-%d')

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

    # Edit/Delete functionality
    st.subheader("Manage Expenses")

    expense_options = [f"{row['Provider']} - {row['Patient']} - ${row['Amount']} ({row['Date of Service'].strftime('%Y-%m-%d')})"
                       for idx, row in filtered_df.iterrows()]

    if expense_options:
        selected_expense = st.selectbox(
            "Select expense to edit/delete",
            options=range(len(expense_options)),
            format_func=lambda x: expense_options[x]
        )

        selected_row_idx = filtered_df.index[selected_expense]
        selected_data = filtered_df.iloc[selected_expense]

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Edit this expense", type="primary"):
                st.session_state.editing_expense = selected_row_idx

        with col2:
            if st.button("Delete this expense", type="secondary"):
                if st.confirm("Are you sure you want to delete this expense?"):
                    if delete_expense(sheet, selected_row_idx):
                        st.success("Expense deleted successfully!")
                        st.rerun()

def show_expense_form(sheet, edit_mode=False, expense_data=None, row_index=None):
    """Display form to add or edit an expense"""
    if edit_mode:
        st.header("✏️ Edit Expense")
    else:
        st.header("➕ Add New Expense")

    with st.form("expense_form", clear_on_submit=not edit_mode):
        col1, col2 = st.columns(2)

        with col1:
            provider = st.text_input(
                "Provider *",
                value=expense_data.get('Provider', '') if expense_data else ''
            )

            patient = st.selectbox(
                "Patient *",
                options=['Tim', 'Amber', 'Scarlett', 'Layla'],
                index=['Tim', 'Amber', 'Scarlett', 'Layla'].index(expense_data.get('Patient', 'Tim'))
                      if expense_data and expense_data.get('Patient') in ['Tim', 'Amber', 'Scarlett', 'Layla'] else 0
            )

            amount = st.number_input(
                "Amount *",
                min_value=0.0,
                value=float(expense_data.get('Amount', 0.0)) if expense_data else 0.0,
                step=0.01,
                format="%.2f"
            )

            in_portal = st.checkbox(
                "In Portal",
                value=expense_data.get('In Portal', False) if expense_data else False
            )

        with col2:
            date_service = st.date_input(
                "Date of Service *",
                value=pd.to_datetime(expense_data.get('Date of Service')).date()
                      if expense_data and pd.notna(expense_data.get('Date of Service')) else datetime.now().date()
            )

            bill_received = st.date_input(
                "Bill Received *",
                value=pd.to_datetime(expense_data.get('Bill Received')).date()
                      if expense_data and pd.notna(expense_data.get('Bill Received')) else datetime.now().date()
            )

            notes = st.text_area(
                "Notes",
                value=expense_data.get('Notes', '') if expense_data else ''
            )

            photo = st.text_input(
                "Photo URL (Google Drive link)",
                value=expense_data.get('Photo', '') if expense_data else '',
                help="Paste the Google Drive link to the receipt photo"
            )

        submitted = st.form_submit_button("Update Expense" if edit_mode else "Add Expense", type="primary")

        if submitted:
            if not provider or not patient or amount <= 0:
                st.error("Please fill in all required fields (Provider, Patient, Amount)")
                return False

            new_expense = {
                'Provider': provider,
                'In Portal': in_portal,
                'Patient': patient,
                'Amount': amount,
                'Date of Service': date_service.strftime('%Y-%m-%d'),
                'Bill Received': bill_received.strftime('%Y-%m-%d'),
                'Notes': notes,
                'Photo': photo
            }

            if edit_mode and row_index is not None:
                if update_expense(sheet, row_index, new_expense):
                    st.success("Expense updated successfully!")
                    st.session_state.editing_expense = None
                    st.rerun()
                    return True
            else:
                if add_expense(sheet, new_expense):
                    st.success("Expense added successfully!")
                    st.rerun()
                    return True

            return False

def main():
    st.title("🏥 Medical Expenses Tracker")

    # Initialize authentication
    client_config = init_google_auth()

    if client_config is None:
        st.error("⚠️ Google OAuth not configured. Please add credentials to Streamlit secrets.")
        st.info("""
        To configure Google OAuth:
        1. Go to Google Cloud Console
        2. Create OAuth 2.0 credentials
        3. Add credentials to Streamlit secrets

        See README.md for detailed instructions.
        """)
        return

    # Check if user is authenticated
    if st.session_state.credentials is None:
        st.warning("Please authenticate with Google to access your medical expenses.")

        # Note: In production, you'll need to implement proper OAuth flow
        # This is a simplified version for demonstration
        st.info("""
        **Authentication Setup Required**

        This app uses Google OAuth to securely access your Google Sheets.
        For local development and deployment instructions, see the README.md file.
        """)

        # For development: Allow manual token input (remove in production)
        with st.expander("Development: Manual Authentication"):
            st.warning("This is for development only. In production, use proper OAuth flow.")
            token_json = st.text_area("Paste your credentials JSON here")
            if st.button("Set Credentials"):
                try:
                    creds = json.loads(token_json)
                    st.session_state.credentials = creds
                    st.rerun()
                except:
                    st.error("Invalid JSON")

        return

    # Get Google Sheets client
    try:
        gc = get_sheets_client()

        # Get sheet URL from secrets or session state
        sheet_url = st.secrets.get("sheet_url", st.session_state.get("sheet_url", ""))

        if not sheet_url:
            sheet_url = st.text_input("Enter your Google Sheet URL:")
            if sheet_url:
                st.session_state.sheet_url = sheet_url
            else:
                st.info("Please enter your Google Sheet URL to continue.")
                return

        # Open the spreadsheet
        sheet = gc.open_by_url(sheet_url).sheet1

        # Fetch data
        df = get_expenses_data(sheet)

        # Show analytics
        show_analytics(df)

        st.divider()

        # Check if we're in edit mode
        if 'editing_expense' in st.session_state and st.session_state.editing_expense is not None:
            expense_data = df.loc[st.session_state.editing_expense].to_dict()
            show_expense_form(sheet, edit_mode=True, expense_data=expense_data,
                            row_index=st.session_state.editing_expense)

            if st.button("Cancel Edit"):
                st.session_state.editing_expense = None
                st.rerun()
        else:
            # Show add form
            show_expense_form(sheet)

        st.divider()

        # Show expenses table
        show_expenses_table(df, sheet)

    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {str(e)}")
        st.info("Make sure you've shared your Google Sheet with the service account or your authenticated Google account.")

if __name__ == "__main__":
    main()
