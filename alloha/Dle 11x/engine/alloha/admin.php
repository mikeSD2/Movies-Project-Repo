<?php
  
if( !defined( 'DATALIFEENGINE' ) OR !defined( 'LOGGED_IN' ) ) {
	header( "HTTP/1.1 403 Forbidden" );
	header ( 'Location: ../../' );
	die( "Hacking attempt!" );
}

if (isset($_POST['q_search']) or $_POST['action']=='parse' or $_POST['action']=='update') {
	require_once ENGINE_DIR . '/alloha/parse.php';
	exit();
}

$__name = "DLE Alloha";
$__descr = "Модуль для автоматического добавления, и обновления фильмов и сериалов сайта DLE по базе alloha";

$config_mod = unserialize( file_get_contents( ENGINE_DIR . '/data/' . $mod . '.config' ) );
if ( !$config_mod ) $config_mod = array();

if ( $action ) {

	if( !$user_group[$member_id['user_group']]['admin_addnews'] ) {
		die( '{"success":false,"message":"' . $lang['index_denied'] . '"}' );
	}

	if ( $action == "config" ) {

		$config_mod = is_array( $_POST['config'] ) ? $_POST['config'] : array();

		file_put_contents( ENGINE_DIR . '/data/' . $mod . '.config', serialize( $config_mod ) );

		die( '{"success":true,"message":"Настройки успешно сохранены"}' );

	}

	if( $action == "sections" ) {

		$row = $db->super_query( "SELECT id, name FROM " . PREFIX . "_admin_sections WHERE name = '{$mod}'" );

		if ( $row ) {

			$db->query("DELETE FROM " . PREFIX . "_admin_sections WHERE name = '{$mod}'");

			die( '{"success":true,"message":"Модуль убран из меню «Сторонние модули»"}' );

		} else {

			$db->query( "INSERT IGNORE INTO " . PREFIX . "_admin_sections (name, title, descr, icon, allow_groups) VALUES ('{$mod}', '{$__name}', '{$descr}', '', '1')" );

			die( '{"success":true,"message":"Модуль добавлен в меню «Сторонние модули»"}' );

		}

	}

}

if( !$user_group[$member_id['user_group']]['admin_addnews'] ) {
	msg( "error", $lang['index_denied'], $lang['index_denied'] );
}

function makeCheckBox($name, $selected) {
  $selected = $selected ? "checked" : "";
  return "<input class=\"iButton-icons-tab\" type=\"checkbox\" name=\"$name\" value=\"1\" {$selected}>";
}

function makeDropDown($options, $name, $selected) {
    $output = "<select class=\"uniform\" style=\"min-width:100px;\" name=\"$name\">\r\n";
    foreach ( $options as $value => $description ) {
        $output .= "<option value=\"$value\"";
        if( $selected == $value ) {
            $output .= " selected ";
        }
        $output .= ">$description</option>\n";
    }
    $output .= "</select>";
    return $output;
}

$tags_arr = array(
    'poster'           => 'Постер',
    'title_ru'         => 'Название',
    'title_en'         => 'Оригинальное название',
    'title_alt'        => 'Альтернативное название',
    'year'             => 'Год выхода',
    'description'      => 'Описание',
    'countries'        => 'Страны',
    'genres'           => 'Жанры',
    'actors'           => 'Актеры',
    'directors'        => 'Режиссеры',
    'producer'         => 'Продюсеры',
    'iframe_url'       => 'Плеер',
    'trailer'          => 'Трейлер',
    'kinopoisk_id'     => 'ID Kinopoisk',
    'imdb_id'          => 'ID IMDB',
    'tmdb_id'          => 'ID TMDB',
    'world_art_id'     => 'ID WORLD ART',
    'translator'       => 'Перевод',
    'quality'          => 'Качество видео',
    'last_season'      => 'Последний сезон',
    'last_episode'     => 'Последний эпизод',
    'episode_count'    => 'Кол-во эпизодов',
    'last_translate'   => 'Последняя озвучка',
    'rating_kp'        => 'Kinopoisk рейтинг',
    'rating_imdb'      => 'IMDB рейтинг',
    'rating_tmdb'      => 'TMDB рейтинг',
    'rating_world_art' => 'WORLD ART рейтинг',
    'rate_mpaa'        => 'Рейтинг материала по шкале MPAA',
    'premiere_ru'      => 'Премьера в россии',
    'premiere_world'   => 'Мировая премьера',
    'video_type'       => 'Тип видео (фильм, сериал...)', 
    'time'             => 'Продолжительность',
    'age'              => 'Возрастное ограничение',
    'slogan'           => 'Слоган',
    ':instream_ads'    => 'Наличие рекламы: да / нет' 
);



