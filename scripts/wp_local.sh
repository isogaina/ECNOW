#!/bin/bash
# ローカル検証用WordPressへのWP-CLIラッパー。
#
# 2026-09-29に、素の `wp` が wp-cli.yml の ssh: 設定を拾って本番のDBを書き換える事故を起こした。
# 以降、ローカルを触るときは必ずこのスクリプトを通す。
#   - --path をこちらで固定するので、向き先を間違えようがない
#   - WP_CLI_CONFIG_PATH を空にして wp-cli.yml を読ませない
#   - 本番へは絶対に接続しない（--ssh を渡されても弾く）
#
# 使い方:
#   ./scripts/wp_local.sh option get siteurl
#   ./scripts/wp_local.sh post list --post_type=post --posts_per_page=5
#   ./scripts/wp_local.sh server            # http://localhost:8080 で起動

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
WP_DIR="$PROJECT_DIR/local/wp"

if [ ! -f "$WP_DIR/wp-config.php" ]; then
    echo "Error: ローカルのWordPressが $WP_DIR にありません。" >&2
    echo "       local/README.md の手順で作り直してください。" >&2
    exit 1
fi

# 本番に飛ぶ引数が混ざっていたら止める
for arg in "$@"; do
    case "$arg" in
        --ssh=*|--http=*|--url=*://ecnow.jp*)
            echo "Error: このスクリプトはローカル専用です。本番向けの引数は使えません: $arg" >&2
            exit 1
            ;;
    esac
done

# MariaDB のクライアントにパスを通す（brew版は /opt/homebrew 配下）
if [ -d /opt/homebrew/opt/mariadb/bin ]; then
    export PATH="/opt/homebrew/opt/mariadb/bin:$PATH"
fi

# wp-cli.yml を読ませない（事故の直接原因だったため）
export WP_CLI_CONFIG_PATH=/dev/null

# PHPのDeprecated警告が標準出力に混ざるので取り除く
wp --path="$WP_DIR" "$@" 2>&1 \
  | sed -e '/^\(PHP \)\?Deprecated:/d' -e '/phar:\/\/\/usr\/local\/bin\/wp/d' \
  | awk 'NR==1 && $0=="" {next} {print}'
