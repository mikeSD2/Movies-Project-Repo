<?php

$episode_row = $db->super_query( "SELECT * FROM " . PREFIX . "_serials WHERE news_id = '{$row['id']}' AND season = '{$season}' AND episode = '{$episode}' " );

if (!$episode_row) {
	define('NOTFOUND', true);
}

else {

	$serial_link = preg_replace('#\.html$#', '', $full_link);

	$canonical = $serial_link.'/'.$season.'-season-'.$episode.'-episode.html';

	$mm_row = $db->super_query( "SELECT MIN(episode) as min, MAX(episode) as max FROM " . PREFIX . "_serials WHERE news_id = '{$row['id']}' AND season = '{$season}' " );
	
	if ($mm_row['max'] == $episode) {
		$tpl->set_block( "'\\[next-episode\\](.*?)\\[/next-episode\\]'si", "" );
	}
	else {
		$tpl->set('{next-episode}', $episode+1);
		$tpl->set('[next-episode]', '<a href="'.$serial_link.'/'.$season.'-season-'.($episode+1).'-episode.html">');
		$tpl->set('[/next-episode]', '</a>');
	}

	if ($mm_row['min'] == $episode) {
		$tpl->set_block( "'\\[prev-episode\\](.*?)\\[/prev-episode\\]'si", "" );
	}
	else {
		$tpl->set('{prev-episode}', $episode-1);
		$tpl->set('[prev-episode]', '<a href="'.$serial_link.'/'.$season.'-season-'.($episode-1).'-episode.html">');
		$tpl->set('[/prev-episode]', '</a>');
	}

}

if ($episode_row['title']) {
	$tpl->set('{episode-title}', stripslashes($episode_row['title']));
	$tpl->set('[episode-title]', '');
	$tpl->set('[/episode-title]', '');
} else {
	$tpl->set_block( "'\\[episode-title\\](.*?)\\[/episode-title\\]'si", "" );
}

$kadr = false;

if(! empty($seasons_row['kadr']))
{
	list($kadr) = explode('|', $episode_row['kadr']);
}

if($kadr) {
	$tpl->set('{kadr}', '/uploads/posts/'.$kadr);	
} else {
	$tpl->set('{kadr}', '/uploads/noimage.jpg');
}

$tpl->set('{story}', $episode_row['story']);


?>