$country_arr = array(
  'Австралия',
  'Австрия',
  'Азербайджан',
  'Албания',
  'Алжир',
  'Американское Самоа',
  'Ангилья',
  'Англия',
  'Ангола',
  'Андорра',
  'Антигуа и Барбуда',
  'Аргентина',
  'Армения',
  'Аруба',
  'Афганистан',
  'Багамы',
  'Бангладеш',
  'Барбадос',
  'Бахрейн',
  'Бейкер',
  'Белиз',
  'Белоруссия',
  'Бельгия',
  'Бенилюкс',
  'Бенин',
  'Болгария',
  'Боливия',
  'Бонэйр',
  'Бопутатсвана',
  'Босния и Герцеговина',
  'Ботсвана',
  'Бразилия',
  'Бруней',
  'Буркина-Фасо',
  'Бурунди',
  'Бутан',
  'Вануату',
  'Ватикан',
  'Великобритания',
  'Венгрия',
  'Венда',
  'Венесуэла',
  'Вьетнам',
  'Габон',
  'Гаити',
  'Гайана',
  'Гамбия',
  'Гана',
  'Гватемала',
  'Гвинея',
  'Гвинея-Бисау',
  'Германия',
  'Гернси',
  'Гибралтар',
  'Гондурас',
  'Гонконг',
  'Сомали',
  'Гренада',
  'Греция',
  'Грузия',
  'Гуам',
  'Дания',
  'Конго',
  'Косово',
  'Джибути',
  'Джонстон',
  'Джубаленд',
  'Доминика',
  'Доминикана',
  'Египет',
  'Замбия',
  'Зимбабве',
  'Израиль',
  'Имамат Оман',
  'Индия',
  'Индонезия',
  'Иордания',
  'Ирак',
  'Иран',
  'Ирландия', 
  'Исландия',
  'Испания',
  'Италия',
  'Йемен',
  'Султанат Касири',
  'Кабо-Верде',
  'Казахстан',
  'Камбоджа',
  'Камерун',
  'Канада',
  'Катар',
  'Кашубия',
  'Кенедугу',
  'Кения',
  'Киргизия',
  'Кирибати',
  'Китай',
  'Колумбия',
  'Коморы',
  'Конго',
  'Корея Северная',
  'Корея Южная',
  'Нидерланды',
  'Конго',
  'Коста-Рика', 
  'Куба',
  'Кувейт',
  'Кюрасао',
  'Лаос',
  'Латвия',
  'Лесото',
  'Либерия',
  'Ливан',
  'Ливия',
  'Литва',
  'Лихтенштейн',
  'Люксембург',
  'Маврикий',
  'Мавритания',
  'Мадагаскар',
  'Малави',
  'Малайзия',
  'Мали',
  'Мальдивы',
  'Мальта',
  'Марокко',
  'Мартиазо',
  'Мексика',
  'Мидуэй',
  'Мозамбик',
  'Молдавия',
  'Молдова',
  'Монако',
  'Монголия',
  'Монтсеррат',
  'Мьянма',
  'Намибия',
  'Науру',
  'Непал',
  'Нигер',
  'Нигерия',
  'Нидерланды',
  'Никарагуа',
  'Ниуэ',
  'Новая Зеландия',
  'Новая Каледония',
  'Норвегия',
  'Остров Норфолк', 
  'ОАЭ',
  'Оман',
  'Пакистан',
  'Палау',
  'Панама',
  'Парагвай',
  'Перу',
  'Польша',
  'Португалия',
  'Пуэрто Рико',
  'Ангилья',
  'Закистан',
  'Кипр',
  'Логон',
  'Россия',
  'Руанда',
  'Румыния',
  'Сальвадор',
  'Самоа',
  'Сан-Марино',
  'Саудовская Аравия',
  'Северная Ирландия',
  'Северная Македония',
  'Сейшельские Острова ',
  'Сенегал',
  'Сент-Люсия',
  'Сербия',
  'Силенд',
  'Сингапур',
  'Синт-Мартен',
  'Синт-Эстатиус',
  'Сирия',
  'Сискей',
  'Словакия',
  'Словения',
  'Соломоновы Острова',
  'Сомали',
  'Сомалиленд',
  'Судан',
  'Суринам',
  'СССР',
  'США',
  'Сьерра-Леоне',
  'Таджикистан',
  'Таиланд',
  'Тайвань',
  'Танзания',
  'Того',
  'Токелау',
  'Тонга',
  'Торо',
  'Транскей',
  'Тринидад',
  'Тобаго',
  'Тувалу',
  'Тунис',
  'Туркмения',
  'Турция',
  'Уганда',
  'Узбекистан',
  'Украина',
  'Уругвай',
  'Уэйк',
  'Уэльс',
  'ФШМ',
  'Фиджи',
  'Филиппины',
  'Финляндия',
  'Фландренсис',
  'Фолклендские острова',
  'Франция',
  'Французская Полинезия',
  'Хауленд',
  'Хиршабелле',
  'Хорватия',
  'Центральноафриканская Республика',
  'Чад',
  'Черногория',
  'Чехия',
  'Чили',
  'Швейцария',
  'Швеция',
  'Шотландия',
  'Шри-Ланка',
  'Эквадор',
  'Экваториальная Гвинея',
  'Эритрея',
  'Эсватини',
  'Эстония',
  'Эфиопия',
  'Южная Георгия',
  'ЮАР',
  'Южный Судан',
  'Ямайка',
  'Япония',
);

$main = "";

foreach ( array( 
  'title'       => 'Заголовок новости', 
  'short_story' => 'Краткое описание',
  'full_story'  => 'Полное описание',  		
  'metatitle'   => 'Метатег Title', 
  'descr'       => 'Метатег Description', 
  'keywords'    => 'Метатег Keywords',
  'tags'        => 'Теги новости',
  'alt_name'    => 'ЧПУ новости',
  'api_token'   => 'API Токен alloha', 
	) as $name => $title ) {

	$main .= "<tr><td class=\"col-xs-6 col-sm-6 col-md-7 white-line\"><h6 class=\"media-heading text-semibold\">{$title}</h6><span></span></td><td class=\"col-xs-6 col-sm-6 col-md-7 white-line\"><input name=\"config[{$name}]\" class=\"form-control\" value=\"" . ( isset( $config_mod[$name] ) ? $config_mod[$name] : "" ) . "\"></td></tr>";

}

