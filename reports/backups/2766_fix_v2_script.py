#!/usr/bin/env python3
"""ID:2766 二次修正 - 見出しの結論化 と 発リンクの追加・改善"""
import sys

SP = "/private/tmp/claude-501/-Users-nana-works-JPholic-ECNOW/e10e0d7f-cd7a-40a7-b877-1fdebe186b77/scratchpad"
s = open(f"{SP}/2766_rewritten.html", encoding="utf-8").read()
orig = len(s)
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


# ── 1. 見出しを結論形に ───────────────────────────────
rep("H2 PayPay見出し",
    '<h2 class="wp-block-heading">代引きでPayPayなどのQRコード決済は使える？</h2>',
    '<h2 class="wp-block-heading">代引きにPayPayは使えない（送料の支払いには使える）</h2>')

rep("H3 コレクト見出し",
    '<h3 class="wp-block-heading">「コレクト」とは？代引き・着払いとの違い</h3>',
    '<h3 class="wp-block-heading">「コレクト」は配送会社が付けた代引きのサービス名</h3>')

# 見出し変更にともない、Q&A内の参照文言も合わせる
rep("Q&A内の参照文言",
    '詳しくは「代引きでPayPayなどのQRコード決済は使える？」をご覧ください。',
    '詳しくは「代引きにPayPayは使えない（送料の支払いには使える）」をご覧ください。')


# ── 2. 手数料セクションのアンカーテキスト改善 ──────────────
LINKS = [
    ("ヤマト",
     '<p>ヤマト運輸の代引き手数料情報は<a href="https://faq-biz.kuronekoyamato.co.jp/app/answers/detail/a_id/4313/~/%E4%BB%A3%E9%87%91%E5%BC%95%E6%8F%9B%EF%BC%88%E5%AE%85%E6%80%A5%E4%BE%BF%E3%82%B3%E3%83%AC%E3%82%AF%E3%83%88%EF%BC%89%E3%81%AE%E6%89%8B%E6%95%B0%E6%96%99%E3%82%92%E6%95%99%E3%81%88%E3%81%A6%E3%81%8F%E3%81%A0%E3%81%95%E3%81%84%E3%80%82">こちら</a></p>',
     '<p>参考：<a href="https://faq-biz.kuronekoyamato.co.jp/app/answers/detail/a_id/4313/" target="_blank" rel="noopener">代引き（宅急便コレクト）の手数料｜ヤマト運輸 公式FAQ</a></p>'),
    ("佐川",
     '<p>佐川急便の代引き手数料情報は<a href="https://www.sagawa-exp.co.jp/service/e-collect/">こちら</a></p>',
     '<p>参考：<a href="https://www.e-collect.jp/cost/index.html" target="_blank" rel="noopener">e-コレクトのサービス料金｜SGシステム 公式サイト</a></p>'),
    ("日本郵便",
     '<p>日本郵政の代引き手数料情報は<a href="https://www.post.japanpost.jp/service/send/domestic/option/daibiki/matome.html">こちら</a></p>',
     '<p>参考：<a href="https://www.post.japanpost.jp/service/send/domestic/option/daibiki/matome.html" target="_blank" rel="noopener">代金引換まとめ送金サービス｜日本郵便 公式サイト</a></p>'),
]
for label, old, new in LINKS:
    rep(f"アンカーテキスト改善（{label}）", old, new)

# 西濃はリンクURLの末尾が不明なため、前方一致で処理
i = s.find('<p>西濃運輸の代引き手数料情報は<a href="')
if i == -1:
    print("!! NOT FOUND: 西濃リンク", file=sys.stderr)
    sys.exit(1)
j = s.find("</p>", i) + 4
s = s[:i] + ('<p>参考：<a href="https://www.seino.co.jp/seino/service/domestic/delivery-collect/"'
             ' target="_blank" rel="noopener">カンガルー代引サービス｜西濃運輸 公式サイト</a></p>') + s[j:]
applied.append("アンカーテキスト改善（西濃）")


# ── 3. 発送方法「1. 配送会社と契約する」に発リンクを追加 ────────
OLD_STEP1 = """<p>代引きサービスを提供している配送業者とサービスの利用契約を結びます。\
<strong>配送業者によって手数料や振込サイクルが異なる</strong>\
ため、自社の条件に合うか事前に比較・検討しましょう。</p>
<!-- /wp:paragraph -->"""

NEW_STEP1 = """<p>代引きサービスを提供している配送業者とサービスの利用契約を結びます。\
<strong>配送業者によって手数料や振込サイクルが異なる</strong>\
ため、自社の条件に合うか事前に比較・検討しましょう。</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>各社の代引きサービスの詳細・申し込み方法は、以下の公式ページで確認できます。</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul><!-- wp:list-item -->
<li><a href="https://faq-biz.kuronekoyamato.co.jp/app/answers/detail/a_id/4315/" \
target="_blank" rel="noopener">宅急便コレクトの契約方法｜ヤマト運輸</a></li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li><a href="https://www.sagawa-exp.co.jp/service/e-collect/" \
target="_blank" rel="noopener">e-コレクト｜佐川急便</a></li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li><a href="https://www.post.japanpost.jp/service/send/domestic/option/daibiki/matome.html" \
target="_blank" rel="noopener">代金引換まとめ送金サービス｜日本郵便</a></li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li><a href="https://www.seino.co.jp/seino/service/domestic/delivery-collect/" \
target="_blank" rel="noopener">カンガルー代引サービス｜西濃運輸</a></li>
<!-- /wp:list-item --></ul>
<!-- /wp:list -->"""

rep("発送方法ステップ1に発リンク追加", OLD_STEP1, NEW_STEP1)


open(f"{SP}/2766_v2.html", "w", encoding="utf-8").write(s)
print(f"適用: {len(applied)}件")
for a in applied:
    print(f"  OK {a}")
print(f"\n文字数: {orig:,} -> {len(s):,} ({len(s)-orig:+,})")
