/*****************************************************************************
 * FILE:    GRACE VIEWER MAIN.JS
 * DATE:    11 May 2017
 * AUTHOR: Sarva Pulla
 * COPYRIGHT: (c) Brigham Young University 2017
 * LICENSE: BSD 2-Clause
 *****************************************************************************/

/*****************************************************************************
 *                      LIBRARY WRAPPER
 *****************************************************************************/

var LIBRARY_OBJECT = (function() {
    // Wrap the library in a package function
    "use strict"; // And enable strict mode for this library

    /************************************************************************
     *                      MODULE LEVEL / GLOBAL VARIABLES
     *************************************************************************/
    var current_layer,
        element,
        layers,
        layers_dict,
        map,
        popup,
        public_interface, // Object returned by the module
        slider_max,
        wms_source,
        wms_layer;




    /************************************************************************
     *                    PRIVATE FUNCTION DECLARATIONS
     *************************************************************************/
    var add_wms,init_slider,init_events,init_map,init_vars,update_wms,graph_animation,new_layer;


    /************************************************************************
     *                    PRIVATE FUNCTION IMPLEMENTATIONS
     *************************************************************************/
    init_vars = function(){
        var $layers_element = $('#layers');
        slider_max = $layers_element.attr('data-slider-max');
    };


    init_events = function() {
        (function () {
            var target, observer, config;
            // select the target node
            target = $('#app-content-wrapper')[0];

            observer = new MutationObserver(function () {
                window.setTimeout(function () {
                    map.updateSize();
                }, 350);
            });
            $(window).on('resize', function () {
                map.updateSize();
            });

            config = {attributes: true};

            observer.observe(target, config);
        }());

        map.on("singleclick",function(evt){

            $(element).popover('destroy');


            if (map.getTargetElement().style.cursor == "pointer") {
                var clickCoord = evt.coordinate;
                popup.setPosition(clickCoord);
                var view = map.getView();
                var viewResolution = view.getResolution();

                var wms_url = current_layer.getSource().getGetFeatureInfoUrl(evt.coordinate, viewResolution, view.getProjection(), {'INFO_FORMAT': 'application/json'}); //Get the wms url for the clicked point
                if (wms_url) {
                    //Retrieving the details for clicked point via the url
                    $.ajax({
                        type: "GET",
                        url: wms_url,
                        dataType: 'json',
                        success: function (result) {
                            var value = parseFloat(result["features"][0]["properties"]["GRAY_INDEX"]);
                            value = value.toFixed(2);
                            $(element).popover({
                                'placement': 'top',
                                'html': true,
                                //Dynamically Generating the popup content
                                'content':'Value: '+value
                            });

                            $(element).popover('show');
                            $(element).next().css('cursor', 'text');


                        },
                        error: function (XMLHttpRequest, textStatus, errorThrown) {
                            console.log(Error);
                        }
                    });
                }
            }
        });

        map.on('pointermove', function(evt) {
            if (evt.dragging) {
                return;
            }
            var pixel = map.getEventPixel(evt.originalEvent);
            var hit = map.forEachLayerAtPixel(pixel, function(layer) {
                if (layer != layers[0]){
                    current_layer = layer;
                    return true;}
            });
            map.getTargetElement().style.cursor = hit ? 'pointer' : '';
        });
    };

    init_map = function(){
        var projection = ol.proj.get('EPSG:3857');
        var baseLayer = new ol.layer.Tile({
            source: new ol.source.BingMaps({
                key: '5TC0yID7CYaqv3nVQLKe~xWVt4aXWMJq2Ed72cO4xsA~ApdeyQwHyH_btMjQS1NJ7OHKY8BK-W-EMQMrIavoQUMYXeZIQOUURnKGBOC7UCt4',
                imagerySet: 'AerialWithLabels' // Options 'Aerial', 'AerialWithLabels', 'Road'
            })
        });
        var fullScreenControl = new ol.control.FullScreen();
        var view = new ol.View({
            center: [15584728.7111+11131949.0793+11131949.0793,1689200.13961],
            projection: projection,
            zoom: 2
        });
        wms_source = new ol.source.ImageWMS();

        wms_layer = new ol.layer.Image({
            source: wms_source
        });
        layers = [baseLayer,wms_layer];

        layers_dict = {};


        map = new ol.Map({
            target: document.getElementById("map"),
            layers: layers,
            view: view
        });
        map.addControl(new ol.control.ZoomSlider());
        map.addControl(fullScreenControl);
        map.crossOrigin = 'anonymous';
        element = document.getElementById('popup');

        popup = new ol.Overlay({
            element: element,
            positioning: 'bottom-center',
            stopEvent: true
        });
        map.addOverlay(popup);
    };

    add_wms = function(){
        // gs_layer_list.forEach(function(item){
        map.removeLayer(wms_layer);
        var store_name = $("#select_layer").find('option:selected').val();
        var layer_name = 'globalgrace:'+store_name;
        var sld_string = '<StyledLayerDescriptor version="1.0.0"><NamedLayer><Name>'+layer_name+'</Name><UserStyle><FeatureTypeStyle><Rule>\
        <RasterSymbolizer> \
        <ColorMap> \
        <ColorMapEntry color="#000000" quantity="-50" label="nodata" opacity="0.0" /> \
        <ColorMapEntry color="#FF0000" quantity="0" label="label1" opacity="0.4"/>\
        <ColorMapEntry color="#0000FF" quantity="50" label="label2" opacity="0.4"/>\
        </ColorMap>\
        </RasterSymbolizer>\
        </Rule>\
        </FeatureTypeStyle>\
        </UserStyle>\
        </NamedLayer>\
        </StyledLayerDescriptor>';

        wms_source = new ol.source.ImageWMS({
            url: 'http://127.0.0.1:8181/geoserver/wms',
            params: {'LAYERS':layer_name,'SLD_BODY':sld_string},
            serverType: 'geoserver',
            crossOrigin: 'Anonymous'
        });

        wms_layer = new ol.layer.Image({
            source: wms_source
        });

        map.addLayer(wms_layer);

    };

    update_wms = function(date_str){
        // map.removeLayer(wms_layer);
        var layer_name = 'globalgrace:'+date_str;
        var sld_string = '<StyledLayerDescriptor version="1.0.0"><NamedLayer><Name>'+layer_name+'</Name><UserStyle><FeatureTypeStyle><Rule>\
        <RasterSymbolizer> \
        <ColorMap> \
        <ColorMapEntry color="#000000" quantity="-50" label="nodata" opacity="0.0" /> \
        <ColorMapEntry color="#FF0000" quantity="0" label="label1" opacity="0.4"/>\
        <ColorMapEntry color="#0000FF" quantity="50" label="label2" opacity="0.4"/>\
        </ColorMap>\
        </RasterSymbolizer>\
        </Rule>\
        </FeatureTypeStyle>\
        </UserStyle>\
        </NamedLayer>\
        </StyledLayerDescriptor>';

        wms_source.updateParams({'LAYERS':layer_name,'SLD_BODY':sld_string});

    };

    init_slider = function(){

        $( "#slider" ).slider({
            value:1,
            min: 0,
            max: slider_max - 1,
            step: 1, //Assigning the slider step based on the depths that were retrieved in the controller
            animate:"fast",
            slide: function( event, ui ) {
                var date_text = $("#select_layer option")[ui.value].text;
                $( "#grace-date" ).val(date_text); //Get the value from the slider
                var date_value = $("#select_layer option")[ui.value].value;
                update_wms(date_value);
            }
        });

    };


    /************************************************************************
     *                        DEFINE PUBLIC INTERFACE
     *************************************************************************/

    public_interface = {

    };

    /************************************************************************
     *                  INITIALIZATION / CONSTRUCTOR
     *************************************************************************/

    // Initialization: jQuery function that gets called when
    // the DOM tree finishes loading
    $(function() {
        // Initialize Global Variables
        init_map();
        init_events();
        init_vars();
        init_slider();

        $("#select_layer").change(function(){
            add_wms();
        }).change();

         var animationDelay = 1000;
        var sliderInterval = {};

        $(".btn-run").on("click", function() {
            //Set the slider value to the current value to start the animation at the correct point.

            var sliderVal = $("#slider").slider("value");
            sliderInterval = setInterval(function() {
                sliderVal += 1;
                $("#slider").slider("value", sliderVal);
                if (sliderVal=== slider_max - 1) sliderVal=0;
            }, animationDelay);
        });
        $(".btn-stop").on("click", function() {
                //Call clearInterval to stop the animation.
                clearInterval(sliderInterval);
            });

        $("#slider").on("slidechange", function(event, ui) {
            var date_text = $("#select_layer option")[ui.value].text;
            $( "#grace-date" ).val(date_text); //Get the value from the slider
            var date_value = $("#select_layer option")[ui.value].value;
            update_wms(date_value);

        });

    });

    return public_interface;

}()); // End of package wrapper
// NOTE: that the call operator (open-closed parenthesis) is used to invoke the library wrapper
// function immediately after being parsed.