var stack = [];
var nextStack = [];
var currentSlide = 0;
var isRotating = false;

var $audioPlayer = null;
var $welcomeScreen = null;
var $welcomeSubmitButton = null;
var $welcomeForm = null;
var $stack = null;


/* balance of power */
var $graphic;
var bar_gap = 5;
var bar_height = 30;
var color;
var graphic_margin = 6;
var is_mobile = false;
var label_width = 30;
var mobile_threshold = 480;
var num_x_ticks = 5;
var round_increment = 10;
var fmt_comma = d3.format(',');
var fmt_year_abbrev = d3.time.format('%y');
var fmt_year_full = d3.time.format('%Y');



var resizeSlide = function(slide) {
    var $w = $(window).width();
    var $h = $(window).height();
    slide.width($w);
    slide.height($h);
}

var rotateSlide = function() {
    console.log('Rotating to next slide');
    isRotating = true;

    currentSlide += 1;

    if (currentSlide >= stack.length) {
        if (nextStack.length > 0) {
            console.log('Switching to new stack');
            stack = nextStack;
            nextStack = [];
        }

        currentSlide = 0;
    }
    
    if (stack[currentSlide]['slug'] === 'state') {
        slide_path = 'slides/state-' + $.cookie('state') + '.html';
    } else {
        slide_path = 'slides/' + stack[currentSlide]['slug'] + '.html';
    }

    $.ajax({
        url: APP_CONFIG.S3_BASE_URL + '/' + slide_path,
        success: function(data) {
            var $oldSlide = $('#stack').find('.slide');
            var $newSlide = $(data);

            $('#stack').append($newSlide);
            
            resizeSlide($newSlide)

            if (slide_path == 'slides/balance-of-power.html') {
				$graphic = $('#graphic');
				render_bop();
				$(window).on('resize', render_bop);
            } else {
				$(window).unbind('resize', render_bop);
            }

            $oldSlide.fadeOut(function(){
                $(this).remove();
            });

            $newSlide.fadeIn(function(){
                console.log('Slide rotation complete');
                setTimeout(rotateSlide, APP_CONFIG.SLIDE_ROTATE_INTERVAL * 1000);
            });
        }
    });
}

function getStack() {
    console.log('Updating the stack');

    $.ajax({
        url: APP_CONFIG.S3_BASE_URL + '/live-data/stack.json',
        dataType: 'json',
        success: function(data) {
            nextStack = data;

            console.log('Stack update complete');

            if (!isRotating) {
                rotateSlide();
            }

            setTimeout(getStack, APP_CONFIG.STACK_UPDATE_INTERVAL * 1000);
        }
    });
}

var onWelcomeFormSubmit = function(e) {
    e.preventDefault();

    var state = $('.state-selector').val();

    $.cookie('state', state);

	$welcomeScreen.hide();
    $stack.show();

    getStack();
}


var setUpAudio = function() {
    $audioPlayer.jPlayer({
        ready: function () {
            $(this).jPlayer('setMedia', {
                mp3: 'http://nprdmp.ic.llnwd.net/stream/nprdmp_live01_mp3'
            }).jPlayer('pause');
        },
        swfPath: 'js/lib',
        supplied: 'mp3',
        loop: false,
    });
}


