$(document).ready(function() {
    var kinopoisk_id = $("#alloha_player_ajax").attr("data-kinopoisk_id");
    var imdb_id = $("#alloha_player_ajax").attr("data-imdb_id");
    var tmdb_id = $("#alloha_player_ajax").attr("data-tmdb_id");
    var token_movie = $("#alloha_player_ajax").attr("data-token_movie");
    var world_art_id = $("#alloha_player_ajax").attr("data-world_art_id");
    var news_id = $("#alloha_player_ajax").attr("data-news_id");
    var with_seasons = $("#alloha_player_ajax").attr("data-with_seasons");
    var my_season = $("#alloha_player_ajax").attr("data-my_season");
    var action = 'load_player';
    var cook = '0';
    var last_translator = '0';
    var last_season = '0';
    var last_episode = '0';
    if ( $.cookie('les_' + news_id) != null && $.cookie('les_' + news_id) != undefined && $.cookie('les_' + news_id) != 'null' ) {
        arr = $.cookie('les_' + news_id).split(',');
        last_translator = arr[0];
        last_season = arr[1];
        last_episode = arr[2];
        cook = 1;
    }
    $.ajax({
        url: "/engine/ajax/controller.php?mod=alloha_playlist",
        type: "POST",
        dataType: "html",
        data: {kinopoisk_id:kinopoisk_id,imdb_id:imdb_id,tmdb_id:tmdb_id,token_movie:token_movie,world_art_id:world_art_id,last_translator:last_translator,last_season:last_season,last_episode:last_episode,action:action,cook:cook,news_id:news_id,with_seasons:with_seasons,my_season:my_season},
        beforeSend: function() {
            showloadpic();
        },
       success: function(data) {
           $("#alloha_player_ajax").html(data);
           hideloadpic();
        },
        complete: function() {
            scrolltoactive();
        }
    });
});
function translates() {
    $('#translators-list').on('click','.b-translator__item',function() {
        var _self = $(this);
        if(!_self.hasClass('active')) {
            $('.b-translator__item').removeClass('active');
            _self.addClass('active');
            var this_translator = _self.attr("data-this_translator");
            var with_seasons = $("#alloha_player_ajax").attr("data-with_seasons");
            var kinopoisk_id = $("#alloha_player_ajax").attr("data-kinopoisk_id");
    		var imdb_id = $("#alloha_player_ajax").attr("data-imdb_id");
            var tmdb_id = $("#alloha_player_ajax").attr("data-tmdb_id");
            var token_movie = $("#alloha_player_ajax").attr("data-token_movie");
    		var world_art_id = $("#alloha_player_ajax").attr("data-world_art_id");
    		var news_id = $("#alloha_player_ajax").attr("data-news_id");
    		var api_token = $("#alloha_player_ajax").attr("data-api_token");
            var action = 'translates';
            $.ajax({
                url: "/engine/ajax/controller.php?mod=alloha_playlist",
                type: "POST",
                dataType: "html",
                data: {this_translator:this_translator,action:action,with_seasons:with_seasons,kinopoisk_id:kinopoisk_id,imdb_id:imdb_id,tmdb_id:tmdb_id,token_movie:token_movie,world_art_id:world_art_id,news_id:news_id,api_token:api_token},
                beforeSend: function() {
                    showloadpic();
                },
                success: function(data) {
                    $('#player').html(data);
                    hideloadpic();
                },
                complete: function() {
                    scrolltoactive();
                }
            });
        }
    });
}
function seasons() {
    $('#simple-seasons-tabs').on('click','.b-simple_season__item',function() {
        var _self = $(this);
        if(!_self.hasClass('active')) {
            $('.b-simple_season__item').removeClass('active');
            _self.addClass('active');
            var this_season = _self.attr("data-this_season");
            var this_translator = _self.attr("data-this_translator");
            var kinopoisk_id = $("#alloha_player_ajax").attr("data-kinopoisk_id");
    		var imdb_id = $("#alloha_player_ajax").attr("data-imdb_id");
            var tmdb_id = $("#alloha_player_ajax").attr("data-tmdb_id");
            var token_movie = $("#alloha_player_ajax").attr("data-token_movie");
    		var world_art_id = $("#alloha_player_ajax").attr("data-world_art_id");
    		var news_id = $("#alloha_player_ajax").attr("data-news_id");
    		var api_token = $("#alloha_player_ajax").attr("data-api_token");
            var action = 'seasons';
            $.ajax({
                url: "/engine/ajax/controller.php?mod=alloha_playlist",
                type: "POST",
                dataType: "html",
                data: {this_translator:this_translator,action:action,this_season:this_season,kinopoisk_id:kinopoisk_id,imdb_id:imdb_id,tmdb_id:tmdb_id,token_movie:token_movie,world_art_id:world_art_id,news_id:news_id,api_token:api_token},
                beforeSend: function() {
                    showloadpic();
                },
                success: function(data) {
                    $('#ibox').html(data);
                    hideloadpic();
                },
                complete: function() {
                    scrolltoactive();
                }
            });
        }
    });
}
function episodes() {
    $('#simple-episodes-list').on('click','.b-simple_episode__item',function() {
        var _self = $(this);
        var this_season = _self.attr("data-this_season");
        var this_translator = '0';
        var this_translator = _self.attr("data-this_translator");
        var trna = $('#translators-list li.active').text();
        var this_episode = _self.attr("data-this_episode");
        var _iframe_block = $('#player').find('iframe').clone();
        var crop = _iframe_block.attr("src").indexOf("episode=");
        var src = _iframe_block.attr("src").slice(0,crop + 8);
        var newsid = $("#alloha_player_ajax").attr("data-news_id");
        if(!_self.hasClass('active')) {
            var cookie_value = this_translator + ',' + this_season + ',' + this_episode;
            var wlp = newsid;
            $.cookie('les_' + wlp, cookie_value, {
                expires: 14
            });
            if ( trna != '' ) {
                $('#les').html('. Вы остановились на ' + this_season + ' сезоне ' + this_episode + ' серии' + ' в озвучке &laquo;' + trna + '&raquo;');
                if ( $('#lesc').html() != '' ) $('#les').append('<i class="fa fa-trash" onclick="del();" id="lesc" title="Удалить отметку"></i>');
            } else {
                $('#les').html('. Вы остановились на ' + this_season + ' сезоне ' + this_episode + ' серии');
                if ( $('#lesc').html() != '' ) $('#les').append('<i class="fa fa-trash" onclick="del();" id="lesc" title="Удалить отметку"></i>');
            }
            $('#ln').html('');
            $('.b-simple_episode__item').removeClass('active');
            _self.addClass('active');
            showloadpic();
            $('#player').find('iframe').attr('src', src + this_episode);
            hideloadpic();
        }
    });
}
function del() {
    var newsid = $("#alloha_player_ajax").attr("data-news_id");
    $('#les').html('');
    $('#ln').html('');
    $('#lesc').remove();
    var wlp = newsid;
    $.cookie('les_' + wlp, null, {
        expires: 14
    });
}
function scrolltoactive() {
    if ( $("div").is("#simple-episodes-tabs") ) {
        if ( ($('#alloha_player_ajax').width() - 30) < document.getElementById('simple-episodes-tabs').scrollWidth ) {
            $('#simple-episodes-tabs').scrollTo($("#simple-episodes-list > .active"), 300);
        } else {
            $('.prevpl').hide();
            $('.nextpl').hide();
            $('#simple-episodes-tabs').css({'margin':'0px 5px'});
        }
    }
}
function prevpl(){
    var scroll = $('#alloha_player_ajax').width()/2;
    $('#simple-episodes-tabs').scrollTo("-=" + scroll + "px", 300);
}
function nextpl(){
    var scroll = $('#alloha_player_ajax').width()/2;
    $('#simple-episodes-tabs').scrollTo("+=" + scroll + "px", 300);
}
function showloadpic(){
    $('#player-loader-overlay').animate({opacity: "show"}, 450);
}
function hideloadpic(){
    $('#player-loader-overlay').animate({opacity: "hide"}, 600).html('');
}

