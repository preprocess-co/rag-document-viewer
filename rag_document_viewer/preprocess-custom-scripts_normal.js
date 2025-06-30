let pf = $("div.pf");

var generalWidth = $(".pf").width() + 150;
var windowWidth = $(window).width();

var documentHeight = 0;
var generalHeight = 0;
var windowHeight = $("#scrollbar").height();
var show_single_chunk = {#_show_single_chunk_#};
var chunks_navigator = {#_chunks_navigator_#};
var scrollbar_bookmarks = {#_scrollbar_bookmarks_#};
var show_page_number = {#_show_page_number_#};
var pages = [];

var theMainPf = $(".pf");
var scroll_to = "";

$("#page-container").html("");

for (let i = 0; i < pf.length; i++) {
    $("#page-container").append(pf[i]);
    generalHeight += $(pf[i]).outerHeight();
    if ($(pf[i]).width() >= generalWidth) {
        generalWidth = $(pf[i]).width() + 150;
        theMainPf = $(pf[i]);
    }

}

zoom_ratio = Math.round(($('#page-container').width() / generalWidth) * 10) / 12;
if (zoom_ratio < 1 && zoom_ratio == 0.9) {
    zoom_ratio = 0.8;
}

max_zoom = zoom_ratio + 0.5;
min_zoom = zoom_ratio - 0.5;
window.zoom = zoom_ratio;
handle_zooming();

$("a:not([href^='#'])").attr('target', '_blank');

$("#page-container").off('scroll').on('scroll', function () {
    let scrollLocation = $("#page-container").scrollTop() / generalHeight;

    let availableScrolling = $("#scrollbar").height() - $('#scroller').height();
    if (scrollLocation <= 0.01) {
        $('#scroller').css("top", "5px");
    }
    else if (scrollLocation <= 1) {
        let location = availableScrolling * scrollLocation;
        $('#scroller').css("top", location + "px");
    }

    if (show_page_number) {
        pageNumber = getCurrentPage();
        $("#page-number").html(pageNumber);
    }
});

$("#scrollbar").click(function (event) {

    let relY = event.pageY - ($('#scroller').height() / 2);
    let availableScrolling = $("#scrollbar").height();

    let scrollLocation = (relY / availableScrolling);
    if (scrollLocation <= 0.01) {
        $("#page-container").animate({
            scrollTop: 0
        }, 250);
    }
    else if (scrollLocation <= 1) {
        let locationDocument = parseFloat(generalHeight) * parseFloat(scrollLocation);

        $("#page-container").animate({
            scrollTop: locationDocument
        }, 250);
    }
});

$("#zoom-in").click(function (event) {
    if (window.zoom <= max_zoom) {
        window.zoom += 0.1;
    }
    handle_zooming();
});

$("#zoom-out").click(function (event) {
    if (window.zoom > min_zoom) {
        window.zoom -= 0.1;
    }
    handle_zooming();
});

$(window).resize(() => {
    handle_right();
    handle_zooming();
});

$(window).on("load", (e) => {
    $(".pf").each((index, item) => {
        pages[index] = $(item).offset().top;
    });

    if (show_page_number) {
        pageNumber = getCurrentPage();
        $("#page-number").html(pageNumber);
        $('#page-number').fadeIn();
    }
    // if (navigator.userAgent.match(/Edge/i) || navigator.userAgent.match(/Chrome/i)) {
        $('.zoom').fadeIn();
    // }
    handle_right();
});

function handle_zooming() {
    $("#page-container").css("zoom", window.zoom);
    documentHeight = window.zoom * generalHeight;
    if (show_page_number) {
        pageNumber = getCurrentPage();
        $("#page-number").html(pageNumber);
    }
    scrollHeight = windowHeight * (windowHeight / documentHeight);

    if (scrollHeight < 3) scrollHeight = 3;

    $('#scroller').css('height', scrollHeight + "px");
}

function get_param_value(key) {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has(key)) {
        list = urlParams.get(key);
        list = list.replace("[", "")
        list = list.replace("]", "")
        list = list.split(",").map(value => parseInt(value, 10));

        return list;
    }
    return [];
}

function handle_right() {
    window.allowed_i = get_param_value("chunks");
    let scroll_number = get_param_value("goto_chunk");

    if (scroll_number.length == 1) {
        scroll_to = "chunk-" + scroll_number[0];
    }

    if (scroll_to === "") {
        if (allowed_i.length > 0) {
            scroll_to = "chunk-" + allowed_i[0]
        }
        else {
            scroll_to = ""
        }
    }

    $("#page-container").scrollTop(0, 0);
    $(".draw-box, .scroll-bookmark").remove();

    let boxes = {#_boxes_data_#};

    for (let i = 0; i < boxes.length; i++) {
        let addedId = false;
        let drawBoxes = boxes[i];
        let addedClass = "text";
        const display_highlight = (allowed_i.indexOf(i) != -1);
        for (let j = 0; j < drawBoxes.length; j++) {
            let currentBox = drawBoxes[j];

            if (currentBox['left'] === 0 && currentBox['top'] === 0 && currentBox['width'] === 1 && currentBox['height'] === 1) {
                addedClass = "slide";
            }
            
            let pageBoxWidth = $(pf[currentBox['page'] - 1]).width();
            let pageBoxHeight = $(pf[currentBox['page'] - 1]).height();

            let drawBox = $("<div />");
            currentBox['left'] = (currentBox['left'] * pageBoxWidth);
            currentBox['top'] = (currentBox['top'] * pageBoxHeight);
            currentBox['height'] = (currentBox['height'] * pageBoxHeight);
            currentBox['width'] = (currentBox['width'] * pageBoxWidth);

            drawBox.addClass("draw-box");
            if (display_highlight) {
                drawBox.addClass("highlight").addClass(addedClass);
            }

            drawBox.css("left", currentBox['left']);
            drawBox.css("top", currentBox['top']);
            drawBox.css("height", currentBox['height']);
            drawBox.css("width", currentBox['width']);
            if (!addedId) {
                addedId = true;
                drawBox.attr("id", "chunk-" + i);
                if (display_highlight && scrollbar_bookmarks) {
                    let div = $('<a class="scroll-bookmark" id="b-' + i + '" href="#chunk-' + i + '"></a>');
                    let percentage = ($(pf[currentBox['page'] - 1]).offset().top + currentBox['top']) / documentHeight;
                    let available_height = $('#scrollbar').height() - $('#scroller').height();
                    let location = (parseFloat(available_height) * parseFloat(percentage)) + ($('#scroller').height() / 2) - 5;
                    div.css("top", location + "px");
                    $('#scrollbar').append(div);
                }
            }
            $(pf[currentBox['page'] - 1]).append(drawBox);
        }
    }

    let scroll_page = get_param_value("goto_page");
    if (scroll_page.length < 1) {
        if (scroll_to.length > 0 && $(`#${scroll_to}`).length) {
            document.getElementById(scroll_to).scrollIntoView({
                behavior: 'smooth'
            });
        }

        if (allowed_i.length > 0) {
            window.currentS = allowed_i.indexOf(scroll_number[0]) + 1;
            if (window.currentS === 0) {
                window.currentS = 1;
            }
            handle_suggestions(allowed_i.length);
        }
    }
    else {
        if (pf.eq(scroll_page[0]).length) {
            pf.eq(scroll_page[0])[0].scrollIntoView({
                behavior: 'smooth'
            });
        }
    }
    // }
    // else {
    //     window.currentS = 0;
    //     window.custom_text = "";
    //     handle_suggestions(0);
    // }
}

function handle_suggestions(total) {
    window.totalS = total;

    if (!chunks_navigator) {
        $("#navigator").fadeOut();
    }
    else if (window.totalS == 1 && !show_single_chunk) {
        $("#navigator").fadeOut();
    }

    else if (window.totalS == 0) {
        $("#navigator").fadeOut();
    }

    else {
        $("#navigator").fadeIn();
        if (currentS < total && currentS > 1) {
            $("#nextS").removeClass("disabled");
            $("#prevS").removeClass("disabled");
        }
        else if (currentS == total) {
            $("#prevS").removeClass("disabled");
            $("#nextS").addClass("disabled");
        }
        else if (currentS == 1) {
            $("#prevS").addClass("disabled");
            $("#nextS").removeClass("disabled");
        }
        $("#currentS").text(currentS);
        $("#totalS").text(totalS);
    }
}

function next_chunk() {
    if (!chunks_navigator) {
        return;
    }
    if (currentS < totalS) {
        currentS++;
        if (currentS < totalS) {
            $("#nextS").removeClass("disabled");
            $("#prevS").removeClass("disabled");
        }
        else if (currentS == totalS) {
            $("#prevS").removeClass("disabled");
            $("#nextS").addClass("disabled");
        }
    }
    else if (currentS == totalS) {
        $("#prevS").removeClass("disabled");
        $("#nextS").addClass("disabled");
    }
    $("#currentS").text(currentS);
    scroll_to = "chunk-" + allowed_i[currentS - 1];
    document.getElementById(scroll_to).scrollIntoView({
        behavior: 'smooth'
    });
}

function prev_chunk() {
    if (!chunks_navigator) {
        return;
    }
    if (currentS > 1) {
        currentS--;
        if (currentS > 1) {
            $("#nextS").removeClass("disabled");
            $("#prevS").removeClass("disabled");
        }
        else if (currentS == 1) {
            $("#prevS").addClass("disabled");
            $("#nextS").removeClass("disabled");
        }
    }
    else if (currentS == 1) {
        $("#prevS").addClass("disabled");
        $("#nextS").removeClass("disabled");
    }
    $("#currentS").text(currentS);
    scroll_to = "chunk-" + allowed_i[currentS - 1];
    document.getElementById(scroll_to).scrollIntoView({
        behavior: 'smooth'
    });
}

function getCurrentPage() {
    pos = ($("#page-container").scrollTop() + 250) * window.zoom;
    page = "";
    for (i in pages) {
        if (pos < pages[i]) {
            if (i == 0) {
                page = "1 / " + pages.length;
            }
            else {
                page = (i) + " / " + pages.length;
            }
            break;
        }
        if (i == pages.length - 1) {
            page = pages.length + " / " + pages.length;
        }
    }
    return page;
}