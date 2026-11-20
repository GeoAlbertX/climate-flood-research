# Data folder

* `raw/` — daily rainfall downloaded by the code is cached here (e.g. `rainfall_nasa_power_6.5244_3.3792_2005_2024.csv`), so the analysis can be rerun offline and the exact input data are available.
* `flood_events.csv` — **optional**, for validating Project 2. Add one row per recorded flood event in the study area. Good sources: news archives (Punch, Vanguard, Premium Times, Channels TV), NEMA / LASEMA situation reports, the Dartmouth Flood Observatory archive and EM-DAT. Always fill in the `source` column.

| column | example |
|---|---|
| date | 2011-07-10 |
| location | Victoria Island / Lekki |
| description | flash flooding after heavy overnight rain |
| source | URL or report title |

Only enter events you have actually found in a source — leave the file with just its header row if you skip this step.
