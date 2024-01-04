"""
Models for data pulled from Montana COPP Campaign Electronic Reporting System

Components
- CommitteeList - List of particular types of committees
- Committee - Individual committees
- Report - Individual financial reports

Design philosiphy: Front-load all slow API calls in object initialization.
Should provide more flexibility with avoiding duplicate scraping.

Ref: https://blog.hartleybrody.com/web-scraping-cheat-sheet/

"""

import requests
import pandas as pd
from io import StringIO

from datetime import date
from datetime import datetime
from dateutil.parser import parse

import os
import json

import re
from bs4 import BeautifulSoup

from cers_report import Report


# Hacky - Alternative reports for places where CERS is choking
# id: filename: filePath (.csv downloaded from CERS on a good day)
MANUAL_CACHES = {
    # 46348: 'scrapers/state-finance-reports/raw/Cooney-Mike--R/manual-46348-cooney-q42019-contributions.csv',
    # 45786: 'scrapers/state-finance-reports/raw/Cooney-Mike--R/manual-45786-cooney-q32019-contributions.csv',
    # 46959: 'scrapers/state-finance-reports/raw/Cooney-Mike--R/manual-46959-cooney-q12020-contributions.csv',
    # 47635: 'scrapers/state-finance-reports/raw/Cooney-Mike--R/manual-47635-cooney-apr2020-contributions.csv',
    # 48320: 'scrapers/state-finance-reports/raw/Cooney-Mike--R/manual-48320-cooney-may2020-contributions.csv',
    # 48513: 'scrapers/state-finance-reports/raw/Cooney-Mike--R/manual-48513-cooney-june2020-contribututions.csv',
    # 50070: 'scrapers/state-finance-reports/raw/Cooney-Mike--R/manual-50070-cooney-aug2020-contribututions.csv',
    # 50595: 'scrapers/state-finance-reports/raw/Cooney-Mike--R/manual-50595-cooney-sept2020-contribututions.csv',
    # 51325: 'scrapers/state-finance-reports/raw/Cooney-Mike--R/manual-51325-cooney-oct2020-contribututions.csv',
}
MANUAL_SUMMARY_CACHES = {
    # 48513: 'scrapers/state-finance-reports/raw/Cooney-Mike--R/manual-48513-cooney-june2020-summary.html',
    # 50070: 'scrapers/state-finance-reports/raw/Cooney-Mike--R/manual-50070-cooney-aug2020-summary.html',
    # 50595: 'scrapers/state-finance-reports/raw/Cooney-Mike--R/manual-50595-cooney-sept2020-summary.html',
    # 51325: 'scrapers/state-finance-reports/raw/Cooney-Mike--R/manual-51325-cooney-oct2020-summary.html',

}


class CommitteeList:
    """List of committees from specific search"""

    def __init__(self, search,
                 fetchReports=True, fetchFullReports=True,
                 filterStatuses=False,
                 filterFunction=None,
                 excludeCommittees=[],
                 cachePath='cache/committees',
                 checkCache=True, writeCache=True,
                 ):
        committee_list = self._fetch_committee_list(search)
        if callable(filterFunction):
            committee_list = [c for c in committee_list if filterFunction(c)]

        if filterStatuses:
            committee_list = [
                c for c in committee_list if c['committeeStatusDescr'] in filterStatuses]
        if len(excludeCommittees) > 0:
            committee_list = [
                c for c in committee_list if c['committeeId'] not in excludeCommittees]
        self.committees = [Committee(c,
                                     fetchReports=fetchReports,
                                     fetchFullReports=fetchFullReports,
                                     cachePath=cachePath,
                                     checkCache=checkCache,
                                     writeCache=writeCache
                                     ) for c in committee_list]
        if fetchReports and fetchFullReports:
            self.contributions = self._get_contributions()
            self.expenditures = self._get_expenditures()
            print(f'{len(self.committees)} committees compiled with {len(self.contributions)} contributions and {len(self.expenditures)} expenditures')

    def _fetch_committee_list(
        self, search, raw=False, filterStatuses=False
    ):
        session = requests.Session()
        committee_search_url = 'https://cers-ext.mt.gov/CampaignTracker/public/searchResults/searchFinancials'
        max_committees = 1000
        committee_list_url = f"""
        https://cers-ext.mt.gov/CampaignTracker/public/searchResults/listFinancialCommitteeResults?sEcho=1&iColumns=4&sColumns=&iDisplayStart=0&iDisplayLength={max_committees}&mDataProp_0=checked&mDataProp_1=committeeName&mDataProp_2=electionYear&mDataProp_3=committeeTypeDescr&sSearch=&bRegex=false&sSearch_0=&bRegex_0=false&bSearchable_0=true&sSearch_1=&bRegex_1=false&bSearchable_1=true&sSearch_2=&bRegex_2=false&bSearchable_2=true&sSearch_3=&bRegex_3=false&bSearchable_3=true&iSortCol_0=0&sSortDir_0=asc&iSortingCols=1&bSortable_0=false&bSortable_1=true&bSortable_2=true&bSortable_3=true&_=1665677891038
        """

        session.post(committee_search_url, search)
        r = session.get(committee_list_url)
        full = r.json()['aaData']

        if raw:
            return full

        # print(json.dumps(full[0], indent=4))

        cleaned = list(map(lambda d: {
            'committeeId': d['committeeId'],
            'committeeName': d['committeeName'],
            'committeeAddress': d['committeeAddress'],
            # 'committeeState': d['entityDTO']['addressList']['state'],
            # 'committeeState': d['entityDTO']['addressList']['zip5'],
            'electionYear': d['electionYear'],
            'committeeStatusDescr': d['committeeStatusDescr'],
            'createdDate': d['createdDate'],

            # Extra information
            'type': d['committeeTypeDescr'],
        }, full))
        return cleaned

    def list_committees(self):
        return [c.data for c in self.committees]

    def export(self, base_dir):
        for committee in self.committees:
            committee.export(base_dir)

    def _get_contributions(self):
        if len(self.committees) == 0:
            # print(f'No committees on list')
            return pd.DataFrame()

        df = pd.DataFrame()
        for committee in self.committees:
            df = pd.concat([df, committee.contributions])
        return df

    def _get_expenditures(self):
        if len(self.committees) == 0:
            # print(f'No committees on list')
            return pd.DataFrame()

        df = pd.DataFrame()
        for committee in self.committees:
            df = pd.concat([df, committee.expenditures])
        return df


