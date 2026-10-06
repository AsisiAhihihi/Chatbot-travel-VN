# Map geography / Dữ liệu địa lý bản đồ

## Sources and reproducibility

Natural Earth 1:10m: admin-0 countries, minor islands, geography regions polygons,
and ocean. Public domain. URLs and SHA-256 hashes of the downloaded source bytes
are recorded in `manifest.json`. Run `frontend/scripts/prepare-geography.py` with
Python (standard library only), optionally `--cache DIRECTORY` to use the exact
downloaded source snapshot. All GeoJSON uses WGS84 `[longitude, latitude]`.

https://www.naturalearthdata.com/downloads/10m-physical-vectors/10m-minor-islands/
https://www.naturalearthdata.com/about/terms-of-use/

## Explicit archipelago coverage

The country dataset has Vietnam and a separate Spratly Islands feature. It does
NOT have a separate Paracel Islands feature. The build therefore explicitly finds
both named archipelagos in geography_regions_polys and classifies actual country
and minor-island polygons against those group geometries. It asserts that both
groups contain actual land polygons. This snapshot yields 19 polygons for each
group; it is NOT a complete island/reef inventory. The group envelopes are never
rendered and are NOT territorial boundaries. Each non-interactive island symbol
is anchored to an actual vertex of a source land polygon, not a fabricated island.
Symbols indicate small features, not land area. Archipelago labels use one of
these verified anchors. The sea text has a cartographic anchor at 113.5 E, 14 N.

## Sovereignty, administration, and uncertainty

“Quần đảo Hoàng Sa (Việt Nam)” and “Quần đảo Trường Sa (Việt Nam)” express Vietnam's
stated sovereignty position. Green fill is a presentation choice, not evidence
of actual administration of every feature. Both archipelagos are disputed.
Paracels: Chinese administration; claims by Vietnam, China and Taiwan.
Spratlys: multiple claimants and mixed administration; this dataset does not
identify the administrator of individual features. No such per-island attribution
is inferred from the original country grouping or from our regional classifier.
Original administrative/dispute fields are retained alongside this qualification.
Claimant lists are group-level and do not imply identical scope of each claim.

Context sources (not the polygon source):
https://amti.csis.org/island-tracker/
https://amti.csis.org/island-tracker/china/
https://www.mofa.gov.vn/en/tt_baochi/pbnfn/ns240122235340/view

## Rendering and limits

The vector basemap supplies land, terrain, coastline, rivers and ocean geometry
in all countries, using the existing green/aqua palette. The generated ocean and
surrounding-land files are legacy data and are NOT loaded or rendered: their
generalized geometry cannot safely mask detailed coastlines or transport.
Basemap water remains below roads and bridges. Archipelago land fills are also
below transport. Water-name layers are replaced by the existing geographic
labels; other base text labels (including country names) are filtered to Vietnam.
Non-text road arrows remain unchanged outside Vietnam. Administrative boundary
layers remain hidden as before. Tourism points and routes remain above the map.
OpenFreeMap / OpenStreetMap attribution is retained, plus Natural Earth credit.

The 1:10m coastline is generalized, not a survey-grade high-zoom coastline. It
does not capture current reclamation, every reef, or tide-dependent land extent.
Detailed coastal exploration uses the basemap geometry, not these local polygons.
The generalized Vietnam polygon is used only for text filtering; labels directly
on its boundary may be excluded. Do not substitute region envelopes for land.
No private key or runtime geographic API is required by these local layers.

`VITE_MAP_STYLE_URL` may still supply an OpenFreeMap-compatible vector style.
Arbitrary raster styles with baked labels are not supported: raster layers other
than Liberty's label-free `natural_earth` relief are hidden. New vector providers
require verification of water, symbol and boundary layer names before deployment.
The approved UI is unchanged. Leave `VITE_OVERVIEW_IMAGE` unset for this geographic
presentation: an externally supplied illustration would otherwise cover the map.