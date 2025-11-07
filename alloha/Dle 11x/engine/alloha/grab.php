<?php

@error_reporting ( E_ALL ^ E_WARNING ^ E_NOTICE );
@ini_set ( 'display_errors', true );
@ini_set ( 'html_errors', false );
@ini_set ( 'error_reporting', E_ALL ^ E_WARNING ^ E_NOTICE );

define( 'DATALIFEENGINE', true );
define( 'ROOT_DIR', substr( dirname(  __FILE__ ), 0, -14 ) );
define( 'ENGINE_DIR', ROOT_DIR . '/engine' );

include ENGINE_DIR . '/data/config.php';

date_default_timezone_set ( $config['date_adjust'] );

require_once ENGINE_DIR . '/classes/mysql.php';
require_once ENGINE_DIR . '/data/dbconfig.php';
require_once ENGINE_DIR . '/modules/functions.php';

ini_set("memory_limit","256M");
ini_set('max_execution_time',200);
ignore_user_abort(true);
set_time_limit(200);
session_write_close();

require_once ENGINE_DIR . '/alloha/func.php';


$config_mod = unserialize( file_get_contents( ENGINE_DIR . '/data/alloha.config' ) );
if ( !$config_mod ) $config_mod = array(); 


$_TIME = time();

check_license_alloha();

if ( isset($_GET['type']) ) {

    $url = '';
    $ex_time = time()-2*24*3600;
    $db->query( "UPDATE " . PREFIX . "_alloha SET status=1, err_time='0' WHERE (err_time>'0' AND err_time<'$ex_time')" );

    $order = $config_mod['first_new'] ? '&order=year' : ''; 

    if(($config_mod['add_film'] or $config_mod['add_multfilm']) && $_GET['type']=='film'){
        $url = 'https://api.apbugall.org/?token='.$config_mod['api_token'].'&list=movie';
    } 
    elseif(($config_mod['add_serial'] or $config_mod['add_multserial']) && $_GET['type']=='serial'){
        $url = 'https://api.apbugall.org/?token='.$config_mod['api_token'].'&list=serial';
    }
    elseif($config_mod['add_anime'] && $_GET['type']=='anime'){
        $url = 'https://api.apbugall.org/?token='.$config_mod['api_token'].'&list=anime';
    }
    elseif($config_mod['add_animeserial'] && $_GET['type']=='animeserial'){
        $url = 'https://api.apbugall.org/?token='.$config_mod['api_token'].'&list=anime-serial';
    }
    elseif($config_mod['add_tvshow'] && $_GET['type']=='tvshow'){
        $url = 'https://api.apbugall.org/?token='.$config_mod['api_token'].'&list=tv-show';
    }     


    if(!$url) die('choise video type. film serial mult or anime');

    if ($config_mod['rating_kp']) {
        $url .= '&rating_kp='.$config_mod['rating_kp'];
    }

    if ($config_mod['rating_imdb']) {
        $url .= '&rating_imdb='.$config_mod['rating_imdb'];
    }

    include ENGINE_DIR . '/alloha/class.php';
    $alloha = new Alloha($_GET['type'], $db);
    $alloha->start($url.$order);

    die('Insert and update data');
}