$main .= "<tr><td class=\"col-xs-6 col-sm-6 col-md-7 white-line\"><h6 class=\"media-heading text-semibold\">Имя пользователя от имени которого добавляются публикации</h6><span></span></td><td class=\"col-xs-6 col-sm-6 col-md-7 white-line\"><input name=\"config[author]\" class=\"form-control\" value=\"" .$config_mod['author'] . "\"></td></tr>";

$add_film        = makeCheckBox('config[add_film]', $config_mod['add_film']);
$add_multfilm    = makeCheckBox('config[add_multfilm]', $config_mod['add_multfilm']);
$add_multserial  = makeCheckBox('config[add_multserial]', $config_mod['add_multserial']);
$add_serial      = makeCheckBox('config[add_serial]', $config_mod['add_serial']);
$add_anime       = makeCheckBox('config[add_anime]', $config_mod['add_anime']);
$add_animeserial = makeCheckBox('config[add_animeserial]', $config_mod['add_animeserial']);
$add_tvshow      = makeCheckBox('config[add_tvshow]', $config_mod['add_tvshow']);

$main .= "<tr><td class=\"col-xs-6 col-sm-6 col-md-7 white-line\"><h6 class=\"media-heading text-semibold\">Добавлять на сайт</h6></td><td class=\"col-xs-6 col-sm-6 col-md-7 white-line\">".
  '<div style="margin-bottom:10px">'.$add_film.' Фильмы</div>'.
  '<div style="margin-bottom:10px">'.$add_multfilm.' Мультфильмы</div>'.
	'<div style="margin-bottom:10px">'.$add_multserial.' Мультсериалы</div>'.
	'<div style="margin-bottom:10px">'.$add_serial.' Сериалы</div>'.
	'<div style="margin-bottom:10px">'.$add_anime.' Аниме</div>'.
  '<div style="margin-bottom:10px">'.$add_animeserial.' Аниме-сериалы</div>'.
	'<div style="margin-bottom:10px">'.$add_tvshow.' TV-шоу</div>'.
	"</td></tr>";

$main .= "<tr><td class=\"col-xs-6 col-sm-6 col-md-7 white-line\"><h6 class=\"media-heading text-semibold\">Черный список</h6><span>Укажите список ID Кинопоиска(каждый с новой строки)</span></td><td class=\"col-xs-6 col-sm-6 col-md-7 white-line\"><textarea name=\"config[blacklist]\" style=\"height:200px;\" class=\"form-control\">" . ( isset( $config_mod['blacklist'] ) ? $config_mod['blacklist'] : "" ) . "</textarea></td></tr>";

$main .= "<tr><td class=\"col-xs-6 col-sm-6 col-md-7 white-line\"><h6 class=\"media-heading text-semibold\">Исключить новости</h6><span>Укажите список ID новостей для которых данные при автоматическом обновлении обновлятся не будут(каждый с новой строки)</span></td><td class=\"col-xs-6 col-sm-6 col-md-7 white-line\"><textarea name=\"config[exclude_news]\" style=\"height:200px;\" class=\"form-control\">" . ( isset( $config_mod['exclude_news'] ) ? $config_mod['exclude_news'] : "" ) . "</textarea></td></tr>";

$first_new = makeCheckBox('config[first_new]', $config_mod['first_new']);
$main .= '<tr>
      <td class="col-xs-6 col-sm-6 col-md-7 white-line">
        <h6 class="media-heading text-semibold">Добавлять сначала новинки:</h6>
        <span class="text-muted text-size-small hidden-xs">если включено, то сначала будут добавлятся новые фильмы (по годам), иначе так как находятся в базе. по порядку</span>
      </td>
      <td class="col-xs-6 col-sm-6 col-md-7 white-line">'.$first_new.'</td>
    </tr>';


$allow_country = $config_mod['allow_country'] ? $config_mod['allow_country'] : [];
foreach ($country_arr as $value) {
	if (in_array(mb_strtolower($value, 'utf-8'), $allow_country)) {
		$country_select[] = '<option value="'.mb_strtolower($value, 'utf-8').'" selected>'.$value.'</option>';
	}
	else {
		$country_select[] = '<option value="'.mb_strtolower($value, 'utf-8').'">'.$value.'</option>';
	}
}


$disallow_country = $config_mod['disallow_country'] ? $config_mod['disallow_country'] : [];
foreach ($country_arr as $value) {
  if (in_array(mb_strtolower($value, 'utf-8'), $disallow_country)) {
    $dcountry_select[] = '<option value="'.mb_strtolower($value, 'utf-8').'" selected>'.$value.'</option>';
  }
  else {
    $dcountry_select[] = '<option value="'.mb_strtolower($value, 'utf-8').'">'.$value.'</option>';
  }
}


$allow_year = $config_mod['allow_year'] ? $config_mod['allow_year'] : [];

for ($i=1920; $i < 2020+date('Y'); $i++) { 
	if (in_array($i, $allow_year)) {
		$year_select[] = '<option value="'.$i.'" selected>'.$i.'</option>';
	}
	else {
		$year_select[] = '<option value="'.$i.'">'.$i.'</option>';
	}
}



