## 実行例

```bash
rye run cli -- --json products add --sku ABC-1 --name Widget --price 10.00 --currency USD
rye run cli -- --json inventory upsert -l default -i ABC-1=5 -i ABC-2=7
rye run cli -- --json orders place -i ABC-1:2 -i ABC-2:3
rye run cli -- --json orders allocate -o <ORDER_ID>
```

## テスト実行例

```bash
rye run pytest src/tests/cli/test_cli_smoke.py -q
```
