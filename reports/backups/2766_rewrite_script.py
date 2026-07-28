#!/usr/bin/env python3
"""ID:2766 rewrite - targeted block replacements"""
import sys

SP = "/private/tmp/claude-501/-Users-nana-works-JPholic-ECNOW/e10e0d7f-cd7a-40a7-b877-1fdebe186b77/scratchpad"
s = open(f"{SP}/2766_current.html", encoding="utf-8").read()
orig_len = len(s)
applied = []


def rep(label, old, new):
    global s
    if old not in s:
        print(f"!! NOT FOUND: {label}", file=sys.stderr)
        sys.exit(1)
    if s.count(old) != 1:
        print(f"!! NOT UNIQUE ({s.count(old)}): {label}", file=sys.stderr)
        sys.exit(1)
    s = s.replace(old, new)
    applied.append(label)


# 1. lead paragraph of fee section
OLD1 = """<p>代引きを利用する場合、配送会社に代金の回収を代行してもらうための手数料が生じます。\
代引き手数料は、購入者が負担することが一般的です。\
代引き決済サービスを提供する主な配送会社の手数料を紹介します（2023年9月執筆時点）。</p>"""

NEW1 = """<p>代引きを利用する場合、配送会社に代金の回収を代行してもらうための手数料が生じます。\
代引き手数料は、購入者が負担することが一般的です。\
代引き決済サービスを提供する主な配送会社の手数料を紹介します（2026年7月時点）。</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>なお、代引き手数料は改定されることがあります。\
実際に導入・利用する際は、各社の公式サイトで最新の料金をご確認ください。</p>"""

rep("手数料リード文", OLD1, NEW1)


# 2. comparison table
OLD2 = """<figure class="wp-block-table"><table><thead><tr><th>配送会社名</th>\
<th>代引き手数料</th></tr></thead><tbody>\
<tr><td>ヤマト運輸（宅急便コレクト）</td><td>330円〜440円</td></tr>\
<tr><td>佐川急便（e-コレクト）</td><td>330円〜430円</td></tr>\
<tr><td>日本郵便（代金引換まとめ送金サービス）</td><td>330円〜550円</td></tr>\
<tr><td>西濃運輸（カンガルー代引サービス）</td><td>330円〜550円</td></tr>\
</tbody></table></figure>"""

NEW2 = """<figure class="wp-block-table"><table><thead><tr><th>配送会社名</th>\
<th>代引き手数料（税込）</th></tr></thead><tbody>\
<tr><td>ヤマト運輸（宅急便コレクト）</td><td>330円〜1,100円</td></tr>\
<tr><td>佐川急便（e-コレクト）</td><td>330円〜2,200円</td></tr>\
<tr><td>日本郵便（代金引換まとめ送金サービス）</td><td>330円〜1,430円<br>※別途送金手数料が必要</td></tr>\
<tr><td>西濃運輸（カンガルー代引サービス）</td><td>料金非公開（要問い合わせ）</td></tr>\
</tbody></table></figure>"""

rep("手数料比較表", OLD2, NEW2)


# 3. Yamato fees
OLD3 = """<ul><!-- wp:list-item -->
<li>代金引換額 9,999円までの場合： 決済手数料 330円（税込）</li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li>代金引換額 29,999円までの場合： 決済手数料 440円（税込）</li>
<!-- /wp:list-item --></ul>
<!-- /wp:list -->"""

NEW3 = """<ul><!-- wp:list-item -->
<li>代金引換額 1円〜9,999円： 決済手数料 330円（税込）</li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li>代金引換額 10,000円〜29,999円： 決済手数料 440円（税込）</li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li>代金引換額 30,000円〜99,999円： 決済手数料 660円（税込）</li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li>代金引換額 100,000円〜300,000円： 決済手数料 1,100円（税込）</li>
<!-- /wp:list-item --></ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p>また、代金引換額が55,000円以上の場合は、上記に加えて印紙代相当額220円（税込）が必要です。</p>
<!-- /wp:paragraph -->"""

rep("ヤマト手数料リスト", OLD3, NEW3)


# 4. Sagawa fees
OLD4 = """<ul><!-- wp:list-item -->
<li>代引き金額 1万円以下の場合： 代引き手数料 330円（税込）</li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li>代引き金額 3万円以下の場合： 代引き手数料 430円（税込）</li>
<!-- /wp:list-item --></ul>
<!-- /wp:list -->"""

