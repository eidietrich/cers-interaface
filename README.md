# CERS interface

A home-brewed API for Montana's [Campaign Electronic Reporting System](https://cers-ext.mt.gov/CampaignTracker/dashboard), operated by Montana's Commissioner of Political Practices as the primary public access point for campaign finance reports submitted by candidates for state office. This project, developed for internal use at [Montana Free Press](https://montanafreepress.org) is designed to allow for easier exports of CERS data to Excel-compatable CSVs and JSON summary files.

Contact edietrich@montanafreepress.org with questions or bug reports.


## Python scripts

- `query-state-22.py` - Runs CERS fetch for 2022 SupCo/PSC races
- `clean-state-22.py` - Gathers fetched data into summary files in `/cleaned`