$main .= '<tr>
      <td class="col-xs-6 col-sm-6 col-md-7 white-line">
        <h6 class="media-heading text-semibold">Допустимые страны:</h6>
        <span class="text-muted text-size-small hidden-xs">будут добавляться публикации только определенных стран. если ничего не выбрано - то все</span>
      </td>
      <td class="col-xs-6 col-sm-6 col-md-7 white-line"><select data-placeholder="Выберите страну" name="config[allow_country][]" class="categoryselect" multiple="" style="width: 100%; max-width: 350px;">'.implode('', $country_select).'</select></td>
    </tr>';



$main .= '<tr>
      <td class="col-xs-6 col-sm-6 col-md-7 white-line">
        <h6 class="media-heading text-semibold">Запрещенные страны:</h6>
        <span class="text-muted text-size-small hidden-xs">будут запрещены для публикации определенные страны. если ничего не выбрано - то все</span>
      </td>
      <td class="col-xs-6 col-sm-6 col-md-7 white-line"><select data-placeholder="Выберите страну" name="config[disallow_country][]" class="categoryselect" multiple="" style="width: 100%; max-width: 350px;">'.implode('', $dcountry_select).'</select></td>
    </tr>';


$main .= '<tr>
      <td class="col-xs-6 col-sm-6 col-md-7 white-line">
        <h6 class="media-heading text-semibold">Допустимые года:</h6>
        <span class="text-muted text-size-small hidden-xs">будут добавляться публикации только определенных годов. если ничего не выбрано - то все</span>
      </td>
      <td class="col-xs-6 col-sm-6 col-md-7 white-line"><select data-placeholder="Выберите год" name="config[allow_year][]" class="categoryselect" multiple="" style="width: 100%; max-width: 350px;">'.implode('', $year_select).'</select></td>
    </tr>';


$main .= '<tr>
      <td class="col-xs-6 col-sm-6 col-md-7 white-line">
        <h6 class="media-heading text-semibold">Фильтр по рейтингу Kinopoisk:</h6>
        <span class="text-muted text-size-small hidden-xs">будет отсортированы фильмы по рейтингу Kinopoisk (например 7.5)</span>
      </td>
      <td class="col-xs-6 col-sm-6 col-md-7 white-line"><input name="config[rating_kp]" class="form-control" value="'.$config_mod['rating_kp'].'"></td>
    </tr>';

$main .= '<tr>
      <td class="col-xs-6 col-sm-6 col-md-7 white-line">
        <h6 class="media-heading text-semibold">Фильтр по рейтингу IMDB:</h6>
        <span class="text-muted text-size-small hidden-xs">будет отсортированы фильмы по рейтингу IMDB (например 7.5)</span>
      </td>
      <td class="col-xs-6 col-sm-6 col-md-7 white-line"><input name="config[rating_imdb]" class="form-control" value="'.$config_mod['rating_imdb'].'"></td>
    </tr>';       


$main .= '<tr>
      <td class="col-xs-6 col-sm-6 col-md-7 white-line">
        <h6 class="media-heading text-semibold">Сколько серий прибавлять:</h6>
        <span class="text-muted text-size-small hidden-xs">будет прибавляться указаное кол-во серий в metatitle (тег {plus_episode})</span>
      </td>
      <td class="col-xs-6 col-sm-6 col-md-7 white-line"><input name="config[plus_episode]" class="form-control" value="'.$config_mod['plus_episode'].'"></td>
    </tr>';


$go_moder = makeCheckBox('config[go_moder]', $config_mod['go_moder']);
$conditionEmptyDescr = makeCheckBox('config[go_moder_empty_descr]', $config_mod['go_moder_empty_descr']);
$conditionEmptyPoster = makeCheckBox('config[go_moder_empty_poster]', $config_mod['go_moder_empty_poster']);

$update_if_quality = makeCheckBox('config[update_if_quality]', $config_mod['update_if_quality']);
$update_if_seasone = makeCheckBox('config[update_if_seasone]', $config_mod['update_if_seasone']);
$update_if_change_translate = makeCheckBox('config[update_if_change_translate]', $config_mod['update_if_change_translate']);

$disable_index = makeCheckBox('config[disable_index]', $config_mod['disable_index']);
$enable_ads = makeCheckBox('config[enable_ads]', $config_mod['enable_ads']);
$upload_poster = makeCheckBox('config[upload_poster]', $config_mod['upload_poster']);

$main .= '<tr>
      <td class="col-xs-6 col-sm-6 col-md-7 white-line">
        <h6 class="media-heading text-semibold">Загружать постер на сайт:</h6>
        <span class="text-muted text-size-small hidden-xs">если включено то постер будет загружатся вам на сервер. иначе будет ссылка на сторонний ресурс</span>
      </td>
      <td class="col-xs-6 col-sm-6 col-md-7 white-line">'.$upload_poster.'</td>
    </tr>';

$main .= <<<HTML
<tr>
    <td class="col-xs-6 col-sm-6 col-md-7 white-line">
        <h6 class="media-heading text-semibold">
            Сначала отправлять на модерацию:
        </h6>
        <h6 class="media-heading text-semibold">
            На модерацию при отсутствии описания:
        </h6>
        <h6 class="media-heading text-semibold">
            На модерацию при отсутствии постера:
        </h6>
        <h6 class="media-heading text-semibold">
            Добавлять с вшитой рекламой:
        </h6>        
    </td>
    <td class="col-xs-6 col-sm-6 col-md-7 white-line">
        <div style="margin-bottom: 7px">
            $go_moder
        </div>
        <div style="margin-bottom: 7px">
            $conditionEmptyDescr
        </div>
        <div style="margin-bottom: 7px">
            $conditionEmptyPoster
        </div>
        <div>$enable_ads</div>
    </td>
