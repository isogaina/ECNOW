#!/bin/bash
# WP-CLI wrapper for post operations
# Usage:
#   wp_post.sh get <post_id>          - Get post content
#   wp_post.sh list [count]           - List recent posts
#   wp_post.sh create <title> <file>  - Create draft from file
#   wp_post.sh update <post_id> <file> - Update post content from file
#   wp_post.sh set-title <post_id> <file> - Set post_title from the file's 1st line
#   wp_post.sh publish <post_id>      - Publish a draft
#   wp_post.sh search <keyword>       - Search posts

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

if [ -f "$PROJECT_DIR/.env" ]; then
    export $(grep -v '^#' "$PROJECT_DIR/.env" | xargs)
fi

# ローカルの wp (phar) が PHP の Deprecated 警告を「標準出力」に出すため、
# そのままだと post_content として取り込んだ内容の先頭に警告文が混入する。
# 出力から警告行と、その結果生じる先頭の空行を取り除く。
strip_wp_noise() {
    sed -e '/^\(PHP \)\?Deprecated:/d' \
        -e '/phar:\/\/\/usr\/local\/bin\/wp/d' \
      | awk 'NR==1 && $0=="" {next} {print}'
}

wp_cmd() {
    if [ -n "${WP_SSH:-}" ]; then
        wp --ssh="$WP_SSH" "$@" | strip_wp_noise
    elif [ -n "${WP_PATH:-}" ]; then
        wp --path="$WP_PATH" "$@" | strip_wp_noise
    else
        echo "Error: Set WP_SSH or WP_PATH in .env" >&2
        exit 1
    fi
}

# WP_SSH 使用時、wp はサーバー側で動くのでローカルのファイルパスを読めない。
# ローカルファイルをサーバーの /tmp に転送し、そのリモートパスを返す。
#
# 注意: stage_file は $(...) の中から呼ばれるためサブシェルで動く。
# 転送済みパスはローカルの STAGE_LOG に記録し、メインシェル側の EXIT トラップで削除する
# （トラップを stage_file 内に置くとサブシェル終了時に発火し、wp 実行前にファイルが消える）。
if [ -n "${WP_SSH:-}" ]; then
    # WP_SSH 形式: user@host:port/path
    SSH_HOST="${WP_SSH%%:*}"
    _rest="${WP_SSH#*:}"
    SSH_PORT="${_rest%%/*}"
    STAGE_LOG="$(mktemp)"

    cleanup_remote_tmp() {
        if [ -s "$STAGE_LOG" ]; then
            ssh -p "$SSH_PORT" "$SSH_HOST" "rm -rf $(tr '\n' ' ' < "$STAGE_LOG")" 2>/dev/null || true
        fi
        rm -f "$STAGE_LOG"
    }
    trap cleanup_remote_tmp EXIT
fi

stage_file() {
    local local_path="$1"
    if [ -z "${WP_SSH:-}" ]; then
        echo "$local_path"
        return
    fi
    if [ ! -f "$local_path" ]; then
        echo "Error: file not found: $local_path" >&2
        exit 1
    fi
    # media import はアップロード先のファイル名に転送元のファイル名をそのまま使うため、
    # 一意化は「ディレクトリ名」側で行い、ファイル名自体は元のまま保つ。
    local remote_dir="/tmp/wp_post_$$"
    local remote_path="$remote_dir/$(basename "$local_path")"
    ssh -p "$SSH_PORT" "$SSH_HOST" "mkdir -p $remote_dir" 2>/dev/null
    scp -P "$SSH_PORT" -q "$local_path" "$SSH_HOST:$remote_path" || {
        echo "Error: failed to copy $local_path to server" >&2
        exit 1
    }
    echo "$remote_dir" >> "$STAGE_LOG"
    echo "$remote_path"
}