if (isset($_GET['last'])) {

    $types = ['serial', 'movie', 'anime', 'anime-serial', 'tv-show'];

    $kp_ids = [];

    $xf_config = array_map(function($el) {
        return str_replace(['{', '}'], '', $el);
    }, $config_mod['xfields']);

    $xf_config = array_flip($xf_config);

    foreach ($types as $type) {

        for ($page=1; $page < 3; $page++) { 

            usleep(300000);
           
            $response = request("https://api.apbugall.org/?token={$config_mod['api_token']}&last=$type&order=date&page=$page");

            $response = json_decode($response, true);

            if (!$response) {
                continue;
            }

            foreach ($response['data'] as $result) {

                $kinopoisk_id = $result['id_kp'];

                if (isset($kp_ids[$kinopoisk_id])) {
                    continue;
                }

                $kp_ids[$kinopoisk_id] = 1;
                    

                $post_row = $db->super_query( "SELECT id, title, category, xfields FROM " . PREFIX . "_post WHERE xfields REGEXP 'kinopoisk_id[|]{$kinopoisk_id}([|]|$)'" );

                if (!$post_row) {
                    $token_movie = $result['token_movie'];
                    $post_row = $db->super_query( "SELECT id, title, category, xfields FROM " . PREFIX . "_post WHERE xfields LIKE '%{$token_movie}%'" );
                }


                if (!$post_row) {
                    echo "{$result['name']} --- {$result['original_name']} --- kp_id {$kinopoisk_id}";
                    echo ' --- <span style="color:red;"'.">not found</span><br>\n";
                    continue;
                }


                if ($config_mod['exclude_news']) {
                    $exclude_news = explode("\n", $config_mod['exclude_news']);
                    if (in_array($post_row['id'], $exclude_news)) {
                        continue;
                    }
                }


                echo "{$result['name']} --- {$result['original_name']} --- kp_id {$kinopoisk_id}";


                $xfields = xfieldsdataload( $post_row['xfields'] );

                $update_news = false;
                $new_date = false;
                $rewrite_meta_resone = false;
                $es_result = [];
                
                $last_season = isset($xfields['last_season']) ? $xfields['last_season'] : '';
                $last_episode = isset($xfields['last_episode']) ? $xfields['last_episode'] : '';

                if ($xfields[$xf_config['quality']]!=$result['quality']) {
                    $update_news = true;
                    $xfields[$xf_config['quality']]=$result['quality'];
                    $config_mod['update_if_quality'] && ($new_date = true);
                }


                if ($xfields[$xf_config['trailer']]!=$result['iframe_trailer']) {
                    $update_news = true;
                    $xfields[$xf_config['trailer']] = $result['iframe_trailer'];
                }

                if ($xfields[$xf_config['instream_ads']]!=$result['instream_ads']) {
                    $update_news = true;
                    $xfields[$xf_config['instream_ads']] = $result['instream_ads'];
                }



                if (in_array($type, ['serial', 'anime-serial', 'tv-show'])) {

                    if ($result['episode']>$last_episode or $result['season']>$last_season) {
                        $update_news = $rewrite_meta_resone = true;
                        $xfields['last_episode']=$result['episode'];
                        $xfields['last_season']=$result['season'];
                        ($config_mod['update_if_seasone'] or $config_mod['update_if_quality']) && ($new_date = true);
                    }


                    if ($xfields[$xf_config['last_translate']] != $all_translate[$result['translation']]) {
                        $update_news = true;
                        $xfields[$xf_config['last_translate']] = $all_translate[$result['translation']];
                        ($config_mod['update_if_change_translate']) && ($new_date = true);
                    }


                    if ($result['episode'] > $xfields[$xf_config['episode_count']]) {
                        $update_news = true;
                        $xfields[$xf_config['episode_count']] = $result['episode'];
                    }


                    $xfields[$xf_config['episode_plus']] = $es_result['episode_plus'] = $result['episode']+intval($config_mod['plus']);
                    $xfields[$xf_config['seasone_plus']] = $es_result['seasone_plus'] = $result['season']+intval($config_mod['plus']);

                    $xfields[$xf_config['episode_type_1']] = $es_result['episode_type_1'] = formatize_alloha($result['episode'], 4);
                    $xfields[$xf_config['episode_type_2']] = $es_result['episode_type_2'] = formatize_alloha($result['episode'], 5);
                    $xfields[$xf_config['episode_type_3']] = $es_result['episode_type_3'] = formatize_alloha($result['episode'], 6);
                    $xfields[$xf_config['episode_type_4']] = $es_result['episode_type_4'] = formatize_alloha($result['episode'], 7);
                    $xfields[$xf_config['episode_type_5']] = $es_result['episode_type_5'] = formatize_alloha($result['episode'], 8);

                    $xfields[$xf_config['season_type_1']] = $es_result['season_type_1'] = formatize_alloha($result['season'], 1);
                    $xfields[$xf_config['season_type_2']] = $es_result['season_type_2'] = formatize_alloha($result['season'], 2);
                    $xfields[$xf_config['season_type_3']] = $es_result['season_type_3'] = formatize_alloha($result['season'], 3);
                    
                }


                if ($update_news) {

                    $xfields[$xf_config['iframe_url']]=$result['iframe'];

                    $xfields = array_diff($xfields, ['']);

                    $date = '';

                    if ($new_date) {
                        $date = date('Y-m-d H:i:s', $_TIME);
                        $date = "date='$date',";
                    }


                    $compile = template($config_mod, [
                        'last_season' => $xfields[$xf_config['last_season']],
                        'last_episode' => $xfields[$xf_config['last_episode']],
                        'title_ru' => $result['name'],
                        'title_en' => $result['original_name'],
                        'year' => $result['year'],
                    ]);
                    
                    $es_type = ['episode_plus', 'seasone_plus', 'episode_type_1', 'episode_type_2', 'episode_type_3', 'episode_type_4', 'episode_type_5', 'season_type_1', 'season_type_2', 'season_type_3'];

                    

                    foreach ($es_type as $key => $value) {
                        if (!isset($xf_config[$value])) {
                            unset($xfields[$xf_config[$value]]);
                        }
                    }


                    if (!empty($config_mod['metatitle'])) {
                        $compile['metatitle'] = check_if_alloha($compile['metatitle'], $es_result);
                        $metatitle = ", metatitle='".$db->safesql($compile['metatitle'])."'";
                    } else {
                        $metatitle = '';
                    }


                    $xfields = $db->safesql(xfieldsdatasave($xfields));

                    $db->query( "UPDATE " . PREFIX . "_post SET $date xfields='$xfields' $metatitle WHERE id='{$post_row['id']}'" );


                    if ($result['episode'] and $rewrite_meta_resone) {
                        $reason = "{$result['season']} сезон {$result['episode']} $series серия - ".date('d.m.Y');
                    } else {
                        $reason = $result['quality'];
                    }
                    


                    $db->query("UPDATE " . PREFIX . "_post_extras SET editdate = '$_TIME', reason='$reason' WHERE news_id = '{$post_row['id']}'");

                    echo ' --- <span style="color:green;"'.">updated</span><br>\n";


                }

                else {
                    echo ' --- <span style="color:red;"'.">no updated</span><br>\n";
                }
//die();
            }

        }


    }

exit();

}




