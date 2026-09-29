<?php
/*
Template Name: Thanks Download Page
*/

/* リファラーチェック用JSをwp_headに追加（外部からの直接アクセスを防止） */
function thanks_download_referrer_check() {
?>
<script type="text/javascript">
	var ref = document.referrer;
	var ptn = "^https?://" + window.location.hostname;
	var rExp = new RegExp(ptn, "i");
	if (ref.length === 0 || !ref.match(rExp)) { location.href = "//ecnow.jp/"; }
</script>
<?php
}
add_action('wp_head', 'thanks_download_referrer_check');
?>

<?php get_header(); ?>

<div class="contact_box">
    <div class="article_title"><h1>資料ダウンロードのお申し込み<br class="pc-only">ありがとうございます。</h1></div>
    <p>このたびは資料ダウンロードをお申し込みいただき、ありがとうございます。<br class="pc-only">以下のリストから資料をダウンロードいただけます。</p>

    <div class="download-list-tile">
        <div class="download-list-tiles">
            <img src="https://ecnow.jp/wp-content/uploads/2023/09/売り上げ向上チェックリスト-1.png" alt="ECサイト売り上げ向上チェックリスト">
            <p>ECサイト売り上げ向上<br>チェックリスト</p>
            <a href="https://ecnow.jp/wp-content/uploads/dlm_uploads/2023/09/ECNOW_%E5%A3%B2%E3%82%8A%E4%B8%8A%E3%81%92%E5%90%91%E4%B8%8A%E3%83%81%E3%82%A7%E3%83%83%E3%82%AF%E3%83%AA%E3%82%B9%E3%83%88-.pdf" download>ダウンロード</a>
        </div>
        <div class="download-list-tiles">
            <img src="https://ecnow.jp/wp-content/uploads/2022/07/download-01-netshop_check_list.jpg" alt="ネットショップ開店チェックリスト">
            <p>ネットショップ開店<br>チェックリスト</p>
            <a href="https://ecnow.jp/wp-content/uploads/2023/05/ECNOW_01_%E9%96%8B%E5%BA%97%E3%83%81%E3%82%A7%E3%83%83%E3%82%AF%E3%83%AA%E3%82%B9%E3%83%88-1.pdf" download>ダウンロード</a>
        </div>
    </div>
</div>

<style>
	.article_title h1 {
		font-feature-settings: "palt";
	}
	@media screen and (max-width: 768px) {
		.main {
			height: auto !important;
		}
		.pc-only {
			display: none;
		}
		p {
			font-feature-settings: "palt";
		}
	}
</style>

<?php get_footer(); ?>