NEW4 = """<ul><!-- wp:list-item -->
<li>代引き金額 1万円以下： 代引き手数料 330円（税込）</li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li>代引き金額 3万円以下： 代引き手数料 440円（税込）</li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li>代引き金額 10万円以下： 代引き手数料 660円（税込）</li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li>代引き金額 30万円以下： 代引き手数料 1,100円（税込）</li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li>代引き金額 50万円以下： 代引き手数料 2,200円（税込）</li>
<!-- /wp:list-item --></ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p>50万円を超える高額帯にも料金設定があり、代引金額の上限は500万円です。</p>
<!-- /wp:paragraph -->"""

rep("佐川手数料リスト", OLD4, NEW4)


# 5. Japan Post fees
OLD5 = """<ul><!-- wp:list-item -->
<li>商品代金（引換金額）3万円まで： 代引き手数料 330円（税込）</li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li>商品代金（引換金額）10万円まで： 代引き手数料 550円（税込）</li>
<!-- /wp:list-item --></ul>
<!-- /wp:list -->"""

NEW5 = """<ul><!-- wp:list-item -->
<li>引換金額 3万円まで： 代引き手数料 330円（税込）</li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li>引換金額 10万円まで： 代引き手数料 550円（税込）</li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li>引換金額 20万円まで： 代引き手数料 880円（税込）</li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li>引換金額 30万円まで： 代引き手数料 990円（税込）</li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li>引換金額 50万円まで： 代引き手数料 1,430円（税込／セキュリティサービス利用時）</li>
<!-- /wp:list-item --></ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p>日本郵便の場合、上記の代引き手数料とは別に、\
売上金を振り込んでもらうための<strong>送金手数料</strong>が必要です。\
ゆうちょ銀行あては一律203円（税込）、\
その他の金融機関あては送金額3万円未満で220円、3万円以上で440円（いずれも税込）です。\
また、引換金額から消費税を差し引いた額が5万円以上の場合は、印紙代200円がかかります。</p>
<!-- /wp:paragraph -->"""

rep("日本郵便手数料リスト", OLD5, NEW5)


# 6. Japan Post link (old URL 301-redirects)
rep(
    "日本郵便リンク",
    "https://www.post.japanpost.jp/service/fuka_service/daibiki/matome.html",
    "https://www.post.japanpost.jp/service/send/domestic/option/daibiki/matome.html",
)


# 7. Seino - fees are not published
OLD7 = """<!-- wp:paragraph -->
<p>こちらも購入者から回収した商品代金に応じて手数料が設定されています。</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul><!-- wp:list-item -->
<li>商品代金（税込）3万円まで： 代引き手数料 330円（税込）</li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li>商品代金（税込）10万円まで： 代引き手数料 550円（税込）</li>
<!-- /wp:list-item --></ul>
<!-- /wp:list -->"""

NEW7 = """<!-- wp:paragraph -->
<p>こちらも購入者から回収した商品代金に応じて手数料が設定されていますが、\
<strong>西濃運輸は公式サイトで代引き手数料の料金表を公開していません</strong>。\
利用を検討する場合は、最寄りの営業所へ問い合わせて見積もりを取る必要があります。</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>なお、商品代金が50,000円（税別）以上で必要になる収入印紙代は、\
西濃運輸が立て替えて一括納税し、回収代金から差し引いて振り込まれる仕組みです。</p>
<!-- /wp:paragraph -->"""

rep("西濃手数料リスト", OLD7, NEW7)


# 8 + 9. new sections inserted before the "purchaser pros/cons" H2
COLLECT = """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">「コレクト」とは？代引き・着払いとの違い</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>代引きについて調べていると「コレクト」という言葉を目にすることがあります。\
これは配送会社が自社の代金引換サービスにつけている<strong>サービス名</strong>であり、\
代引きと別の仕組みではありません。</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul><!-- wp:list-item -->
<li>ヤマト運輸の代金引換サービス ＝ <strong>宅急便コレクト</strong></li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li>佐川急便の代金引換サービス ＝ <strong>e-コレクト</strong></li>
<!-- /wp:list-item --></ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p>つまり<strong>「コレクトと代引きの違い」は、呼び方の違いだけ</strong>です。\
一方で<strong>「コレクトと着払いの違い」は、そのまま代引きと着払いの違い</strong>にあたります。\
コレクト（＝代引き）では商品代金・送料・代引き手数料をまとめて支払うのに対し、\
着払いでは送料のみを支払います。</p>
<!-- /wp:paragraph -->

"""

