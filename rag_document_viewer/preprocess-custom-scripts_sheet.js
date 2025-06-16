zoom_ratio = 1;
max_zoom = 2;
min_zoom = 1;
currentS = 0;
totalS = 0;
to_load = -1;
window.zoom = zoom_ratio;
window.sheets = [];
window.show_single_chunk = {#_show_single_chunk_#};
window.chunks_navigator = {#_chunks_navigator_#};
window.chunks = {#_boxes_data_#};

if (navigator.userAgent.match(/Edge/i) || navigator.userAgent.match(/Chrome/i)) {
    $('.zoom').fadeIn();
}

$(window).on("load", (e) => {
    $("#sheet_preview").css('zoom', window.zoom);
    window.all_links = $("a", $("#tabs").contents());
    window.all_links.click(
        (e) => {
            window.all_links.removeClass('bold');
            $(e.currentTarget).addClass("bold");
        }
    );
    const chunks_i = get_param_value("chunks");
    for (let i = 0; i < chunks_i.length; i++) {
        if (chunks_i[i] < chunks.length) {
            sheet = chunks[chunks_i[i]][0]['page'];
            if (sheet - 1 < window.all_links.length) {
                sheets.push(sheet - 1);
                if (to_load == -1) {
                    to_load = sheet - 1;
                }
            }
        }
    }

    const chunk_load = get_param_value("goto_chunk");
    if (chunk_load.length > 0) {
        to_load = chunk_load[0];
    }

    const page_load = get_param_value("goto_page");
    if (page_load.length > 0) {
        to_load = page_load[0];
    }


    totalS = sheets.length;

    window.all_links.each(function (index, element) {
        if (sheets.indexOf(index) != -1) {
            $(element).parents("td").addClass("highlight");
        }
    });

    if (currentS == 0) {
        currentS = sheets.indexOf(to_load) + 1;
    }

    if (to_load >= 0 && to_load < window.all_links.length) {
        window.all_links[to_load].click();
    }
    else {
        if (sheets.length > 0) {
            if (window.currentS >= 1) {
                if (window.currentS - 1 < window.all_links.length) {
                    window.all_links[sheets[window.currentS - 1]].click();
                }
            }
            else {
                if (to_load == -1) {
                    to_load = 0;
                }
                currentS = 1;
                window.all_links[sheets[window.currentS - 1]].click();
            }
        }
        else {
            to_load = 0;
            currentS = 0;
            window.all_links[0].click();
        }
    }
    handle_suggestions();
});



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
    window.all_links[sheets[window.currentS - 1]].click();
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
    window.all_links[sheets[window.currentS - 1]].click();
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

function zoom_in() {
    if (window.zoom <= max_zoom) {
        window.zoom += 0.1;
    }
    $("#sheet_preview").css('zoom', window.zoom);
};

function zoom_out() {
    if (window.zoom > min_zoom) {
        window.zoom -= 0.1;
    }
    $("#sheet_preview").css('zoom', window.zoom);
};

function handle_suggestions() {
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
        if (currentS < window.totalS && currentS > 1) {
            $("#nextS").removeClass("disabled");
            $("#prevS").removeClass("disabled");
        }
        else if (currentS == window.totalS) {
            $("#prevS").removeClass("disabled");
            $("#nextS").addClass("disabled");
        }
        else if (currentS == 1) {
            $("#prevS").addClass("disabled");
            $("#nextS").removeClass("disabled");
        }
        $("#currentS").text(currentS);
        $("#totalS").text(window.totalS);
    }
    return;
}
