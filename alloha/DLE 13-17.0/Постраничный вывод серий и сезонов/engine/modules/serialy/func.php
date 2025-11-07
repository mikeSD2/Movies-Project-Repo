<?php

function get_full_link($row) {

	global $config;

	if( intval( $row['category'] ) and $config['seo_type'] == 2 ) {
		$full_link = $config['http_home_url'] . get_url( intval( $row['category'] ) ) . "/" . $row['id'] . "-" . $row['alt_name'] . "/";
	} else {
		$full_link = $config['http_home_url'] . $row['id'] . "-" . $row['alt_name'] . "/";
	}

	return $full_link;
}

function custom_season($match) {

	global $full_link;

	$link = preg_replace('#\.html$#', '', $full_link);

	$season = intval($match[1]);

	if (defined('SEASON') && isset($_GET['season']) && (SEASON == '0' || $season < SEASON)) {
		define('NOTFOUND', true);
	}

	$links = '';

	for ($i=1; $i <= $season; $i++) { 
		$season_link = $link.'/'.$i.'-season.html';
		if (defined('SEASON') && SEASON == $i) {
			$links .= '<a class="active" href="'.$season_link.'">'.$i.'</a>';
		} else {
			$links .= '<a href="'.$season_link.'">'.$i.'</a>';
		}
		
	}

	return $links;

}


function custom_series($match) {

	global $db, $tpl;

	$param_str = trim($match[1]);

	$where = [];

	if( preg_match( "#news-id=['\"](.+?)['\"]#i", $param_str, $match ) ) {
		$news_id = intval($match[1]);
		$where[] = "s.news_id = '{$news_id}'";
	} 

	if( preg_match( "#season=['\"](.+?)['\"]#i", $param_str, $match ) ) {
		$season = intval($match[1]);
		$where[] = "s.season = '{$season}'";
	}

	if( preg_match( "#limit=['\"](.+?)['\"]#i", $param_str, $match ) ) {
		$limit = intval($match[1]);
	}

	else {
		$limit = 1000;
	}

	// if( preg_match( "#last=['\"]yes['\"]#i", $param_str, $match ) ) {
	// 	$order = 's.id desc';
	// }

	if( preg_match( "#sort=['\"](.+?)['\"]#i", $param_str, $match ) ) {

		$order = !empty($match[1]) && in_array($match[1], ["id", "date"]) ? 's.' . $match[1] : "s.id";

		if( preg_match( "#order=['\"](.+?)['\"]#i", $param_str, $match ) ) {
			$order .= " " . (!empty($match[1]) && in_array($match[1], ["asc", "desc"]) ? $match[1] : "desc");
		} else {
			$order .= " desc";
		}

		's.date desc' == $order && $order = 's.date desc, s.id desc';

	} else {

		$order = 's.episode ASC';	
		
	}

	if( preg_match( "#template=['\"](.+?)['\"]#i", $param_str, $match ) ) {
		$template = $match[1].'.tpl';
	}

	else {
		$template = 'serialy/series.tpl';	
	}

	$where = count($where) ? 'WHERE '.implode(' AND ', $where) : '';


	$db->query( "SELECT s.title, s.season, s.episode, s.kadr, p.id, p.title as news_title, p.category, p.alt_name FROM " . PREFIX . "_serials s LEFT JOIN " . PREFIX . "_post p ON(s.news_id=p.id) $where ORDER BY $order LIMIT $limit");

	$tpl->load_template($template);

	while ($row = $db->get_row()) {
		
		$tpl->set('{news-title}', stripslashes($row['news_title']));

		$tpl->set('{season}', $row['season']);

		$tpl->set('{episode}', $row['episode']);

		if ($row['title']) {
			$tpl->set('{title}', stripslashes($row['title']));
			$tpl->set('[title]', '');
			$tpl->set('[/title]', '');
		} else {
			$tpl->set_block( "'\\[title\\](.*?)\\[/title\\]'si", "" );
		}

		if (defined('EPISODE') && EPISODE == $row['episode']) {
			$tpl->set('[active]', '');
			$tpl->set('[/active]', '');
		} else {
			$tpl->set_block( "'\\[active\\](.*?)\\[/active\\]'si", "" );
		}
		

	    if($row['kadr']) {
	    	$tpl->set('{kadr}', '/uploads/posts/'.$row['kadr']);	
	    } else {
	    	$tpl->set('{kadr}', '/uploads/noimage.jpg');
	    }

	    $full_link = get_full_link($row).$row['season'].'-season-'.$row['episode'].'-episode.html';

	    $tpl->set('{full-link}', $full_link);

	    $tpl->compile('episode'); 

	}    

	return $tpl->result['episode'];

}




?>