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

from typing import List

class Builder(object):
    def __init__(self, client, customer_id):
        self._service = client.get_service('GoogleAdsService')
        self._client = client
        self._customer_id = customer_id

    def _get_rows(self, query):
        search_request = self._client.get_type("SearchGoogleAdsStreamRequest")
        search_request.customer_id = self._customer_id
        search_request.query = query
        response = self._service.search_stream(request=search_request)
        return response


class MccBuilder(Builder):
    """Gets all client accounts' IDs under the MCC."""

    def __init__(self, client):
        super().__init__(client, client.login_customer_id)
        self._client = client

    def get_accounts(self, with_names=False):
        """Used to get all client accounts using API"""
        accounts = []
        query = '''
        SELECT
          customer_client.descriptive_name,
          customer_client.id
        FROM
          customer_client
        WHERE
          customer_client.manager = False
        AND customer_client.status = 'ENABLED'
    	'''

        rows = self._get_rows(query)
        for batch in rows:
            for row in batch.results:
                row = row._pb
                account = str(row.customer_client.id)
                if with_names:
                    account += ' - ' + str(row.customer_client.descriptive_name)
                accounts.append(account)

        return accounts
    
    def get_labels(self):
        """Gets all account labels from the main MCC"""

        labels = set()
        rows = self._get_rows("""
        SELECT
            label.name
        FROM
            label
        """) 

        for batch in rows:
            for row in batch.results:
                row = row._pb
                labels.add(row.label.name)

        return list(labels)

    def get_accounts_by_label(self, labels: List[str]):
        """Get all child accounts that have any of the given labels."""
    
        # First we get all resource names for all given labels.
        # A single label can have multiple resource names (IDs),
        # one for each account they are linked to. 
        label_rows = self._get_rows(f"""
        SELECT
            label.resource_name
        FROM
            label
        WHERE
            label.name IN ({", ".join([f"'{elem}'" for elem in labels])})
        """)

        labels_resource_names = []
        for batch in label_rows:
            for row in batch.results:
                row = row._pb
                labels_resource_names.append(row.label.resource_name)

        
        # Next we get all the child accounts that have the specified labels
        # applied to them. We have to use resource names for that.
        accounts_rows = self._get_rows(f"""
        SELECT 
            customer_client.id, 
            customer_client.descriptive_name 
        FROM customer_client 
        WHERE 
            customer_client.manager = False
        AND
            customer_client.status = 'ENABLED'
        AND
            customer_client.applied_labels CONTAINS ANY ({", ".join([f"'{elem}'" for elem in labels_resource_names])})
        """)
        accounts = []
        for batch in accounts_rows:
            for row in batch.results:
                row = row._pb
                accounts.append(row.customer_client.id)
        
        return accounts
    

class RecBuilder(Builder):
    """Gets Keywords recommendations from a single account."""

    def build(self):
        rows = self._get_rows("""
        SELECT
          recommendation.keyword_recommendation
        FROM recommendation
        """)

        recommendations = []

        for batch in rows:
            for row in batch.results:
                row = row._pb
                recommendations.append(row.recommendation.keyword_recommendation.keyword.text)
        return recommendations
    

class KeywordRemover(Builder):
    """Gets Keywords from a single account, removes from rec list"""
    def build(self, kw_rec):
        rows = self._get_rows('''
        SELECT 
            ad_group_criterion.keyword.text 
        FROM ad_group_criterion 
        WHERE 
            campaign.status = 'ENABLED' 
            AND ad_group.status = 'ENABLED' 
            AND ad_group_criterion.type = 'KEYWORD' 
        ''')
        for batch in rows:
            for row in batch.results:
                try:
                    kw_rec.remove(row.ad_group_criterion.keyword.text)
                except:
                    pass
