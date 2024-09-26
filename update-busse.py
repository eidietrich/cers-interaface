
# Standalone script for Busse 2024 updates because they keep crashing the main script
# Writes into the cache referenced by the braod 2024 update script

from models.cers_interface import Interface

cers = Interface()
FILTER_STATUSES = ['Active', 'Reopened', 'Amended','Closed']

cers.get_candidate_by_name('2024', 'Ryan', 'Busse', filterStatuses=FILTER_STATUSES)