</tr>
<tr>
    <td class="col-xs-6 col-sm-6 col-md-7 white-line">
        <h6 class="media-heading text-semibold">
            Поднимать фильмы / мультфильмы / аниме при  смене качества:
        </h6>
        <h6 class="media-heading text-semibold">
            Поднимать сериалы / мультсериалы / аниме-сериалы при смене сезонов и серий:
        </h6>
        <h6 class="media-heading text-semibold">
            Поднимать сериалы при смене озвучки:
        </h6>
        <h6 class="media-heading text-semibold">
            Запретить индексацию страницы для поисковиков:
        </h6>
    </td>
    <td class="col-xs-6 col-sm-6 col-md-7 white-line">
        <div style="margin-bottom: 7px">
            $update_if_quality
        </div>
        <div style="margin-bottom: 7px">
            $update_if_seasone
        </div>
        <div style="margin-bottom: 7px">
            $update_if_change_translate
        </div>
        <div style="margin-bottom: 7px">
            $disable_index
        </div>
    </td>
</tr>
HTML;



$xfields = "";

foreach ( xfieldsload() as $xfield ) {

	$options = "";

	foreach ($tags_arr as $key => $value) {
		if ( ($xfield[3] == "yesorno" && substr($key, 0, 1) == ":") 
			|| (in_array($xfield[3], array('text', 'textarea', 'htmljs', 'select')) && substr($key, 0, 1) != ":")
			|| (in_array($xfield[3], array('image', 'imagegalery')) && $key == 'image') ) {
			$key = trim($key, ':');

			if ( $key == 'image' && in_array($xfield[3], array('image', 'imagegalery') ) ) {
				$key = 'xf-' . $key;
			} 

			if ( in_array($config_mod['xfields'][$xfield[0]], array('{' . $key . '}', '{xf-' . $key . '}' ) ) ) {
				$selected = " selected";
			} else {
				$selected = "";
			}

			$options .= '<option value="{' . $key . '}"' . $selected . '>' . $value . '</option>';
		}
	}

	if ( $options != "" )  $xfields .= "<tr><td class=\"col-xs-6 col-sm-6 col-md-7 white-line\"><h6 class=\"media-heading text-semibold\">{$xfield[1]}</h6><span>Дополнительное поле [{$xfield[0]}]</span></td><td class=\"col-xs-6 col-sm-6 col-md-7 white-line\"><select name=\"config[xfields][{$xfield[0]}]\" style=\"width:100%;max-width:350px;\" class=\"uniform\"><option value=\" \">--- не выбрано ---</option>{$options}</select></td></tr>";

}


$genre_arr = array(
  'сериал',
  'фильм',
  'зарубежный',
  'арт-хаус',
  'дорама',
  'аниме',
  'аниме сериал',
  'биография',
  'боевик', 
  'вестерн',
  'военный',
  'детектив',
  'детский', 
  'документальный',
  'драма',
  'игра',
  'история',
  'комедия',
  'концерт',
  'короткометражка',
  'полнометражный',
  'криминал',
  'мелодрама',
  'мистический',
  'музыка',
  'мультфильм',
  'мультсериал',
  'мюзикл',
  'новости',
  'путешествия',
  'приключения',
  'развлекательный',
  'реальное тв',
  'семейный',	
  'спортивный',
  'ток-шоу',
  'тв шоу',
  'триллер',
  'ужасы',
  'фантастика',
  'фильм-нуар',
  'фэнтези',
  'церемония',
  'для взрослых',
  'США',
  'Россия',
  'Украина',
  'Белоруссия',
  'Корея Южная',
  'Япония',
  'Франция',
  'Китай',
  'Германия',
  'СССР',
  'Турция',
  'Великобритания',
  'Индия',
  'Гаити',
  'Пуэрто Рико',
  'Пакистан',
  'Панама',
  'Буркина-Фасо',
  'Мьянма',
  'Монголия',
  'Египет',
  'Иордания',
  'Конго',
  'Молдова',
  'Нигерия',
  'Гана',
  'Албания',
  'Косово',
  'Словакия',
  'Армения',
  'Монако',
  'Судан',
  'Кения',
);

for($i=date('Y')+4;$i>=1920;$i--) $genre_arr[] = $i;

$cats = "";

foreach ($cat_info as $cat) {
	$options = "";

	foreach ($genre_arr as $genre)
		$options .= '<option value="' . $genre . '"' . (in_array($genre, $config_mod['category'][$cat['id']]) ? ' selected' : '') . '>' . $genre . '</option>';

	$cat_id = $cat['parentid'];
	$name = $cat['name'];

	while ($cat_id) {
		$name = $cat_info[$cat_id]['name'] . ' / ' . $name;
		$cat_id = $cat_info[$cat_id]['parentid'];
	}

	$cats .= "<tr><td class=\"col-xs-6 col-sm-6 col-md-7 white-line\"><h6 class=\"media-heading text-semibold\">{$name}</h6><span>категория [ID:{$cat['id']}]</span></td><td class=\"col-xs-6 col-sm-6 col-md-7 white-line\"><select name=\"config[category][{$cat['id']}][]\" style=\"width:100%;max-width:350px;\" class=\"categoryselect\" multiple>{$options}</select></td></tr>";
}


$tags = "";

