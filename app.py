# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from utils.config import Config
from utils.utils import get_all_child_accounts, get_account_labels, get_accounts_by_labels
from server import run
from io import StringIO
import streamlit as st
import yaml
import csv

OAUTH_HELP = """Refer to
        [Create OAuth2 Credentials](https://developers.google.com/google-ads/api/docs/client-libs/python/oauth-web#create_oauth2_credentials)
        for more information"""

RUN_TYPE_TOOLTIP = """Choose 'Full Run' to pull new keywords and categorize them. Choose 'Filter' to upload a CSV file with keywords to filter and categorize"""

FILE_UPLOAD_HELP = """Upload a CSV file with keywords you want to filter and categorize. Use a single column with one KW each line"""


def run_tool():
    run(st.session_state.config, st.session_state.accounts_selected, st.session_state.run_type, st.session_state.uploaded_kws)    
    results_url = config.spreadsheet_url
    st.success(f'Keyword Factory run completed successfully. [Open in Google Sheets]({results_url})', icon="✅")

def validate_config(config):
    if config.valid_config:
        st.session_state.valid_config = True
    else:
        st.session_state.valid_config = False

def update_btn_state():
    # Needed to cloes settings expander before starting to process
    st.session_state.run_btn_clicked = True 

def reset_config():
    st.session_state.valid_config=False
    st.session_state.config.valid_config = False


def initialize_session_state():
    if "valid_config" not in st.session_state:
        st.session_state.valid_config = False
    if "config" not in st.session_state:
        st.session_state.config = Config()
    if "accounts_for_ui" not in st.session_state:
        st.session_state.accounts_for_ui = []
    if "account_labels" not in st.session_state:
        st.session_state.account_labels = []

def authenticate(config_params):
    st.session_state.config.client_id = config_params['client_id']
    st.session_state.config.client_secret = config_params['client_secret']
    st.session_state.config.refresh_token = config_params['refresh_token']
    st.session_state.config.developer_token = config_params['developer_token']
    st.session_state.config.login_customer_id = config_params['login_customer_id']
   
    st.session_state.config.check_valid_config()
    st.session_state.valid_config = True 
    st.session_state.config.save_to_file()


def get_accounts_list():
    st.session_state.accounts_for_ui = get_all_child_accounts(st.session_state.config, True)

def get_label_list():
    st.session_state.account_labels = get_account_labels(st.session_state.config)

def value_placeholder(value):
    if value: return value
    else: return ''

def is_run_not_ready():
    if not st.session_state.valid_config:
        return True
    if st.session_state.all_accounts == "Selected Accounts" and st.session_state.accounts_selected == []:
        return True
    if st.session_state.all_accounts == "By Label" and st.session_state.labels_selected == []:
        return True
    if st.session_state.run_type == "Filter" and st.session_state.uploaded_kws == []:
        return True
    
    return False

# The Page UI starts here
st.set_page_config(
    page_title="Keyword Factory",
    page_icon="🏭",
    layout="centered",
)

customized_button = st.markdown("""
        <style >
            div.stButton {text-align:center}
        </style>""", unsafe_allow_html=True)

st.header("Keyword Factory 🏭")

initialize_session_state()
config = st.session_state.config
validate_config(config)

with st.expander("**Authentication**", expanded=not st.session_state.valid_config):
    if not st.session_state.valid_config:
        st.info(f"Credentials are not set. {OAUTH_HELP}", icon="⚠️")
        client_id = st.text_input("Client ID", value=value_placeholder(config.client_id))
        client_secret = st.text_input("Client Secret", value=value_placeholder(config.client_secret))
        refresh_token = st.text_input("Refresh Token", value=value_placeholder(config.refresh_token))
        developer_token = st.text_input("Developer Token", value=value_placeholder(config.developer_token))
        mcc_id = st.text_input("MCC ID", value=value_placeholder(config.login_customer_id))
        login_btn = st.button("Save", type='primary',on_click=authenticate, args=[{
            'client_id': client_id,
            'client_secret': client_secret,
            'refresh_token': refresh_token,
            'developer_token': developer_token,
            'login_customer_id': mcc_id
        }])
    else:
        st.success(f'Credentials succesfully set ', icon="✅")
        st.text_input("Client ID", value=config.client_id, disabled= True)
        st.text_input("Client Secret", value=config.client_secret, disabled= True)
        st.text_input("Refresh Token", value=config.refresh_token, disabled=True)
        st.text_input("Developer Token", value=config.developer_token, disabled= True)
        st.text_input("MCC ID", value=config.login_customer_id, disabled= True)
        edit = st.button("Edit Credentials", on_click=reset_config)

with st.expander("**Run Settings**", expanded=st.session_state.valid_config and ("run_btn_clicked" not in st.session_state or not st.session_state.run_btn_clicked)):

    # Accounts picker
    st.radio("Run on all accounts under MCC or selecet specific accounts", [
             "All Accounts", "Selected Accounts", "By Label"], index=0, key="all_accounts", label_visibility="visible")
    if st.session_state.all_accounts == 'Selected Accounts':
        if "accounts_for_ui" not in st.session_state or st.session_state.accounts_for_ui == []:
            get_accounts_list()
    
        accounts_selected_explicit = st.multiselect("Choose Accounts", st.session_state.accounts_for_ui)
    
        st.session_state.accounts_selected = [x.split(' - ')[0] for x in accounts_selected_explicit]
    
    elif st.session_state.all_accounts == 'All Accounts':
        st.session_state.accounts_selected = [] 
    
    elif st.session_state.all_accounts == 'By Label':
        if "account_labels" not in st.session_state or st.session_state.account_labels == []:
            get_label_list()

        st.session_state.labels_selected = st.multiselect("Choose Labels", st.session_state.account_labels)

   
    # Choose run type (full run / filter)
    st.radio("Choose run type: Full run or filter existing file", ["Full Run", "Filter"], index=0, key="run_type", help=RUN_TYPE_TOOLTIP)
   
    # If run type is filter, let them upload a file
    if st.session_state.run_type == "Filter":
        uploaded_file = st.file_uploader("Choose a CSV file", type=['csv'], help=FILE_UPLOAD_HELP)
        # Read file content to a list
        if uploaded_file is not None and not st.session_state.uploaded_kws:
            stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
            for row in csv.reader(stringio):
                st.session_state.uploaded_kws.append(row[0])
    else:
        st.session_state.uploaded_kws = []

st.session_state.run_btn_clicked = st.button("**Run**",type='primary', disabled=is_run_not_ready(), on_click=update_btn_state)

if st.session_state.run_btn_clicked:
    # Get accounts by label
    if st.session_state.all_accounts == 'By Label':
        st.session_state.accounts_selected = get_accounts_by_labels(st.session_state.config, st.session_state.labels_selected)
    # Get all child accounts
    if st.session_state.all_accounts == 'All Accounts':
        st.session_state.accounts_selected = get_all_child_accounts(st.session_state.config, False)

    with st.spinner(text='Factory running... This may take a few minutes'):
        run_tool()
