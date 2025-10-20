# Anti-corruption Layer (ACL)

## 目的

- 外部システムのペイロード（命名・構造・制約が異なる）を、内部のコマンド/VOへ正規化して取り込む。
- バリデーションエラーは MappingError(MappingIssue[]) として体系化し、呼び出し側（API/バッチ等）で機械的に扱える。

## 設計

- 外部DTO: pydantic v2 で構造/型/範囲を検証（extra=forbid, strip）。
- VO変換: Sku などの内部VOへ変換し、VO 側の厳格チェックをもう一段適用。
- エラー: PydanticのValidationError -> MappingIssue(path, code, message) に落とし、VO変換エラーは invalid_sku 等の code で統一。

## 拡張

- 外部側のバージョン差（v1/v2）をクラスで分ける or version フィールドでスイッチ。
- エラーコード体系: codeは "invalid_sku", "value_error.min_items", "field_required", "extra_forbidden" 等に統一。
- API統合: adapters/inbound/api に external 専用ルータを用意し、MappingErrorをHTTP 422に変換する。
