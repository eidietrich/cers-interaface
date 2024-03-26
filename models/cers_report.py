import requests
import pandas as pd
from io import StringIO

from datetime import date
from datetime import datetime
from dateutil.parser import parse

import os
import json
import csv

import re
from bs4 import BeautifulSoup

from manual.config import MANUAL_CONTRIBUTION_CACHES
from manual.config import MANUAL_SUMMARY_CACHES

class Report:
    def __init__(self, data, cachePath, checkCache=True, writeCache=True, fetchFullReports=True):
        self.id = data['reportId']
        self.data = data
        self.type = data['formTypeCode']
        self.start_date = data['fromDateStr']
        self.end_date = data['toDateStr']
        self.label = f'{self.start_date} to {self.end_date}'

        self.fetchFullReports = fetchFullReports

        self.contributions = pd.DataFrame()
        self.expenditures = pd.DataFrame()

        filePath = os.path.join(cachePath, f'{self.type}-{self.id}.json')

        if checkCache and os.path.isfile(filePath):
            self._get_cached_data(filePath)
            # This checks for updates and reroutes for newly amended forms
        elif (self.type == 'C4'):
            self._get_c4_data_from_scrape()
        elif (self.type == 'C5'):
            if self.id in MANUAL_CONTRIBUTION_CACHES.keys():
                # Files that are too big to reliably download from CERS
                # Downloaded once separately and plugged into manual cache system as a workaround
                self._get_c5_data_from_manual_cache()
            else:
                self._get_c5_data_from_scrape()
        elif (self.type == 'C7'):
            self._get_c7_data_from_scrape()
        elif (self.type == 'C7E'):
            self._get_c7e_data_from_scrape()
        elif (self.type == 'C6'):
            self._get_c6_data_from_scrape()
        else:
            print('Warning - unhandled report type', self.type, self.id)
            self.expenditures = pd.DataFrame()
            self.contributions = pd.DataFrame()
            self.unitemized_contributions = 0
            self.summary = {
                'report_start_date': self.start_date,
                'report_end_date': self.end_date,
            }

        # Add cache
        if writeCache:
            if not os.path.exists(cachePath):
                os.makedirs(cachePath)
            self.export(filePath)

    def _get_cached_data(self, file_path):
        print(
            f'--- From cache, loading {self.type} {self.start_date}-{self.end_date} ({self.id})')
        with open(file_path) as f:
            cache = json.load(f)

        if (('data' in cache) and (cache['data']['amendedDate'] == self.data['amendedDate'])):
            self.summary = cache['summary']
            self.contributions = pd.read_json(cache['contributions'])
            self.expenditures = pd.read_json(cache['expenditures'])
            self.unitemized_contributions = self._calc_unitemized_contributions()
        else:
            print(f'----- Actually, amendment found on {self.id}')
            if self.id in MANUAL_CONTRIBUTION_CACHES.keys():
                if (self.type != 'C5'):
                    print('Wrong report type')
                self._get_c5_data_from_manual_cache()
            elif self.type == 'C4':
                self._get_c4_data_from_scrape()
            elif self.type == 'C5':
                self._get_c5_data_from_scrape()
            elif self.type == 'C7':
                self._get_c7_data_from_scrape()
            elif self.type == 'C7E':
                self._get_c7e_data_from_scrape()
            elif (self.type == 'C6'):
                self._get_c6_data_from_scrape()
            else:
                print('Bad cache on unhandled report type', self.type)

    def _get_c4_data_from_scrape(self):
        # Same code as C6 — maybe refactor?
        print(f'Fetching C4 {self.start_date}-{self.end_date} ({self.id})')

        post_url = 'https://cers-ext.mt.gov/CampaignTracker/public/viewFinanceReport/retrieveReport'
        post_payload = {
            'committeeId': self.data['committeeId'],
            'reportId': self.id,
            'searchPage': 'public'
        }
        session = requests.Session()
        p = session.post(post_url, post_payload)
        text = p.text

        # Parse report
        soup = BeautifulSoup(text, 'html.parser')
        labels = [
            'previous report',
            'Receipts',
            'Expenditures',
            'Ending Balance',
        ]
        table = soup.find('div', id='summaryAccordionId').find('table')
        parsed = {label: self._committee_parse_html_get_row(
            table, label) for label in labels}
        parsed['report_start_date'] = self.start_date
        parsed['report_end_date'] = self.end_date
        self.summary = parsed

        if self.fetchFullReports:
            self.contributions = self._fetch_form_schedule(
                'C4A', self.data['committeeName'])
            self.expenditures = self._fetch_form_schedule(
                'C4B', self.data['committeeName'])

            # Unnecessary for political committees?
            self.unitemized_contributions = self._calc_unitemized_contributions()

    def _get_c5_data_from_manual_cache(self):
        file = MANUAL_CONTRIBUTION_CACHES[self.id]
        print(f'Fetching manual cache {file}')
        self.summary = self._fetch_report_summary()
        if self.fetchFullReports:
            self.contributions = self._fetch_form_schedule(
                'A', self.data['candidateName'])
            self.expenditures = self._fetch_form_schedule(
                'B', self.data['candidateName'])
            # TODO - move this to cleaning step?
            self.unitemized_contributions = self._calc_unitemized_contributions()

    def _get_c5_data_from_scrape(self):
        print(f'Fetching C5 {self.start_date}-{self.end_date} ({self.id})')
        self.summary = self._fetch_report_summary()
        if self.fetchFullReports:
            self.contributions = self._fetch_form_schedule(
                'A', self.data['candidateName'])
            self.expenditures = self._fetch_form_schedule(
                'B', self.data['candidateName'])

            # TODO - move this to cleaning step?
            self.unitemized_contributions = self._calc_unitemized_contributions()

    def _get_c7_data_from_scrape(self):
        print(f'Fetching C7 {self.start_date}-{self.end_date} ({self.id})')

        post_url = 'https://cers-ext.mt.gov/CampaignTracker/public/viewFinanceReport/retrieveReport'
        if 'candidateId' in self.data:
            post_payload = {
                'candidateId': self.data['candidateId'],
                'reportId': self.id,
                'searchPage': 'public'
            }
        elif 'committeeId' in self.data:
            post_payload = {
                'committeeId': self.data['committeeId'],
                'reportId': self.id,
                'searchPage': 'public'
            }
        session = requests.Session()
        session.post(post_url, post_payload)

        # C7 reports contain a bunch of different tables - need to parse each individually
        detail_url = 'https://cers-ext.mt.gov/CampaignTracker/public/viewFinanceReport/financeRepDetailList'

        individual_raw = session.post(detail_url, {'listName': "individual"})
        individual = self._parse_c7_table(individual_raw)

        committees_raw = session.post(detail_url, {'listName': "committee"})
        committees = self._parse_c7_table(committees_raw)

        loans_raw = session.post(detail_url, {'listName': "loan"})
        loans = self._parse_c7_table(loans_raw)

        # For time being, just check other categories are null
        candidate_raw = session.post(detail_url, {'listName': "candidate"})
        if (candidate_raw.json() != []):
            print('## Need to handle C7 candidate self contributions')

        fundraisers_raw = session.post(detail_url, {'listName': "fundraisers"})
        if (fundraisers_raw.json() != []):
            print('## Need to handle C7 fundraiers')

        refunds_raw = session.post(detail_url, {'listName': "refunds"})
        if (refunds_raw.json() != []):
            print('## Need to handle C7 refunds')

        payments_raw = session.post(detail_url, {'listName': "payment"})
        if (payments_raw.json() != []):
            print('## Need to handle C7 payments')

        # print('B',pd.DataFrame(individual).iloc[3])
        contributions = pd.DataFrame(individual + committees + loans)
        expenditures = pd.DataFrame()  # Reported w/ C7E

        if (len(contributions) > 0):
            pri_receipts = contributions[contributions['Election Type']
                                         == 'Primary']['Amount'].sum()
            gen_receipts = contributions[contributions['Election Type']
                                         == 'General']['Amount'].sum()
            total = contributions['Amount'].sum()
        else:
            pri_receipts = 0
            gen_receipts = 0
            total = 0

        self.expenditures = expenditures
        self.contributions = contributions
        self.unitemized_contributions = 0
        self.summary = {
            'report_start_date': self.start_date,
            'report_end_date': self.end_date,
            "Receipts": {
                "primary": pri_receipts,
                "general": gen_receipts,
                "total": total,
            },
            "Expenditures": {
                "primary": 0,
                "general": 0,
                "total": 0
            },
        }

    def _get_c7e_data_from_scrape(self):
        print(f'Fetching C7E {self.start_date}-{self.end_date} ({self.id})')
        # print(self.data)

        post_url = 'https://cers-ext.mt.gov/CampaignTracker/public/viewFinanceReport/retrieveReport'

        if 'candidateId' in self.data:
            post_payload = {
                'candidateId': self.data['candidateId'],
                'reportId': self.id,
                'searchPage': 'public'
            }
        elif 'committeeId' in self.data:
            post_payload = {
                'committeeId': self.data['committeeId'],
                'reportId': self.id,
                'searchPage': 'public'
            }

        # post_payload = {
        #     'candidateId': self.data['candidateId'],
        #     'reportId': self.id,
        #     'searchPage': 'public'
        # }
        session = requests.Session()
        session.post(post_url, post_payload)

        detail_url = 'https://cers-ext.mt.gov/CampaignTracker/public/viewFinanceReport/financeRepDetailList'

        expenditures_raw = session.post(
            detail_url, {'listName': "expendOther"})
        expenditures = self._parse_c7e_table(expenditures_raw)

        # Unhandled for now
        candidate_raw = session.post(detail_url, {'listName': "candidate"})
        if (candidate_raw.json() != []):
            print('## Need to handle C7E candidate expenditures')

        pettycash_raw = session.post(detail_url, {'listName': "pettyCash"})
        if (pettycash_raw.json() != []):
            print('## Need to handle C7E petty cash')

        debt_raw = session.post(detail_url, {'listName': "debtLoan"})
        if (debt_raw.json() != []):
            print('## Need to handle debts --')

        expenditures = pd.DataFrame(expenditures)
        self.expenditures = expenditures
        self.contributions = pd.DataFrame()
        self.unitemized_contributions = 0

        if (len(expenditures) > 0):
            pri_exp = expenditures[expenditures['Election Type']
                                   == 'Primary']['Amount'].sum()
            gen_exp = expenditures[expenditures['Election Type']
                                   == 'General']['Amount'].sum()
            total = expenditures['Amount'].sum()
        else:
            pri_exp = 0
            gen_exp = 0
            total = 0

        self.summary = {
            'report_start_date': self.start_date,
            'report_end_date': self.end_date,
            'Receipts': {
                "primary": 0,
                "general": 0,
                "total": 0
            },
            'Expenditures': {
                "primary": pri_exp,
                "general": gen_exp,
                "total": total,
            }
        }

    def _get_c6_data_from_scrape(self):
        print(f'Fetching C6 {self.start_date}-{self.end_date} ({self.id})')
        # print(self.data)

        post_url = 'https://cers-ext.mt.gov/CampaignTracker/public/viewFinanceReport/retrieveReport'
        post_payload = {
            'committeeId': self.data['committeeId'],
            'reportId': self.id,
            'searchPage': 'public'
        }
        session = requests.Session()
        p = session.post(post_url, post_payload)
        text = p.text

        # Parse report
        soup = BeautifulSoup(text, 'html.parser')
        labels = [
            'previous report',
            'Receipts',
            'Expenditures',
            'Ending Balance',
        ]
        table = soup.find('div', id='summaryAccordionId').find('table')
        parsed = {label: self._committee_parse_html_get_row(
            table, label) for label in labels}
        parsed['report_start_date'] = self.start_date
        parsed['report_end_date'] = self.end_date
        self.summary = parsed

        if self.fetchFullReports:
            self.contributions = self._fetch_form_schedule(
                'C6A', self.data['committeeName'])
            self.expenditures = self._fetch_form_schedule(
                'C6B', self.data['committeeName'])

            # Unnecessary for political committees?
            self.unitemized_contributions = self._calc_unitemized_contributions()

    def export(self, filePath):
        output = {
            'data': self.data,
            'summary': self.summary,
            'contributions': self.contributions.to_json(orient='records'),
            'expenditures': self.expenditures.to_json(orient='records'),
            'unitemized_contributions': self.unitemized_contributions,
        }
        with open(filePath, 'w') as f:
            json.dump(output, f, indent=4)
        # print(f'Cached to {filePath}')

    def _fetch_report_summary(self):
        if self.id in MANUAL_SUMMARY_CACHES.keys():
            print(f'--- Report summary from cache ({self.id})')
            path = MANUAL_SUMMARY_CACHES[self.id]
            with open(path, 'r') as f:
                text = f.read()
        else:
            post_url = 'https://cers-ext.mt.gov/CampaignTracker/public/viewFinanceReport/retrieveReport'
            post_payload = {
                'candidateId': self.data['candidateId'],
                'reportId': self.id,
                'searchPage': 'public'
            }
            session = requests.Session()
            p = session.post(post_url, post_payload)
            text = p.text

        # Parse report
        soup = BeautifulSoup(text, 'html.parser')
        labels = [
            'previous report',
            'Receipts',
            'Expenditures',
            'Ending Balance',
        ]
        table = soup.find('div', id='summaryAccordionId').find('table')
        parsed = {label: self._parse_html_get_row(
            table, label) for label in labels}
        parsed['report_start_date'] = self.start_date
        parsed['report_end_date'] = self.end_date
        return parsed

    # def _fetch_contributions_schedule(self):
    #     return self._fetch_c5_schedule('A')

    # def _fetch_expenditures_schedule(self):
    #     return self._fetch_c5_schedule('B')

    # def _fetch_c5_schedule(self, schedule):
    #     report_id = self.id
    #     candidate_name = self.data['candidateName']

    #     raw_text = ''

    #     post_url = 'https://cers-ext.mt.gov/CampaignTracker/public/viewFinanceReport/prepareDownloadFileFromSearch'
    #     get_url = 'https://cers-ext.mt.gov/CampaignTracker/public/viewFinanceReport/downloadFile'
    #     post_payload = {
    #         'reportId': report_id,  # This is from checkbox on candidate report page
    #         'scheduleCode': schedule,  # A is contributions, # B is expenditures
    #         'fname': candidate_name,
    #     }

    #     session = requests.Session()
    #     p = session.post(post_url, post_payload, timeout=120)
    #     if 'fileName' in p.json():
    #         r = session.get(get_url, params=p.json())
    #         if r.text == '':
    #             print('Empty file. Report ID:', report_id)
    #         raw_text = r.text
    #     else:
    #         print(
    #             f'No file for schedule {schedule}, {self.start_date}-{self.end_date}. Report ID:', report_id)

    #     parsed_text = self._parse_schedule_text(raw_text)

    #     return parsed_text

    def _fetch_form_schedule(self, schedule, name):
        # Fetches downloads for itemized contributions/expenditures of C5 and C6 forms
        report_id = self.id
        raw_text = ''

        if (schedule == 'A' and self.id in MANUAL_CONTRIBUTION_CACHES.keys()):
            print(f'--- Contributions from cache ({self.id})')
            path = MANUAL_CONTRIBUTION_CACHES[self.id]
            with open(path, 'r') as f:
                raw_text = f.read()
        else:
            post_url = 'https://cers-ext.mt.gov/CampaignTracker/public/viewFinanceReport/prepareDownloadFileFromSearch'
            get_url = 'https://cers-ext.mt.gov/CampaignTracker/public/viewFinanceReport/downloadFile'
            post_payload = {
                'reportId': report_id,  # This is from checkbox on candidate report page
                'scheduleCode': schedule,  # A is contributions, # B is expenditures
                'fname': name,  # Either candidate or committee name
            }

            session = requests.Session()
            p = session.post(post_url, post_payload, timeout=120)
            if 'fileName' in p.json():
                r = session.get(get_url, params=p.json())
                if r.text == '':
                    print('Empty file. Report ID:', report_id)
                raw_text = r.text
            else:
                print(
                    f'No file for schedule {schedule}, {self.start_date}-{self.end_date}. Report ID:', report_id)

        parsed_text = self._parse_schedule_text(raw_text)
        return parsed_text

    def _parse_schedule_text(self, text):
        if (text == ''):
            return pd.DataFrame()
        parsed = pd.read_csv(StringIO(
            text), sep='|', on_bad_lines='warn', index_col=False, quoting=csv.QUOTE_NONE)
        return parsed

    def _parse_html_get_row(self, table, label):
        # For candidates, where pri/general distinction matters
        # label can be partial text or regex
        row = table.find('td', text=re.compile(label)).parent
        # replaces remove "$" and "," from strings
        pri = self._clean_value(row.find_all('td')[2].text)
        gen = self._clean_value(row.find_all('td')[3].text)
        return {
            'primary': pri,
            'general': gen,
            'total': round(pri + gen, 2),
        }

    def _committee_parse_html_get_row(self, table, label):
        # label can be partial text or regex
        row = table.find('td', text=re.compile(label)).parent
        # replaces remove "$" and "," from strings
        total = self._clean_value(row.find_all('td')[2].text)
        # Keeping extra hierarchy here to maintain parallelism w/ committee reports
        return {
            'total': total
        }

    def _parse_c7_table(self, raw):
        cleaned = []
        if( raw.text == ""): return cleaned # null response
        for row in raw.json():
            addressLn1, city, state, zip_code = self._parse_address(
                row['entityAddress'])
            date = self._parse_date(row['datePaid'])
            if (row['cashAmt'] > 0 and row['inKindAmt'] > 0):
                amount_type = 'Mixed'
            elif (row['cashAmt'] > 0):
                amount_type = 'CA'
            elif (row['inKindAmt'] > 0):
                amount_type = 'IK'
            cleaned.append({
                # 'Candidate': candidate, # added at Candidate object level
                # 'Reporting Period': self.label, # added at Candidate object level
                'Date Paid': date,
                'Entity Name': row['entityName'],
                'First Name': '',
                'Middle Initial': '',
                'Last Name': '',
                'Addr Line1': addressLn1,
                'City': city,
                'State': state,
                'Zip': zip_code,
                'Zip4': '',
                'Country': '',
                'Occupation': row['occupationDescr'],
                'Employer': row['employerDescr'],
                'Contribution Type': row['lineItemCompositeDescr'],
                'Amount': row['totalAmt'],
                'Amount Type': amount_type,
                'Purpose': row['purposeDescr'],
                'Election Type': row['amountTypeDescr'],
                'Total Primary': row['totalToDatePrimary'],
                'Total General': row['totalToDateGeneral'],
                'Refund Transaction Type': '',
                'Refund Original Transaction Date': row['refundOrigTransDate'],
                'Refund Original Transaction Total': row['refundOrigTransTotalVal'],
                'Refund Original Transaction Descr': row['refundOrigTransDesc'],
                'Previous Transaction (Y/N)': row['previousTransactionInd'],
                'Fundraiser Name': row['fundraiserName'],
                'Fundraiser Location': row['fundraiserLocation'],
                'Fundraiser Attendees': row['fundraiserAttendees'],
                'Fundraiser Tickets Sold': row['fundraiserTicketsSold'],
            })
        return cleaned

    def _parse_c7e_table(self, raw):
        cleaned = []
        for row in raw.json():
            addressLn1, city, state, zip_code = self._parse_address(
                row['entityAddress'])
            date = self._parse_date(row['datePaid'])
            cleaned.append({
                'Date Paid': date,
                'Entity Name': row['entityName'],
                'First Name': '',
                'Middle Initial': '',
                'Last Name': '',
                'Addr Line1': addressLn1,
                'City': city,
                'State': state,
                'Zip': zip_code,
                'Zip4': '',
                'Expenditure Type': row['lineItemCompositeDescr'],
                'Amount': row['totalAmt'],
                'Purpose': row['purposeDescr'],
                'Election Type': row['amountTypeDescr'],
                'Expenditure Paid Communications Platform': row['expenditurePaidCommPlatform'],
                'Expenditure Paid Communications Quantity': row['expenditurePaidCommQuantity'],
                'Expenditure Paid Communications Subject Matter': row['expenditurePaidCommSubMatter']
            })
        return cleaned

    # TODO: Dedupe with cers_committees
    def _parse_address(self, raw):
        if (raw == ''):
            return '','','',''
        # Assumes address format '1008 Prospect Ave, Helena, MT 59601'
        # Edge cases will be a pain in the ass here
        address = raw.replace(
            'Washington, DC', 'Washington DC, DC').split(', ')
        addressLn1 = (', ').join(address[0:len(address)-2])
        city = address[-2].strip()
        state_zip = address[-1].split(' ')
        state = state_zip[0]
        if (len(state_zip) > 1):
            zip_code = state_zip[1]
        else:
            zip_code = ''

        # hacky Testing
        # if (len(address) != 3):
        #     # print(f'Raw address string: "{raw}"')
        #     print('Address parse warning, not len 3', address)
        #     print([addressLn1,city,state,zip_code])
        if (len(state_zip) != 2):
            print('Address parse error, not len 2', state_zip)
        if (len(state) != 2):
            print("State parse error, not len 2", state)

        return addressLn1, city, state, zip_code

    def _parse_date(self, raw):
        return datetime.fromtimestamp(raw / 1000).strftime('%m/%d/%y')

    def _clean_value(self, val):
        if re.compile(r'\(*\)').search(val):
            # check for negative numbers indicated by parenthesis
            return -1 * float(val.replace('$', '').replace(',', '').replace(',', '').replace(')', '').replace('(', ''))
        else:
            return float(val.replace('$', '').replace(',', '').replace(',', ''))

    def _calc_unitemized_contributions(self):
        totalSum = self.summary['Receipts']['total']
        if (len(self.contributions) > 0):
            cashContributions = self.contributions[self.contributions['Amount Type'] == 'CA']
            itemizedSum = cashContributions['Amount'].sum()
        else:
            itemizedSum = 0
        # Only bothering with totals for now
        return totalSum - itemizedSum
