var soon_id = $('#soon-tv-ajax').data('soon-id');
 
var soon_hash = $('#soon-tv-ajax').data('soon-hash');

var soon_season = $('#soon-tv-ajax').data('soon-season');

if (soon_id) {

var data = { action: '3', user_hash: soon_hash, soon_id: soon_id, soon_season: soon_season };

 $.ajax({
            url: '/engine/ajax/controller.php?mod=pspvolt_soon_tv',
            type: 'POST',
            data: data,
            dataType: 'html',
            crossDomain: true,
            success: function(data) {
            
            if (!data) {
                    return false;
                }
                
                $('#soons-tv-ajax').empty();
            
                $('#soon-tv-ajax').html(data);
                
            },
        });
        
}
        
        
function epscapeShowHide(){
    $(".epscape_tr").css('display', '');
    $("#epscape_showmore").html('');
    return false;
}

function ShowOrHideEp(a, el) {
    var c = $("#" + a);
    a = document.getElementById("image-" + a) ? document.getElementById("image-" + a) : null;
    var b = c.height() / 200 * 1E3;
    3E3 < b && (b = 3E3);
    250 > b && (b = 250);
    "none" == c.css("display") ? $("#showhide_"+el).html("свернуть") : $("#showhide_"+el).html("развернуть");
    "none" == c.css("display") ? (c.show("blind", {}, b), a && (a.src = dle_root + "templates/" + dle_skin + "/siteimages/spoiler-minus.gif")) : (2E3 < b && (b = 2E3), c.hide("blind", {}, b), a && (a.src = dle_root + "templates/" + dle_skin + "/siteimages/spoiler-plus.gif"))
}
