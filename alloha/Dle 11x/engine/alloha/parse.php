<?php

require_once ENGINE_DIR . '/alloha/func.php';


$config_mod = unserialize( file_get_contents( ENGINE_DIR . '/data/alloha.config' ) );
if ( !$config_mod ) $config_mod = array(); 

$ads_xf = preg_replace('#[\\{\\}]#', '', $config_mod['xfields']['instream_ads']);

if (isset($_POST['q_search']) ) {

	check_license_alloha();

	if ($member_id['user_group']>1) {
		die('{"error": "for admin user only"}');
	}

	$q_search = trim($_POST['q_search']);

	if (preg_match('/[^0-9]/', $q_search)) {
		$search_type = 'by_name';
		$res = request('https://api.apbugall.org/?token='.$config_mod['api_token'].'&list&name='.urlencode($q_search));
	} else {
		$search_type = 'by_kpid';
		$res = request('https://api.apbugall.org/?token='.$config_mod['api_token'].'&kp='.intval($q_search));
	}


	$res = json_decode($res, true);
//	print_r($res);

	if(!count($res['data'])) die('{"error": "нет результатов"}');

	if($res['status']=='error') die('{"error": "'.$res['error_info'].'"}');

	if ($search_type=='by_kpid') {
		$res['data'] = [$res['data']];
	}

	foreach ($res['data'] as $value) {
		$src = $value['poster'] ? $value['poster'] : 'data:image/gif;base64,R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=';
		$data[] = '<div class="alloha_item" data-id="'.$value['id_kp'].'"><div class="aone"><img src="'.$value['poster'].'"></div><div class="atwo"><span class="kp-id" title="kinopoisk id"><b>КП: </b>'.$value['id_kp'].'</span> <div class="title" title="Жми чтобы спарсить">'.$value['name'].'</div><div class="title_origin">'.$value['original_name'].'</div></div></div>';
	}

	echo json_encode(["ok" => true, "result" => implode("\n", $data)]);

	exit();

}



if ($_POST['action']=='update') {

	check_license_alloha();

	$res = request('https://api.apbugall.org/?token='.$config_mod['api_token'].'&kp='.intval($_POST['id_kp']));

	$type = $_POST['type'];

	$res = json_decode($res, true);

	if(!count($res['data'])) die('{"error": "нет результатов"}');

	if ($type=='iframe' and $res['data']['iframe']) {
		die('{"ok": "'.$res['data']['iframe'].'"}');
	} elseif ($type=='trailer' and $res['data']['iframe_trailer']) {
		die('{"ok": "'.$res['data']['iframe_trailer'].'"}');	
	} else {
		die('{"error": "нет iframe"}');
	}


}





