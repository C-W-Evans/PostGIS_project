## How to run this project:

Clone the repo.

Copy io_config.yaml.example to io_config.yaml.

Create a local PostGIS database named transport_etl and add a postgis extension to 
it by running an SQL command "CREATE EXTENSION postgis;" in the database.

Update the password in io_config.yaml to match your local PostGIS password.

Download the raw CSV data and place it in the transport_etl/data/old and transport_etl/data/new folders.

Run docker compose up, access Mage at localhost:6789 and run the pipeline.

## Data information

Missing data
2016 - 1,2,3
2017 - 1,2,3
2018 - 1,2
2019 - 1,2,3
2020 - 1,2 (on the websitesite but empty files)

We can't use the old data for the stations table because we don't know where those stations are.
The stations table requires Latitude and Longitude to be plotted on a map in PostGIS.

The "Old" CSVs do not have these columns. They only have the Station ID.

If a station only exists in the old data (and was removed before the "new" format started), we have its ID but zero location data. We cannot plot a point on a map for it.