case "${1:-help}" in
    get)
        post_id="$2"
        wp_cmd post get "$post_id" --format=json --fields=ID,post_title,post_content,post_status,post_date,post_name
        ;;
    list)
        count="${2:-20}"
        wp_cmd post list --post_type=post --format=table --fields=ID,post_title,post_status,post_date --posts_per_page="$count"
        ;;
    create)
        title="$2"
        content_file="$(stage_file "$3")"
        wp_cmd post create "$content_file" \
            --post_title="$title" \
            --post_status=draft \
            --post_type=post \
            --porcelain
        ;;
    update)
        post_id="$2"
        content_file="$(stage_file "$3")"
        wp_cmd post update "$post_id" "$content_file" --porcelain
        ;;
    set-title)
        # 本番のタイトルは post_title から出力される（AIOSEO のタイトル欄は空でフォールバック）。
        # 引数の取り違えで別記事を書き換えないよう、更新後のタイトルを表示して終わる。
        post_id="$2"
        title_file="$3"
        [ -f "$title_file" ] || { echo "Error: file not found: $title_file" >&2; exit 1; }
        new_title="$(head -1 "$title_file")"
        wp_cmd post update "$post_id" --post_title="$new_title" --porcelain >/dev/null
        wp_cmd post get "$post_id" --field=post_title
        ;;
    publish)
        post_id="$2"
        wp_cmd post update "$post_id" --post_status=publish --porcelain
        ;;
    search)
        keyword="$2"
        wp_cmd post list --post_type=post --format=table \
            --fields=ID,post_title,post_status,post_date \
            --s="$keyword"
        ;;
    get-content)
        post_id="$2"
        wp_cmd post get "$post_id" --field=post_content
        ;;
    get-meta)
        post_id="$2"
        wp_cmd post meta list "$post_id" --format=table
        ;;
    media)
        # ローカル画像をメディアライブラリに登録し、添付ID を返す
        media_file="$(stage_file "$2")"
        alt_text="${3:-}"
        attach_id="$(wp_cmd media import "$media_file" --title="$(basename "${2%.*}")" --porcelain)"
        if [ -n "$alt_text" ]; then
            wp_cmd post meta update "$attach_id" _wp_attachment_image_alt "$alt_text" >/dev/null
        fi
        echo "$attach_id"
        ;;
    media-url)
        wp_cmd post get "$2" --field=guid
        ;;
    set-desc)
        # メタディスクリプションは All in One SEO の wp_aioseo_posts.description で管理されている。
        # wp db query はシェル/SSH を経由する間に日本語が欠落するため、
        # PHP ファイルごと転送して eval-file で $wpdb->update() を実行する。
        post_id="$2"
        desc_file="$3"
        [ -f "$desc_file" ] || { echo "Error: file not found: $desc_file" >&2; exit 1; }
        php_local="$(mktemp -t setdesc).php"
        {
            echo '<?php'
            echo 'global $wpdb;'
            echo "\$post_id = $post_id;"
            printf '$desc = <<<\047EOT\047\n'
            cat "$desc_file"
            printf '\nEOT;\n'
            cat <<'PHPEOF'
$desc = trim($desc);
$table = $wpdb->prefix . 'aioseo_posts';
$exists = $wpdb->get_var($wpdb->prepare("SELECT id FROM $table WHERE post_id = %d", $post_id));
if ($exists) {
    $wpdb->update($table, ['description' => $desc, 'updated' => current_time('mysql')], ['post_id' => $post_id]);
} else {
    $wpdb->insert($table, ['post_id' => $post_id, 'description' => $desc, 'created' => current_time('mysql'), 'updated' => current_time('mysql')]);
}
echo $wpdb->get_var($wpdb->prepare("SELECT description FROM $table WHERE post_id = %d", $post_id)) . "\n";
PHPEOF
        } > "$php_local"
        php_remote="$(stage_file "$php_local")"
        wp_cmd eval-file "$php_remote"
        rm -f "$php_local"
        ;;
    help|*)
        echo "Usage: wp_post.sh {get|list|create|update|publish|search|get-content|get-meta|media|media-url|set-title|set-desc} [args]"
        ;;
esac
