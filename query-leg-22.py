#!/usr/bin/env python3

"""Check finance records from CERS for 2022 MT Legislature candidates

run as: python3 query-leg-22.py
"""

from cers_interface import Interface

cers = Interface()

print('# Fetching Legislative candidates')

# cers.list_2022_legislative_candidates()

legislative = cers.list_2022_legislative_candidates()
legislative.export('raw/2022/leg')

# cers.get_candidate_by_name('2022', '', 'Walsh')  # For testing
