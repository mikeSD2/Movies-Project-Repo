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



require_once ENGINE_DIR . '/alloha/func.php';

$config_mod = unserialize( file_get_contents( ENGINE_DIR . '/data/alloha.config' ) );
if ( !$config_mod ) $config_mod = array(); 

check_license_alloha();

if ($member_id['user_group']>1) {
	die('{"error": "for admin user only"}');
}


$last_file = ENGINE_DIR.'/data/alloha.last.file';
$last = ($_POST['start_new']) ? 0 : intval(@file_get_contents($last_file));

if($_POST['start_new']) file_put_contents($log_file, "");

$startfrom = intval($_POST['startfrom']);
$step = 0;
$count_per_step = 10;


$result = $db->query("SELECT id, date, xfields, category, alt_name, approve FROM " . PREFIX . "_post LIMIT ".$startfrom.", ".$count_per_step);

while($row = $db->get_row($result))
{
	$xfields = xfieldsdataload(stripslashes($row['xfields']));

	$res = request('https://api.apbugall.org/?token='.$config_mod['api_token'].'&kp='.intval($xfields['kinopoisk_id']));

	$res = json_decode($res, true);

	if(!count($res['data'])) continue;

	if($res['status']=='error') die('{"error": "'.$res['error_info'].'"}');

	$res = $res['data'];

	$request = [];

	$request['last_translate'] = trim( array_shift(explode(',', $res['translation'])) );
	$request['iframe_url'] = $res['iframe'];

	$episodes = array_shift($res['seasons']);
	$episodes = count($episodes['episodes']);
	$request['episode_count'] = $episodes;

	$request['instream_ads'] = ($res['ads']=='') ? '' : 1;

	$request['trailer'] = $res['iframe_trailer'];
	$request['translator']    = $res['translation'];

	$request['last_season'] = $res['seasons_count'];
	$request['last_episode'] = $res['last_episode'];

	$request['quality'] = $res['quality'];


	$compile = template($config_mod, $request);

	$new_xfields = array_diff($compile['xfields'], [' ', '']);
	$new_xfields = array_replace($xfields,$new_xfields);

	$xfields = $db->safesql(xfieldsdatasave($new_xfields));

	$db->query( "UPDATE " . PREFIX . "_post SET $date xfields='$xfields' WHERE id='{$row['id']}'" );

	file_put_contents($last_file, ++$last);
	$step++;
}

clear_cache();
$rebuildcount = $startfrom + $step;
echo "{\"status\": \"ok\",\"rebuildcount\": {$rebuildcount}}";


?>