<?php
  
$serial_statuses = [
    'offline' => 'Завершен/закрыт',
    'online' => 'Идёт показ',
    'paused' => 'Приостановлен',
    'pending' => 'В ожидании',
];  


$all_translate = [
    '1' => '2x2',
    '2' => 'Agatha Studdio',
    '3' => 'Alexfilm',
    '4' => 'AlFair Studio',
    '5' => 'Alt Pro',
    '6' => 'AMS',
    '7' => 'Amedia',
    '8' => 'Ancord',
    '9' => 'AniDUB',
    '10' => 'Anilibria',
    '11' => 'AXN Sci-fi',
    '12' => 'BaibaKo',
    '13' => 'Coldfilm',
    '14' => 'CTC',
    '15' => 'datynet',
    '16' => 'den904',
    '17' => 'Discovery',
    '18' => 'Diva Universal',
    '19' => 'DreamRecords',
    '20' => 'Filiza Studio',
    '21' => 'Flux-Team',
    '22' => 'Fox',
    '23' => 'F-TRAIN',
    '24' => 'Gears Media',
    '25' => 'GladiolusTV',
    '26' => 'GREEN TEA',
    '27' => 'HamsterStudio ',
    '28' => 'HTB',
    '29' => 'IdeaFilm',
    '30' => 'Jaskier',
    '31' => 'Jetvis Studio',
    '32' => 'Jimmy J.',
    '33' => 'Lord32x',
    '34' => 'LostFilm',
    '35' => 'Lw13pro',
    '36' => 'MC Entertainment',
    '38' => 'Narkom Pro',
    '39' => 'Newstudio',
    '40' => 'Nice-Media',
    '41' => 'Novafilm',
    '42' => 'Novamedia',
    '43' => 'Ozz',
    '44' => 'Paramount Comedy',
    '45' => 'PashaUp',
    '46' => 'Prichudiki',
    '47' => 'ProjektorShow',
    '48' => 'R.A.I.M',
    '49' => 'SET Russia',
    '50' => 'Sony Sci-Fi',
    '51' => 'Sony Turbo',
    '52' => 'To4ka',
    '53' => 'Tycoon',
    '54' => 'Universal Russia',
    '55' => 'Victory-Films',
    '56' => 'ViruseProject',
    '57' => 'VO-production',
    '58' => 'xaros',
    '59' => 'xixidok',
    '60' => 'Zamez',
    '61' => 'АРК ТВ',
    '62' => 'Гаврилов',
    '63' => 'Гоблин',
    '64' => 'Дасевич',
    '65' => 'Двухголосый закадровый',
    '66' => 'Дублированный',
    '67' => 'Есарев',
    '68' => 'Живов',
    '69' => 'Кубик в Кубе',
    '70' => 'Кураж-бамбей',
    '71' => 'Матвеев',
    '72' => 'Многоголосый закадровый',
    '73' => 'Невафильм',
    '74' => 'Несмертельное оружие',
    '75' => 'Одноголосый закадровый',
    '76' => 'Первый канал',
    '77' => 'Сербин',
    '78' => 'Студия Райдо',
    '79' => 'Субтитры',
    '80' => 'Сыендук',
    '81' => 'Шадинский',
    '82' => 'Не требуется',
    '83' => 'Пифагор',
    '84' => 'Синема УС',
    '85' => 'HDrezka Studio',
    '86' => 'MuzoBoz',
    '87' => 'Профессиональный многоголосый',
    '88' => 'Любительский двухголосый',
    '89' => 'Любительский',
    '90' => 'Дублированный (звук с TS)',
    '91' => 'Двухголосый (звук с TS)',
    '92' => 'Не требуется (звук с TS)',
    '93' => 'Оригинальная',
    '94' => 'KiraiMedia',
    '95' => 'Студийная банда',
    '96' => 'TVShows',
    '98' => 'Studio Films',
    '99' => 'VSI Moscow',
    '100' => 'RG.Paravozik',
    '101' => 'Кириллица',
    '102' => 'СВ-Дубль',
    '103' => 'Любительский одноголосый',
    '104' => '1001 Cinema',
    '105' => 'MTV',
    '106' => 'Кравец',
    '107' => 'OMSKBIRD records',
    '109' => 'SDI Media',
    '110' => 'NewStation',
    '111' => 'Finargot',
    '112' => 'Good People',
    '114' => 'FocusStudio',
    '115' => 'Т.О Друзей',
    '116' => 'Эй Би Видео',
    '117' => 'SunShine Studio',
    '118' => 'Pazl Voice',
    '120' => 'GoldTeam',
    '121' => 'Профессиональный двухголосый',
    '122' => 'KerobTV',
    '123' => 'Любительский многоголосый',
    '124' => 'Octopus',
    '125' => 'Crazy Cat',
    '126' => 'SoftBox',
    '127' => 'Levelin',
    '128' => 'JAM',
    '129' => 'Кубик в Кубе & Ко',
    '130' => 'MoyGolos',
    '131' => 'Киреев',
    '132' => 'Чадов',
    '133' => 'Гланц и Королёва',
    '134' => 'ТВ3',
    '135' => 'Гоблин (Кинотеатр)',
    '136' => 'Гоблин - цензура',
    '137' => 'DoubleRec',
    '138' => 'Рен-ТВ',
    '139' => 'FanStudio',
    '140' => 'Zone Vision',
    '141' => 'Honey&Haseena',
    '143' => 'Гоблин ПП',
    '144' => 'Zee TV',
    '146' => 'ShowJet',
    '147' => 'Greb&Creative',
    '148' => 'Профессиональный многоголосый (звук с TS)',
    '149' => 'Россия 2',
    '150' => 'KosharaSerials',
    '151' => 'WestFilm',
    '152' => 'WVoice',
    '153' => 'Колобок',
    '154' => 'Украинский',
    '155' => 'Amber',
    '156' => 'Kansai',
    '157' => 'Akari Group',
    '158' => 'AniStar',
    '159' => 'HardSub',
    '160' => 'Erai-raws',
    '161' => 'JekaSub',
    '162' => 'Rezan & Linok',
    '163' => 'AniMaunt',
    '164' => 'AniMedia',
    '165' => 'Anything Group',
    '166' => 'Onibaku',
    '167' => 'SHIZA Project',
    '168' => 'Flarrow Films',
    '169' => 'SoundFilm',
    '170' => 'SDI Moscow',
    '171' => 'ТВЦ',
    '173' => 'Рыбов & Трындяйкина',
    '174' => 'Red Media',
    '175' => 'Selena',
    '176' => 'ICG',
    '177' => 'OnisFilms',
    '178' => 'AniFilm',
    '179' => 'ДТВ',
    '180' => 'CBS Drama',
    '181' => 'AnimeVos',
    '182' => 'Lucky Production',
    '183' => 'субтитры СоветРомантики',
    '184' => 'STEPonee',
    '185' => 'LovelyVox',
    '186' => 'Позитив',
    '187' => 'NewComers',
    '188' => 'Дохалов',
    '189' => 'SDIncorporation',
    '190' => 'Мобильное телевидение',
    '191' => 'Инис',
    '192' => 'Ultradox',
    '193' => 'Сrunchyroll',
    '194' => 'Rumble',
    '195' => 'Persona99',
    '196' => 'XDub Dorama',
    '197' => 'Amazing Dubbing',
    '198' => 'HighHopes',
    '199' => 'Храм Дорам',
];



