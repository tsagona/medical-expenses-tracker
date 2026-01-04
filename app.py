import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Medical Expenses Tracker",
    page_icon="🏥",
    layout="wide"
)

# Constants
FSA_TOTAL = 3400.00

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

@st.cache_resource
def get_sheets_client():
    """Get authenticated gspread client using service account"""
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    # Get credentials from Streamlit secrets
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes
    )

    return gspread.authorize(credentials)

@st.cache_data(ttl=10)
def get_expenses_data(_sheet):
    """Fetch all expenses from Google Sheet"""
    try:
        # Get all values from the sheet
        data = _sheet.get_all_records()
        if not data:
            return pd.DataFrame(columns=COLUMNS)

        df = pd.DataFrame(data)

        # Clean up Amount column - handle different formats
        if 'Amount' in df.columns:
            # Remove $ and commas if present
            if df['Amount'].dtype == 'object':
                df['Amount'] = df['Amount'].astype(str).str.replace('$', '').str.replace(',', '')
            df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)

        # Convert In Portal to boolean
        if 'In Portal' in df.columns:
            df['In Portal'] = df['In Portal'].astype(str).str.upper().isin(['TRUE', 'YES', '1'])

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
        sheet.append_row(row, value_input_option='USER_ENTERED')
        get_expenses_data.clear()  # Clear cache
        return True
    except Exception as e:
        st.error(f"Error adding expense: {str(e)}")
        return False

def update_expense(sheet, row_index, expense_data):
    """Update an existing expense"""
    try:
        # row_index is 0-based from dataframe, sheet is 1-based, +2 for header
        sheet_row = row_index + 2

        updates = [
            {'range': f'A{sheet_row}', 'values': [[expense_data.get('Provider', '')]]},
            {'range': f'B{sheet_row}', 'values': [['TRUE' if expense_data.get('In Portal', False) else 'FALSE']]},
            {'range': f'C{sheet_row}', 'values': [[expense_data.get('Patient', '')]]},
            {'range': f'D{sheet_row}', 'values': [[expense_data.get('Amount', 0)]]},
            {'range': f'E{sheet_row}', 'values': [[expense_data.get('Date of Service', '')]]},
            {'range': f'F{sheet_row}', 'values': [[expense_data.get('Bill Received', '')]]},
            {'range': f'G{sheet_row}', 'values': [[expense_data.get('Notes', '')]]},
            {'range': f'H{sheet_row}', 'values': [[expense_data.get('Photo', '')]]}
        ]

        sheet.batch_update(updates, value_input_option='USER_ENTERED')
        get_expenses_data.clear()  # Clear cache
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
        get_expenses_data.clear()  # Clear cache
        return True
    except Exception as e:
        st.error(f"Error deleting expense: {str(e)}")
        return False

def show_analytics(df):
    """Display analytics and FSA tracking"""
    st.header("📊 FSA Summary")

    if df.empty:
        st.info("No expenses recorded yet.")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total FSA Budget", f"${FSA_TOTAL:,.2f}")
        with col2:
            st.metric("Total Spent", "$0.00")
        with col3:
            st.metric("Remaining", f"${FSA_TOTAL:,.2f}")
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
                 delta=f"-{percentage_used:.1f}%" if percentage_used > 0 else "0%",
                 delta_color="inverse")

    with col4:
        st.metric("Total Expenses", len(df))

    # Progress bar
    st.progress(min(percentage_used / 100, 1.0))
    if percentage_used >= 90:
        st.warning(f"⚠️ You've used {percentage_used:.1f}% of your FSA budget!")
    elif percentage_used >= 100:
        st.error(f"🚨 You've exceeded your FSA budget by ${total_spent - FSA_TOTAL:,.2f}!")

    # Breakdown by patient
    st.subheader("Spending by Patient")
    patient_totals = df.groupby('Patient')['Amount'].sum().sort_values(ascending=False)

    if not patient_totals.empty:
        col1, col2 = st.columns([1, 2])
        with col1:
            for patient, amount in patient_totals.items():
                percentage = (amount / total_spent) * 100 if total_spent > 0 else 0
                st.metric(patient, f"${amount:,.2f}", f"{percentage:.1f}%")

        with col2:
            st.bar_chart(patient_totals)

