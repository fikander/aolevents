

google.load("maps", "3", {other_params:"sensor=false"});

// jquery comes with the package
// google.load("jquery", "1.3.2");


////////////////////////////////////////////////////////////////////////////////////////
//
// Add event form google maps support
//
////////////////////////////////////////////////////////////////////////////////////////

var LocationShow = {
    map: null,
    
    initialize: function(location, title)
    {
        var myOptions = {
            zoom: 9,
            center: location,
            mapTypeId: google.maps.MapTypeId.ROADMAP,
            mapTypeControl: false
        }
    	LocationShow.map = new google.maps.Map(document.getElementById("map_canvas"), myOptions);

    	var marker = new google.maps.Marker({
    		position: location,
    		map: LocationShow.map,
    		title: title,
    		draggable: false
    		});
    }
}

var LocationSetter = {

    map: null,
    marker: null,
    geocoder: null,
    
    location_elem: 'id_location',
    
    initialize: function()
    {
        //try to get the value from id_location
        var myLatlng = null;

        var latlng_string = document.getElementById(LocationSetter.location_elem).value;
        if (latlng_string.length > 0) {
           var latlng_array = latlng_string.split(',');
           if (latlng_array.length == 2)
               myLatlng = new google.maps.LatLng(parseFloat(latlng_array[0]), parseFloat(latlng_array[1]));
        }

        if (myLatlng == null)
            myLatlng = new google.maps.LatLng(0, 0);

        var myOptions = {
            zoom: 2,
            center: myLatlng,
            mapTypeId: google.maps.MapTypeId.ROADMAP,
            mapTypeControl : false
        }
        LocationSetter.map = new google.maps.Map(document.getElementById("map_canvas"), myOptions);
        LocationSetter.geocoder = new google.maps.Geocoder();

        var marker = new google.maps.Marker({
            position: myLatlng,
            map: LocationSetter.map,
            title: "New Event",
            draggable: true
        });
        LocationSetter.marker = marker

        // set drag listeners
        google.maps.event.addListener(marker, 'dragstart', function(){});

        google.maps.event.addListener(marker, 'drag', function(){ });

        google.maps.event.addListener(marker, 'dragend', function(){
            LocationSetter.geocodePosition(marker.getPosition());
        });

        google.maps.event.addListener(LocationSetter.map, 'click', function(event){
            LocationSetter.setMarkerLocation(event.latLng);
            LocationSetter.geocodePosition(marker.getPosition());            
        });

    },
  
    geocodePosition: function(position)
    {
        LocationSetter.geocoder.geocode( { latLng: position },
                          function (responses) {
            if (responses && responses.length > 0) {

                LocationSetter.updateMarkerAddressFromResponse(responses[0]);
                LocationSetter.updateMarkerLocation();

            } else {
                LocationSetter.updateMarkerAddress('Cannot determine address at this location.', null, null)
            }

            }
        );
    },
    

    geocodeAddress: function(address)
    {
        LocationSetter.geocoder.geocode( {'address': address}, function(results, status) {

            if (status == google.maps.GeocoderStatus.OK) {

                var location = results[0].geometry.location;

                LocationSetter.setMarkerLocation(location);
                LocationSetter.map.setCenter(location);

                if (LocationSetter.map.getZoom() < 10)
                    LocationSetter.map.setZoom(10);

                // fill address fields
                LocationSetter.updateMarkerAddressFromResponse(results[0]);
            } else {
                alert("Couldnt find address for the following reason: " + status);
            }
        });

    },    
    
    updateMarkerAddressFromResponse: function(response)
    {
        var r = response

        // Find country and region
        var country = null;
        var administrative_area_1 = null;
        var formatted_address = [];

        for (var i = 0; i < r.address_components.length; i++)  {
            var comp = r.address_components[i];
            var found_country = false;
            var found_administrative_area_1 = false;

            for (var j = 0; j < comp.types.length; j++) {
                found_country = found_country || (comp.types[j] === "country");
                found_administrative_area_1 = found_administrative_area_1 || (comp.types[j] === "administrative_area_level_1");
            }

            if (found_country)
                country = comp.long_name + ' [' + comp.short_name + ']';
            if (found_administrative_area_1)
                if (comp.long_name == comp.short_name)
	                administrative_area_1 = comp.long_name;
	            else
    	            administrative_area_1 = comp.long_name + ' [' + comp.short_name + ']';
            if (!(found_country || found_administrative_area_1))
                // remember it as part of address
                formatted_address.push(comp.long_name);
        }
            LocationSetter.updateMarkerAddress(formatted_address.join(', '), country, administrative_area_1);    
    },


    setMarkerLocation: function(location) {
        LocationSetter.marker.setPosition(location);
        LocationSetter.updateMarkerLocation();
    },

    updateMarkerLocation: function() {
        pos = LocationSetter.marker.getPosition();
        document.getElementById(LocationSetter.location_elem).value = [pos.lat(), pos.lng()].join(',');
    },
    
    updateMarkerAddress: function(addr, country, region)
    {
        document.getElementById('address').innerHTML = addr;        
        document.getElementById('id_country').value = country;
        document.getElementById('id_region').value = region;
    }

};