function xfieldsdatasave($xfields) {
    $filecontents = [];
    foreach ($xfields as $xfielddataname => $xfielddatavalue) {
        if ($xfielddatavalue === '') continue;
        $xfielddataname = str_replace( "|", "&#124;", $xfielddataname);
        $xfielddataname = str_replace( "\r\n", "__NEWL__", $xfielddataname);
        $xfielddatavalue = str_replace( "|", "&#124;", $xfielddatavalue);
        $xfielddatavalue = str_replace( "\r\n", "__NEWL__", $xfielddatavalue);
        $filecontents[] = "$xfielddataname|$xfielddatavalue";
    }
    $filecontents = join('||', $filecontents );
    return $filecontents;
}

  
function CheckDir($dir){
    if( !is_dir( $dir ) ) {
        @mkdir( $dir, 0777 );
        @chmod( $dir, 0777 );
    }
}

function request($url, $file = false){
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL,$url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
    curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 60 );
    curl_setopt($ch, CURLOPT_TIMEOUT, 60 );
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, 0);
    curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, 0);

    $headers = array(
        'User-Agent: Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.2924.87 Safari/537.36',
        'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language: ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        'Connection: keep-alive',
        'Cache-Control: max-age=0',
        'Upgrade-Insecure-Requests: 1'
    );
    if($file){
        $fp = fopen($file, "wb");
        curl_setopt($ch, CURLOPT_FILE, $fp);
    }
    curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    $res = curl_exec($ch);
    curl_close($ch);
    if($file) {
        fclose($fp);
        @chmod($file, 0666);
        $info = @getimagesize($file);
        if(is_array($info)){
            if( $info[2] == 2 ) {
                $ext = 'jpg';
            } elseif( $info[2] == 3 ) {
                $ext =  'png';
            } elseif( $info[2] == 1 ) {
                $ext = 'gif';
            } else $ext = 'jpg';
            rename($file, $file.'.'.$ext);
            return $file.'.'.$ext;
        } else {
            @unlink($file);
            return false;
        }
    }
    return $res;
}