$and = [];
if($config_mod['add_film'] or $config_mod['add_multfilm']) 
    $and[] = "'film'";
if($config_mod['add_serial'] or $config_mod['add_multserial'])       
    $and[] = "'serial'";
if($config_mod['add_anime'])        
    $and[] = "'anime'";
if($config_mod['add_animeserial'])  
    $and[] = "'animeserial'";
if($config_mod['add_tvshow'])       
    $and[] = "'tvshow'";

if(count($and)) $and = "AND type IN(".implode(", ", $and).")";

if($config_mod['first_new']){
    $alloha = $db->super_query( "SELECT * FROM " . PREFIX . "_alloha WHERE status>0 $and ORDER BY `status` ASC, `year` DESC" );
}
else {
    $alloha = $db->super_query( "SELECT * FROM " . PREFIX . "_alloha WHERE status>0 $and ORDER BY `status` ASC" );
}


$post_row = $db->super_query( "SELECT id, title, xfields FROM " . PREFIX . "_post WHERE xfields LIKE '%kinopoisk_id|{$alloha['kp_id']}%'" );

if ($post_row) {
    if ($post_row && $alloha['status']==1) {
        $alloha['news_id'] = $post_row['id'];
    } else {
        $db->query( "UPDATE " . PREFIX . "_alloha SET status=0, news_id='{$post_row['id']}' WHERE kp_id='{$alloha['kp_id']}'" );
        die("news exists --- {$post_row['id']} --- {$post_row['title']}");
    }

    $xfdata = xfieldsdataload($post_row['xfields']);
    
} else {
    $alloha['news_id'] = 0;
}


if($config_mod['blacklist']){
    $blacklist = explode("\n", $config_mod['blacklist']);
    if(in_array($alloha['kp_id'], $blacklist)) {
        $db->query( "UPDATE " . PREFIX . "_alloha SET status=0, err_time='$_TIME' WHERE kp_id='{$alloha['kp_id']}'" );
        die("in blacklist --- kinopoisk_id --- {$alloha['kp_id']}");    
    }
}