////////////////////////////////////////////////////////////////////////////////////////
//
// CSV parser
// handles actual rendering of html for events in the list
//
////////////////////////////////////////////////////////////////////////////////////////

var EventsInfo = {

    _getIconUrlForEventType: function(type_id)
    {
        var icon_params = {
            0 : 'C|FFCC00|000000',
            1 : 'C|FFCC00|000000',
            2 : 'C|FFCC00|000000',
            3 : 'C|FFCC00|000000',
            4 : 'C|FFCC00|000000',
            5 : 'C|FFCC00|000000',
            //TODO
        };
        var icon = icon_params[type_id];
        if (icon == null)
            icon = 'O|CCFF00|000000';
        // definition at:
        //http://groups.google.com/group/google-chart-api/web/chart-types-for-map-pins?pli=1
        return "http://chart.apis.google.com/chart?chst=d_map_pin_letter&chld=" + icon;
    },

    getIconForEventType: function(type_id)
    {
        /*
        var default_icon='icons-sun-64 icon-sun-64-1'
        var icons = {
            0 : 'icons-sun-64 icon-sun-64-2',
            1 : 'icons-sun-64 icon-sun-64-3'
            //TODO
        }

        var ico = icons[type_id];
        if (ico == null)
            ico = default_icon

        // if it was normal images, we'd use this:
        //return site_data.settings.MEDIA_URL + ico
        return '<img class="' + ico + '"/>' 
        */
        // this returns 21x34
        return "<img src='" + EventsInfo._getIconUrlForEventType(type_id) + "' width='15' height='23'/>"
    },

    parseCSVLine: function(data)
    {
        var values = data.split(",");
        var params = {
            name: values[0],
            type: values[1],
            type_id: parseInt(values[2], 10),
            start_date: values[3],
            end_date: values[4],
            recurrent: values[5],
            lat: parseFloat(values[6]),
            lng: parseFloat(values[7]),
            url_show: values[8],
            key_id: values[9],
            featured_priority: parseInt(values[10], 10),
            is_free: values[11] != '0',
            is_fav: values[12] != '0',
            rsvp: parseInt(values[13], 10)
        };
        return params;
    },

    getHTMLForHeader: function()
    {
        var html = '<table id="item_list_header"><tr>';
        html += '<td style="width:65px">Subscribe</td>';
        html += '<td>Description</td>';
        html += '<td style="width:100px">Start date</td>';
        html += '<td style="width:100px">End date</td>';
        html += '</tr></table>';
        
        return html;
    },

    getHTMLForEvent: function(params, href)
    {
        var free_desc = '';
		if (params['is_free'])
		    free_desc = ' [FREE]';

        var html = '<table><tr>';
        if (href)
        {
            html += '<td style="width:30px">' +
	    	        '<a href="' + href + '">' +
	    	        EventsInfo.getIconForEventType(params['type_id']) +
	    	        '</a></td>';
	    }
		html += '<td style="width:35px"> <div id="event_'+params['key_id']+'">' + params['is_fav'] + '</div>' + '</td>';
        html += '<td> <span class="title"><a href="' + params['url_show'] + '">' + params['type'] + free_desc + '</a></span><br>' +
                params['name'] + '</td>';
        html += '<td style="width:100px">' + params['start_date'] +'<br>'+ params['recurrent'] + '</td>';
        html += '<td style="width:100px">' + params['end_date'] + '</td>';
        html += '</tr></table>';

    	return html;
    }

};