function fixGenres(array $genres) {

    $replaces = array(
        'арт-хаус' => 'арт-хаус',
        'зарубежные' => 'зарубежный',
        'блокбастеры' => 'блокбастер',
        'русский' => 'русский',
        'биографический' => 'биография',
        'боевики' => 'боевик',
        'блокбастер' => 'блокбастер',
        'вестерны' => 'вестерн',
        'военные' => 'военный',
        'детективы' => 'детектив',
        'детский' => 'детский',
        'документальные' => 'документальный',
        'драмы' => 'драма',
        'игры' => 'игра',
        'история' => 'история',
        'комедии' => 'комедия',
        'концерты' => 'концерт',
        'короткометражный' => 'короткометражка',
        'полнометражный' => 'полнометражный',
        'криминал' => 'криминал',
        'мелодрамы' => 'мелодрама', 
        'музыкальные' => 'музыка',
        'мультфильмы' => 'мультфильм',
        'мультсериалы' => 'мультсериал',
        'мюзикл' => 'мюзикл',
        'новости' => 'новости',
        'путешествия' => 'путешествия',
        'приключения' => 'приключения',
        'развлекательный' => 'развлекательный',
        'семейные' => 'семейный',
        'спортивный' => 'спортивный',
        'триллеры' => 'триллер',
        'ужасы' => 'ужасы',
        'церемонии' => 'церемония',
        'для взрослых' => 'для взрослых',
    );

    foreach ($genres as $key => $genre) {
        $genre = mb_strtolower($genre, 'UTF-8');

        if (!empty($replaces[$genre])) {
            $genres[$key] = $replaces[$genre];
        } else {
            $genres[$key] = $genre;
        }
    }

    return $genres;
}