PAYPAY = """<!-- wp:heading -->
<h2 class="wp-block-heading">代引きでPayPayなどのQRコード決済は使える？</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>「代引きの支払いにPayPayを使いたい」という疑問はよく聞かれます。結論から言うと、\
<strong>商品代金の代引き（代金引換）にQRコード決済は使えません</strong>。\
ただし、同じ配達員へのお金の支払いでも「送料（運賃）」であればQRコード決済が使えるため、\
この2つが混同されやすくなっています。</p>
<!-- /wp:paragraph -->

<!-- wp:table -->
<figure class="wp-block-table"><table><thead><tr><th>支払う対象</th>\
<th>QRコード決済</th><th>主な支払い方法</th></tr></thead><tbody>\
<tr><td>商品代金（代引き・コレクト）</td><td>使えない</td>\
<td>現金・クレジットカード・電子マネー</td></tr>\
<tr><td>送料（着払い運賃・元払い運賃）</td><td>使える</td>\
<td>現金・電子マネー・QRコード決済</td></tr>\
</tbody></table></figure>
<!-- /wp:table -->

<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">商品代金の代引きにQRコード決済は使えない</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>ヤマト運輸の「宅急便コレクト」、佐川急便の「e-コレクト」はいずれも、\
商品代金の代金引換にPayPay・楽天ペイ・d払いなどのQRコード決済を利用できません。\
ヤマト運輸は公式FAQで、QRコード決済は\
「宅急便コレクト（代引き）のお支払いにはご利用いただけません」と明記しています。</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>代引きで使える支払い方法は、一般的に\
<strong>現金・クレジットカード・電子マネー</strong>です。\
ただし、どの方法に対応しているかはネットショップや配送会社によって異なるため、\
購入前に注文画面で確認しておくと安心です。</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">送料（運賃）の支払いにはQRコード決済が使える</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>一方、荷物の運賃を支払う場面ではQRコード決済が利用できます。\
ヤマト運輸では、PayPay・楽天ペイ・d払い・au PAY・メルペイ・にゃんPayに対応しています。\
佐川急便でも、着払い運賃や元払いの送料の支払いにQRコード決済を使えます。</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>「着払いの荷物はPayPayで払えたのに、代引きでは断られた」というケースは、\
この違いによるものです。\
<strong>支払う対象が「商品代金」なのか「送料」なのかで、使える決済手段が変わる</strong>\
と覚えておくとよいでしょう。</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>※対応状況は変更される場合があります。\
最新の情報は各配送会社の公式サイトでご確認ください（2026年7月時点）。</p>
<!-- /wp:paragraph -->

"""

ANCHOR = """<!-- wp:heading -->
<h2 class="wp-block-heading">購入者が代引きを利用するメリット・デメリット</h2>"""

rep("コレクト解説＋PayPayセクション挿入", ANCHOR, COLLECT + PAYPAY + ANCHOR)


# 10. Q&A PayPay entry
OLD10 = """A．配送サービス各社（ヤマト運輸・佐川急便・日本郵便）は、\
<strong>代引き決済のPayPay支払いに対応していません</strong>（2023年9月執筆時点）。\
ただし、その他の電子マネー決済に対応している場合があるため、購入するサイトで事前に確認が必要です。"""

NEW10 = """A．配送サービス各社は、\
<strong>商品代金の代引き決済でのPayPay支払いに対応していません</strong>（2026年7月時点）。\
ただし、着払い運賃など「送料」の支払いにはPayPayを利用できます。\
詳しくは「代引きでPayPayなどのQRコード決済は使える？」をご覧ください。"""

rep("Q&A PayPay項目", OLD10, NEW10)


open(f"{SP}/2766_rewritten.html", "w", encoding="utf-8").write(s)
print(f"適用: {len(applied)}件")
for a in applied:
    print(f"  OK {a}")
print(f"\n文字数: {orig_len:,} -> {len(s):,} ({len(s)-orig_len:+,})")