////////////////////////////////////////////////////////////////////////////////////////
//
//  Favourite button
//
////////////////////////////////////////////////////////////////////////////////////////


var FavButton = {

// Smaller fav icons don't look as obvious as bigger ones, methinks...
//    fav_on: '<img class="icons-fav-20 icons-fav-on-20" alt="This is your favourite item"/>',
//    fav_off: '<img class="icons-fav-20 icons-fav-off-20" alt="Click to make it your favourite!"/>',
//    fav_disabled: '<a href="/account/login/"><img class="icons-fav-20 icons-fav-off-20" alt="Log in to mark this item as favourite"/></a>',

// Slightly bigger icons here.
    fav_on: '<img class="icons-fav-32 icons-fav-on-32" />',
    fav_off: '<img class="icons-fav-32 icons-fav-off-32" />',
    fav_disabled: '<a href="/account/login/"><img class="icons-fav-32 icons-fav-off-32" /></a>',

    makeButton: function(element, initial_state, is_authenticated)
    // NOTE: element must have 'id' named "event_XXXX", where XXXX is key_id of the event
    {
        // init the button
        if (! is_authenticated)
        {
            $(element).html( FavButton.fav_disabled );
            return;
        }

        if (initial_state)
            $(element).html( FavButton.fav_on );
        else
            $(element).html( FavButton.fav_off );

        // attach event to click
        $(element).click(function(){
            $.ajax({
                type:"POST",
                url:"/events/favourite/toggle/",
                data: 'key_id=' + $(this).attr("id").substring(6), // need to strip leading 'event_'
                dataType: "text",
                global: false,
                // we only 
                success: function(data, status) {

                              if (data != '0')
                                  $(element).html( FavButton.fav_on );
                              else
                                  $(element).html( FavButton.fav_off );
                          }
            });
        });
    }
};

////////////////////////////////////////////////////////////////////////////////////////
//
//  Map with event markers on it
//
////////////////////////////////////////////////////////////////////////////////////////


