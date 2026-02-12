var mapView;

$(function() {

	var map = null;
	var draw = null;
	var geocoder = null;
	var bar = null;

	var cancellationToken = null;
	var requests = [];

	
	var sources = {

		"=== FREE / NO AUTH REQUIRED ===": "",
		
		"OpenStreetMap": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
		"OpenStreetMap DE": "https://tile.openstreetmap.de/{z}/{x}/{y}.png",
		"Wikimedia Maps": "https://maps.wikimedia.org/osm-intl/{z}/{x}/{y}.png",
		
		"div-osm": "",

		"ESRI World Imagery (Free)": "https://services.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
		"ESRI World Topo (Free)": "https://services.arcgisonline.com/arcgis/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
		"ESRI World Street (Free)": "https://services.arcgisonline.com/arcgis/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",

		"div-cycle": "",

		"OpenCycleMap": "https://tile.thunderforest.com/cycle/{z}/{x}/{y}.png",
		"OpenTopoMap": "https://tile.opentopomap.org/{z}/{x}/{y}.png",
		"Stamen Terrain": "https://tiles.stadiamaps.com/tiles/stamen_terrain/{z}/{x}/{y}.png",
		"Stamen Toner": "https://tiles.stadiamaps.com/tiles/stamen_toner/{z}/{x}/{y}.png",

		"div-nasa": "",

		"NASA GIBS (Free)": "https://map1.vis.earthdata.nasa.gov/wmts-webmerc/MODIS_Terra_CorrectedReflectance_TrueColor/default/GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg",

		"=== REQUIRES AUTH / API KEY ===": "",

		"Google Maps": "https://mt0.google.com/vt?lyrs=m&x={x}&s=&y={y}&z={z}",
		"Google Satellite": "https://mt0.google.com/vt?lyrs=s&x={x}&s=&y={y}&z={z}",
		"Google Hybrid": "https://mt0.google.com/vt?lyrs=h&x={x}&s=&y={y}&z={z}",
		"Google Terrain": "https://mt0.google.com/vt?lyrs=p&x={x}&s=&y={y}&z={z}",

		"div-bing": "",

		"Bing Maps": "https://ecn.t0.tiles.virtualearth.net/tiles/r{quad}.jpeg?g=129&mkt=en&stl=H",
		"Bing Satellite": "https://ecn.t0.tiles.virtualearth.net/tiles/a{quad}.jpeg?g=129&mkt=en&stl=H",
		"Bing Hybrid": "https://ecn.t0.tiles.virtualearth.net/tiles/h{quad}.jpeg?g=129&mkt=en&stl=H",

		"div-mapbox": "",

		"Mapbox Streets": "https://api.mapbox.com/styles/v1/mapbox/streets-v11/tiles/{z}/{x}/{y}?access_token=YOUR_MAPBOX_TOKEN",
		"Mapbox Satellite": "https://api.mapbox.com/styles/v1/mapbox/satellite-v9/tiles/{z}/{x}/{y}?access_token=YOUR_MAPBOX_TOKEN",

	};

	function initializeMap() {

		// MapLibre GL doesn't require access token for basic usage
		// Using OpenStreetMap-based style for open source compatibility

		map = new maplibregl.Map({
			container: 'map-view',
			style: {
				version: 8,
				sources: {
					'osm-tiles': {
						type: 'raster',
						tiles: [
							'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
						],
						tileSize: 256,
						attribution: '© OpenStreetMap contributors'
					}
				},
				layers: [
					{
						id: 'osm-tiles-layer',
						type: 'raster',
						source: 'osm-tiles',
						minzoom: 0,
						maxzoom: 19
					}
				]
			},
			center: [-73.983652, 40.755024], 
			zoom: 12
		});

		// Wait for map to load before adding controls
		map.on('load', function() {
			console.log('Map loaded successfully');
			
			// Debug: Check what's available
			console.log('Available globals:');
			console.log('maplibregl:', typeof maplibregl);
			console.log('MapboxDraw:', typeof MapboxDraw);
			console.log('window.MapboxDraw:', typeof window.MapboxDraw);
			console.log('DrawRectangle:', typeof DrawRectangle);
			
			// Check all possible draw library names
			const drawNames = ['MapboxDraw', 'mapboxDraw', 'MaplibreDraw', 'Draw', 'GLDraw'];
			drawNames.forEach(name => {
				if (window[name]) console.log(`Found ${name}:`, typeof window[name]);
			});
			
			// List all window properties containing 'draw' (case insensitive)
			const drawProps = Object.keys(window).filter(k => k.toLowerCase().includes('draw'));
			console.log('All draw-related properties:', drawProps);
			
			// Initialize center point if available
			console.log('🎯 About to initialize center point...');
			try {
				if (typeof initializeCenterPoint === 'function') {
					initializeCenterPoint(map);
					console.log('✅ Center point initialized successfully');
				} else {
					console.log('ℹ️ Center point function not available');
				}
			} catch (error) {
				console.error('❌ Error in center point initialization:', error);
			}
			
			console.log('🎯 About to initialize rectangle tool...');
			
			// Try initializing rectangle tool with retry for fallback loading
			function tryInitializeRectangleTool(attempt = 1) {
				const maxAttempts = 5;
				if (attempt > maxAttempts) {
					console.error('❌ Failed to initialize drawing tools after', maxAttempts, 'attempts');
					return;
				}
				
				// Check if any drawing library is available
				const hasDrawLib = typeof MapboxDraw !== 'undefined' || 
								 typeof window.MapboxDraw !== 'undefined';
				
				if (hasDrawLib) {
					console.log('✅ Drawing library found, initializing...');
					initializeRectangleTool();
				} else {
					console.log(`⏳ Waiting for drawing library to load (attempt ${attempt}/${maxAttempts})...`);
					setTimeout(() => tryInitializeRectangleTool(attempt + 1), 1000);
				}
			}
			
			tryInitializeRectangleTool();
		});

		// Add basemap selector control
		addBasemapSelector(map);

		// Add simple location search functionality
		console.log('Adding location search functionality');
		
		// Function to search for location using Nominatim
		async function searchLocation(query) {
			try {
			// Show immediate acknowledgement
			M.toast({html: `🔍 Searching for "${query}"...`, displayLength: 1000});
			
			const response = await fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&limit=1`);
			const results = await response.json();
			
			if (results.length > 0) {
				const result = results[0];
				const lat = parseFloat(result.lat);
				const lon = parseFloat(result.lon);
				
				console.log(`Found location: ${result.display_name} at [${lon}, ${lat}]`);
				
				// Fly to location
				map.flyTo({
					center: [lon, lat],
					zoom: 12,
					duration: 2000
				});
				
				M.toast({html: `✓ Found: ${result.display_name}`, displayLength: 3000});
			} else {
				M.toast({html: '❌ Location not found', displayLength: 2000});
			}
		} catch (error) {
			console.error('Search error:', error);
			M.toast({html: '⚠️ Search failed - please try again', displayLength: 3000});
		}
	}
	
	// Add event listener for location search
	$('#search-form').on('submit', function(e) {
		e.preventDefault();
		const location = $('#location-box').val().trim();
		if (location) {
			console.log('Searching for:', location);
			searchLocation(location);
		}
	});
}

function addBasemapSelector(map) {
	// Define available basemaps
	const basemaps = {
		'OpenStreetMap': {
			name: 'OpenStreetMap',
			url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
		},
		'Satellite': {
			name: 'Satellite Imagery',
			url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
		},
		'Terrain': {
			name: 'Terrain',
			url: 'https://tile.opentopomap.org/{z}/{x}/{y}.png'
		},
		'CartoDB': {
			name: 'CartoDB Light',
			url: 'https://cartodb-basemaps-a.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png'
		}
	};

	let currentBasemap = 'OpenStreetMap';

	// Create basemap control container
	const basemapControl = document.createElement('div');
	basemapControl.className = 'basemap-control';
	
	// Create header
	const header = document.createElement('div');
	header.className = 'basemap-control-header';
	header.textContent = 'Basemap';
	
	// Create options container
	const options = document.createElement('div');
	options.className = 'basemap-control-options';
	
	// Add basemap options
	Object.keys(basemaps).forEach(key => {
		const option = document.createElement('div');
		option.className = 'basemap-option';
		if (key === currentBasemap) {
			option.classList.add('active');
		}
		option.textContent = basemaps[key].name;
		option.dataset.basemap = key;
		
		option.addEventListener('click', () => {
			// Remove active class from all options
			document.querySelectorAll('.basemap-option').forEach(opt => {
				opt.classList.remove('active');
			});
			
			// Add active class to clicked option
			option.classList.add('active');
			
			// Update map source
			currentBasemap = key;
			
			// Create new style with updated source
			const newStyle = {
				version: 8,
				sources: {
					'osm-tiles': {
						type: 'raster',
						tiles: [basemaps[key].url],
						tileSize: 256,
						attribution: basemaps[key].attribution || '© Map data providers'
					}
				},
				layers: [
					{
						id: 'osm-layer',
						type: 'raster',
						source: 'osm-tiles'
					}
				]
			};
			
			// Update map style
			map.setStyle(newStyle);
			
			// Re-add draw control after style change
			map.once('style.load', () => {
				if (typeof draw !== 'undefined' && draw) {
					map.addControl(draw, 'top-left');
				}
			});
			
			// Close dropdown
			basemapControl.classList.remove('open');
			
			console.log(`Switched to basemap: ${basemaps[key].name}`);
			M.toast({html: `Basemap: ${basemaps[key].name}`, displayLength: 2000});
		});
		
		options.appendChild(option);
	});
	
	header.addEventListener('click', () => {
		basemapControl.classList.toggle('open');
	});
	
	// Close dropdown when clicking outside
	document.addEventListener('click', (e) => {
		if (!basemapControl.contains(e.target)) {
			basemapControl.classList.remove('open');
		}
	});
	
	basemapControl.appendChild(header);
	basemapControl.appendChild(options);
	
	// Add to map container
	map.getContainer().appendChild(basemapControl);
}

	function initializeMaterialize() {
		$('select').formSelect();
		$('.dropdown-trigger').dropdown({
			constrainWidth: false,
		});
	}

	function initializeSources() {

		var dropdown = $("#sources");

		for(var key in sources) {
			var url = sources[key];

			// Handle section dividers
			if(url == "") {
				if(key.startsWith("===")) {
					// Create header for categories
					var header = $("<li class='dropdown-header'></li>");
					header.text(key);
					dropdown.append(header);
				} else {
					// Regular divider
					dropdown.append("<li class='divider'></li>");
				}
				continue;
			}

			var item = $("<li><a href='#!'></a></li>");
			item.attr("data-url", url);
			item.find("a").text(key);

			item.click(function() {
				var url = $(this).attr("data-url");
				$("#source-box").val(url);
				M.toast({html: 'Tile source updated: ' + $(this).find('a').text(), displayLength: 2000});
			});

			dropdown.append(item);
		}
	}

	// initializeSearch - removed, search functionality integrated into map initialization

	function initializeMoreOptions() {

		$("#more-options-toggle").click(function() {
			$("#more-options").toggle();
		})
		var outputFileBox = $("#output-file-box");

		$("#output-type").change(function() {
			outputFileBox.val("{z}/{x}/{y}.png");
		});

	}

	function initializeRectangleTool() {
		
		console.log('🔧 Initializing rectangle tool...');
		
		// Check for drawing library
		var DrawClass = null;
		if (typeof MapboxDraw !== 'undefined') {
			DrawClass = MapboxDraw;
			console.log('✅ Found MapboxDraw');
		} else if (window.MapboxDraw) {
			DrawClass = window.MapboxDraw;
			console.log('✅ Found window.MapboxDraw');
		} else {
			console.error('❌ No drawing library found!');
			console.log('Available window properties:', Object.keys(window).filter(k => k.toLowerCase().includes('draw')));
			return;
		}
		
		// Initialize basic drawing tools
		try {
			draw = new DrawClass({
				displayControlsDefault: true,
				controls: {
					polygon: true,
					line_string: false,
					point: false,
					trash: true
				}
			});
			
			console.log('Draw instance created:', draw);
			map.addControl(draw);
			console.log('Draw control added successfully');
			
			// Store reference globally
			window.mapDraw = draw;
			
			// Debug: Check if controls are actually in DOM
			setTimeout(() => {
				const controls = document.querySelectorAll('[class*="draw"]');
				console.log('Found draw controls in DOM:', controls.length);
				controls.forEach((ctrl, i) => {
					console.log(`Control ${i}:`, ctrl.className, ctrl.style.display);
				});
			}, 1000);
			
			// Success - no overlay message to avoid interference
			console.log('✅ Drawing tools successfully loaded and ready');
			
		} catch (error) {
			console.error('Error initializing drawing tools:', error);
			document.getElementById('map-view').insertAdjacentHTML('afterbegin', 
				'<div style="position: absolute; top: 10px; left: 10px; background: red; color: white; padding: 10px; z-index: 1000;">Error: ' + error.message + '</div>');
		}

		map.on('draw.create', function (e) {
			M.Toast.dismissAll();
			if (e.features[0].geometry.type === 'Polygon') {
				var coordinates = e.features[0].geometry.coordinates[0];
				var originalBounds = coordinates.reduce(function(bounds, coord) {
					return [
						Math.min(bounds[0], coord[0]), // west
						Math.min(bounds[1], coord[1]), // south
						Math.max(bounds[2], coord[0]), // east
						Math.max(bounds[3], coord[1])  // north
					];
				}, [Infinity, Infinity, -Infinity, -Infinity]);

				// Get current zoom level for tile calculations
				var zoomLevel = getMaxZoom();
				
				// Convert bounds to corners following Python logic
				var boundArray = originalBounds;
				
				// Create corner coordinates (lat, lon) as in Python
				var sw = [boundArray[1], boundArray[0]]; // (south, west)
				var nw = [boundArray[3], boundArray[0]]; // (north, west)
				var ne = [boundArray[3], boundArray[2]]; // (north, east)
				var se = [boundArray[1], boundArray[2]]; // (south, east)
				
				// Convert to tile coordinates
				var sw_tile_x = long2tile(sw[1], zoomLevel);
				var sw_tile_y = lat2tile(sw[0], zoomLevel);
				var nw_tile_x = long2tile(nw[1], zoomLevel);
				var nw_tile_y = lat2tile(nw[0], zoomLevel);
				var ne_tile_x = long2tile(ne[1], zoomLevel);
				var ne_tile_y = lat2tile(ne[0], zoomLevel);
				var se_tile_x = long2tile(se[1], zoomLevel);
				var se_tile_y = lat2tile(se[0], zoomLevel);
				
				// Calculate height and width in tiles (following Python logic)
				var height = Math.abs(sw_tile_y - nw_tile_y);
				var width = Math.abs(ne_tile_x - nw_tile_x);
				
				console.log("Original bounds:", originalBounds);
				console.log("Tile coordinates:", {
					sw: [sw_tile_x, sw_tile_y],
					nw: [nw_tile_x, nw_tile_y], 
					ne: [ne_tile_x, ne_tile_y],
					se: [se_tile_x, se_tile_y]
				});
				console.log("Calculated dimensions - width:", width, "height:", height);
				
				var tileBounds;
				if (height !== width) {
					// Make it square by taking the minimum dimension
					var squareSize = Math.min(height, width);
					console.log("Making square with size:", squareSize);
					
					// Start from northwest corner and extend square size
					tileBounds = {
						"northwest": [nw_tile_x, nw_tile_y],
						"northeast": [nw_tile_x + squareSize, nw_tile_y],
						"southwest": [nw_tile_x, nw_tile_y + squareSize],
						"southeast": [nw_tile_x + squareSize, nw_tile_y + squareSize]
					};
				} else {
					tileBounds = {
						"northwest": [nw_tile_x, nw_tile_y],
						"northeast": [ne_tile_x, ne_tile_y],
						"southwest": [sw_tile_x, sw_tile_y],
						"southeast": [se_tile_x, se_tile_y]
					};
				}
				
				console.log("Final tile bounds:", tileBounds);
				
				// Convert tile bounds back to geographic coordinates with consistent logic
				var true_nw = [tile2lat(tileBounds.northwest[1], zoomLevel), tile2long(tileBounds.northwest[0], zoomLevel)]; // (north, west)
				var true_ne = [tile2lat(tileBounds.northeast[1], zoomLevel), tile2long(tileBounds.northeast[0], zoomLevel)]; // (north, east)
				var true_sw = [tile2lat(tileBounds.southwest[1], zoomLevel), tile2long(tileBounds.southwest[0], zoomLevel)]; // (south, west)
				var true_se = [tile2lat(tileBounds.southeast[1], zoomLevel), tile2long(tileBounds.southeast[0], zoomLevel)]; // (south, east)
				
				// Create the snapped bounds array [west, south, east, north] - ensure perfect rectangle
				var snappedBounds = [
					Math.min(true_nw[1], true_sw[1]), // west (minimum longitude)
					Math.min(true_sw[0], true_se[0]), // south (minimum latitude)
					Math.max(true_ne[1], true_se[1]), // east (maximum longitude)
					Math.max(true_nw[0], true_ne[0])  // north (maximum latitude)
				];
				
				// Create perfectly rectangular coordinates for the polygon
				var snappedCoordinates = [[
					[snappedBounds[0], snappedBounds[1]], // SW: [west, south]
					[snappedBounds[2], snappedBounds[1]], // SE: [east, south]
					[snappedBounds[2], snappedBounds[3]], // NE: [east, north]
					[snappedBounds[0], snappedBounds[3]], // NW: [west, north]
					[snappedBounds[0], snappedBounds[1]]  // SW: close polygon
				]];
				
				// Use a timeout to ensure the feature is fully created before updating
				setTimeout(function() {
					var featureId = e.features[0].id;
					var updatedFeature = {
						id: featureId,
						type: 'Feature',
						geometry: {
							type: 'Polygon',
							coordinates: snappedCoordinates
						},
						properties: e.features[0].properties
					};
					
					// Update the feature
					draw.delete(featureId);
					draw.add(updatedFeature);
				}, 50);
				
				window.launchBounds = snappedBounds;
				var center = [
					(snappedBounds[0] + snappedBounds[2]) / 2,
					(snappedBounds[1] + snappedBounds[3]) / 2
				];
				window.launchLocation = center;

				// Store the selected region for later restoration
				window.selectedRegion = {
					type: 'Feature',
					geometry: {
						type: 'Polygon',
						coordinates: snappedCoordinates
					},
					properties: e.features[0].properties
				};

				// Remove existing markers if they exist and create new one
				removeLaunchPadMarker();
				createLaunchPadMarker();

				// Calculate and show square dimensions
				var squareTileWidth = Math.abs(tileBounds.northeast[0] - tileBounds.northwest[0]);
				var squareTileHeight = Math.abs(tileBounds.southwest[1] - tileBounds.northwest[1]);
				var tilesInSquare = squareTileWidth * squareTileHeight;
				
				// Clear any pending messages first
				M.Toast.dismissAll();
				
				// Show success message with details
				M.toast({
					html: `Area snapped to a Square (${tilesInSquare} tiles total)`, 
					displayLength: 4000
				});
			}
		});

		$("#rectangle-draw-button").click(function() {
			startDrawing();
		})

	}

	function startDrawing() {
		if (!draw) {
			console.error('Draw control not initialized');
			M.toast({html: 'Drawing tools not ready', displayLength: 2000});
			return;
		}
		
		removeGrid();
		draw.deleteAll();
		draw.changeMode('draw_polygon');

		// Remove markers if they exist
		removeLaunchPadMarker();

		M.Toast.dismissAll();
		M.toast({html: 'Click to draw a polygon region on the map', displayLength: 3000});
		
		console.log('✅ Polygon drawing mode activated');
	}

	function initializeGridPreview() {
		$("#grid-preview-button").click(previewGrid);

		map.on('click', showTilePopup);
	}

	function showTilePopup(e) {

		if(!e.originalEvent.ctrlKey) {
			return;
		}

		var maxZoom = getMaxZoom();

		var x = lat2tile(e.lngLat.lat, maxZoom);
		var y = long2tile(e.lngLat.lng, maxZoom);

		var content = "X, Y, Z<br/><b>" + x + ", " + y + ", " + maxZoom + "</b><hr/>";
		content += "Lat, Lng<br/><b>" + e.lngLat.lat + ", " + e.lngLat.lng + "</b>";

        new maplibregl.Popup()
            .setLngLat(e.lngLat)
            .setHTML(content)
            .addTo(map);

        console.log(e.lngLat)

	}

	function long2tile(lon,zoom) {
		return (Math.floor((lon+180)/360*Math.pow(2,zoom)));
	}

	function lat2tile(lat,zoom)  {
		return (Math.floor((1-Math.log(Math.tan(lat*Math.PI/180) + 1/Math.cos(lat*Math.PI/180))/Math.PI)/2 *Math.pow(2,zoom)));
	}

	function tile2long(x,z) {
		return (x/Math.pow(2,z)*360-180);
	}

	function tile2lat(y,z) {
		var n=Math.PI-2*Math.PI*y/Math.pow(2,z);
		return (180/Math.PI*Math.atan(0.5*(Math.exp(n)-Math.exp(-n))));
	}

	function getTileRect(x, y, zoom) {

		var c1 = new maplibregl.LngLat(tile2long(x, zoom), tile2lat(y, zoom));
		var c2 = new maplibregl.LngLat(tile2long(x + 1, zoom), tile2lat(y + 1, zoom));

		return new maplibregl.LngLatBounds(c1, c2);
	}


	function getMaxZoom() {
		return parseInt($("#zoom-from-box").val());
	}

	function area(){
		var bounds = getBounds(); // Assuming you have a function to get bounds
		var polygon = getPolygonByBounds(bounds); // Assuming getPolygonByBounds returns a Turf.js polygon

		// Calculate the area of the polygon using Turf.js
		var area = turf.area(polygon);
		return area
	}

	function getArrayByBounds(bounds) {

		var tileArray = [
			[ bounds.getSouthWest().lng, bounds.getNorthEast().lat ],
			[ bounds.getNorthEast().lng, bounds.getNorthEast().lat ],
			[ bounds.getNorthEast().lng, bounds.getSouthWest().lat ],
			[ bounds.getSouthWest().lng, bounds.getSouthWest().lat ],
			[ bounds.getSouthWest().lng, bounds.getNorthEast().lat ],
		];

		return tileArray;
	}

	function getPolygonByBounds(bounds) {

		var tilePolygonData = getArrayByBounds(bounds);

		var polygon = turf.polygon([tilePolygonData]);

		return polygon;
	}

	function isTileInSelection(tileRect) {

		var polygon = getPolygonByBounds(tileRect);

		var areaPolygon = draw.getAll().features[0];

		if(turf.booleanDisjoint(polygon, areaPolygon) == false) {
			return true;
		}

		return false;
	}

	function getBounds() {

		var coordinates = draw.getAll().features[0].geometry.coordinates[0];

		var bounds = coordinates.reduce(function(bounds, coord) {
			return bounds.extend(coord);
		}, new maplibregl.LngLatBounds(coordinates[0], coordinates[0]));

		return bounds;
	}

	function getGrid(zoomLevel) {

		var bounds = getBounds();

		var rects = [];

		var outputScale = $("#output-scale").val();
		//var thisZoom = zoomLevel - (outputScale-1)
		var thisZoom = zoomLevel

		var TY    = lat2tile(bounds.getNorthEast().lat, thisZoom);
		var LX   = long2tile(bounds.getSouthWest().lng, thisZoom);
		var BY = lat2tile(bounds.getSouthWest().lat, thisZoom);
		var RX  = long2tile(bounds.getNorthEast().lng, thisZoom);
		for(var y = TY; y <= BY; y++) {
			for(var x = LX; x <= RX; x++) {

				var rect = getTileRect(x, y, thisZoom);

				if(isTileInSelection(rect)) {
					rects.push({
						x: x,
						y: y,
						z: thisZoom,
						rect: rect,
					});
				}

			}
		}

		return rects
	}

	function getAllGridTiles() {
		var allTiles = [];
		var grid = getGrid(getMaxZoom());
		// TODO shuffle grid via a heuristic (hamlet curve? :/)
		allTiles = allTiles.concat(grid);

		return allTiles;
	}

	function removeGrid() {
		removeLayer("grid-preview");
	}

	function previewGrid() {

		var maxZoom = getMaxZoom();
		var grid = getGrid(maxZoom);

		var pointsCollection = []

		for(var i in grid) {
			var feature = grid[i];
			var array = getArrayByBounds(feature.rect);
			pointsCollection.push(array);
		}

		removeGrid();

		map.addLayer({
			'id': "grid-preview",
			'type': 'line',
			'source': {
				'type': 'geojson',
				'data': turf.polygon(pointsCollection),
			},
			'layout': {},
			'paint': {
				"line-color": "#fa8231",
				"line-width": 3,
			}
		});

		var totalTiles = getAllGridTiles().length;
		M.toast({html: 'Total ' + totalTiles.toLocaleString() + ' tiles in the region.', displayLength: 5000})

	}

	function previewRect(rectInfo) {

		var array = getArrayByBounds(rectInfo.rect);

		var id = "temp-" + rectInfo.x + '-' + rectInfo.y + '-' + rectInfo.z;

		map.addLayer({
			'id': id,
			'type': 'line',
			'source': {
				'type': 'geojson',
				'data': turf.polygon([array]),
			},
			'layout': {},
			'paint': {
				"line-color": "#ff9f1a",
				"line-width": 3,
			}
		});

		return id;
	}

	function removeLayer(id) {
		if(map.getSource(id) != null) {
			map.removeLayer(id);
			map.removeSource(id);
		}
	}

	function generateQuadKey(x, y, z) {
	    var quadKey = [];
	    for (var i = z; i > 0; i--) {
	        var digit = '0';
	        var mask = 1 << (i - 1);
	        if ((x & mask) != 0) {
	            digit++;
	        }
	        if ((y & mask) != 0) {
	            digit++;
	            digit++;
	        }
	        quadKey.push(digit);
	    }
	    return quadKey.join('');
	}

	function initializeDownloader() {

		bar = new ProgressBar.Circle($('#progress-radial').get(0), {
			strokeWidth: 12,
			easing: 'easeOut',
			duration: 200,
			trailColor: '#eee',
			trailWidth: 1,
			from: {color: '#0fb9b1', a:0},
			to: {color: '#20bf6b', a:1},
			svgStyle: null,
			step: function(state, circle) {
				circle.path.setAttribute('stroke', state.color);
			}
		});

		$("#download-button").click(startDownloading)
		$("#stop-button").click(stopDownloading)

		var timestamp = Date.now().toString();
		//$("#output-directory-box").val(timestamp)
	}

	function showTinyTile(base64) {
		var currentImages = $(".tile-strip img");

		for(var i = 4; i < currentImages.length; i++) {
			$(currentImages[i]).remove();
		}

		var image = $("<img/>").attr('src', "data:image/png;base64, " + base64)

		var strip = $(".tile-strip");
		strip.prepend(image)
	}
	// Function to poll the task status
	async function pollTaskStatus() {
	    try {
	        // Call the /task-status endpoint
	        var response = await $.ajax({
	            url: "/task-status",
	            async: true,
	            timeout: 30 * 1000,
	            type: "get",
	            dataType: 'json',
	        });
			
			if (response.code === 200) {
				var status = response.message.status; // Extract the status field
				console.log("Task status:", status); // Debugging log
	
				// Check the task status
				if (status === "completed") {
					logItemRaw("Gazebo world generated successfully.");
					$("#stop-button").html("FINISH");
					
					// Add the launch pad marker when generation is complete
					createLaunchPadMarker();
				} else if (status === "in_progress") {
					logItemRaw("World Generation Inprogress..");
					setTimeout(() => pollTaskStatus(), 5000); // Poll every 5 seconds
				} else {
					logItemRaw("Unexpected status: " + status);
				}
			} else {
				logItemRaw("Unexpected response code: " + response.code);
			}
	    } catch (error) {
	        logItemRaw("Error while checking task status: " + error.statusText);
	        setTimeout(() => pollTaskStatus(taskId), 5000); // Retry after 5 seconds
	    }
	}
	async function startDownloading() {

		if(draw.getAll().features.length == 0) {
			M.toast({html: 'You need to select a region first.', displayLength: 3000})
			return;
		}

		cancellationToken = false; 
		requests = [];

		$("#main-sidebar").hide();
		$("#download-sidebar").show();
		$(".tile-strip").html("");
		$("#stop-button").html("STOP");
		removeGrid();
		clearLogs();
		M.Toast.dismissAll();

		// Remove the launch pad marker when download starts
		removeLaunchPadMarker();

		var timestamp = Date.now().toString();

		var allTiles = getAllGridTiles();
		updateProgress(0, allTiles.length);

		var numThreads = parseInt($("#parallel-threads-box").val()) || 4;
		var outputDirectory = $("#output-directory-box").val();
		var outputFile = "{z}/{x}/{y}.png"; 
		var outputType = "png"; 
		var outputScale = "1"; 
		var source = $("#source-box").val()

		var bounds = getBounds();
		var area_rect = area();
		var boundsArray = [[bounds.getSouthWest().lng,bounds.getSouthWest().lat],[bounds.getNorthEast().lng,bounds.getNorthEast().lat]];
		var centerArray = [bounds.getCenter().lng,bounds.getCenter().lat];
		var launchLocation = window.launchLocation ? window.launchLocation : centerArray;
		var data = new FormData();
		data.append('maxZoom', getMaxZoom());
		data.append('outputDirectory', outputDirectory);
		data.append('outputFile', outputFile);
		data.append('outputType', outputType);
		data.append('outputScale', outputScale);
		data.append('source', source);
		data.append('timestamp', timestamp);
		data.append('bounds', boundsArray.join(","));
		data.append('center', centerArray.join(","));
		data.append('launchLocation', launchLocation.join(","));
		data.append('area', area_rect);

		var request = await $.ajax({
			url: "/start-download",
			async: true,
			timeout: 30 * 1000,
			type: "post",
			contentType: false,
			processData: false,
			data: data,
			dataType: 'json',
		})

		let i = 0;
		var iterator = async.eachLimit(allTiles, numThreads, function(item, done) {

			if(cancellationToken) {
				return;
			}

			var boxLayer = previewRect(item);

			var url = "/download-tile";

			var data = new FormData();
			data.append('x', item.x)
			data.append('y', item.y)
			data.append('z', item.z)
			data.append('quad', generateQuadKey(item.x, item.y, item.z))
			data.append('outputDirectory', outputDirectory)
			data.append('outputFile', outputFile)
			data.append('outputType', outputType)
			data.append('outputScale', outputScale)
			data.append('timestamp', timestamp)
			data.append('source', source)
			data.append('bounds', boundsArray.join(","))
			data.append('center', centerArray.join(","))
			data.append('launchLocation', launchLocation.join(","))
			data.append('area', area_rect)

			var request = $.ajax({
				"url": url,
				async: true,
				timeout: 30 * 1000,
				type: "post",
			    contentType: false,
			    processData: false,
				data: data,
				dataType: 'json',
			}).done(function(data) {

				if(cancellationToken) {
					return;
				}

				if(data.code == 200) {
					showTinyTile(data.image)
					logItem(item.x, item.y, item.z, data.message);
				} else {
					logItem(item.x, item.y, item.z, data.code + " Error downloading tile");
				}

			}).fail(function(data, textStatus, errorThrown) {

				if(cancellationToken) {
					return;
				}

				logItem(item.x, item.y, item.z, "Error while relaying tile");
				//allTiles.push(item);

			}).always(function(data) {
				i++;

				removeLayer(boxLayer);
				updateProgress(i, allTiles.length);

				done();
				
				if(cancellationToken) {
					return;
				}
			});

			requests.push(request);

		}, async function(err) {

			var request = await $.ajax({
				url: "/end-download",
				async: true,
				timeout: 30 * 1000,
				type: "post",
				contentType: false,
				processData: false,
				data: data,
				dataType: 'json',
			})

			updateProgress(allTiles.length, allTiles.length);
			logItemRaw("Starting World Generation");
			pollTaskStatus(); // Start polling with the task ID

		},


	);


	}

	function updateProgress(value, total) {
		var progress = value / total;

		bar.animate(progress);
		bar.setText(Math.round(progress * 100) + '<span>%</span>');

		$("#progress-subtitle").html(value.toLocaleString() + " <span>out of</span> " + total.toLocaleString())
	}

	function logItem(x, y, z, text) {
		logItemRaw(x + ',' + y + ',' + z + ' : ' + text)
	}

	function logItemRaw(text) {

		var logger = $('#log-view');
		logger.val(logger.val() + '\n' + text);

		logger.scrollTop(logger[0].scrollHeight);
	}

	function clearLogs() {
		var logger = $('#log-view');
		logger.val('');
	}

	function stopDownloading() {
		// Check if the process is finished (button shows "FINISH")
		if ($("#stop-button").html() === "FINISH") {
			// Process is complete, restore the main view
			$("#main-sidebar").show();
			$("#download-sidebar").hide();
			
			// Ensure the region selection is visible (if it was removed)
			if (window.selectedRegion && draw.getAll().features.length === 0) {
				draw.add(window.selectedRegion);
			}
			
			// Ensure the launch pad marker is visible
			
			removeGrid();
			clearLogs();
			createLaunchPadMarker();

			// Show completion message
			M.toast({
				html: 'Region and launch pad are now visible. Ready for next operation.', 
				displayLength: 3000
			});
			
			return;
		}
		
		// Otherwise, it's a regular stop operation during download
		cancellationToken = true;

		for(var i =0 ; i < requests.length; i++) {
			var request = requests[i];
			try {
				request.abort();
			} catch(e) {

			}
		}


		$("#main-sidebar").show();
		$("#download-sidebar").hide();

		removeGrid();
		clearLogs();

	}

	function createLaunchPadMarker() {
		// Only create if launch location exists and marker doesn't already exist
		if (window.launchLocation && !window.centerMarker) {
			// Add a helipad icon at the center
			var helipadIcon = document.createElement('div');
			helipadIcon.className = 'helipad-icon';
			helipadIcon.style.width = '50px';
			helipadIcon.style.height = '50px';
			helipadIcon.style.backgroundImage = 'url(launchpad.svg)';
			helipadIcon.style.backgroundSize = 'contain';
			helipadIcon.style.backgroundRepeat = 'no-repeat';
			helipadIcon.style.backgroundPosition = 'center';

			window.centerMarker = new maplibregl.Marker({
				element: helipadIcon,
				draggable: true
			})
			.setLngLat(window.launchLocation)
			.addTo(map);

			// Constrain the helipad icon within the bounds
			window.centerMarker.on('dragend', function() {
				var lngLat = window.centerMarker.getLngLat();
				var bounds = window.launchBounds;
				var newLng = Math.min(Math.max(lngLat.lng, bounds[0]), bounds[2]);
				var newLat = Math.min(Math.max(lngLat.lat, bounds[1]), bounds[3]);
				window.centerMarker.setLngLat([newLng, newLat]);
				window.launchLocation = [newLng, newLat];
			});
		}
	}

	function removeLaunchPadMarker() {
		if (window.centerMarker) {
			window.centerMarker.remove();
			window.centerMarker = null;
		}
	}

	initializeMaterialize();
	initializeSources();
	initializeMap();
	// initializeSearch(); // Removed - search functionality integrated into map initialization
	// initializeRectangleTool(); // Now called after map loads
	initializeGridPreview();
	initializeMoreOptions();
	initializeDownloader();
});