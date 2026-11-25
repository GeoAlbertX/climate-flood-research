// ---------------------------------------------------------------------------
// CHIRPS daily rainfall for central Lagos, 1981–2024 -> CSV in Google Drive
//
// Why: ERA5 and NASA POWER disagree on whether Lagos rainfall has gone up or
// down since 1981 (see project1_rainfall_trends/LONG_RECORD_CHECK.md). CHIRPS
// blends satellite estimates with rain-gauge records, so it is the tie-breaker.
//
// How to use:
//   1. Paste this into a new script at code.earthengine.google.com and click Run.
//   2. Check the Console: the number of days should be 16071.
//   3. Open the Tasks tab and click Run next to "chirps_lagos_daily_1981_2024".
//   4. When it finishes, download the CSV from Google Drive (folder "GEE") and save it as
//      data/raw/chirps_lagos_daily_1981_2024.csv in this repository.
//   5. From the repository root run:
//      python project1_rainfall_trends/analysis.py --csv data/raw/chirps_lagos_daily_1981_2024.csv
//             --start 1981 --end 2024 --out results_chirps_1981_2024
// ---------------------------------------------------------------------------

var point = ee.Geometry.Point([3.3792, 6.5244]);   // same point as config.yaml

var chirps = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY')
  .filterDate('1981-01-01', '2025-01-01')          // end date is exclusive
  .select('precipitation');

var series = chirps.map(function (img) {
  var v = img.reduceRegion({
    reducer: ee.Reducer.first(),
    geometry: point,
    scale: 5566                                     // native CHIRPS pixel, about 0.05 degrees
  });
  return ee.Feature(null, {
    date: img.date().format('YYYY-MM-dd'),
    precip_mm: v.get('precipitation')
  });
});

print('Number of days (expect 16071):', series.size());
print('First five days:', series.limit(5));

Map.centerObject(point, 9);
Map.addLayer(point, {color: 'red'}, 'Rainfall point (central Lagos)');

Export.table.toDrive({
  collection: series,
  description: 'chirps_lagos_daily_1981_2024',
  folder: 'GEE',
  fileFormat: 'CSV',
  selectors: ['date', 'precip_mm']
});