jQuery.cookie = function(name, value, options) {
    if (typeof value != 'undefined') {
        options = options || {};
        if (value === null) {
            value = '';
            options.expires = -1;
        }
        var expires = '';
        if (options.expires && (typeof options.expires == 'number' || options.expires.toUTCString)) {
            var date;
            if (typeof options.expires == 'number') {
                date = new Date();
                date.setTime(date.getTime() + (options.expires * 24 * 60 * 60 * 1000));
            } else {
                date = options.expires;
            }
            expires = '; expires=' + date.toUTCString();
        }
        
        var path = options.path ? '; path=' + (options.path) : '';
        var domain = options.domain ? '; domain=' + (options.domain) : '';
        var secure = options.secure ? '; secure' : '';
        document.cookie = [name, '=', encodeURIComponent(value), expires, path, domain, secure].join('');
    } else { 
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
};

;(function(f){"use strict";"function"===typeof define&&define.amd?define(["jquery"],f):"undefined"!==typeof module&&module.exports?module.exports=f(require("jquery")):f(jQuery)})(function($){"use strict";function n(a){return!a.nodeName||-1!==$.inArray(a.nodeName.toLowerCase(),["iframe","#document","html","body"])}function h(a){return $.isFunction(a)||$.isPlainObject(a)?a:{top:a,left:a}}var p=$.scrollTo=function(a,d,b){return $(window).scrollTo(a,d,b)};p.defaults={axis:"xy",duration:0,limit:!0};$.fn.scrollTo=function(a,d,b){"object"=== typeof d&&(b=d,d=0);"function"===typeof b&&(b={onAfter:b});"max"===a&&(a=9E9);b=$.extend({},p.defaults,b);d=d||b.duration;var u=b.queue&&1<b.axis.length;u&&(d/=2);b.offset=h(b.offset);b.over=h(b.over);return this.each(function(){function k(a){var k=$.extend({},b,{queue:!0,duration:d,complete:a&&function(){a.call(q,e,b)}});r.animate(f,k)}if(null!==a){var l=n(this),q=l?this.contentWindow||window:this,r=$(q),e=a,f={},t;switch(typeof e){case "number":case "string":if(/^([+-]=?)?\d+(\.\d+)?(px|%)?$/.test(e)){e= h(e);break}e=l?$(e):$(e,q);case "object":if(e.length===0)return;if(e.is||e.style)t=(e=$(e)).offset()}var v=$.isFunction(b.offset)&&b.offset(q,e)||b.offset;$.each(b.axis.split(""),function(a,c){var d="x"===c?"Left":"Top",m=d.toLowerCase(),g="scroll"+d,h=r[g](),n=p.max(q,c);t?(f[g]=t[m]+(l?0:h-r.offset()[m]),b.margin&&(f[g]-=parseInt(e.css("margin"+d),10)||0,f[g]-=parseInt(e.css("border"+d+"Width"),10)||0),f[g]+=v[m]||0,b.over[m]&&(f[g]+=e["x"===c?"width":"height"]()*b.over[m])):(d=e[m],f[g]=d.slice&& "%"===d.slice(-1)?parseFloat(d)/100*n:d);b.limit&&/^\d+$/.test(f[g])&&(f[g]=0>=f[g]?0:Math.min(f[g],n));!a&&1<b.axis.length&&(h===f[g]?f={}:u&&(k(b.onAfterFirst),f={}))});k(b.onAfter)}})};p.max=function(a,d){var b="x"===d?"Width":"Height",h="scroll"+b;if(!n(a))return a[h]-$(a)[b.toLowerCase()]();var b="client"+b,k=a.ownerDocument||a.document,l=k.documentElement,k=k.body;return Math.max(l[h],k[h])-Math.min(l[b],k[b])};$.Tween.propHooks.scrollLeft=$.Tween.propHooks.scrollTop={get:function(a){return $(a.elem)[a.prop]()}, set:function(a){var d=this.get(a);if(a.options.interrupt&&a._last&&a._last!==d)return $(a.elem).stop();var b=Math.round(a.now);d!==b&&($(a.elem)[a.prop](b),a._last=this.get(a))}};return p});