class Committee:
    """
    Single political committee
    """

    def __init__(self, data, cachePath,
                 fetchSummary=True,
                 fetchReports=True,
                 fetchFullReports=True,
                 checkCache=True,
                 writeCache=True
                 ):
        # print(data)
        self.id = data['committeeId']
        self.name = data['committeeName']
        self.slug = str(self.id) + '-' + \
            self.name.strip().replace(' ', '-').replace(',', '')
        self.data = data
        self.finance_reports = []

        cachePath = os.path.join(cachePath, self.slug)

        if fetchReports:
            self.raw_reports = self._fetch_committee_finance_reports()
            # Filter to more recent than 2021
            self.raw_reports = [r for r in self.raw_reports if parse(r['toDateStr'])
                                >= datetime(2021, 1, 1)]

        if (fetchReports and fetchFullReports):
            print(
                f'## Fetching {len(self.raw_reports)} finance reports for {self.name} ({self.id})')
            self.finance_reports = [Report(r,
                                           cachePath=cachePath,
                                           checkCache=checkCache,
                                           writeCache=writeCache, fetchFullReports=fetchFullReports
                                           ) for r in self.raw_reports]
            self.summary = self._get_summary()
            self.contributions = self._get_contributions()
            self.expenditures = self._get_expenditures()
            # self.unitemized_contributions = self._get_unitemized_contributions()
            self.summarized_reports = self._summarize_reports()
            print(
                f'Found {len(self.contributions)} contributions and {len(self.expenditures)} expenditures in {len(self.finance_reports)} reports')
            self.export(cachePath)
            print('\n')

    def _fetch_committee_finance_reports(self, raw=False):
        post_url = 'https://cers-ext.mt.gov/CampaignTracker/public/publicReportList/retrieveCommitteeReports'
        list_max = 1000
        get_url = f"""
        https://cers-ext.mt.gov/CampaignTracker/public/publicReportList/listFinanceReports?sEcho=1&iColumns=6&sColumns=&iDisplayStart=0&iDisplayLength={list_max}&mDataProp_0=checked&mDataProp_1=fromDateStr&mDataProp_2=toDateStr&mDataProp_3=formTypeDescr&mDataProp_4=formTypeCode&mDataProp_5=statusDescr&sSearch=&bRegex=false&sSearch_0=&bRegex_0=false&bSearchable_0=true&sSearch_1=&bRegex_1=false&bSearchable_1=true&sSearch_2=&bRegex_2=false&bSearchable_2=true&sSearch_3=&bRegex_3=false&bSearchable_3=true&sSearch_4=&bRegex_4=false&bSearchable_4=true&sSearch_5=&bRegex_5=false&bSearchable_5=true&iSortCol_0=0&sSortDir_0=asc&iSortingCols=1&bSortable_0=false&bSortable_1=true&bSortable_2=true&bSortable_3=true&bSortable_4=true&bSortable_5=true&_=1549557879524
        """
        post_payload = {
            'committeeId': self.id,
            'financialSearchType': 'COMMITTEE',
            'searchPage': 'public',
            # 'searchType': 'Expenditures',
        }

        session = requests.Session()
        session.post(post_url, post_payload)
        r = session.get(get_url)
        full = r.json()['aaData']
        if raw:
            return full

        cleaned = list(map(lambda d: {
            'reportId': d['reportId'],
            'fromDateStr': d['fromDateStr'],
            'toDateStr': d['toDateStr'],
            'formTypeCode': d['formTypeCode'],
            'formTypeDescr': d['formTypeDescr'],
            'committeeId': d['committeeDTO']['committeeId'],
            'committeeName': d['committeeDTO']['committeeName'],
            'filingTypeDescr': d['filingTypeDescr'],
            "amendedDate": d['amendedDate']
        }, full))
        return cleaned

    def list_reports(self):
        return self.raw_reports

    def _get_summary(self):
        c6_summaries = [
            r.summary for r in self.finance_reports if r.type == 'C6'
        ]
        c7_summaries = [
            r.summary for r in self.finance_reports if r.type == 'C7']
        c7e_summaries = [
            r.summary for r in self.finance_reports if r.type == 'C7E']

        summaries = c6_summaries + c7_summaries + c7e_summaries

        summaries = sorted(
            summaries, key=lambda i: parse(i['report_end_date']))
        tot_contributions = sum(s['Receipts']['total'] for s in summaries)
        tot_expenditures = sum(s['Expenditures']['total'] for s in summaries)

        return {
            'contributions': {
                'total': tot_contributions
            },
            'expenditures': {
                'total': tot_expenditures
            },
            'cash_on_hand': {
                'total': tot_contributions - tot_expenditures
            },
            'report_counts': {
                'c6': len(c6_summaries),
                'C7': len(c7_summaries),
                'C7E': len(c7e_summaries),
            }
        }

    def _get_contributions(self):
        """
        Return all contributions to candidate across multiple reports
        """
        if len(self.finance_reports) == 0:
            return pd.DataFrame()

        df = pd.DataFrame()
        for report in self.finance_reports:
            dfi = report.contributions.copy()
            dfi.insert(0, 'Committee', self.name)
            dfi.insert(1, 'Reporting Period',
                       f'{report.start_date} to {report.end_date}')
            dfi.insert(2, 'Report Type', report.type)
            df = pd.concat([df, dfi])
        return df

    def _get_expenditures(self):
        """
        Return all expenditures made by candidate across multiple reports
        """
        if len(self.finance_reports) == 0:
            return pd.DataFrame()

        df = pd.DataFrame()
        for report in self.finance_reports:
            dfi = report.expenditures.copy()
            dfi.insert(0, 'Committee', self.name)
            dfi.insert(1, 'Reporting Period',
                       f'{report.start_date} to {report.end_date}')
            dfi.insert(2, 'Report Type', report.type)
            df = pd.concat([df, dfi])
        return df

    def _summarize_reports(self):
        """
        Return total + by-report unitemized contributions
        """
        reports = self.finance_reports
        return [{
            'report': r.label,
            'id': r.id,
            'type': r.data['formTypeCode'],
            'start_date': r.start_date,
            'end_date': r.end_date,
            # 'unitemized_contributions': r.unitemized_contributions,
            'num_contributions': len(r.contributions),
            'num_expenditures': len(r.expenditures),
            'summary': r.summary
        } for r in reports]

    def export(self, write_dir):
        # write_dir = os.path.join(base_dir, self.slug)
        # make folder if it doesn't exist
        if not os.path.exists(write_dir):
            os.makedirs(write_dir)
        summary_path = os.path.join(
            os.getcwd(), write_dir, self.slug + '-summary.json')
        contributions_path = os.path.join(
            os.getcwd(), write_dir, self.slug + '-contributions-itemized.json')
        expenditures_path = os.path.join(
            os.getcwd(), write_dir, self.slug + '-expenditures-itemized.json')
        summary = {
            'slug': self.slug,
            'committeeName': self.name,
            'scrape_date': date.today().strftime('%Y-%m-%d'),
            'periods': len(self.finance_reports),
            'receipts': self.summary['contributions']['total'],
            'expenditures': self.summary['expenditures']['total'],
            'balance': self.summary['cash_on_hand']['total'],
            'summary': self.summary,
            # 'unitemized_contributions': self.unitemized_contributions,
            'reports': self.summarized_reports
        }
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=4)
        self.contributions.to_json(contributions_path, orient='records')
        self.expenditures.to_json(expenditures_path, orient='records')
        print(self.slug, 'written to', os.path.join(os.getcwd(), write_dir))

    # def _summarize_reports(self):
    #     """
    #     Return total + by-report unitemized contributions
    #     """