var EventMap = {

    map_element: "map_canvas",

    map: null,

    // contains list of: ( { 'start': values['start_date'], 'type': values['type'], 'html': html, 'marker': marker })
    event_list: [],

    // this is to keep independent list of markers for links triggering 'click' events on map, since event_list is being re-sorted
    markers: [],

	//current map bounds
    bounds: null,
    initial_bounds: null,

	// last visible info window for marker
    visibleInfoWindow: null,

	// elements in the DOM
	country_select_elem: null,
	region_select_elem: null,
	forfree_boolean_elem: null,
	forwho_radio_elem: null,
	sort_select_elem: null,
	typelist_select_elem: null,
	dest_elem: null,

	// used to decide if loadData should be called
    last_country_select_elem_val: '',
    last_region_select_elem_val: '',

    OPEN_EVENTS_MASK: 0,
    MEMBERS_EVENTS_MASK: 0,
    
    // true before fetch_content handler is called
    loading_data: false,
    
    // whether user is authenticated. need this information to
    // display some parts of user interface
    is_authenticated: false,
    
    extra_GET_parameters: '',

    initialize: function(	country_select,
    						region_select,
    						forfree_boolean,
    						forwho_radio,
    						typelist_select,    						
    						sort_select,
    						dest,
    						search_button,
    						OPEN_EVENTS_MASK,
    						MEMBERS_EVENTS_MASK,
    						is_authenticated,
    						extra_GET_parameters )
    {
        var myLatlng = new google.maps.LatLng(0, 0);
        var myOptions = {
            zoom: 1,
            center: myLatlng,
            mapTypeId: google.maps.MapTypeId.ROADMAP,
            mapTypeControl : false
        }
        EventMap.map = new google.maps.Map(document.getElementById(EventMap.map_element), myOptions);

        EventMap.country_select_elem = $(country_select);
		EventMap.region_select_elem = $(region_select);
		EventMap.forfree_boolean_elem = $(forfree_boolean);
		EventMap.forwho_radio_elem = forwho_radio;
		EventMap.typelist_select_elem = typelist_select;
		EventMap.sort_select_elem = $(sort_select);
		EventMap.dest_elem = $(dest);
		
		EventMap.OPEN_EVENTS_MASK = OPEN_EVENTS_MASK;
		EventMap.MEMBERS_EVENTS_MASK = MEMBERS_EVENTS_MASK;

		EventMap.is_authenticated = is_authenticated;
		
		EventMap.extra_GET_parameters = extra_GET_parameters;


        // register event on map being idle
        google.maps.event.addListener(EventMap.map, 'idle', function(){
            if (EventMap.loading_data)
            {
                //console.log("event: map idle IGNORED");
                EventMap.loading_data = false;                    
                return;
            }
            //console.log("event: map idle");
            EventMap.filterDisplayEvents( EventMap.map.getBounds() );
        });

		// register event for search button and trigger it initially
        $(search_button).click( function() {
            //console.log("event: search button");
            EventMap.loading_data = true;

            // display waiting icon
            EventMap.dest_elem.html( "<center><img src='" + site_data.settings.MEDIA_URL + "global/wait.gif'/></center>" );

            // only reload data if something has changed
            if ( (EventMap.country_select_elem.val() != EventMap.last_country_select_elem_val) ||
                 (EventMap.region_select_elem.val() != EventMap.last_region_select_elem_val) )
            {
                // something has changed - reload data from the server
                EventMap.last_country_select_elem_val = EventMap.country_select_elem.val();
                EventMap.last_region_select_elem_val = EventMap.region_select_elem.val();

                EventMap.loadData( EventMap.country_select_elem.val(), EventMap.region_select_elem.val() );
            }
            else
            {
                // filter data again - no need to reload data
                // use wide original bounds, so that all markers are recalculated
                EventMap.bounds = EventMap.filterDisplayEvents( EventMap.initial_bounds );
                EventMap.setMapBoundsZoom();
            }

        });

		// triggr event initially
		$(search_button).click();

		// register event for filter change
		EventMap.sort_select_elem.change( function() {
		    //console.log("event: filter change");
			// all that needs to be done is sort and display
	        EventMap.sortEvents( EventMap.sort_select_elem.val() );
			new_bounds = EventMap.filterDisplayEvents( null );
			// ignore new_bounds, because we haven't moved the map or changed filtering
		});
    },
    
    setMapBoundsZoom: function() {
        // set proper map zoom from bounds
        if (EventMap.bounds != null) {
            EventMap.map.fitBounds(EventMap.bounds);
            if (EventMap.map.getZoom() > 10)
                EventMap.map.setZoom(10);
        }
    },

    openInfoWindow: function(infoWindow, marker) {
        return function() {
            if (EventMap.visibleInfoWindow) {
                EventMap.visibleInfoWindow.close();
            }

            EventMap.visibleInfoWindow = infoWindow;         
            infoWindow.open(EventMap.map, marker);

        };
    },
  
    addMarker: function(values)
    {
        //console.log("addMarker");
    
        var pos = new google.maps.LatLng(values['lat'], values['lng']);
        var marker = new google.maps.Marker({
            position: pos,
            map: EventMap.map,
            title: values['name'],
            draggable: false,
            icon: EventsInfo._getIconUrlForEventType(values['type_id'])
        });
        EventMap.markers.push(marker);

        EventMap.bounds.extend(pos);

        // create info window for the marker
        var infoWindow = new google.maps.InfoWindow({
            content: [
                '<a href="', values['url_show'], '">',
                '<h3 style="">', values['name'], '</h3></a>',
                values['type'], '<br/> starts:', values['start_date']
            ].join(''),
            size: new google.maps.Size(200, 80)
        });
    
        //add marker click event listener
        google.maps.event.addListener(marker, 'click', EventMap.openInfoWindow(infoWindow, marker));

        //return marker handle
        return { 'handle': marker, 'id': EventMap.markers.length - 1 } ;
    },

    removeMarkersAndList: function()
    {
        //console.log("removeMarkersAndList");

        var m = null;
        while ( m = EventMap.event_list.pop() )
            m['marker'].setMap(null);

        bounds = null;
    },


    clickOnIconInTheList: function(marker_id)
    {
        google.maps.event.trigger(EventMap.markers[marker_id], 'click');
        // jump to the map
        window.location = "#" + EventMap.map_element;
    },


    addEventToList: function(params, marker_handle, marker_id)
    {
        var click_js = "javascript:EventMap.clickOnIconInTheList("+marker_id+");";
	    var html = EventsInfo.getHTMLForEvent(params, click_js );

        EventMap.event_list.push(
                { 'start': params['start_date'],
                  'type': params['type'],
                  'type_id' : params['type_id'],
                  'is_free' : params['is_free'],
                  'html': html,
                  'key_id': params['key_id'],
                  'is_fav': params['is_fav'],
                  'marker': marker_handle,
                  'visible': true})
    },

    filterEvent: function( event_data )
    // this is filtering according to filter form
    // return false if shouldnt be visible
    {
        if ( !event_data['is_free'] && EventMap.forfree_boolean_elem.attr('checked') )
            return false;

        switch ( $(EventMap.forwho_radio_elem).val() )
        {
            case 'everyone':
                return ((1 << event_data['type_id']) & EventMap.OPEN_EVENTS_MASK) > 0;
            case 'members':
                return true;
            case 'custom':
                var sum = 0;
                $(EventMap.typelist_select_elem).each(function(i, selected) {
                        sum += 1 << parseInt($(selected).val(), 10);
                    });
                return ((1 << event_data['type_id']) & sum) > 0;
        }

        return true;
    },

    filterDisplayEvents: function( map_bounds )
    // filter only visible events, sort them, and display on the list
    {
        //console.log("filterDisplayEvents, loading_data", EventMap.loading_data);

		if (map_bounds != null) {
	        // first filter out invisible events
	        for (var i = 0; i < EventMap.event_list.length; i++)
	        	EventMap.event_list[i]['visible'] = map_bounds.contains( EventMap.event_list[i]['marker'].getPosition() )
	    }

        // reset data just before adding new stuff
        EventMap.dest_elem.html( EventsInfo.getHTMLForHeader() );

        var new_bounds = new google.maps.LatLngBounds();

        for (var j = 0; j < EventMap.event_list.length; j++)
        {
        	if (EventMap.event_list[j]['visible'])
        	    if (EventMap.filterEvent( EventMap.event_list[j] ))
        	    {
        	        // produce some html in the table
	                EventMap.dest_elem.append( EventMap.event_list[j]['html'] );

	                // attach fav icon system
	                FavButton.makeButton( "#event_" + EventMap.event_list[j]['key_id'],
	                                      EventMap.event_list[j]['is_fav'] != '0',
	                                      EventMap.is_authenticated );

	                // show marker
	                EventMap.event_list[j]['marker'].setVisible(true);
	                new_bounds.extend( EventMap.event_list[j]['marker'].getPosition() );
	            }
	            else
	            {
	                // hide marker
	                EventMap.event_list[j]['marker'].setVisible(false);
                }
        }

        return new_bounds;
    },


    handleFetchContent: function(response, status)
    {
        if (response === null || (status !== "success"))
            return;

        //console.log("handleFetchContent, loading_data", EventMap.loading_data);

        // remove existing markers
        EventMap.removeMarkersAndList();
        
        EventMap.bounds = new google.maps.LatLngBounds()

        // parse data about events
        var markerData = response.split("\n");

        for (var i = 0; i < markerData.length; i++)
        {
            if (markerData[i] !== "")
            {
                var params = EventsInfo.parseCSVLine(markerData[i]);
                var marker_data = EventMap.addMarker(params);
                EventMap.addEventToList(params, marker_data['handle'], marker_data['id']);
            }
        }

        EventMap.sortEvents( EventMap.sort_select_elem.val() )

        EventMap.initial_bounds = new google.maps.LatLngBounds(
                EventMap.bounds.getSouthWest(),
                EventMap.bounds.getNorthEast() );

        // after re-zooming the map we can now finally sort and display events
        // all events will be displayed as bounds encompass all of them
        // NOTE: whenever map bounds change this function is called anyway!
        //EventMap.filterDisplayEvents( EventMap.bounds );
        EventMap.bounds = EventMap.filterDisplayEvents( EventMap.initial_bounds );
        EventMap.setMapBoundsZoom();
    },

    sortEvents: function(sort_type)
    {
        // event_list contains lists of: ([values['start_date'], values['type'], html])
        f = null;
        switch (sort_type) {
            case 'date-asc': f = function(a, b) {
							            if (a['start'] === b['start'])
							                return 0;
							            else if (a['start'] < b['start'])
							                return -1;
							            else
							                return 1;
				            	}
				            break;

			case 'date-desc': f = function(a, b) {
							            if (a['start'] === b['start'])
							                return 0;
							            else if (a['start'] < b['start'])
							                return 1;
							            else
							                return -1;
				            	}
				            break;
			case 'type' : f = function(a, b) {
							            if (a['type'] === b['type'])
							                return 0;
							            else if (a['type'] < b['type'])
							                return -1;
							            else
							                return 1;
				            	}
				            break;
        }

		if (f)
	        EventMap.event_list.sort( f );
    },


    loadData: function(country, region)
    {
        //console.log("loadData :", country, ", ", region);
        var url = "/events/serialise/" + country + "/" + region + "/?format=csv" + EventMap.extra_GET_parameters;
        
        //this is to block first 'click' event which will be triggered unnecessarily after data has been fetched
        $.get(url, {}, EventMap.handleFetchContent, "text")
    }

};