if ($_POST['action']=='parse') {

	check_license_alloha();

	if (!empty($_POST['id_kp'])) {
		$res = request('https://api.apbugall.org/?token='.$config_mod['api_token'].'&kp='.intval($_POST['id_kp']));
	} else {
		$res = request('https://api.apbugall.org/?token='.$config_mod['api_token'].'&name='.urlencode($_POST['name']));
	}


	$res = json_decode($res, true);

	if(!count($res['data'])) die('{"error": "нет результатов"}');

	if($res['status']=='error') die('{"error": "'.$res['error_info'].'"}');

	$res = $res['data'];

	$res['country'] = str_replace(', ', ',', $res['country']);  
	$res['genre'] = str_replace(', ', ',', $res['genre']);  


	if( ($premiere = strtotime($res['premiere']))!==false && $res['premiere'] ){
	    $res['premiere'] = date('j', $premiere).' '.$langdate[date('F', $premiere)].' '.date('Y', $premiere);
	}
	if( ($premiere_ru = strtotime($res['premiere_ru']))!==false && $res['premiere_ru'] ){
	    $res['premiere_ru'] = date('j', $premiere_ru).' '.$langdate[date('F', $premiere_ru)].' '.date('Y', $premiere_ru);
	}

	$request = [];

	$is_serial = false;

	if($res['seasons_count']){

	    $request['last_season'] = $res['seasons_count'];
	    $request['last_episode'] = $res['last_episode'];

	    $episodes = array_shift($res['seasons']);
	    $episodes = count($episodes['episodes']);
	    $request['episode_count'] = $episodes;

	    $request['last_translate'] = trim( array_shift(explode(',', $res['translation'])) );

	    $is_serial = true;
	}

	$ex_genres = array();

	if ($res['category']=='2' && mb_stripos($res['genre'], 'мультфильм')===false) {
	    $ex_genres[] = "сериал"; $request['video_type'] = 'сериал';
	    if (!$config_mod['add_serial']) {
	        die('{"error": "not allowed serial"}');
	    }
	}

	if ($res['category']=='1' && mb_stripos($res['genre'], 'мультфильм')===false) {
	    $ex_genres[] = "фильм"; $request['video_type'] = 'фильм';
	    if (!$config_mod['add_film']) {
	        die('{"error": "not allowed film"}');
	    }
	}

	if ($res['category']=='5') {
	    $ex_genres[] = "тв шоу"; $request['video_type'] = 'тв шоу';
	}

	if (mb_stripos($res['genre'], 'мультфильм')!==false) {
	    if ($is_serial) {
	        $request['video_type'] = "мультсериал";
	        $ex_genres[] = "мультсериал";

	        if (!$config_mod['add_multserial'] && !$config_mod['add_animeserial']) {
	            die('{"error": "not allowed multserial"}');
	        }

	    } else {
	        $request['video_type'] = 'мультфильм';
	        $ex_genres[] = "мультфильм";

	        if (!$config_mod['add_multfilm'] && !$config_mod['add_anime']) {
	            die('{"error": "not allowed multfilm"}');
	        }

	    }
	}

	if (mb_stripos($res['country'], 'россия')===false && mb_stripos($res['country'], 'ссср')===false) {
	    $ex_genres[] = "зарубежный";
	}

	if ($res['category']=='4') {
	    $ex_genres[] = "аниме сериал"; $request['video_type'] = 'аниме сериал';
	}

	if ($res['category']=='3') {
	    $ex_genres[] = "аниме"; $request['video_type'] = 'аниме';
	}


	$cats = array();
	$genres = fixGenres(explode(',', $res['genre']));


	$inter = array_merge($ex_genres, $genres, explode(',', $res['country']), array($res['year']));

	if ($request['video_type'] == 'мультсериал') {
	    $inter = array_diff($inter, ['мультфильм']);
	}

	if ($res['category']=='3') {
	    $inter = array_diff($inter, ['зарубежный', 'мультфильм']);
	}

	if ($res['category']=='4') {
	    $inter = array_diff($inter, ['зарубежный', 'мультсериал', 'мультфильм', 'аниме']);
	}


	foreach ($config_mod['category'] as $cat_id => $values) {
	    $f = true;

	    foreach ($values as $value) {
	        if ( !in_array($value, $inter) ) {
	            $f = false;
	            break;
	        }
	    }

	    if ( $f ) $cats[] = $cat_id;
	}

	$config_mod['category'] = implode(",", $cats);

	$request['title_ru']      = $res['name'];
	$request['title_en']      = $res['original_name'];
	$request['title_alt']     = $res['alternative_name'];
	$request['year']          = $res['year'];
	$request['description']   = html_entity_decode($res['description'], ENT_HTML5);
	$request['countries']     = $res['country'];
	$request['genres']        = $res['genre'];
	$request['actors']        = $res['actors'];
	$request['iframe_url']    = $res['iframe'];
	$request['quality']       = $res['quality'];
	$request['slogan']        = $res['tagline'];
    $request['directors']     = $res['directors'];
	$request['producer']      = $res['producers'];
	$request['translator']    = $res['translation'];
	$request['trailer']       = $res['iframe_trailer'];

	$request['premiere_ru']    = $res['premiere_ru'];
	$request['premiere_world'] = $res['premiere'];

	$request['rating_kp']        = $res['rating_kp'];
	$request['rating_imdb']      = $res['rating_imdb'];
	$request['rating_world_art'] = $res['world_art'];
	$request['rate_mpaa']        = $res['rating_mpaa'];

	$request['kinopoisk_id']     = $res['id_kp'];
	$request['imdb_id']          = $res['id_imdb'];
	$request['tmdb_id']          = $res['id_tmdb'];
	$request['world_art_id']     = $res['id_world_art'];

	$request['age']          = $res['age_restrictions'];
	$request['time']         = $res['time'];
	$request['instream_ads'] = ($res['ads']=='') ? '' : 1;

	if($request['title_en']==$request['title_ru']) $request['title_en']='';

	if ($config_mod['upload_poster']) {
		$poster_file = $_POST['id_kp'].'_'.time();
		$poster = request($res['poster'], ROOT_DIR . "/uploads/posts/" . FOLDER_PREFIX.'/' .$poster_file);
		if($poster){
		    $request['poster'] = str_replace(ROOT_DIR.'/' , $config['http_home_url'], $poster);
		    $poster = str_replace(ROOT_DIR."/uploads/posts/" , '', $poster);
		}
	} else {
		$request['poster'] = $res['poster'];
	}


	if ($is_serial) {
		$request['episode_plus'] = $res['last_episode']+1;
		$request['seasone_plus'] = $res['seasons_count']+1;

		$request['episode_type_1'] = formatize_alloha($res['last_episode'], 4);
		$request['episode_type_2'] = formatize_alloha($res['last_episode'], 5);
		$request['episode_type_3'] = formatize_alloha($res['last_episode'], 6);
		$request['episode_type_4'] = formatize_alloha($res['last_episode'], 7);
		$request['episode_type_5'] = formatize_alloha($res['last_episode'], 8);

		$request['season_type_1'] = formatize_alloha($res['last_episode'], 1);
		$request['season_type_2'] = formatize_alloha($res['last_episode'], 2);
		$request['season_type_3'] = formatize_alloha($res['last_episode'], 3);
	}


	$news_id = intval($_POST['news_id']);
	$author = isset($_POST['author']) ? $_POST['author'] : $member_id['name'];
	$author = $db->safesql($author);

	$old_poster = !empty($_POST['poster']) ? $_POST['poster'] : '';

	$images_row = $db->super_query( "SELECT * FROM " . PREFIX . "_images WHERE news_id='$news_id' AND author='$author'" );

	if ($old_poster && preg_match('#/uploads/posts/(\d{4}-\d{2}/[^/]+)#i', $old_poster, $find)) {
		if ($images_row) {
			@unlink(ROOT_DIR.'/uploads/posts/'.$find[1]);
			$new_images = preg_replace('#((^|\|\|\|)?'.$find[1].'($|\|\|\|))#', '', $images_row['images']);
			$new_images = $poster ? ($new_images ? $new_images.'|||'.$poster : $poster) : $new_images ;
			$db->query( "UPDATE " . PREFIX . "_images SET images='$new_images' WHERE id='{$images_row['id']}'" );
		}
		
	}




	if($poster && !$images_row){
	    $db->query( "INSERT INTO " . PREFIX . "_images (images,news_id,author,date) VALUES('{$poster}','$news_id','".$author."','{$_TIME}')" );
	}



	$compile = template($config_mod, $request);
	

	if (!empty($config_mod['metatitle'])) {
	    $compile['meta_title'] = check_if_alloha($compile['metatitle'],$request);
	}


	unset($compile['api_token'], $compile['allow_year']);
	unset($compile['metatitle'], $compile['lickey'],$compile['api_token']);

	echo json_encode(['ok' => true, 'result' => $compile]);

	exit();
}


