"""
Models for data pulled from Montana COPP Campaign Electronic Reporting System

Components
- CandidateList - List of particular types of candidates (e.g. statewide)
- Candidate - Individual candidates
- Report - Individual financial reports (e.g., C-5s)

Design philosophy: Front-load all slow API calls in object initialization.
Should provide more flexibility with avoiding duplicate scraping.

Ref: https://blog.hartleybrody.com/web-scraping-cheat-sheet/

TODO:
- Add logic for fetching/aggregating report financial summaries to catch non-itemized contributions (adapt fetch-finance-summaries.py)
- Build testing suite --> Or just prep an iPython notebook with tests for each individual component?
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

from models.cers_report import Report


class CandidateList:
    """List of candidates from specific search
    - fetchReports - flag to run costly scrape of individual financial reports
    - filterStatuses - if non-false, filter to candidates with statuses in array

    """

    def __init__(self, search,
                 fetchReports=True, fetchFullReports=True,
                 filterStatuses=False,
                 filterFunction=None,
                 excludeCandidates=[],
                 cachePath='cache/candidates',
                 checkCache=True, writeCache=True,
                 ):
        candidate_list = self._fetch_candidate_list(search)
        if callable(filterFunction):
            candidate_list = [c for c in candidate_list if filterFunction(c)]

        if filterStatuses:
            candidate_list = [
                c for c in candidate_list if c['candidateStatusDescr'] in filterStatuses]
        if len(excludeCandidates) > 0:
            candidate_list = [
                c for c in candidate_list if c['candidateId'] not in excludeCandidates]
        self.candidates = [Candidate(c,
                                     fetchReports=fetchReports,
                                     fetchFullReports=fetchFullReports,
                                     cachePath=cachePath,
                                     checkCache=checkCache,
                                     writeCache=writeCache
                                     ) for c in candidate_list]
        if fetchReports and fetchFullReports:
            self.contributions = self._get_contributions()
            self.expenditures = self._get_expenditures()
            print(f'{len(self.candidates)} candidates compiled with {len(self.contributions)} contributions and {len(self.expenditures)} expenditures')

    def _fetch_candidate_list(self, search, raw=False, filterStatuses=False):
        session = requests.Session()
        candidate_search_url = 'https://cers-ext.mt.gov/CampaignTracker/public/searchResults/searchCandidates'
        max_candidates = 1000
        candidate_list_url = f"""
        https://cers-ext.mt.gov/CampaignTracker/public/searchResults/listCandidateResults?sEcho=1&iColumns=9&sColumns=&iDisplayStart=0&iDisplayLength={max_candidates}&mDataProp_0=checked&mDataProp_1=candidateName&mDataProp_2=electionYear&mDataProp_3=candidateStatusDescr&mDataProp_4=c3FiledInd&mDataProp_5=candidateAddress&mDataProp_6=candidateTypeDescr&mDataProp_7=officeTitle&mDataProp_8=resCountyDescr&sSearch=&bRegex=false&sSearch_0=&bRegex_0=false&bSearchable_0=true&sSearch_1=&bRegex_1=false&bSearchable_1=true&sSearch_2=&bRegex_2=false&bSearchable_2=true&sSearch_3=&bRegex_3=false&bSearchable_3=true&sSearch_4=&bRegex_4=false&bSearchable_4=true&sSearch_5=&bRegex_5=false&bSearchable_5=true&sSearch_6=&bRegex_6=false&bSearchable_6=true&sSearch_7=&bRegex_7=false&bSearchable_7=true&sSearch_8=&bRegex_8=false&bSearchable_8=true&iSortCol_0=0&sSortDir_0=asc&iSortingCols=1&bSortable_0=false&bSortable_1=true&bSortable_2=true&bSortable_3=true&bSortable_4=false&bSortable_5=false&bSortable_6=true&bSortable_7=true&bSortable_8=true&_=1586980078555
        """

        session.post(candidate_search_url, search)
        r = session.get(candidate_list_url)
        full = r.json()['aaData']

        if raw:
            return full

        cleaned = list(map(lambda d: {
            'candidateId': d['candidateId'],
            'candidateName': d['candidateName'],
            'candidateLastName': d['personDTO']['lastName'],
            'partyDescr': d['partyDescr'],
            'electionYear': d['electionYear'],
            'resCountyDescr': d['resCountyDescr'],
            'officeTitle': d['officeTitle'],
            'candidateStatusDescr': d['candidateStatusDescr'],
            # More available here - home address, phone, etc.
        }, full))
        return cleaned

    def get_candidate(self, id):
        return [c for c in self.candidates if c.id == id][0]

    def list_candidates(self):
        return [c.data for c in self.candidates]

    def list_reports(self):
        # TODO: Flatten this
        reports_by_candidate = [c.list_reports() for c in self.candidates]
        return reports_by_candidate

    def list_candidates_with_reports(self):
        return [{**c.data, 'reports': c.list_reports()} for c in self.candidates]

    def export(self, base_dir):
        for candidate in self.candidates:
            candidate.export(base_dir)

    def _get_contributions(self):
        if len(self.candidates) == 0:
            # print(f'No candidates on list')
            return pd.DataFrame()

        df = pd.DataFrame()
        for candidate in self.candidates:
            df = pd.concat([df, candidate.contributions])
        return df

    def _get_expenditures(self):
        if len(self.candidates) == 0:
            # print(f'No candidates on list')
            return pd.DataFrame()

        df = pd.DataFrame()
        for candidate in self.candidates:
            df = pd.concat([df, candidate.expenditures])
        return df


class Candidate:
    """
    Single candidate for given election cycle
    """

    def __init__(self, data, cachePath, fetchSummary=True, fetchReports=True, fetchFullReports=True, checkCache=True, writeCache=True):
        self.id = data['candidateId']
        self.name = data['candidateName']
        self.slug = self.name.strip().replace(' ', '-').replace(',', '')
        self.data = data
        self.finance_reports = []

        cachePath = os.path.join(cachePath, self.slug)

        if fetchReports:
            self.raw_reports = self._fetch_candidate_finance_reports()
        if (fetchReports and fetchFullReports):
            print(
                f'## Fetching {len(self.raw_reports)} finance reports for {self.name} ({self.id})')
            self.finance_reports = [Report(r, cachePath=cachePath, checkCache=checkCache,
                                           writeCache=writeCache, fetchFullReports=fetchFullReports) for r in self.raw_reports]
            self.summary = self._get_summary()
            self.contributions = self._get_contributions()
            self.expenditures = self._get_expenditures()
            # self.unitemized_contributions = self._get_unitemized_contributions()
            self.summarized_reports = self._summarize_reports()
            print(
                f'Found {len(self.contributions)} contributions and {len(self.expenditures)} expenditures in {len(self.finance_reports)} reports')
            self.export(cachePath)
            print('\n')

    def _fetch_candidate_finance_reports(self, raw=False):
        post_url = 'https://cers-ext.mt.gov/CampaignTracker/public/publicReportList/retrieveCampaignReports'
        list_max = 1000
        get_url = f"""
        https://cers-ext.mt.gov/CampaignTracker/public/publicReportList/listFinanceReports?sEcho=1&iColumns=6&sColumns=&iDisplayStart=0&iDisplayLength={list_max}&mDataProp_0=checked&mDataProp_1=fromDateStr&mDataProp_2=toDateStr&mDataProp_3=formTypeDescr&mDataProp_4=formTypeCode&mDataProp_5=statusDescr&sSearch=&bRegex=false&sSearch_0=&bRegex_0=false&bSearchable_0=true&sSearch_1=&bRegex_1=false&bSearchable_1=true&sSearch_2=&bRegex_2=false&bSearchable_2=true&sSearch_3=&bRegex_3=false&bSearchable_3=true&sSearch_4=&bRegex_4=false&bSearchable_4=true&sSearch_5=&bRegex_5=false&bSearchable_5=true&iSortCol_0=0&sSortDir_0=asc&iSortingCols=1&bSortable_0=false&bSortable_1=true&bSortable_2=true&bSortable_3=true&bSortable_4=true&bSortable_5=true&_=1549557879524
        """
        post_payload = {
            'candidateId': self.id,
            'searchType': '',
            'searchPage': 'public',
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
            'candidateId': d['candidateDTO']['candidateId'],
            'candidateName': d['candidateDTO']['candidateName'],
            'officeTitle': d['candidateDTO']['officeTitle'],
            'electionYear': d['candidateDTO']['electionYear'],
            'statusDescr': d['statusDescr'],
            "amendedDate": d['amendedDate']
        }, full))
        return cleaned

    def list_reports(self):
        return self.raw_reports

    def list_report_summaries(self):
        summaries = [c.summary for c in self.finance_reports]
        summaries_sorted = sorted(
            summaries, key=lambda i: parse(i['report_end_date']))
        return summaries_sorted

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
            'candidateName': self.name,
            'scrape_date': date.today().strftime('%Y-%m-%d'),
            'officeTitle': self.data['officeTitle'],
            'partyDescr': self.data['partyDescr'],
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

    def _get_summary(self):
        c5_summaries = [
            r.summary for r in self.finance_reports if r.type == 'C5']
        # c5_summaries = sorted(c5_summaries, key=lambda i: parse(i['report_end_date']))

        c7_summaries = [
            r.summary for r in self.finance_reports if r.type == 'C7']
        c7e_summaries = [
            r.summary for r in self.finance_reports if r.type == 'C7E']

        summaries = c5_summaries + c7_summaries + c7e_summaries
        summaries = sorted(
            summaries, key=lambda i: parse(i['report_end_date']))

        pri_contributions = sum(s['Receipts']['primary'] for s in summaries)
        gen_contributions = sum(s['Receipts']['general'] for s in summaries)
        tot_contributions = sum(s['Receipts']['total'] for s in summaries)

        pri_expenditures = sum(s['Expenditures']['primary'] for s in summaries)
        gen_expenditures = sum(s['Expenditures']['general'] for s in summaries)
        tot_expenditures = sum(s['Expenditures']['total'] for s in summaries)

        return {
            'contributions': {
                'primary': pri_contributions,
                'general': gen_contributions,
                'total': tot_contributions,
            },
            'expenditures': {
                'primary': pri_expenditures,
                'general': gen_expenditures,
                'total': tot_expenditures,
            },
            'cash_on_hand': {
                'primary': pri_contributions - pri_expenditures,
                'general': gen_contributions - gen_expenditures,
                'total': tot_contributions - tot_expenditures,
            },
            'report_counts': {
                'C5': len(c5_summaries),
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
            dfi.insert(0, 'Candidate', self.name)
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
            dfi.insert(0, 'Candidate', self.name)
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
            'unitemized_contributions': r.unitemized_contributions,
            'num_contributions': len(r.contributions),
            'num_expenditures': len(r.expenditures),
            'summary': r.summary
        } for r in reports]