foreach ($tags_arr as $key => $value) {
	$tags .= "<tr><td class=\"col-xs-6 col-sm-6 col-md-7 white-line\"><h6 class=\"media-heading text-semibold\">{$value}</h6><span></span></td><td class=\"col-xs-6 col-sm-6 col-md-7 white-line\">[if_{$key}] {{$key}} [/if_{$key}]<br>[ifnot_{$key}] данных нету [/ifnot_{$key}]</td></tr>";
}

echoheader( $__name, $__descr );


$row = $db->super_query( "SELECT COUNT(*) as count FROM " . PREFIX . "_post" );

$last_file = ENGINE_DIR.'/data/alloha.last.file';

$last = intval(@file_get_contents($last_file));



$serial_arr = [
  'episode_plus' => 'Последняя серия + 1',
  'seasone_plus' => 'Последний сезон + 1',
  'episode_type_1' => 'Форматированная серия вида 1 серия, 2 серия, 3 серия',
  'episode_type_2' => 'Форматированная серия вида 1 серия, 1-2 серия, 1-3 серия, 1-4 серия',
  'episode_type_3' => 'Форматированная серия вида 1 серия, 1,2 серия, 1,2,3 серия, 1,2,3,4 серия',
  'episode_type_4' => 'Форматированная серия + 1 вида: если 1 серия - 1,2 серия, если 2 серия - 1,2,3 серия, если 5 серия - 4,5,6 серия',
  'episode_type_5' => 'Форматированная серия + 1 вида 1,2 серия, 1,2,3 серия, 1,2,3,4,5 серия, 1-5,6,7 серия',
  'season_type_1' => 'Форматированный сезон вида 1 сезон, 2 сезон, 3 сезон',
  'season_type_2' => 'Форматированный сезон вида 1 сезон, 1-2 сезон, 1-3 сезон',
  'season_type_3' => 'Форматированный сезон вида 1 сезон, 1,2 сезон, 1,2,3 сезон',
];


  

foreach ($serial_arr as $key => $value) {

  $options = "";

  foreach ( xfieldsload() as $xfield ) {

    if ( $xfield[3]=='text' ) {


      
      if ( isset($config_mod['xfields'][$key]) && '{'.$xfield[0].'}'== $config_mod['xfields'][$key]) {
        $selected = " selected";
      } else {
        $selected = "";
      }

      $options .= '<option value="{' . $key . '}"' . $selected . '>' . $xfield[1] . '</option>';
    }
  }

  if ( $options != "" )  $serial_tab .= "<tr><td class=\"col-xs-6 col-sm-6 col-md-7\"><h8 class=\"media-heading text-semibold\">{$value}</h8></td><td class=\"col-xs-6 col-sm-6 col-md-7 white-line\"><select name=\"config[xfields][$key]\" style=\"width:100%;max-width:350px;\" class=\"uniform\"><option value=\" \">--- не выбрано ---</option>{$options}</select></td></tr>";

}



$serial_tab = <<<HTML
<style type="text/css">
  .rcol-2col {
      width: 100%;
      margin: 0 20px 0 0;
  }
  .rcol-2col-header {
      background: #e1e1e1;
      font: 400 14px/1.5 'Trebuchet MS';
      color: #7d7d7f;
      height: 40px !important;
      padding: 10px 20px;
      z-index: 5;
      position: relative;
      cursor: pointer;
  }
  .rcol-2col-header span {
      float: left;
  }
  .show-hide {
      float: right;
  }
</style>
<script type="text/javascript">
  $(function(){
    $('.rcol-2col-header').click(function(){
      $('.rcol-2col-body').toggle()
    });
  });
