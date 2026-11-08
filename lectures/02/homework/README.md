# 第2回 宿題（実装）

FAQ・GROUNDED・UNGROUNDED を「架空の大学図書館の利用案内 FAQ（5 項目）」に置き換えて LoRA 学習し、学習前後を比較した。
説明と結果は [../answer.md](../answer.md) の「宿題」欄にまとめている。

| ファイル | 内容 |
|---|---|
| `lora_format_tuning_library.ipynb` | 講座のノートブックのセクション 2・3・6・7 を図書館 FAQ 用に書き換えたもの（Colab の T4 で上から実行） |
| `result.json` | 設定・ライブラリの版・学習前後の要約・知識質問の結果 |
| `eval_before.json` / `eval_after.json` | 学習前 / 学習後の test 21 問の出力と採点 |
| `eval_before_4bit.json` | 参考：4bit で読み込んだ学習前の出力（セクション 8） |
| `gold.json` | test の正解（needs_review と必須語句） |
