// =====================================================================
// Google Earth Engine script — built-up (impervious) fraction of the
// study catchments from the Global Human Settlement Layer (GHSL R2023A).
//
// HOW TO USE
// 1. Sign up free at https://code.earthengine.google.com
// 2. Paste this whole script into the Code Editor and press "Run".
// 3. Copy the printed "land only" fractions into config.yaml →
//    catchments → <name> → impervious_fraction_by_year, and the land area
//    into area_km2 (use the 2025 epoch value for 2024, the nearest available).
//
// Each catchment is a 25 km² circle (radius = sqrt(25e6 / pi) ≈ 2821 m).
// Water present more than half the time (JRC Global Surface Water) is
// removed, so the fraction refers to land only and catchments next to the
// lagoon or the sea can be compared fairly. Replace the circles with real
// drainage-catchment boundaries if you have them.
// =====================================================================

var catchments = [
  {name: 'Central Lagos',       lon: 3.3792, lat: 6.5244},
  {name: 'Lekki–Ajah corridor', lon: 3.545,  lat: 6.445}
];
var epochs = [2005, 2010, 2015, 2020, 2025];

// Land mask from JRC Global Surface Water (occurrence 1984–2021)
var water = ee.Image('JRC/GSW1_4/GlobalSurfaceWater').select('occurrence').unmask(0).gt(50);
var land = water.not();

catchments.forEach(function (c) {
  var aoi = ee.Geometry.Point([c.lon, c.lat]).buffer(2821);
  Map.addLayer(aoi, {color: 'red'}, c.name);

  var landArea = ee.Image.pixelArea().updateMask(land).reduceRegion({
    reducer: ee.Reducer.sum(), geometry: aoi, scale: 30, maxPixels: 1e9}).get('area');
  print('===== ' + c.name + ' =====');
  print('Land area in circle (km²):', ee.Number(landArea).divide(1e6));

  epochs.forEach(function (year) {
    var built = ee.Image('JRC/GHSL/P2023A/GHS_BUILT_S/' + year).select('built_surface');
    var onLand = built.updateMask(land).reduceRegion({
      reducer: ee.Reducer.mean(), geometry: aoi, scale: 100, maxPixels: 1e9}).get('built_surface');
    // fraction = mean built m² per 100 m cell / 10,000 m² cell area
    print(year + ' built-up fraction, land only:', ee.Number(onLand).divide(10000));
  });
});

Map.setCenter(3.46, 6.49, 11);
Map.addLayer(ee.Image('JRC/GHSL/P2023A/GHS_BUILT_S/2005').select('built_surface').selfMask(),
             {min: 0, max: 10000, palette: ['ffffcc', 'fd8d3c', '800026']}, 'Built-up 2005', false);
Map.addLayer(ee.Image('JRC/GHSL/P2023A/GHS_BUILT_S/2025').select('built_surface').selfMask(),
             {min: 0, max: 10000, palette: ['ffffcc', 'fd8d3c', '800026']}, 'Built-up 2025', false);

// If the image IDs above ever change, search the Earth Engine data catalog
// for "GHS-BUILT-S" and "Global Surface Water" and update the paths.