function template($config, $data) {
    $find = array();
    $replace = array();

    foreach ($data as $name => $value) {
        if ( is_array($value) ) $value = implode(", ", $value);

        $find[] = "'{{$name}}'i";
        $replace[] = $value;
        $find[] = "'\\[if_{$name}\\](.*?)\\[/if_{$name}\\]'is";
        $replace[] = $value ? '\1' : '';
        $find[] = "'\\[ifnot_{$name}\\](.*?)\\[/ifnot_{$name}\\]'is";
        $replace[] = $value ? '' : '\1';
    }

    foreach ($config as $key => $value) {
        $value = preg_replace($find, $replace, $value);

        $value = preg_replace_callback('#\\[(if|ifnot)? (.+?)\\](.*?)\\[/\1\\]#isuU', function($matches) use($data) {
            foreach (explode("||", $matches[2]) as $key => $value) {
                $value = explode("=", $value);
                $name = array_shift($value);
                $value = implode("=", $value);
                $value = explode("|", $value);

                if ( isset($data[$name]) ) {
                    $val = $data[$name];
                    if ( !is_array($val) ) $val = explode(",", $val);
                    if ( array_intersect($value, $val) ) {
                        if ( $matches[1] == "ifnot" ) return '';
                    } elseif( $matches[1] == "if" ) return '';
                }
            }

            return $matches[3];
        }, $value);

        $value = preg_replace('#\\[ifnot_(.+)\\](.*)\\[/ifnot_\1\\]#isuU', '\2', $value);
        $value = preg_replace('#\\[if_(.+)\\](.*)\\[/if_\1\\]#isuU', '', $value);
        $value = preg_replace("'{[a-zA-Z0-9-_:]+}'i", '', $value);

        if ( $value ) $config[$key] = preg_replace('#\s{2,}#', ' ', $value);
        else unset($config[$key]);
    }

    return $config;
}

function db_query($query, $data = false) {
    return preg_replace_callback('":([a-z0-9_\\-]+)"is', function($match) use($data) {
        if ( isset($data[$match[1]]) ) {
            if ($data[$match[1]] !== null) {
                return "'" . addslashes($data[$match[1]]) . "'";
            } else {
                return "NULL";
            }

        } else {
            return "NULL";
        }
    }, $query);
}

function allow_country($country, $allow_country){
    if (count($allow_country)) {
        $country2 = [];
        foreach ($country as $value) {
            $country2[] = mb_strtolower($value, 'utf-8');
        }
        if (count(array_intersect($country2, $allow_country))) {
            return true;
        } else {
            return false;
        }
    }
    return true;
}

function disallow_country($country, $allow_country){
    if (count($allow_country)) {
        $country2 = [];
        foreach ($country as $value) {
            $country2[] = mb_strtolower($value, 'utf-8');
        }
        if (count(array_intersect($country2, $allow_country))) {
            return true;
        } else {
            return false;
        }
    }
    return false;
}

function xfcompile( $in ) {
    if ( $in == "" ) return $in;

    foreach ( $in as $name => $value ) {
        if ( trim($name) == "" || trim($value) == "" ) continue;

        $name = str_replace( "|", "&#124;", $name );
        $name = str_replace( "\r\n", "__NEWL__", $name );
        $value = str_replace( "|", "&#124;", $value );
        $value = str_replace( "\r\n", "__NEWL__", $value );

        $out[] = "{$name}|{$value}";
    }

    return implode("||", $out);
}



