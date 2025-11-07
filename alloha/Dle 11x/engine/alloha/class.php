<?php


$qual_list = [
	'TS 720p'         => 0,
	'TS '             => 1,	
	'CAMRip'          => 2,
	'Workprint-AVC'   => 3,
	'WEB-DLRip 720p'  => 4,
	'WEB-DLRip 1080p' => 5,
	'WEB-DLRip 1080p' => 6,
	'WEB-DLRip'       => 7,
	'WEBRip'       => 7,
	'VHSRip'          => 8,
	'TVRip 720p'      => 9,
	'TVRip'           => 10,
	'SuperTS'         => 11,
	'SATRip'          => 12,
	'Laserdisc-RIP'   => 13,
	'IPTVRip'         => 14,
	'DVDSrc'          => 15,
	'DVDRip'          => 16,
	'DVBRip 720p'     => 17,
	'DVBRip'          => 18,
	'DVB'          => 18,
	'HDDVDRip 720p'   => 19,
	'HDDVDRip 1080p'  => 20,
	'HDDVDRip'        => 21,
	'HDTVRip 720p'    => 22,
	'HDTVRip 1080p'   => 23,
	'HDTVRip'         => 24,
	'HDRip 720p'      => 25,
	'HDRip 1080p'     => 26,
	'HDRip'           => 27,
	'D-VHS'           => 28,
	'BDRip 720p'      => 29,
	'BDRip 1080p'     => 30,
	'BDRip'           => 31
];


class Alloha {
	
	function __construct($type, $db) {
		$this->log  = $this->getLog();
		$this->next = empty($this->log[$type]['next']) ? '' : $this->log[$type]['next'];
		
		$this->db   = $db;
		$this->type = $type;
	}

    public function start($url){

    	$request_url = $url;

        for ($i=0; $i < 10; $i++) { 

        	$result = request($request_url);
        	$res = json_decode($result, true);

        	if(!$res) {
        		die($result);
        	}

        	if ($res['status']=='error') {
        		die($res['error_info']);
        	}

        	if(empty($res['data'])) {
        		$this->setLog($this->type, 'next', '');
        		die('empty results');
        	}

            $this->render($res['data']);

            if($i==0 && $this->next) {
            	$request_url = $url.'&page='.$this->next;
            } else {
            	$request_url = $res['next_page'] ? $url.'&page='.$res['next_page'] : '';
            }

      	    $this->setLog($this->type, 'next', $res['next_page'] ? $res['next_page'] : '');
            if(!$request_url) break;

        }

    }


    private function render($data){

	    foreach ($data as $k => $value) {
	        $kp_id        = intval($value['id_kp']);
	        $year         = intval($value['year']);
	        $type         = $this->type;
	        $quality      = $this->db->safesql($value['quality']);
	        $episode      = $season = 0;

	        if($kp_id<10) continue;

	        if(in_array($this->type, ['serial', 'multserial', 'animeserial'])){
	        	$season  = (int)$value['seasons_count'];
	        	$episode = (int)$value['last_episode'];
	        }

	        global $qual_list;

	        $row = $this->db->super_query( "SELECT * FROM " . PREFIX . "_alloha WHERE kp_id='$kp_id'" );

	        if ($row) {
	            if($qual_list[$row['quality']]<$qual_list[$quality] or $row['season']<$season or $row['episode']<$episode)
	                $this->db->query( "UPDATE " . PREFIX . "_alloha SET status='1', quality='{$quality}', episode='{$episode}', season='{$season}' WHERE kp_id='$kp_id'" );
	            
	        } else {
	            $this->db->query( "INSERT INTO " . PREFIX . "_alloha (kp_id, year, quality, type, episode, season) VALUES('{$kp_id}', '{$year}', '{$quality}', '{$type}', '{$episode}', '{$season}')" );
	        }

	    }

    }

    function getLog(){
    	$log = unserialize( file_get_contents( ENGINE_DIR . '/data/alloha.log' ) );
    	if (!$log) $log = array();
    	return $log;
    }

    function setLog($type, $name, $val){
    	$this->log[$type][$name] = $val;
    	file_put_contents( ENGINE_DIR . '/data/alloha.log', serialize($this->log));
    }

}


?>