</script>
<table class="table table-normal">$serial_tab</table>
<div class="rcol-2col">
      <div class="rcol-2col-header">
          <span>Список доступных тегов</span>
          <div class="show-hide">Show</div>
      </div>
          <div class="rcol-2col-body" style="display: none;padding: 10px 20px;">
          <table width="100%" border="0" cellspacing="0" cellpadding="0">
              <tbody><tr class="rcol-2col-body-tr-even">
                            <td width="50%">Теги для поля</td>
                            <td width="50%">Описание тега для поля</td>
                        </tr>
                <tr class="rcol-2col-body-tr-even">
                  <td width="50%">1. <b>[data_episode_plus]{episode_plus}[/data_episode_plus]</b><br>2. <b>[nodata_episode_plus]ваш текст[/nodata_episode_plus]</b></td>
                  <td width="50%">1. Заменит тег на цифру с номером последней серии + 1.<br>2. В случае если поле не задано у источника, заменит теги на ваш текст</td>
                </tr><tr class="rcol-2col-body-tr-even">
                  <td width="50%">1. <b>[data_season_plus]{season_plus}[/data_season_plus]</b><br>2. <b>[nodata_season_plus]ваш текст[/nodata_season_plus]</b></td>
                  <td width="50%">1. Заменит тег на цифру с номером последнего сезона + 1.<br>2. В случае если поле не задано у источника, заменит теги на ваш текст</td>
                </tr><tr class="rcol-2col-body-tr-even">
                  <td width="50%">1. <b>[data_episode_type_1]{episode_type_1}[/data_episode_type_1]</b><br>2. <b>[nodata_episode_type_1]ваш текст[/nodata_episode_type_1]</b></td>
                  <td width="50%">1. Заменит тег на форматированную серию вида 1 серия, 2 серия, 3 серия.<br>2. В случае если поле не задано у источника, заменит теги на ваш текст</td>
                </tr><tr class="rcol-2col-body-tr-even">
                  <td width="50%">1. <b>[data_episode_type_2]{episode_type_2}[/data_episode_type_2]</b><br>2. <b>[nodata_episode_type_2]ваш текст[/nodata_episode_type_2]</b></td>
                  <td width="50%">1. Заменит тег на форматированную серию вида 1 серия, 1-2 серия, 1-3 серия, 1-4 серия.<br>2. В случае если поле не задано у источника, заменит теги на ваш текст</td>
                </tr><tr class="rcol-2col-body-tr-even">
                  <td width="50%">1. <b>[data_episode_type_3]{episode_type_3}[/data_episode_type_3]</b><br>2. <b>[nodata_episode_type_3]ваш текст[/nodata_episode_type_3]</b></td>
                  <td width="50%">1. Заменит тег на форматированную серию вида 1 серия, 1,2 серия, 1,2,3 серия, 1,2,3,4 серия.<br>2. В случае если поле не задано у источника, заменит теги на ваш текст</td>
                </tr><tr class="rcol-2col-body-tr-even">
                  <td width="50%">1. <b>[data_episode_type_4]{episode_type_4}[/data_episode_type_4]</b><br>2. <b>[nodata_episode_type_4]ваш текст[/nodata_episode_type_4]</b></td>
                  <td width="50%">1. Заменит тег на форматированную серию + 1 вида: если 1 серия - 1,2 серия, если 2 серия - 1,2,3 серия, если 5 серия - 4,5,6 серия.<br>2. В случае если поле не задано у источника, заменит теги на ваш текст</td>
                </tr>
                <tr class="rcol-2col-body-tr-even">
                  <td width="50%">1. <b>[data_episode_type_5]{episode_type_5}[/data_episode_type_5]</b><br>2. <b>[nodata_episode_type_5]ваш текст[/nodata_episode_type_5]</b></td>
                  <td width="50%">1. Заменит тег на форматированную серию + 1 вида 1,2 серия, 1,2,3 серия, 1,2,3,4,5 серия, 1-5,6,7 серия.<br>2. В случае если поле не задано у источника, заменит теги на ваш текст</td>
                </tr><tr class="rcol-2col-body-tr-even">
                  <td width="50%">1. <b>[data_season_type_1]{season_type_1}[/data_season_type_1]</b><br>2. <b>[nodata_season_type_1]ваш текст[/nodata_season_type_1]</b></td>
                  <td width="50%">1. Заменит тег на форматированный сезон вида 1 сезон, 2 сезон, 3 сезон.<br>2. В случае если поле не задано у источника, заменит теги на ваш текст</td>
                </tr><tr class="rcol-2col-body-tr-even">
                  <td width="50%">1. <b>[data_season_type_2]{season_type_2}[/data_season_type_2]</b><br>2. <b>[nodata_season_type_2]ваш текст[/nodata_season_type_2]</b></td>
                  <td width="50%">1. Заменит тег на форматированный сезон вида 1 сезон, 1-2 сезон, 1-3 сезон.<br>2. В случае если поле не задано у источника, заменит теги на ваш текст</td>
                </tr><tr class="rcol-2col-body-tr-even">
                  <td width="50%">1. <b>[data_season_type_3]{season_type_3}[/data_season_type_3]</b><br>2. <b>[nodata_season_type_3]ваш текст[/nodata_season_type_3]</b></td>
                  <td width="50%">1. Заменит тег на форматированный сезон вида 1 сезон, 1,2 сезон, 1,2,3 сезон.<br>2. В случае если поле не задано у источника, заменит теги на ваш текст</td>
                </tr>
          </tbody></table>
        </div>
      </div>
HTML;


