import json
from datetime import datetime

from models.cers_interface import Interface
from models.cleaners import CommitteeCleaner
from models.cleaners import CandidateCleaner

cers = Interface()
committee_cleaner = CommitteeCleaner()
candidate_cleaner = CandidateCleaner()

YEARS = [
    '2022',
    '2020',
    '2018',
    '2016',
]

FILTER_STATUSES = ['Active', 'Reopened', 'Amended','Closed']

# TODO - look up race codes for past statewide and state district races

# STATEWIDE_RACE_CODES = {
#     # Manually from CERS
#     'gov': '81',
#     'sos': '193',
#     'ag': '2',
#     'opi': '245',
#     # 'auditor': , # None as of 1/8
# }

# STATE_DISTRICT_RACE_CODES = {
#     'supcoChief': '246',
#     'supco3': '249',
#     'psc2': '188',
#     'psc4': '190',
# }

# # PACS
# committees = cers.get_committees_with_spending(cycle=YEAR)
# committees.export(f'raw/{YEAR}/committees')
# committee_cleaner.clean(
#     raw_directory=f'raw/{YEAR}/committees',
#     out_path=f'cleaned/{YEAR}/committees', 
# )

# Legislative candidates
for year in YEARS:
    legislative = cers.get_legislative_candidates(cycle=year, filterStatuses=FILTER_STATUSES)
    legislative.export(f'raw/{year}/leg')
    candidate_cleaner.clean(
        raw_directory=f'raw/{year}/leg',
        out_path=f'cleaned/{year}/leg', 
    )

# # Testing for specific hangup
# cers.get_candidate_by_name('2020', 'Connie', 'Keogh', filterStatuses=FILTER_STATUSES)

# # Statewide races
# for key in STATEWIDE_RACE_CODES:
#     code = STATEWIDE_RACE_CODES[key]
#     candidates = cers.get_candidates_by_race(YEAR, code)
#     candidates.export(f'raw/{YEAR}/{key}')
#     candidate_cleaner.clean(
#         raw_directory=f'raw/{YEAR}/{key}',
#         out_path=f'cleaned/{YEAR}/{key}',
#     )
    
# # State districts
# for key in STATE_DISTRICT_RACE_CODES:
#     code = STATE_DISTRICT_RACE_CODES[key]
#     candidates = cers.get_candidates_by_race({YEAR}, code)
#     candidates.export(f'raw/{YEAR}/{key}')
#     candidate_cleaner.clean(
#         raw_directory=f'raw/{YEAR}/{key}',
#         out_path=f'cleaned/{YEAR}/{key}',
#     )

# # Log completion time
# with open('logs.json','w') as f:
#     json.dump({
#     'lastUpdateTime': str(datetime.now())
# }, f)
print("Done")