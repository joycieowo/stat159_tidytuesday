# Data Sources and Definitions

This project uses baby-name datasets from three UK statistical agencies:

- **England & Wales:** [Office for National Statistics](https://www.ons.gov.uk/peoplepopulationandcommunity/birthsdeathsandmarriages/livebirths/datasets/babynamesinenglandandwalesfrom1996)
- **Northern Ireland:** [Northern Ireland Statistics and Research Agency](https://www.nisra.gov.uk/publications/baby-names-2025)
- **Scotland:** [National Records of Scotland](https://www.nrscotland.gov.uk/publications/babies-first-names-2025/)

The supplied data dictionaries describe `Year`, `Sex`, `Name`, `Number` (birth count), and `Rank`. Spellings are treated as distinct names. The Northern Ireland and Scotland data dictionaries indicate accents are omitted from names; confidentiality suppression rules also differ across sources.

See the original data dictionaries in `data/england_wales_names.md`, `data/ni_names.md`, and `data/scotland_names.md`.
