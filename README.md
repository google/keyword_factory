# Keyword Factory
Use different techniques to generate business relevant keywords, categorise them, and upload to the relevant campaigns at scale

This tool is a web app that can be easily deployed on GCP. It helps Google Ads users generate new keywords for their campaigns.

## Prerequisites

1. [A Google Ads Developer token](https://developers.google.com/google-ads/api/docs/first-call/dev-token#:~:text=A%20developer%20token%20from%20Google,SETTINGS%20%3E%20SETUP%20%3E%20API%20Center.)

1. A new GCP project with billing attached

1. Create OAuth2 Credentials of type **Web** and refresh token with scopes **"Google Ads API"** and **"Google Sheets API"**. Follow instructions in [this video](https://www.youtube.com/watch?v=KFICa7Ngzng)

1. [Enable Google ads API](https://developers.google.com/google-ads/api/docs/first-call/oauth-cloud-project#enable_the_in_your_project)

1. Enable Sheets API


## Installation

1. Click the big blue button to deploy:
   
   [![Run on Google Cloud](https://deploy.cloud.run/button.svg)](https://deploy.cloud.run)

1. Choose your designated GCP project and desired region.

1. Once installation is finished you will recieve your tool's URL. Save it.


## Usage

1. On first use - set you credentials under the "Authentication" tab and click "Save"

1. Under "Run Settings" tab, configure desired parameters

1. Choose if you want to run on all the accounts, selected specifics accouns, or all accounts under certain labels

1. Choose run type:

    1. Choose "Full Run" if you want to get all non-existing keyword recommendations from selected accounts and categorize them

    1. Choose "Filter Run" if you want to supply a CSV of keywords and have them categorized. (Use a csv file with one column and one keyword in each line)

1. Wait a few minutes for the run to complete. Once done, you will be provided with a link to the results spreadsheet.


## Costs

Costs are derived from GCP services usage and may vary dependaing on the frequancy of use, the size of tha accounts and the amount of keywords. Usage may also very likely stay in the free tier.
Costs can result from two services:
1. Categorization Service(NLP) - Monthly:
    1. If you stay below 30K keywords each month, this will be free.
    1. If you categorize between 30k-220k keywords, you will pay 2$ for each 1k keywords (max 440$)
1. Cloud Run services (Hosting and running the app)
    1. This will most likely remain in the free tier, but you can calculate estimated costs using [this calculator](https://cloud.google.com/products/calculator#id=)

## Disclaimer
This is not an officially supported Google product.