?>




<script type="text/javascript">
$(function(){
	var regexp = /id=(\d+)/;
	var href = window.location.href;
	var news_id = regexp.test(href) ? href.match(regexp)[1] : 0;
	var author = $("input[name='old_author']").val();
	var ads_xf = '<?php echo $ads_xf; ?>';
	$('#related_news').before('<div id="parser_btns"></div>');
    $('#parser_btns').append('<button id="parse_start" class="btn btn-green">Искать в базе alloha</button>&nbsp;');
    $('#xf_iframe_url').after('<br><button data-type="iframe" type="button" class="upd-iframe btn btn-green">Обновить плеер</button>');
   $('#xf_trailer').after('<br><button data-type="trailer" type="button" class="upd-iframe btn btn-green">Обновить трейлер</button>');
    $(document).on("click", "#parse_start", function(){
        var btn = $(this);
        btn.attr("disabled", "disabled").text('Ждем...');
        var q_search = $('#title').val();
        $.post("?mod=alloha", {q_search:q_search,news_id:news_id,author:author}, function(data){
            if(data.error) {
            	Growl.info({
            	    title: 'Информация',
            	    text: data.error
            	});
            }
            if(data.ok){
				$("#alloha_results").remove();
                $("body").append("<div id='alloha_results' title='Результаты поиска' style='display:none'>"+data.result+"</div>");
                var b = {};
                b["Закрыть"] = function() {
                    $(this).dialog("close")
                };
                $("#alloha_results").dialog({
                    autoOpen: 1,
                    width: 600,
                    height: 400,
                    resizable: !1,
                    buttons: b
                });                
            }
            btn.removeAttr("disabled").text('Искать в базе alloha');
        },"json");
        return false;
    })
    .on("click", ".alloha_item", function(){
    	$("#alloha_results").remove();
        var t = $(this), id_kp = t.data('id'), name = t.find('.title').text(), poster = $('xf_poster').val() || $('[name="xfield[poster]"]').val();
        $.post("?mod=alloha", {action: 'parse', id_kp: id_kp, name:name, news_id:news_id,author:author, poster:poster}, function(data){
            if(data.error) {
            	Growl.info({
            	    title: 'Информация',
            	    text: data.error
            	});
            }
            if(data.result){
                $.each(data.result, function(key,val) {
                	$('[name="'+key+'"]').val(val);
                	if($.inArray(key, ['tags', 'keywords'] )>-1) {
                		$('[name="'+key+'"]').tokenfield('setTokens', val);
                	}
                	if($('#'+key).attr('data-rel')=='links'){
                		$('#'+key).tokenfield('setTokens', val);
                	}
                	if ( key == "short_story" || key == "full_story" ) {
                		if (typeof $.fn.froalaEditor != 'undefined') {
                			$('#' + key).froalaEditor('html.set', val);
                		} else $('#' + key);
                	}
                });
                $.each(data.result['xfields'], function(key,val) {
                	if($('#xf_'+key).attr('data-rel')=='links'){
                		$('#xf_'+key).tokenfield('setTokens', val);
                	} else {
                		$('#xf_'+key).val(val)
                	}
                });
                var cats = data.result['category'].split(',');
                var opt = $('#category option');
                opt.each(function(indx, element){
                    $(this).removeAttr('selected');
                });
                for (var i = 0; i < cats.length; i++) {
                    opt.each(function(indx, element){
	                    var o = $(this).val();
	                    if ( $.trim(o) == $.trim(cats[i] ) ) {$(this).prop("selected", true).trigger("liszt:updated");}
                    });
                }
                
                if (!ads_xf) return;
                var ads = $('[name="xfield['+ads_xf+']"]'), is_ads = ads.prop('checked');  
                if (data.result['xfields'][ads_xf] == '1') {
                	if (!is_ads) ads.trigger('click');
                } else {
                	if (is_ads) ads.trigger('click');
                }
            }
        },"json");
        return false;
    })
    .on("click", ".upd-iframe", function(){
    	var id_kp = $('#xf_kinopoisk_id').val();

    	if (!id_kp) {
    		Growl.error({
    			title: 'Error',
    			text: 'Нужен kinopoisk id'
    		});
    		return;
    	}
    	var t = $(this); t.attr("disabled", "disabled").text('Ждем...');

    	var type = t.data('type');

		$.post('?mod=alloha',{action:'update', type:type, id_kp:id_kp}, function(d){
			if (d.ok) {
				t.parent().find('input').val(d.ok)
			} else {
				Growl.error({
					title: 'Error',
					text: d.error
				});
			}
			t.removeAttr("disabled").text(type=='iframe' ? 'Обновить плеер' : 'Обновить трейлер');
		}, 'json');
    })
});
</script>


<style>
.atwo {
	padding-left: 10px;
    flex-grow: 1;
    position: relative;
}
.title_origin {
    font-size: 13px;
    color: #7c7f8a;
}
.alloha_item .kp-id {
    font-size: 12px;
    color: cadetblue;
    display: inline-block;
    position: absolute;
    right: 0;
    bottom: 0;
}
#alloha_results {
	counter-reset: li;
}
.alloha_item {
	display: flex;
    cursor: pointer;
    font-size: 15px;
    margin-bottom: 4px;
    text-overflow: ellipsis;
    overflow: hidden;
    white-space: nowrap;
    background: #f7f7f7;
    padding: 6px 6px;
    border-radius: 5px;
}
.alloha_item:hover {
	color: yellowgreen;
}
.alloha_item img {
    width: 90px;
    height: 130px;
    object-fit: cover;
}
.alloha_item:before {
    content: counter(li);
    display: inline-block;
    height: 28px;
    width: 28px;
    border: 3px solid yellowgreen;
    margin-right: 8px;
    counter-increment: li;
    text-align: center;
    border-radius: 20px;
    line-height: 1.7;
    font-size: 12px;
}
</style>