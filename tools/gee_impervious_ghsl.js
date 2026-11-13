// =====================================================================
// Google Earth Engine script — built-up (impervious) fraction of the
// study catchment from the Global Human Settlement Layer (GHSL R2023A).
//
// HOW TO USE
// 1. Sign up free at https://code.earthengine.google.com
// 2. Paste this whole script into the Code Editor and press "Run".
// 3. Copy the printed fractions into config.yaml → urban → impervious_fraction_by_year
//    (use the 2025 epoch value for 2024 — it is the nearest available).
// =====================================================================

// --- Study catchment: a circle of 25 km² around central Lagos -------------
// (radius = sqrt(25e6 / pi) ≈ 2821 m). Replace with your own polygon if you
// have a real drainage-catchment boundary (draw it with the geometry tools).
var centre = ee.Geometry.Point([3.3792, 6.5244]);   // [longitude, latitude]
var aoi = centre.buffer(2821);
Map.centerObject(aoi, 13);
Map.addLayer(aoi, {color: 'red'}, 'Study catchment');

// --- GHSL built-up surface: m² of built-up area in each 100 m × 100 m cell --
var epochs = [2005, 2010, 2015, 2020, 2025];

epochs.forEach(function (year) {
  var img = ee.Image('JRC/GHSL/P2023A/GHS_BUILT_S/' + year).select('built_surface');
  var meanBuilt = img.reduceRegion({
    reducer: ee.Reducer.mean(),
    geometry: aoi,
    scale: 100,
    maxPixels: 1e9
  }).get('built_surface');
  // fraction = mean built m² per cell / 10,000 m² cell area
  var fraction = ee.Number(meanBuilt).divide(10000);
  print('Built-up fraction ' + year + ':', fraction);
  if (year === 2005 || year === 2025) {
    Map.addLayer(img.updateMask(img.gt(0)),
      {min: 0, max: 10000, palette: ['ffffcc', 'fd8d3c', '800026']},
      'Built-up ' + year, false);
  }
});

// If the image ID above ever changes, search the Earth Engine data catalog
// for "GHS-BUILT-S" and update the path.
