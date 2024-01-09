#!/usr/bin/env python3

"""Check finance records from CERS for 2022 PSC and SupCo candidates

run as: python3 query-state-22.py
"""

from models.cers_interface import Interface

cers = Interface()

print('# Fetching PSC and SupCo candidates')

# office codes collected manually from CERS
# '247',  # 'Supreme Court Justice No. 01',
# '248',  # 'Supreme Court Justice No. 02',
# '187',  # 'Public Service Commission District No. 01',
# '191',  # 'Public Service Commission District No. 05',

supco_1 = cers.get_candidate_by_race('2022', '247')
supco_2 = cers.get_candidate_by_race('2022', '248')
psc_1 = cers.get_candidate_by_race('2022', '187')
psc_5 = cers.get_candidate_by_race('2022', '191')

# print(supco_1.list_candidates())

supco_1.export('raw/2022/supco_1')
supco_2.export('raw/2022/supco_2')
psc_1.export('raw/2022/psc_1')
psc_5.export('raw/2022/psc_5')