////////////////////////////////////////////////////////////////////////////////////////
//
// FeaturedEvents
//
////////////////////////////////////////////////////////////////////////////////////////


var FeaturedEvents = {

	dest_elem: null,
	is_authenticated: false,
	extra_GET_parameters: '',


    initialize: function(   dest_elem,
    						is_authenticated,
    						extra_GET_parameters )
    {
    	FeaturedEvents.dest_elem = $(dest_elem);
		FeaturedEvents.is_authenticated = is_authenticated;
		FeaturedEvents.extra_GET_parameters = extra_GET_parameters;
    },

    handleFetchContentFeatured: function(response, status)
    {
        if (response === null || (status !== "success"))
            return;

        // parse data about events
        var markerData = response.split("\n");

        FeaturedEvents.dest_elem.html( EventsInfo.getHTMLForHeader() );

        for (var i = 0; i < markerData.length; i++)
        {
            if (markerData[i] !== "")
            {
                var params = EventsInfo.parseCSVLine(markerData[i]);
                var html = EventsInfo.getHTMLForEvent(params, null);
            	FeaturedEvents.dest_elem.append( html );
                // attach fav icon system
                FavButton.makeButton( "#event_" + params['key_id'],
                                      params['is_fav'],
                                      FeaturedEvents.is_authenticated );
            }
        }
    },

    loadDataFeatured: function(priority)
    {
        // load featured only with featured_priority >= specified
        var url = "/events/serialise/_featured/" + priority + "/?format=csv" + FeaturedEvents.extra_GET_parameters;

        $.get(url, {}, FeaturedEvents.handleFetchContentFeatured, "text")
    }

}

