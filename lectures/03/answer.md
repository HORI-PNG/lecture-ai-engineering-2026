# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：
- `--trace` で見えたツール呼び出し（ツール名と引数）：`"LoRAとQLoRAの違いは？"` で `search_glossary({'query': 'LoRA'})` と `search_glossary({'query': 'QLoRA'})` が1回ずつ呼ばれた（用語を1つずつ検索している）
- 1つの質問での LLM 呼び出し回数（`requests`）：2（ツールを呼ぶ判断で1回、検索結果を見て回答を作るので1回）
- 追加したツールと、docstring に書いた説明：`make_quiz(lecture)`。「指定した回の用語から確認問題を1問作り、問題と答えを返す。『第2回の確認問題を出して』のように、復習用の問題を求められたときに使う」

## 宿題

- 取り組んだレベル：実装

- やったこと：
  - `app/tools.py` に `save_learning_log(title, content)` を追加。`learning_log/` に `YYYYMMDD-HHMMSS_見出し.md` で保存する（見出しのファイル名に使えない文字は `_` に置換、空の入力は保存しない）
  - docstring には、使う場面（保存を頼まれたとき）と使わない場面（頼まれていないとき）の両方を書いた
  - `app/agent.py` で `agent.tool_plain(tools.save_learning_log, requires_approval=True)` として登録し、`output_type=[str, DeferredToolRequests]` に変更
  - CLI に `run_with_approval()` を追加。`result.output` が `DeferredToolRequests` の間は、`approvals` の呼び出しごとにツール名と引数（title / content）を表示して `y/N` を聞き、`DeferredToolResults`（承認＝`True`、拒否＝`ToolDenied(...)`）と `message_history=result.all_messages()` を渡して `run_sync` を再実行する
  - `INSTRUCTIONS` に「学習ログに残すよう頼まれたら save_learning_log を使う。頼まれていなければ保存しない」を追加
  - `tests/test_learning_log.py` を追加。`FunctionModel` で「save_learning_log を呼ぶ偽モデル」を作り、(1) 承認前はファイルが作られず `DeferredToolRequests` で止まる、(2) `y` で保存される、(3) `n` で保存されない、を API キーなしで確認

- 結果：
  - `uv run pytest -q`：`21 passed`
  - 【修正前】docstring の最後に「ファイルを書き込む操作なので、実行の前に利用者の承認を求める」と書いていたところ、`"LoRAとQLoRAの違いを調べて、学習ログに保存して"` で **save_learning_log が呼ばれなかった**。モデルは回答の文章で「保存してもよろしいでしょうか？」と聞いて終わった（1回で終わる CLI なので答えようがない）
    ```text
    [tool call]   search_glossary({'query': 'LoRA'})
    [tool call]   search_glossary({'query': 'QLoRA'})
    [usage] ... requests=2, tool_calls=2
    ```
  - 【修正後】その1文を「保存前の確認はプログラム側が行うので、会話で確認を求めずにそのままこのツールを呼ぶ」に変えたら、ツールが呼ばれ、承認待ちで止まるようになった
  - 承認した場合（`y`）：title と content が表示され、承認後に保存。`learning_log/20261108-094520_LoRAとQLoRAの違い.md` ができた
    ```text
    [approval] save_learning_log を実行しようとしています
      content: - **LoRA**: 事前学習済みの重みを固定し、…
      title: LoRAとQLoRAの違い
    実行してよいですか？ [y/N]: y
      → 承認しました
    …（回答）… ご依頼の通り、今回の学習内容を学習ログに保存しました。

    --- trace ---
    [tool call]   search_glossary({'query': 'LoRA'})
    [tool call]   search_glossary({'query': 'QLoRA'})
    [tool call]   save_learning_log({'content': '- **LoRA**: …', 'title': 'LoRAとQLoRAの違い'})
    [tool return] save_learning_log -> 学習ログを保存しました: learning_log/20261108-094520_LoRAとQLoRAの違い.md…
    [usage] ... requests=1, tool_calls=1
    ```
  - 拒否した場合（`n`）：拒否がツールの結果としてモデルに返り、モデルは「利用者の許可が得られなかったため保存はキャンセルされました」と回答を続けた。`ls learning_log/` のファイルは1つのままで、保存されていない
    ```text
    実行してよいですか？ [y/N]: n
      → 拒否しました
    [tool return] save_learning_log -> 利用者が保存を許可しませんでした。保存していません。…
    [usage] ... requests=1
    ```
  - 保存を頼まない質問（`"LoRAとQLoRAの違いは？"`）：save_learning_log は呼ばれなかった（search_glossary の2回のみ、`requests=2`）

- 気づき・疑問：
  - **docstring の「承認を求める」という一文が、逆にツールを呼ばせなくしていた**。モデルは「承認を求める」を「自分が会話で聞く」と解釈した。承認の仕組みはコード（`requires_approval=True`）側にあるので、docstring には「誰が何をするか」をはっきり書く必要がある。ツールの説明文はモデルへの指示そのものだと実感した
  - 承認待ちのツールが呼ばれると、エージェントのループはそこで一度終わり、出力が文字列ではなく `DeferredToolRequests` になる。会話履歴と承認結果を渡して改めて実行する形で、ループの外（CLI）に人間の判断を挟める
  - `--trace` は全履歴を表示するが、`[usage]` は承認後の再実行分（`requests=1`）だけだった。1つの質問全体のコストを見るには、両方の実行の usage を足す必要がある
  - 拒否も「ツールの結果」としてモデルに返るので、モデルは拒否を受けて自然に回答を続けられた
  - 承認画面に引数（保存される本文）を表示したことで、何を許可しているのかが分かった。確認を挟むだけでなく「何を確認させるか」が大事
  - 疑問：Streamlit などの Web UI では、承認待ちの間の会話履歴をどこに保持するのがよいか。また、ファイル削除のような操作では、承認に加えて引数の検証（保存先の制限など）も必要になると思う