?>
<div class="row">
	<div class="col-md-12">
		<div class="<?=($config['version_id']>=12)?"panel":"box"?>">
		    <div class="<?=($config['version_id']>=12)?"panel-heading":"box-header"?>">
				<ul class="nav nav-tabs <?=($config['version_id']>=12)?"nav-tabs-solid":"nav-tabs-left"?>">
					<li class="active">
						<a href="#main" data-toggle="tab">
							<i class="fa fa-home position-left"></i> 
							Заголовок и метатеги
						</a>
					</li>		

					<li>
						<a href="#xfields" data-toggle="tab">
							<i class="fa fa-tasks position-left"></i> 
							Дополнительные поля
						</a>
					</li>	

					<li>
						<a href="#cats" data-toggle="tab">
							<i class="fa fa-tasks position-left"></i> 
							Категории
						</a>
					</li>	

					<li>
						<a href="#tags" data-toggle="tab">
							<i class="fa fa-pencil-square-o position-left"></i>
							Теги
						</a>
					</li>
          <li>
            <a href="#serial" data-toggle="tab">
              <i class="fa fa-tv position-left"></i>
              Сериалы
            </a>
          </li> 	
          <li>
            <a href="#rebuild" data-toggle="tab">
              <i class="fa fa-code position-left"></i>
              Простановка
            </a>
          </li> 			
				</ul>
			</div>

			<form id="config">
	            <div class="box-content">
	                <div class="tab-content">  	                  
		                <div class="tab-pane active" id="main">
				<div class="panel-body">
					Общие настройки
				</div>
	                    	<table class="table table-normal">
							    <tbody>
									<?=$main?>
							    </tbody>
							</table>							
	                    </div>

	                    <div class="tab-pane" id="xfields">
	                    	<table class="table table-normal">
							    <tbody>
									<?=$xfields?>
							    </tbody>
							</table>							
	                    </div>

	                    <div class="tab-pane" id="cats">
	                    	<table class="table table-normal">
							    <tbody>
									<?=$cats?>
							    </tbody>
							</table>							
	                    </div>

                      <div class="tab-pane" id="serial">
                        
                        <?=$serial_tab ?>
                                  
                      </div>
                      

	                    <div class="tab-pane" id="tags">
	                    	<div style="padding: 25px;text-align: center;font-size: 14px">Список тегов для вывода информации в заголовок, метатеги и теги новости. Используйте на вкладке «Заголовок и метатеги».</div>
	                    	<table class="table table-normal">
							    <tbody>
									<?=$tags?>
							    </tbody>
							</table>							
	                    </div>

                      <div class="tab-pane" id="rebuild">
                        <div class="panel-body">
                          Простановка данных на уже существующих фильмах.<br>
                          <b>Внимание:</b> Перед простановкой пожалуйста заполните все предыдущие вкладки и сохраните. А так же настоятельно рекомендуем сделать бекап своей базы данных.<br>
                          Простановка будет происходить не зависимо от включения автодобавление и автообновления. Заполняться будут только выбраные вами категории и доп поля.
                        </div>
                        
                        <div class="panel-body">
                          <div class="progress">
                            <div id="progressbar" class="progress-bar progress-blue" style="width:0%;"><span></span></div>
                          </div>
                        </div>
                        
                        <div class="panel-body">
                          Общее количество новостей:&nbsp;<?=$row['count'];?>,&nbsp;обработано:&nbsp;<span class="text-danger"><span id="newscount"><?=$last;?></span></span>&nbsp;<span id="progress"></span>
                        </div>
                        
                        <div class="panel-footer">
                          <a id="button" class="btn btn-sm btn-black"><?if($last>0):?>Продолжить простановку<?else:?>Начать простановку<?endif;?></a>
                          <?if($last>0):?><a id="start_new" class="btn btn-blue">Начать заново</a><?endif;?>
                        </div>
                      </div>

	                </div>

	                <div class="<?=($config['version_id']>=12)?"panel-footer":"box-footer"?> padded">
						<input onclick="save_config(); return false;" class="btn <?=($config['version_id']>=12)?"bg-teal":"btn-green"?>" type="submit" value="Сохранить настройки">

						<input onclick="switch_sections(); return false" class="btn <?=($config['version_id']>=12)?"btn-bluebg-primary-600":"btn-blue"?>" style="float: right;" type="button" value="Ссылка в меню «Сторонние модули» (вкл/выкл)">
					</div>
	            </div>
	        </form>
        </div>
    </div>
</div>

<script type="text/javascript">
function save_config() {	
	$.post('<?=$config['admin_path']?>?mod=<?=$mod?>&action=config', $('#config').serialize(), function(data){ 
		data = JSON.parse(data);
		DLEalert( data.message, '<?=$__name?>' );
	});  
}

function switch_sections() {	
	$.get('<?=$config['admin_path']?>?mod=<?=$mod?>&action=sections', null, function(data){
		data = JSON.parse(data);
		DLEalert( data.message, '<?=$__name?>' );
	});  
}

$('.categoryselect').chosen({no_results_text: 'Ничего не найдено'});
</script>

<script>
var total = <?=$row['count'];?>;
var start_count = <?=$last;?>;

var proc = Math.round( (100 * start_count) / total );
if (proc>=100){
  proc = 100;
  $('#button').attr("disabled", "disabled");
}
$('#progressbar').css( "width", proc + '%' );

$(function() {
  $('#button').click(function() {
    $("#progress").ajaxError(function(event, request, settings){
      $(this).html('<?=$lang['nl_error'];?>');
      $('#button').attr("disabled", false);
    });
    $('#progress').html('<?=$lang['rebuild_status'];?>');
    $('#button').attr("disabled", "disabled");
    $('#button').val("<?=$lang['rebuild_forw'];?>");
    senden(start_count);
    return false;
  });
  
  $('#start_new').click(function() {
    $('#newscount').html(0);
    $('#progressbar').css("width", '0%');
    $('#start_new').hide();
    $("#progress").ajaxError(function(event, request, settings){
      $(this).html('<?=$lang['nl_error'];?>');
      $('#button').attr("disabled", false);
    });
    $('#progress').html('<?=$lang['rebuild_status'];?>');
    $('#button').attr("disabled", "disabled");
    $('#button').val("<?=$lang['rebuild_forw'];?>");
    senden(0,1);
    return false;
  });
});

function senden(startfrom, start_new=0){
  $.post("engine/alloha/ajax.php", { startfrom: startfrom, start_new: start_new },
    function(data){
      if (data) {
        if (data.status == "ok") {
          $('#newscount').html(data.rebuildcount);
          var proc = Math.round( (100 * data.rebuildcount) / total );
          if ( proc > 100 ) proc = 100;
          $('#progressbar').css( "width", proc + '%' );
              if (data.rebuildcount >= total) {
                 $('#progress').html('<?=$lang['rebuild_status_ok'];?>');
              }
              else { 
                 senden(data.rebuildcount);
              }
        }
      }
    }, "json").fail(function() {
      $('#progress').html('<?=$lang['nl_error'];?>');
      $('#button').attr("disabled", false);
    });
  return false;
}
</script>

<?php echofooter(); ?>
  