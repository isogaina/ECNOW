<?php
/**
 * CONTACT_LP フォーム（投稿ID 2732）のメール設定を修正する。
 *
 *  1. お問い合わせ項目（menu-934）が本文に無く、選択内容が届かない
 *  2. 件名がフォームに存在しない [your-subject] を参照していて空欄になる
 *  4. 管理者宛（Mail 1）の本文が顧客向け自動返信の文面になっている
 *
 * 日本語は wp db query を経由すると欠落するため eval-file で流し込む。
 */

// 48 = CONTACT（本番の /contact/ で使用）、2732 = CONTACT_LP（複製・非公開ページ2722で使用）
// 2つは項目が同一なので、同じ本文を当てて内容を揃える。
foreach ([48, 2732] as $form_id) {

$mail1 = get_post_meta($form_id, '_mail', true);
$mail2 = get_post_meta($form_id, '_mail_2', true);

if (!is_array($mail1) || !is_array($mail2)) {
    echo "ERROR: {$form_id} のメール設定を読み込めませんでした\n";
    continue;
}

$mail1['subject'] = '[_site_title]【お問い合わせ】[menu-934]／[your-name] 様';

$mail1['body'] = <<<'EOT'
ECNOWのお問い合わせフォームから、新しいお問い合わせが届きました。

━━━ お問い合わせ内容 ━━━━━━━━━━━━━━━━

お名前：　[your-name]
メールアドレス：　[your-email]
お電話番号：　[your-tel]
お問い合わせ項目：　[menu-934]

お問い合わせ内容：
[your-message]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

送信元ページ：[_url]
送信日時：[_date] [_time]

※このメールは社内向けの通知です。
　お客様へは別途、自動返信メールをお送りしています。
EOT;

$mail2['body'] = <<<'EOT'
[your-name] 様

この度はEC NOWにお問い合わせをいただき、誠にありがとうございます。
以下の内容でお問い合わせを受け付けいたしました。
改めて、担当よりご連絡をさせていただきます。

なお、営業時間は平日9時〜18時となっております。
時間外のお問い合わせは翌営業日にご連絡差し上げます。

━━━ お問い合わせ内容 ━━━━━━━

お名前：　[your-name]
メールアドレス：　[your-email]
お電話番号：　[your-tel]
お問い合わせ項目：　[menu-934]

お問い合わせ内容：
[your-message]

━━━━━━━━━━━━━━━━━━━

そのほか、「ECサイトの構築」や「IT導入補助金の活用」についてのご質問やご不明点、ご依頼などございましたら、
info@jpholic.jpよりお問い合わせいただくか、以下よりWEBミーティングも承っております。

■WEBミーティング予約する

https://timerex.net/s/jpholic_team/e4d3e063

貴社ビジネスのお役に立てれば幸いです。

-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

JPholic株式会社 EC NOW事業部

〒141-0033 東京都品川区西品川1-1-1住友不動産大崎ガーデンタワー9F

E-mail：info@jpholic.jp

TEL：050-3570-0020

-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
EOT;

update_post_meta($form_id, '_mail', $mail1);
update_post_meta($form_id, '_mail_2', $mail2);

$after1 = get_post_meta($form_id, '_mail', true);
$after2 = get_post_meta($form_id, '_mail_2', true);

echo "===== フォーム {$form_id} =====\n";
echo "Mail1 件名        : " . $after1['subject'] . "\n";
echo "Mail1 宛先        : " . $after1['recipient'] . "\n";
echo "Mail1 お問合せ項目 : " . (strpos($after1['body'], '[menu-934]') !== false ? 'OK' : 'NG') . "\n";
echo "Mail1 空件名の解消 : " . (strpos($after1['subject'], 'your-subject') !== false ? 'NG' : 'OK') . "\n";
echo "Mail2 お問合せ項目 : " . (strpos($after2['body'], '[menu-934]') !== false ? 'OK' : 'NG') . "\n";
echo "Mail2 宛先        : " . $after2['recipient'] . "\n";

}
