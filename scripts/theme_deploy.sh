#!/bin/bash
# 子テーマ（theme/swell_child/）を本番へ反映する。
#
# 既定はドライラン。--apply を付けない限り本番には1バイトも書かない。
# 本番へ書く前に、本番側の子テーマを必ずタイムスタンプ付きで退避する。
#
# 使い方:
#   ./scripts/theme_deploy.sh diff            本番との差分を見る（読むだけ）
#   ./scripts/theme_deploy.sh push            反映内容の確認（ドライラン）
#   ./scripts/theme_deploy.sh push --apply    実際に反映する
#   ./scripts/theme_deploy.sh push --apply --prune   本番にしか無いファイルも消す
#   ./scripts/theme_deploy.sh pull            本番の子テーマをリポジトリに取り込む
#   ./scripts/theme_deploy.sh backup          本番の子テーマを退避するだけ
#   ./scripts/theme_deploy.sh rollback <名前> 退避から戻す

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SRC="$PROJECT_DIR/theme/swell_child/"

SSH_HOST="jpholic"
REMOTE_ROOT="/home/jpholic/ecnow.jp/public_html"
REMOTE_THEME="$REMOTE_ROOT/wp-content/themes/swell_child"
REMOTE_BACKUP_DIR="/home/jpholic/theme_backups"

if [ ! -d "$SRC" ]; then
    echo "Error: $SRC がありません。" >&2
    exit 1
fi

CMD="${1:-}"
shift || true

APPLY=0
PRUNE=0
for arg in "$@"; do
    case "$arg" in
        --apply) APPLY=1 ;;
        --prune) PRUNE=1 ;;
        *) echo "Error: 知らないオプション: $arg" >&2; exit 1 ;;
    esac
done

RSYNC_OPTS=(-az --itemize-changes --exclude '.DS_Store' --exclude '*.orig')
[ "$PRUNE" -eq 1 ] && RSYNC_OPTS+=(--delete)

backup_remote() {
    local name="swell_child_$(date +%Y%m%d-%H%M%S)"
    ssh "$SSH_HOST" "mkdir -p $REMOTE_BACKUP_DIR && cp -a $REMOTE_THEME $REMOTE_BACKUP_DIR/$name && echo '退避しました: $REMOTE_BACKUP_DIR/$name'"
    echo "$name"
}

case "$CMD" in
    diff)
        echo "本番との差分（左=リポジトリ 右=本番）。何も出なければ同一です。"
        rsync -an --itemize-changes --exclude '.DS_Store' --exclude '*.orig' \
            "$SRC" "$SSH_HOST:$REMOTE_THEME/" | grep -v '^$' || echo "  差分なし"
        ;;

    push)
        echo "== 反映元 : $SRC"
        echo "== 反映先 : $SSH_HOST:$REMOTE_THEME"
        [ "$PRUNE" -eq 1 ] && echo "== --prune: 本番にしか無いファイルは削除されます"
        echo

        if [ "$APPLY" -eq 0 ]; then
            echo "--- ドライラン（本番には書きません）---"
            rsync -n "${RSYNC_OPTS[@]}" "$SRC" "$SSH_HOST:$REMOTE_THEME/"
            echo
            echo "問題なければ --apply を付けて実行してください。"
            exit 0
        fi

        echo "--- 本番の子テーマを退避 ---"
        backup_remote
        echo
        echo "--- 反映 ---"
        rsync "${RSYNC_OPTS[@]}" "$SRC" "$SSH_HOST:$REMOTE_THEME/"
        echo
        echo "--- 反映後の確認 ---"
        for u in / /beginner/91/ /category/beginner/ /contact/; do
            printf "  %-24s " "$u"
            curl -s -o /dev/null -w "%{http_code}\n" --max-time 30 -A "Mozilla/5.0" "https://ecnow.jp$u"
        done
        echo
        echo "すべて200でなければ rollback してください:"
        echo "  ./scripts/theme_deploy.sh rollback <退避名>"
        ;;

    pull)
        echo "本番の子テーマをリポジトリへ取り込みます（手元の変更が上書きされます）。"
        rsync -az --itemize-changes --exclude '.DS_Store' "$SSH_HOST:$REMOTE_THEME/" "$SRC"
        echo "完了。git diff で確認してください。"
        ;;

    backup)
        backup_remote
        ;;

    rollback)
        NAME="${1:-}"
        if [ -z "$NAME" ]; then
            echo "退避の一覧:"
            ssh "$SSH_HOST" "ls -1 $REMOTE_BACKUP_DIR 2>/dev/null" || echo "  まだありません"
            echo
            echo "使い方: ./scripts/theme_deploy.sh rollback <退避名>"
            exit 1
        fi
        ssh "$SSH_HOST" "test -d $REMOTE_BACKUP_DIR/$NAME && rsync -a --delete $REMOTE_BACKUP_DIR/$NAME/ $REMOTE_THEME/ && echo '戻しました: $NAME'"
        for u in / /beginner/91/; do
            printf "  %-24s " "$u"
            curl -s -o /dev/null -w "%{http_code}\n" --max-time 30 -A "Mozilla/5.0" "https://ecnow.jp$u"
        done
        ;;

    *)
        sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'
        exit 1
        ;;
esac