$res = request('https://api.apbugall.org/?token='.$config_mod['api_token'].'&kp='.$alloha['kp_id']);
// $res = request('https://api.apbugall.org/?token='.$config_mod['api_token'].'&kp=707836');

$res = json_decode($res, true);

$res = $res['data'];

if ($res['status']=='error') {
    $db->query( "UPDATE " . PREFIX . "_alloha SET status=0, err_time='$_TIME' WHERE kp_id='{$alloha['kp_id']}'" );
    die($res['error_info']);
}


$res['country'] = str_replace(', ', ',', $res['country']);  
$res['genre'] = str_replace(', ', ',', $res['genre']);  

if(!allow_country(explode(',', $res['country']), (array)$config_mod['allow_country'])) {
    $db->query( "UPDATE " . PREFIX . "_alloha SET status=0, err_time='$_TIME' WHERE kp_id='{$alloha['kp_id']}'" );
    die('not allowed countryes');
}


if(disallow_country(explode(',', $res['country']), (array)$config_mod['disallow_country'])) {
    $db->query( "UPDATE " . PREFIX . "_alloha SET status=0, err_time='$_TIME' WHERE kp_id='{$alloha['kp_id']}'" );
    die('disallow countryes');
}


if($config_mod['allow_year'] && !in_array(intval($res['year']), $config_mod['allow_year'])){
    $db->query( "UPDATE " . PREFIX . "_alloha SET status=0, err_time='$_TIME' WHERE kp_id='{$alloha['kp_id']}'" );
    die('not allowed year');
}

if(!$config_mod['enable_ads'] && $res['ads']=='1'){
    $db->query( "UPDATE " . PREFIX . "_alloha SET status=0, err_time='$_TIME' WHERE kp_id='{$alloha['kp_id']}'" );
    die('not allowed. ads');
}

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
        $db->query( "UPDATE " . PREFIX . "_alloha SET status=0 WHERE kp_id='{$alloha['kp_id']}'" );
        die('not allowed. serial');
    }
}

if ($res['category']=='1' && mb_stripos($res['genre'], 'мультфильм')===false) {
    $ex_genres[] = "фильм"; $request['video_type'] = 'фильм';
    if (!$config_mod['add_film']) {
        $db->query( "UPDATE " . PREFIX . "_alloha SET status=0 WHERE kp_id='{$alloha['kp_id']}'" );
        die('not allowed. film');
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
            $db->query( "UPDATE " . PREFIX . "_alloha SET status=0 WHERE kp_id='{$alloha['kp_id']}'" );
            die('not allowed. multserial');
        }

    } else {
        $request['video_type'] = 'мультфильм';
        $ex_genres[] = "мультфильм";

        if (!$config_mod['add_multfilm'] && !$config_mod['add_anime']) {
            $db->query( "UPDATE " . PREFIX . "_alloha SET status=0 WHERE kp_id='{$alloha['kp_id']}'" );
            die('not allowed. multfilm');
        }

    }
}

if (mb_stripos($res['country'], 'россия')===false && mb_stripos($res['country'], 'ссср')===false) {
    $ex_genres[] = "зарубежный";
}

if ($res['category']=='4') {
    $ex_genres[] = "аниме сериал"; $request['video_type'] = 'аниме сериал';
}

