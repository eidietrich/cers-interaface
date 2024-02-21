import json
from datetime import datetime

from models.cers_interface import Interface
from models.cleaners import CommitteeCleaner
from models.cleaners import CandidateCleaner

cers = Interface()
committee_cleaner = CommitteeCleaner()
candidate_cleaner = CandidateCleaner()

YEARS = [
    {
        'year': '2022',
        'races': [

        ]
    },
    {
        'year': '2020',
        'races': [
            # {'key': 'gov', 'code': 'tk'},
            {'key': 'ag', 'code': 'tk'},
            # etc. etc.
        ]
    },
    {
        'year': '2018',
        'races': [
            
        ]
    },
    {
        'year': '2016',
        'races': [
            
        ]
    },
]

FILTER_STATUSES = ['Active', 'Reopened', 'Amended','Closed']

print("TODO: Implement this")

# # # State districts
# for cycle in YEARS:
#     for race in cycle['races']
#     candidates = cers.get_candidates_by_race(cycle['year'], race['code'], filterStatuses=FILTER_STATUSES)
#     candidates.export(f'raw/{cycle['year']}/{race['key']}')
#     candidate_cleaner.clean(
#         raw_directory=f'raw/{cycle['year']}/{race['key']}',
#         out_path=f'cleaned/{cycle['year']}/{race['key']}', 
#     )






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
    

# for key in STATE_DISTRICT_RACE_CODES:
#     code = STATE_DISTRICT_RACE_CODES[key]
#     candidates = cers.get_candidates_by_race({YEAR}, code)
#     candidates.export(f'raw/{YEAR}/{key}')
#     candidate_cleaner.clean(
#         raw_directory=f'raw/{YEAR}/{key}',
#         out_path=f'cleaned/{YEAR}/{key}',
#     )

print("Done")