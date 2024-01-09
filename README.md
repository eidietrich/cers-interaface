# CERS interface

A home-brewed API for Montana's [Campaign Electronic Reporting System](https://cers-ext.mt.gov/CampaignTracker/dashboard), or CERS. CERS is operated by Montana's Commissioner of Political Practices as the primary public access point for campaign finance reports submitted by candidates for state office. This project, developed for internal use at [Montana Free Press](https://montanafreepress.org), is designed to allow for easier exports of CERS data to Excel-compatable CSVs and JSON summary files.

Contact edietrich@montanafreepress.org with questions or bug reports.

## Data models

CERS tracks two primary entities: `candidates`, individuals who are seeking public office, and `committees`, third-party organizations who required to report political spending under state law. See https://politicalpractices.mt.gov/Home/Forms for a list of forms.

This interface system uses the following data models:

For candidates:
- CandidateList - List of candidates, intended to facilitate data gathering for specific lists of candidates  (e.g. statewide candidates who ran in 2022)
- Candidate - Individual candidates
- Report - Individual financial reports filed by candidates. Supported types:
    - C-5 reports - periodic campaign finance reporting, comprehensive coverage for their reporting period
    - C-7 reports - notice of last-minute contributions immediately before an election
    - C-7E reports - notice of last-minute spending immediately before an election

For committees:
- CommitteeList - List of particular types of committees
- Committee - Individual committees
- Report - Individual financial reports. Supported types:
    - C-6 reports - periodic campaign finance reports for political committees
    - C-7 reports - notice of last-minute contributions immediately before an election
    - C-7E reports - notice of last-minute spending immediately before an election


## Usage scripts

These require you to have a way of running Python 3 with some third-party libraries installed. Run with a command in the form of `python3 script-name.py`

Update data for 2024 races
- `python3 update-2024.py`

Archival 2022 scripts are in `archive` directory; may need some refactoring.

Script logs 'raw' outputs to non-version-controlled `raw/2024` folder, as well as the following outputs to `cleaned/2024`:
- contributions.csv — itemized list of contributions available from CERS
- expenditures.csv - itemized list of expenditures
- summary.json - totals and other summary information for specific entities and reports