////////////////////////////////////////////////////////////////////////////////////////
//
// Getting regions for country and updating combo box
//
////////////////////////////////////////////////////////////////////////////////////////


var RegionComboBox = {


    region_element: null,
	country_element: null,    
	add_all: false,


	handle_updateComboBoxWithRegions: function(response, status)
	{
		RegionComboBox.region_element.empty();	
		if (RegionComboBox.add_all) {
			RegionComboBox.region_element.append("<option value='all'>All</option>");
		}

        if (response === null || (status !== "success")) {
			if (!RegionComboBox.add_all) {
				RegionComboBox.region_element.append("<option value='error'>Error loading data</option>");
			}
            return;
        }

        // parse data about regions
        var regionData = response.split("\n");

        for (var i = 0; i < regionData.length; i++)
        {
            if (regionData[i] !== "")
            {
                var values = regionData[i].split(",");
                var html = "<option value='" + values[0] + "'>" + values[1] + "</option>";
                RegionComboBox.region_element.append(html);
            }
        }
	},

	updateComboBoxWithRegions: function(country)
	{
		
	    // erase all exisitng options and put 'wait...'
	    RegionComboBox.region_element.empty();
	    RegionComboBox.region_element.append("<option value=''>just a sec...</option>");

	    //download data
	    $.get("/events/serialise/_regions/" + country + "/?format=csv", {}, RegionComboBox.handle_updateComboBoxWithRegions, "text");
	},
	


	attachOnChangeToComboBox: function(country_select_id, region_select_id, add_all, initial_trigger) {
	
	    RegionComboBox.region_element = $(region_select_id);
	    RegionComboBox.country_element = $(country_select_id);
		RegionComboBox.add_all = add_all;

        RegionComboBox.country_element.change( function() {

			country = $(this).val();
        	RegionComboBox.updateComboBoxWithRegions(country);
        })

        if (initial_trigger)
        	RegionComboBox.updateComboBoxWithRegions( RegionComboBox.country_element.val() );

    }	
};


