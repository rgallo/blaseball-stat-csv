# blaseball-stat-csv

Generates a CSV file with details on all active Blaseball player stlats.

Arguments:

`--output`
Path of the output file, defaults to output.csv

`--inactive`
If added, includes bench/bullpen players

`--archive`
If specified and a file already exists at the output path, the existing file is moved to a new file before rewriting.  Can be used for a Windows scheduled task or cronjob to get full season stlat data.

`--tournament`
If added, run for tournament teams rather than league teams