def show_expenses_table(df, sheet):
    """Display and manage expenses table"""
    st.header("📋 All Expenses")

    if df.empty:
        st.info("No expenses recorded yet. Add your first expense below or use the Google Form on your phone!")
        return

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        patient_filter = st.multiselect(
            "Filter by Patient",
            options=sorted(df['Patient'].unique().tolist()),
            default=sorted(df['Patient'].unique().tolist())
        )

    with col2:
        provider_search = st.text_input("Search Provider")

    with col3:
        years = sorted(df['Date of Service'].dt.year.dropna().unique().tolist(), reverse=True)
        year_filter = st.selectbox(
            "Filter by Year",
            options=['All'] + [int(y) for y in years],
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

    # Sort by date (most recent first)
    filtered_df = filtered_df.sort_values('Date of Service', ascending=False)

    # Format for display
    display_df = filtered_df.copy()
    display_df['Amount'] = display_df['Amount'].apply(lambda x: f"${x:,.2f}")
    display_df['Date of Service'] = display_df['Date of Service'].dt.strftime('%Y-%m-%d')
    display_df['Bill Received'] = display_df['Bill Received'].dt.strftime('%Y-%m-%d')
    display_df['In Portal'] = display_df['In Portal'].apply(lambda x: '✓' if x else '')

    # Make photo column clickable
    if 'Photo' in display_df.columns:
        display_df['Photo'] = display_df['Photo'].apply(
            lambda x: f'[View]({x})' if x and str(x).startswith('http') else ''
        )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Photo": st.column_config.LinkColumn("Receipt")
        }
    )

    st.caption(f"Showing {len(filtered_df)} of {len(df)} expenses")

    # Edit/Delete functionality
    if len(filtered_df) > 0:
        st.subheader("✏️ Manage Expenses")

        expense_options = [
            f"{row['Provider']} - {row['Patient']} - ${row['Amount']:.2f} ({row['Date of Service'].strftime('%Y-%m-%d')})"
            for idx, row in filtered_df.iterrows()
        ]

        selected_expense = st.selectbox(
            "Select expense to edit/delete",
            options=range(len(expense_options)),
            format_func=lambda x: expense_options[x],
            key="expense_selector"
        )

        selected_row_idx = filtered_df.index[selected_expense]
        selected_data = filtered_df.iloc[selected_expense]

        col1, col2 = st.columns(2)

        with col1:
            if st.button("✏️ Edit this expense", type="primary", use_container_width=True):
                st.session_state.editing_expense = selected_row_idx
                st.rerun()

        with col2:
            if st.button("🗑️ Delete this expense", type="secondary", use_container_width=True):
                with st.form("confirm_delete"):
                    st.warning(f"Are you sure you want to delete this expense?\n\n{expense_options[selected_expense]}")
                    col1, col2 = st.columns(2)
                    with col1:
                        confirm = st.form_submit_button("Yes, delete", type="primary", use_container_width=True)
                    with col2:
                        cancel = st.form_submit_button("Cancel", use_container_width=True)

                    if confirm:
                        if delete_expense(sheet, selected_row_idx):
                            st.success("✅ Expense deleted successfully!")
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
                value=expense_data.get('Provider', '') if expense_data else '',
                help="Name of the medical provider (e.g., Dr. Smith, ABC Hospital)"
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
                format="%.2f",
                help="Dollar amount of the medical expense"
            )

            in_portal = st.checkbox(
                "In Portal",
                value=bool(expense_data.get('In Portal', False)) if expense_data else False,
                help="Check if this bill is available in the provider's online portal"
            )

        with col2:
            date_service = st.date_input(
                "Date of Service *",
                value=pd.to_datetime(expense_data.get('Date of Service')).date()
                      if expense_data and pd.notna(expense_data.get('Date of Service')) else datetime.now().date(),
                help="When the medical service was provided"
            )

            bill_received = st.date_input(
                "Bill Received *",
                value=pd.to_datetime(expense_data.get('Bill Received')).date()
                      if expense_data and pd.notna(expense_data.get('Bill Received')) else datetime.now().date(),
                help="When you received the bill"
            )

            notes = st.text_area(
                "Notes",
                value=expense_data.get('Notes', '') if expense_data else '',
                help="Any additional information about this expense"
            )

            photo = st.text_input(
                "Photo URL (Google Drive link)",
                value=expense_data.get('Photo', '') if expense_data else '',
                help="Paste the Google Drive link to the receipt photo"
            )

        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button(
                "💾 Update Expense" if edit_mode else "➕ Add Expense",
                type="primary",
                use_container_width=True
            )
        with col2:
            if edit_mode:
                cancel = st.form_submit_button("Cancel", use_container_width=True)
                if cancel:
                    st.session_state.editing_expense = None
                    st.rerun()

        if submitted:
            if not provider or not patient or amount <= 0:
                st.error("❌ Please fill in all required fields (Provider, Patient, Amount > 0)")
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
                    st.success("✅ Expense updated successfully!")
                    st.session_state.editing_expense = None
                    st.rerun()
                    return True
            else:
                if add_expense(sheet, new_expense):
                    st.success("✅ Expense added successfully!")
                    st.rerun()
                    return True

            return False

def main():
    st.title("🏥 Medical Expenses Tracker")
    st.caption("Track your medical expenses for FSA reimbursement")

    try:
        # Get Google Sheets client
        gc = get_sheets_client()

        # Get sheet URL from secrets
        sheet_url = st.secrets.get("sheet_url", "")

        if not sheet_url:
            st.error("⚠️ Sheet URL not configured in secrets.")
            st.info("Please add your Google Sheet URL to Streamlit secrets.")
            return

        # Open the spreadsheet
        spreadsheet = gc.open_by_url(sheet_url)

        # Try to use the first sheet, or a specific sheet name
        sheet_name = st.secrets.get("sheet_name", "Sheet1")
        try:
            sheet = spreadsheet.worksheet(sheet_name)
        except:
            # If sheet_name doesn't exist, use the first sheet
            sheet = spreadsheet.sheet1

        # Fetch data
        df = get_expenses_data(sheet)

        # Show analytics
        show_analytics(df)

        st.divider()

        # Check if we're in edit mode
        if 'editing_expense' in st.session_state and st.session_state.editing_expense is not None:
            try:
                expense_data = df.loc[st.session_state.editing_expense].to_dict()
                show_expense_form(sheet, edit_mode=True, expense_data=expense_data,
                                row_index=st.session_state.editing_expense)
            except KeyError:
                st.warning("The expense you were editing no longer exists.")
                st.session_state.editing_expense = None
                st.rerun()
        else:
            # Show add form
            show_expense_form(sheet)

        st.divider()

        # Show expenses table
        show_expenses_table(df, sheet)

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        st.info("""
        **Troubleshooting:**
        - Make sure your Google Sheet is shared with the service account email
        - Verify the sheet URL in Streamlit secrets is correct
        - Check that the Google Sheets API is enabled in your Google Cloud project
        """)

        with st.expander("Error Details"):
            st.code(str(e))

if __name__ == "__main__":
    main()