if ($alloha['type']=='anime') {
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


if(!$config_mod['category']) {
    $db->query( "UPDATE " . PREFIX . "_alloha SET status=0, err_time='$_TIME' WHERE kp_id='{$alloha['kp_id']}'" );
    die('not allowed category');
}

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


if(!$alloha['news_id']){
    if ($config_mod['upload_poster']) {
        $poster_file = $alloha['kp_id'].'_'.time();
        $poster = request($res['poster'], ROOT_DIR . "/uploads/posts/" . FOLDER_PREFIX.'/' .$poster_file);
        if($poster){
            $request['poster'] = str_replace(ROOT_DIR.'/' , $config['http_home_url'], $poster);
            $poster = str_replace(ROOT_DIR."/uploads/posts/" , '', $poster);
        }
    } else {
        $request['poster'] = $res['poster'];
    }
}
else {
    foreach ($request as $key => $value) {
        if(!$xfdata[$key]) $xfdata[$key] = $request[$key];
    }

    $xfdata['last_season'] = $res['seasons_count'];
    $xfdata['last_episode']   = $res['last_episode'];

    if (empty($xfdata['poster'])) {
        if ($config_mod['upload_poster']) {
            $poster_file = $alloha['kp_id'].'_'.time();
            $poster = request($res['poster'], ROOT_DIR . "/uploads/posts/" . FOLDER_PREFIX.'/' .$poster_file);
            if($poster){
                $xfdata['poster'] = str_replace(ROOT_DIR.'/' , $config['http_home_url'], $poster);
                $poster = str_replace(ROOT_DIR."/uploads/posts/" , '', $poster);
            }
        } else {
            $xfdata['poster'] = $res['poster'];
        }
    }

    $request = $xfdata;
} 


$compile = template($config_mod, $request);

if($compile['category']=='') $compile['category']=0;
if(!$compile['tags']) $compile['tags'] = '';


$compile['xfields'] = !$alloha['news_id'] ? xfcompile($compile['xfields']) : xfcompile($xfdata);
$compile['alt_name'] = totranslit( stripslashes( $compile['alt_name'] ), true, false );
$compile['date'] = date('Y-m-d H:i:s');


if (empty($compile['short_story'])) {
    $compile['short_story'] = '';
    $compile['full_story'] = '';
    $compile['keywords'] = '';
    $compile['descr'] = $compile['title'];
}

if (empty($compile['full_story'])) {
    $compile['full_story'] = '';
}

if (empty($compile['keywords'])) {
    $compile['keywords'] = '';
}

if (empty($compile['descr'])) {
    $compile['descr'] = '';
}

if (empty($compile['metatitle'])) {
    $compile['metatitle'] = '';
}

$approve = (!empty($config_mod['go_moder']) && (bool)$config_mod['go_moder'] === true) ? 0 : 1;

if (!empty($config_mod['go_moder_empty_descr'])
    && (bool)$config_mod['go_moder_empty_descr'] === true
    && empty(trim($request['description']))
) {
    $approve = 0;
}

if (!empty($config_mod['go_moder_empty_poster'])
    && (bool)$config_mod['go_moder_empty_poster'] === true
    && !$poster 
) {
    $approve = 0;
}

$disable_index = 0;
if (!empty($config_mod['disable_index'])
    && (bool)$config_mod['disable_index'] === true
) {
    $disable_index = 1;
}

$updateNewsDate = false;
if (!empty($config_mod['update_news_date'])
    && (bool)$config_mod['update_news_date'] === true
) {
    $updateNewsDate = true;
}

$user_row = $db->super_query(" SELECT user_id, name FROM " . PREFIX . "_users WHERE name='{$config_mod['author']}' ");


if(!$alloha['news_id']){
    $db->query(db_query("INSERT INTO `" . PREFIX . "_post` (`autor`, `date`, `short_story`, `full_story`, `xfields`, `title`, `descr`, `keywords`, `category`, `alt_name`, `comm_num`, `allow_comm`, `allow_main`, `approve`, `fixed`, `allow_br`, `symbol`, `tags`, `metatitle`) VALUES ('{$user_row['name']}', :date, :short_story, :full_story, :xfields, :title, :descr, :keywords, :category, :alt_name, 0, 1, 1, $approve, 0, 0, '', :tags, :metatitle);", $compile));

  
    $news_id = $db->insert_id();
    $db->query( "INSERT INTO " . PREFIX . "_post_extras (news_id,user_id,disable_index) VALUES('$news_id','{$user_row['user_id']}', '$disable_index')" );

    if($poster){
        $db->query( "INSERT INTO " . PREFIX . "_images (images,news_id,author,date) VALUES('{$poster}','$news_id','{$user_row['name']}','{$_TIME}')" );
    }


    $quality = $db->safesql($res['quality']);
    $db->query("UPDATE " . PREFIX . "_alloha SET status = '0', news_id = '$news_id', quality='$quality' WHERE kp_id = '{$alloha['kp_id']}'");
  
    echo "insert news --- $news_id --- {$res['name']}";
}

else {
    $news_id = $alloha['news_id'];
    $db->query( "DELETE FROM " . PREFIX . "_xfsearch WHERE news_id='{$alloha['news_id']}' "  );

    $xfields = $db->safesql($compile['xfields']);
    $title = $db->safesql($compile['title']);
    $category = $db->safesql($compile['category']);

    $upd_title = $is_serial ? "title = '$title'," : "";

    if ($is_serial) {
        if ($xfdata['episode_count']!=$episodes) {
            $updateNewsDate = true;
        }
        $upd_title = "title = '$title',";
    } else {
        $upd_title = '';
    }
    

    if($updateNewsDate){
        $date = date( "Y-m-d H:i:s", time() );
        $db->query("UPDATE " . PREFIX . "_post SET category='$category', $upd_title xfields = '$xfields', date='$date' WHERE id = '{$alloha['news_id']}'");
        $db->query("UPDATE " . PREFIX . "_post_extras SET disable_index = '$disable_index', editdate = '$_TIME', editor='{$user_row['name']}', reason='Парсер обновил данный материал' WHERE news_id = '{$alloha['news_id']}'");
    }
    else {
        $db->query("UPDATE " . PREFIX . "_post SET $upd_title category='$category', xfields = '$xfields' WHERE id = '{$alloha['news_id']}'");
    }

    if($poster){

        $images = $poster;

        $row = $db->super_query(" SELECT * FROM " . PREFIX . "_images WHERE news_id='{$post_row['id']}' ");
        
        if( $row['id'] ) {
            if ($row['images']) {
                $db->query(" UPDATE " . PREFIX . "_images SET images=CONCAT(images, '|||', '".$images."') WHERE news_id='{$post_row['id']}'");
            } else {
                $db->query(" UPDATE " . PREFIX . "_images SET images='{$images}' WHERE news_id='{$post_row['id']}'");
            }
            
        } else {
            $db->query(" INSERT INTO " . PREFIX . "_images (images, news_id, author, date) VALUES ('{$images}', '{$post_row['id']}', '{$user_row['name']}', '".time()."') ");
        }
    }

    $quality = $db->safesql($res['quality']);
    $last_episode = intval($request['last_episode']);
    $db->query("UPDATE " . PREFIX . "_alloha SET status = '0', news_id='{$alloha['news_id']}', quality = '{$quality}', episode='{$last_episode}' WHERE kp_id = '{$alloha['kp_id']}'");

    echo "update news --- {$post_row['id']} --- {$post_row['title']}";
}


if(version_compare('13.2', $config['version_id'], '<=') && !$alloha['news_id']){
    $ex_cats = explode(',', $compile['category']);
    foreach ($ex_cats as $ex_cat) {
        $ex_cat = intval($ex_cat);
        $db->query( "INSERT INTO " . PREFIX . "_post_extras_cats (news_id, cat_id) VALUES ('{$news_id}', '{$ex_cat}')" );
    }
}

$xfields = xfieldsload();
$news_xf = xfieldsdataload($compile['xfields']);
$xf_words = $xf_search_words = $newnews_xf = array ();

foreach ($xfields as $name => $value) {
    if($value[6] == 1 && !empty($news_xf[$value[0]])){
        $news_xf[$value[0]] = html_entity_decode($news_xf[$value[0]], ENT_QUOTES, $config['charset']);
        $newnews_xf[$value[0]] = trim( htmlspecialchars(strip_tags( stripslashes($news_xf[$value[0]]) ), ENT_QUOTES, $config['charset'] ));
        $temp_array = explode( ",", $newnews_xf[$value[0]] );

        foreach ($temp_array as $value2) {
            $value2 = trim($value2);
            if($value2) $xf_search_words[] = array( $db->safesql($value[0]), $db->safesql($value2) );
        }
    }
}

if (count($xf_search_words)) {
    $temp_array = array();
    foreach ( $xf_search_words as $value ) {
        $temp_array[] = "('" . $news_id . "', '" . $value[0] . "', '" . $value[1] . "')";
    }
    $xf_search_words = implode( ", ", $temp_array );
    $db->query( "INSERT INTO " . PREFIX . "_xfsearch (news_id, tagname, tagvalue) VALUES " . $xf_search_words );
}

if(!$alloha['news_id'] && $approve && function_exists('updateSocialPosting')) updateSocialPosting($news_id);

?>