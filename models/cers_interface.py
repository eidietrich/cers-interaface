"""
Interface for fetching CERS data

Components
- Interface - List of queries (e.g. all statewide 2020 candidates)
"""

from models.cers_candidate import CandidateList
from models.cers_committee import CommitteeList

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

COMMITTEE_SEARCH_DEFAULT = {
    'independentExpendSearch': 'false',
    'electioneeringCommSearch': 'false',
    'financialSearchType': 'EXPEND',
    'expendSearchTypeCode': 'COMMITTEE',
    'expendCanLastName': '',
    'expendCanFirstName': '',
    'expendCommitteeName': '',
    'payeeLastName': '',
    'payeeFirstName': '',
    'expendPartyCode': '',
    'expendCandidateTypeCode': '',
    'expendOfficeCode': '',
    'expendAmountRangeCode': '',
    'electionYear': '',
    'expendSearchFromDate': '',
    'expendSearchToDate': '',
}

ACTIVE_STATUSES = ['Active', 'Reopened', 'Amended']

class Interface:
    """
    Interface for Montana COPP Campaign Electronic Reporting System
    """

    def get_candidates_by_race(self, election_year, office_code):
        search = CANDIDATE_SEARCH_DEFAULT.copy()
        search['electionYear'] = election_year
        search['officeCode'] = office_code
        return CandidateList(search, 
                             cachePath=f'cache/{election_year}/candidates',
                             filterStatuses=ACTIVE_STATUSES)
    
    def list_candidates_by_race(self, election_year, office_code):
        search = CANDIDATE_SEARCH_DEFAULT.copy()
        search['electionYear'] = election_year
        search['officeCode'] = office_code
        results = CandidateList(search, 
                                cachePath=f'cache/{election_year}/candidates',
                                filterStatuses=ACTIVE_STATUSES, 
                                fetchReports=False)
        print(results.list_candidates()) 
        
    def get_candidate_by_name(self, election_year, first, last, filterStatuses=ACTIVE_STATUSES):
        search = CANDIDATE_SEARCH_DEFAULT.copy()
        search['electionYear'] = election_year
        search['lastName'] = last
        search['firstName'] = first
        return CandidateList(search,
                             cachePath=f'cache/{election_year}/candidates',
                             filterStatuses=filterStatuses)

    def get_committee_by_name(self, name, election_year, **kwargs):
        search = COMMITTEE_SEARCH_DEFAULT.copy()
        search['expendCommitteeName'] = name
        return CommitteeList(search,
                             cachePath=f'cache/{election_year}/committees')

    # Recipes

    def list_committees_with_spending(self, cycle):
        """Prints list of committees spending in 2022
        cycle="2022" or "2024"
        """
        search = COMMITTEE_SEARCH_DEFAULT.copy()
        search['electionYear'] = cycle
        committees = CommitteeList(
            search,
            cachePath=f'cache/{cycle}/committees',
            fetchReports=False,  # avoids costly report scrape
        )
        print('Num:', len(committees.list_committees()))
        print(committees.list_committees())

    def get_committees_with_spending(self, cycle, excludeCommittees=[1895]):
        """Returns list of committees with reported spending in given election cycle
        cycle="2022" or "2024"
        excludeCommittees= list of commitees to exclude
            ActBlue (1895) is excluded by default because it's too big for the state system
        """
        search = COMMITTEE_SEARCH_DEFAULT.copy()
        search['electionYear'] = cycle
        print(f'Fetching committees for {cycle} cycle')
        print('Note: Unless otherwise specified, this skips ActBlue')
        return CommitteeList(
            search,
            cachePath=f'cache/{cycle}/committees',
            excludeCommittees=excludeCommittees
        )
    
    def get_legislative_candidates(self, cycle, excludeCandidates=[], filterStatuses=ACTIVE_STATUSES):
        """Returns data for legislative candidates running in given cycle"""

        def office_is_legislative(candidate):
            return 'House District' in candidate['officeTitle'] or 'Senate District' in candidate['officeTitle']

        search = CANDIDATE_SEARCH_DEFAULT.copy()
        search['electionYear'] = cycle
        search['candidateTypeCode'] = 'SD' # State District in CERS shorthand
        return CandidateList(
            search,
            cachePath=f'cache/{cycle}/candidates',
            filterStatuses=filterStatuses,
            filterFunction=office_is_legislative,
            # excludeCandidates=[18322]  # Fake Coffee J candidate for testing
            excludeCandidates=excludeCandidates
        )
    

    # OLD FOR 2022 cycle

    def list_2022_committees_with_spending(self):
        """Prints list of committees spending in 2022"""
        search = COMMITTEE_SEARCH_DEFAULT.copy()
        search['electionYear'] = '2022'
        committees = CommitteeList(
            search,
            cachePath=f'cache/2022/committees',
            fetchReports=False,  # avoids costly report scrape
        )
        

    def get_2022_committees_with_spending(self):
        """Returns list of committees spending in 2022"""
        search = COMMITTEE_SEARCH_DEFAULT.copy()
        search['electionYear'] = '2022'
        return CommitteeList(
            search,
            cachePath=f'cache/2022/committees',
            excludeCommittees=[1895]  # ActBlue
        )

    def list_2022_legislative_candidates(self):
        """Prints lists of legislative candidates running in 2022 w/out fetching reports"""

        def office_is_legislative(candidate):
            return 'House District' in candidate['officeTitle'] or 'Senate District' in candidate['officeTitle']

        search = CANDIDATE_SEARCH_DEFAULT.copy()
        search['electionYear'] = '2022'
        search['candidateTypeCode'] = 'SD'
        candidates = CandidateList(
            search,
            cachePath=f'cache/2022/committees',
            fetchReports=False,  # avoids costly scraping operation
            filterStatuses=ACTIVE_STATUSES,
            filterFunction=office_is_legislative,
        )
        print('## 2022 legislative')
        print(candidates.list_candidates())
        print('Num:', len(candidates.list_candidates()))

    def get_2022_legislative_candidates(self):
        """Returns data for legislative candidates running in 2022"""

        def office_is_legislative(candidate):
            return 'House District' in candidate['officeTitle'] or 'Senate District' in candidate['officeTitle']

        search = CANDIDATE_SEARCH_DEFAULT.copy()
        search['electionYear'] = '2022'
        search['candidateTypeCode'] = 'SD'
        return CandidateList(
            search,
            cachePath=f'cache/2022/committees',
            filterStatuses=ACTIVE_STATUSES,
            filterFunction=office_is_legislative,
            excludeCandidates=[18322]  # Fake Coffee J candidate for testing
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
                cachePath=f'cache/2022/committees',
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
            cachePath=f'cache/2020/committees',
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
            cachePath=f'cache/2020/committees',
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
