from models.cers_interface import Interface
from models.cleaners import CommitteeCleaner

cers = Interface()
committee_cleaner = CommitteeCleaner()

YEARS = [
    '2022',
    '2020',
    '2018',
    '2016',
]

# PACS
for year in YEARS:
    committees = cers.get_committees_with_spending(cycle=year)
    committees.export(f'raw/{year}/committees')
    committee_cleaner.clean(
        raw_directory=f'raw/{year}/committees',
        out_path=f'cleaned/{year}/committees', 
    )

# For testing on specific committees
# cers.get_committee_by_name('Consulting Engineers Council of Montana / American Council of Engineering Companies of MT', '2020')

print("Done")