function formatize_alloha($number, $type) {
    if ( $type == 1 ) $result = $number." сезон";
    elseif ( $type == 2 ) {
        if ( $number == 1 ) $result = $number." сезон";
        elseif ( $number > 1 ) $result = "1-".$number." сезон";
    }
    elseif ( $type == 3 ) {
        if ( $number == 1 ) $result = $number." сезон";
        elseif ( $number > 1 ) {
            $number_mas = array();
            for ($i = 1; $i <= $number; $i++) {
                $number_mas[] = $i;
            }
            $result = implode(",", $number_mas)." сезон";
        }
    }
    elseif ( $type == 4 ) $result = $number." серия";
    elseif ( $type == 5 ) {
        if ( $number == 1 ) $result = $number." серия";
        elseif ( $number > 1 ) $result = "1-".$number." серия";
    }
    elseif ( $type == 6 ) {
        if ( $number == 1 ) $result = $number." серия";
        elseif ( $number > 1 ) {
            $number_mas = array();
            for ($i = 1; $i <= $number; $i++) {
                $number_mas[] = $i;
            }
            $result = implode(",", $number_mas)." серия";
        }
    }
    elseif ( $type == 7 ) {
        if ( $number == 1 ) $result = "1,2 серия";
        elseif ( $number == 2 ) $result = "1,2,3 серия";
        elseif ( $number > 2 ) {
            $number_mas = array();
            for ($i = $number-1; $i <= $number+1; $i++) {
                $number_mas[] = $i;
            }
            $result = implode(",", $number_mas)." серия";
        }
    }
    elseif ( $type == 71 ) {
        if ( $number == 1 ) $result = "1 серия";
        elseif ( $number == 2 ) $result = "1,2 серия";
        elseif ( $number >= 3 ) {
            $number_mas = array();
            for ($i = $number-2; $i <= $number; $i++) {
                $number_mas[] = $i;
            }
            $result = implode(",", $number_mas)." серия";
        }
    }
    elseif ( $type == 8 ) {
        if ( $number == 1 ) $result = "1 серия";
        elseif ( $number > 1 AND $number <= 5 ) {
            $number_mas = array();
            for ($i = 1; $i <= $number; $i++) {
                $number_mas[] = $i;
            }
            $result = implode(",", $number_mas)." серия";
        }
        elseif ( $number > 5 ) {
            $number_mas = array();
            for ($i = $number-1; $i <= $number+1; $i++) {
                $number_mas[] = $i;
            }
            $result = "1-".implode(",", $number_mas)." серия";
        }
    }
    elseif ( $type == 81 ) {
        if ( $number == 1 ) $result = "1 серия";
        elseif ( $number > 1 AND $number <= 5 ) {
            $number_mas = array();
            for ($i = 1; $i <= $number; $i++) {
                $number_mas[] = $i;
            }
            $result = implode(",", $number_mas)." серия";
        }
        elseif ( $number > 5 ) {
            $number_mas = array();
            for ($i = $number-2; $i <= $number; $i++) {
                $number_mas[] = $i;
            }
            $result = "1-".implode(",", $number_mas)." серия";
        }
    }
    return $result;
}

function check_if_alloha($check_value, $dataArray) {
    foreach($dataArray as $named => $zna4enie) {
        if (strpos($check_value, '[data_'.$named.']') !== false) {
            if ($zna4enie) $check_value = preg_replace(';\[data_'.$named.'\](.*?)\[\/data_'.$named.'\];is', $dataArray[$named], $check_value);
            else $check_value = preg_replace(';\[data_'.$named.'\](.*?)\[\/data_'.$named.'\];is', '', $check_value);
        }
        if (strpos($check_value, '[nodata_'.$named.']') !== false) {
            if ($zna4enie) $check_value = preg_replace(';\[nodata_'.$named.'\](.*?)\[\/nodata_'.$named.'\];is', '', $check_value);
            else $check_value = preg_replace(';\[nodata_'.$named.'\](.*?)\[\/nodata_'.$named.'\];is', '$1', $check_value);
        }
    }

    return $check_value;
}




function check_license_alloha() {
    global $config_mod;
    preg_match('#[^.]+\.[^.]+$#', trim(getenv('HTTP_HOST')), $host);
    if(md5($host[0].'alloha-11.2.evo')!=$config_mod['lickey']) {
       // die('{"error": "Требуется лицензионный ключ"}');
    }
}



define( 'FOLDER_PREFIX', date( "Y-m" ) );

CheckDir(ROOT_DIR . "/uploads/posts/" . FOLDER_PREFIX .'/');
CheckDir(ROOT_DIR . "/uploads/posts/" . FOLDER_PREFIX .'/thumbs/');
CheckDir(ROOT_DIR . "/uploads/posts/" . FOLDER_PREFIX .'/medium/');

?>