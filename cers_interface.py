"""
Interface for fetching CERS data

Components
- Interface - List of queries (e.g. all statewide 2020 candidates)
"""

from cers_models import CandidateList

CANDIDATE_SEARCH_DEFAULT = {
    'lastName': '',
    'firstName': '',
    'middleInitial': '',
    'electionYear': '',
    'candidateTypeCode': '',
    'officeCode': '',  # NOT officeTitle
    'countyCode': '',
    'partyCode': '',
}

ACTIVE_STATUSES = ['Active', 'Reopened', 'Amended']


class Interface:
    """
    Interface for Montana COPP Campaign Electronic Reporting System
    """

    def get_candidate_by_race(self, election_year, office_code):
        search = CANDIDATE_SEARCH_DEFAULT.copy()
        search['electionYear'] = election_year
        search['officeCode'] = office_code
        return CandidateList(search, filterStatuses=ACTIVE_STATUSES,)

    def get_candidate_by_name(self, election_year, first, last):
        search = CANDIDATE_SEARCH_DEFAULT.copy()
        search['electionYear'] = election_year
        search['lastName'] = last
        search['firstName'] = first
        return CandidateList(search, filterStatuses=ACTIVE_STATUSES)

    # Recipes

    def list_2022_legislative_candidates(self):
        """Prints lists of legislative candidates running in 2022 w/out fetching reports"""

        def office_is_legislative(candidate):
            return 'House District' in candidate['officeTitle'] or 'Senate District' in candidate['officeTitle']

        search = CANDIDATE_SEARCH_DEFAULT.copy()
        search['electionYear'] = '2022'
        search['candidateTypeCode'] = 'SD'
        candidates = CandidateList(
            search,
            fetchReports=False,  # avoids costly scraping operation
            filterStatuses=ACTIVE_STATUSES,
            filterFunction=office_is_legislative,
        )
        print('## 2022 legislative')
        print(candidates.list_candidates())
        print('Num:', len(candidates.list_candidates()))

    def list_2022_legislative_candidates(self):
        """Returns data for legislative candidates running in 2022"""

        def office_is_legislative(candidate):
            return 'House District' in candidate['officeTitle'] or 'Senate District' in candidate['officeTitle']

        search = CANDIDATE_SEARCH_DEFAULT.copy()
        search['electionYear'] = '2022'
        search['candidateTypeCode'] = 'SD'
        return CandidateList(
            search,
            filterStatuses=ACTIVE_STATUSES,
            filterFunction=office_is_legislative,
        )

    def list_state_2022_state_candidates(self):
        """Prints lists of state (i.e. PSC and SupCo) candidates running in 2022 w/out fetching reports"""

        OFFICES_ON_BALLOT = [
            # office codes collected manually from CERS
            '247',  # 'Supreme Court Justice No. 01',
            '248',  # 'Supreme Court Justice No. 02',
            '187',  # 'Public Service Commission District No. 01',
            '191',  # 'Public Service Commission District No. 05',
        ]
        for office in OFFICES_ON_BALLOT:
            search = CANDIDATE_SEARCH_DEFAULT.copy()
            search['electionYear'] = '2022'
            search['candidateTypeCode'] = office
            candidates = CandidateList(
                search,
                fetchReports=False,  # avoids costly scraping operation
                filterStatuses=ACTIVE_STATUSES
            )
            print('## 2022', office)
            print(candidates.list_candidates())

    # OLD 2020 queries

    def list_statewide_2020_candidates(self):
        """Lists statewide 2020 candidates without fetching all their reports"""
        search = CANDIDATE_SEARCH_DEFAULT.copy()
        search['electionYear'] = '2020'
        search['candidateTypeCode'] = 'SW'  # statewide
        candidates_state_2020 = CandidateList(
            search,
            fetchReports=False,  # avoids costly scraping operation
            filterStatuses=ACTIVE_STATUSES
        )
        return candidates_state_2020.list_candidates()

    def list_statewide_2020_candidates_with_reports(self):
        """Lists statewide 2020 candidates and reports without fetching full reports"""
        search = CANDIDATE_SEARCH_DEFAULT.copy()
        search['electionYear'] = '2020'
        search['candidateTypeCode'] = 'SW'  # statewide
        candidates_state_2020 = CandidateList(
            search,
            fetchReports=True,
            fetchFullReports=False,  # avoids costly scraping operation
            filterStatuses=ACTIVE_STATUSES
        )
        return candidates_state_2020.list_candidates_with_reports()

    def statewide_2020(self, excludeCandidates=[]):
        """Runs a full data fetch on statewide 2020 candidates"""
        search = CANDIDATE_SEARCH_DEFAULT.copy()
        search['electionYear'] = '2020'
        search['candidateTypeCode'] = 'SW'  # statewide
        return CandidateList(search, filterStatuses=ACTIVE_STATUSES, excludeCandidates=excludeCandidates)

    def statewide_2020_johnsons(self):
        """For testing"""
        search = CANDIDATE_SEARCH_DEFAULT.copy()
        search['electionYear'] = '2020'
        search['candidateTypeCode'] = 'SW'  # statewide
        search['lastName'] = 'Johnson'
        return CandidateList(search)

    def legislature_2020(self, excludeCandidates=[], cachePath='scrapers/state-finance-reports/raw'):
        """Runs a full data fetch on statewide 2020 candidates"""
        search = CANDIDATE_SEARCH_DEFAULT.copy()
        search['electionYear'] = '2020'
        search['candidateTypeCode'] = 'SD'  # state district
        return CandidateList(search,
                             filterStatuses=ACTIVE_STATUSES,
                             excludeCandidates=excludeCandidates,
                             cachePath=cachePath,
                             )

    # TODO - interfaces here for single-candidate-by-id search
