# 環境構築

## ryeインストール

https://note.spectee.com/n/n12fae344a538

## python仮想環境に入る

```
source .venv/bin/activate
```

## vscodeのpythonインタープリタに設定

```
which python
// /home/user/.rye/shims/python
```
vscodeにて、コマンドパレットで「Python: Select Interpreter」> 「Enter interpreter path」に上記のpathを登録


## 開発ツールを追加（dev 依存）

```
rye add --dev ruff mypy pytest hypothesis
rye sync
```

## Ruff（厳しめ）設定

```
cat > .ruff.toml << 'EOF'
target-version = "py313"
line-length = 100
indent-width = 4

[lint]
select = ["ALL"]
ignore = [
  "COM812", "ISC001",  # フォーマッタ衝突回避
  "D203", "D212", "D401",  # Docstring は最初は緩め
]
preview = true

[format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
EOF
```

## mypy（--strict）設定

```
cat > mypy.ini << 'EOF'
[mypy]
python_version = 3.13
strict = True
warn_unreachable = True
show_error_codes = True
pretty = True
explicit_package_bases = True

[mypy-tests.*]
# テスト側は必要に応じて緩和
disallow-untyped-defs = False
EOF
```
