<?php
/**
 * 電話番号欄に「半角でご入力ください」の注記を出す。
 *
 * CF7 の tel バリデーションは全角数字を弾き、「電話番号に間違いがあります。」
 * とだけ表示するため、入力者が理由を分からず離脱しうる。
 *
 * テーマ側の CSS に依存せず /contact/ と LP の両方で同じ見た目にしたいので、
 * span に inline style を直接書いている。
 */

$hint = '<span style="display:block;margin-top:.45em;font-size:12px;color:#8a94a6;line-height:1.6;">半角数字でご入力ください（例：03-1234-5678）</span>';

$before = '<dd>[tel your-tel]</dd>';
$after  = '<dd>[tel your-tel]' . $hint . '</dd>';

foreach ([48, 2732] as $form_id) {
    $form = get_post_meta($form_id, '_form', true);

    if (!is_string($form) || $form === '') {
        echo "{$form_id}: フォーム定義を読み込めませんでした\n";
        continue;
    }
    if (strpos($form, '半角数字でご入力ください') !== false) {
        echo "{$form_id}: 既に注記があります（スキップ）\n";
        continue;
    }
    if (strpos($form, $before) === false) {
        echo "{$form_id}: 電話番号欄の記述が想定と違うため中止しました\n";
        continue;
    }

    update_post_meta($form_id, '_form', str_replace($before, $after, $form));

    // 差し替え後もフォームとして壊れていないか確認する
    wpcf7_contact_form(null); // キャッシュ回避
    $f = WPCF7_ContactForm::get_instance($form_id);
    $names = [];
    foreach ($f->scan_form_tags() as $t) {
        if ($t->name) $names[] = $t->name;
    }
    $names = array_values(array_unique($names));

    echo "{$form_id}: 注記を追加しました / 項目 = " . implode(', ', $names) . "\n";
}
