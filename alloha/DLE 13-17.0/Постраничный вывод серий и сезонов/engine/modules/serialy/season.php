<?php

$seasons_row = $db->super_query( "SELECT * FROM " . PREFIX . "_seasons WHERE news_id = '{$row['id']}' AND season = '{$season}'" );

if (!$seasons_row) {
	define('NOTFOUND', true);
}

else {

	$serial_link = preg_replace('#\.html$#', '', $full_link);

	$canonical = $serial_link.'/'.$season.'-season-'.$season.'-season.html';

	$mm_row = $db->super_query( "SELECT MIN(season) as min, MAX(season) as max FROM " . PREFIX . "_seasons WHERE news_id = '{$row['id']}' AND season = '{$season}' " );
	
	if ($mm_row['max'] == $season) {
		$tpl->set_block( "'\\[next-season\\](.*?)\\[/next-season\\]'si", "" );
	}
	else {
		$tpl->set('{next-season}', $season+1);
		$tpl->set('[next-season]', '<a href="'.$serial_link.'/'.$season.'-season-'.($season+1).'-season.html">');
		$tpl->set('[/next-season]', '</a>');
	}

	if ($mm_row['min'] == $season) {
		$tpl->set_block( "'\\[prev-season\\](.*?)\\[/prev-season\\]'si", "" );
	}
	else {
		$tpl->set('{prev-season}', $season-1);
		$tpl->set('[prev-season]', '<a href="'.$serial_link.'/'.$season.'-season-'.($season-1).'-season.html">');
		$tpl->set('[/prev-season]', '</a>');
	}

}

if ($seasons_row['title']) {
	$tpl->set('{season-title}', stripslashes($seasons_row['title']));
	$tpl->set('[season-title]', '');
	$tpl->set('[/season-title]', '');
} else {
	$tpl->set_block( "'\\[season-title\\](.*?)\\[/season-title\\]'si", "" );
}


$kadr = false;

if(! empty($seasons_row['kadr']))
{
	list($kadr) = explode('|', $seasons_row['kadr']);
}


if($kadr) {
	$tpl->set('{kadr}', '/uploads/posts/'.$kadr);	
} else {
	$tpl->set('{kadr}', '/uploads/noimage.jpg');
}

$tpl->set('{story}', $seasons_row['story']);


?>