/* BALANCE OF POWER */
function render_bop() {
	var container_width = $('#stack').width();
	var graphic_width = Math.floor((container_width - 22) / 2);

    if (container_width <= mobile_threshold) {
    	is_mobile = true;
    } else {
    	is_mobile = false;
    }

    // clear out existing graphics
    $graphic.empty();
    
    draw_bop('house', graphic_width);    
    draw_bop('senate', graphic_width);    
}
function draw_bop(id, graphic_width) {
	var graphic_data = eval('data_' + id);
	var majority = eval('majority_' + id);
	var majority_rounded = Math.ceil(majority / round_increment) * round_increment;
    var margin = { top: 20, right: 10, bottom: 20, left: (label_width + 6) };
    var num_bars = graphic_data.length;
    var width = graphic_width - margin['left'] - margin['right'];
    var height = ((bar_height + bar_gap) * num_bars);
    
    var graph = d3.select('#graphic')
    	.append('div')
    		.attr('class', 'chart ' + classify(id))
    		.attr('width', graphic_width);

    var header = graph.append('h3')
    	.attr('style', 'margin-left: ' + margin['left'] + 'px;')
		.text(eval('header_' + id));
    
    var x = d3.scale.linear()
        .domain([0,
        	d3.max(graphic_data, function(d) { 
				return Math.ceil(d['seats'] / round_increment) * round_increment;
            })
	    ]);
	
	if (x.domain()[1] < majority_rounded) {
		x.domain()[1] = majority_rounded;
	}
	
	x.range([0, width]);
	
    var y = d3.scale.linear()
        .range([height, 0]);

    var xAxis = d3.svg.axis()
        .scale(x)
        .orient('bottom')
        .ticks(num_x_ticks);
        
    var x_axis_grid = function() { 
        return xAxis;
    }

    var svg = graph.append('svg')
        .attr('width', width + margin['left'] + margin['right'])
        .attr('height', height + margin['top'] + margin['bottom'])
        .append('g')
        .attr('transform', 'translate(' + margin['left'] + ',' + margin['top'] + ')');

    svg.append('g')
        .attr('class', 'x axis')
        .attr('transform', 'translate(0,' + height + ')')
        .call(xAxis);

    svg.append('g')
        .attr('class', 'x grid')
        .attr('transform', 'translate(0,' + height + ')')
        .call(x_axis_grid()
            .tickSize(-height, 0, 0)
            .tickFormat('')
        );
    
    svg.append('g')
        .attr('class', 'bars')
        .selectAll('rect')
            .data(graphic_data)
        .enter().append('rect')
            .attr('y', function(d, i) { 
                return i * (bar_height + bar_gap);
            })
            .attr('width', 0)
            .attr('height', bar_height)
            .attr('class', function(d, i) { 
                return 'bar-' + i + ' ' + classify(d['party']);
            })
            .transition()
				.attr('width', function(d){
					return x(d['seats']);
				});
            	
    
    svg.append('g')
        .attr('class', 'value')
        .selectAll('text')
            .data(graphic_data)
        .enter().append('text')
            .attr('x', function(d) { 
                return x(d['seats']);
            })
            .attr('y', function(d, i) { 
                return i * (bar_height + bar_gap);
            })
            .attr('dx', function(d) {
            	if (x(d['seats']) > 20) {
            		return -6;
            	} else {
            		return 6;
            	}
            })
            .attr('dy', (bar_height / 2) + 3)
            .attr('text-anchor', function(d) {
            	if (x(d['seats']) > 20) {
            		return 'end';
            	} else {
            		return 'begin';
            	}
            })
            .attr('fill', function(d) {
            	if (x(d['seats']) > 20) {
            		return '#fff';
            	} else {
            		return '#999';
            	}
            })
            .attr('class', function(d) { 
                return classify(d['party']);
            })
            .text(function(d) { 
                return d['seats'].toFixed(0);
            });

	svg.append('g')
        .attr('class', 'labels')
        .selectAll('text')
            .data(graphic_data)
        .enter().append('text')
        	.attr('x', -margin['left'] + 6)
        	.attr('y', function(d,i) {
        		return (i * (bar_height + bar_gap));
        	})
        	.attr('dx', -6)
            .attr('dy', (bar_height / 2) + 4)
        	.attr('text-anchor', 'begin')
            .attr('class', function(d) {
                return classify(d['party']);
            })
			.text(function(d) { 
				return d['party_abbr'];
			});
	
	var majority_marker = svg.append('g')
		.attr('class', 'majority');
	
	majority_marker.append('line')
		.attr('x1', x(majority))
		.attr('y1', 0)
		.attr('x2', x(majority))
		.attr('y2', height)
		.attr('stroke', '#000');

	majority_marker.append('text')
		.attr('class', 'majority')
		.attr('x', x(majority))
		.attr('y', 0)
		.attr('dx', '1')
		.attr('dy', '-6')
		.attr('text-anchor', 'end')
		.html('Majority: ' + majority + '&#11022;');
}

function classify(str) {
    return str.replace(/\s+/g, '-').toLowerCase();
}



$(document).ready(function() {
    $audioPlayer = $('#pop-audio');
    $welcomeScreen = $('.welcome');
    $welcomeSubmitButton = $('.welcome-submit');
    $welcomeForm = $('form.welcome-form');
    $stack = $('.stack');

    $(window).resize(function() {
        var thisSlide = $('#stack .slide');
        resizeSlide(thisSlide);
    });

    $welcomeForm.submit(onWelcomeFormSubmit);

    setUpAudio();
});
