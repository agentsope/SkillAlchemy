<div align="center">

# SkillAlchemy

**人物・方法・経験を、インストール可能で再利用可能なエージェントスキルへ。**

[English](README.md) · [中文](README_CN.md) · [日本語](README_JA.md)

</div>

<p align="center">
  <a href="https://arxiv.org/abs/2608.23417"><img src="https://img.shields.io/badge/arXiv-2608.23417-b31b1b.svg" alt="arXiv"></a>
  <a href="https://github.com/agentsope/SkillAlchemy/stargazers"><img src="https://img.shields.io/github/stars/agentsope/SkillAlchemy?logo=github&color=ffca28" alt="Stars"></a>
  <img src="https://img.shields.io/badge/agents-Claude%20Code%20%7C%20Codex-6E56CF" alt="Supported agents">
</p>

SkillAlchemy は、不完全なスキル要件とオープンワールドの情報源から、インストール可能で再利用可能なエージェントスキルを生成する**オープンワールド・エージェントスキル作成システム**です。

不足している要件を発見し、多様な公開情報から実行可能な手順を特定し、各手順をどこまで一般化できるかを根拠に基づいて判断したうえで、採用した知識をエージェントスキルパッケージにまとめます。

<div align="center">
  <img src="assets/framework.png" alt="SkillAlchemy framework" width="100%">
</div>

## 🔥 最新情報

* **2026-08-24** — 論文 **[SkillAlchemy: Open-World Agent Skill Creation](https://arxiv.org/abs/2608.23417)** を arXiv で公開しました。

## 概要

対象とする能力に馴染みがない場合、信頼できるエージェントスキルの作成は容易ではありません。タスク記述には重要な要件が欠けていることがあり、専門家が作成した手順や完全な実行履歴を利用できるとも限りません。

SkillAlchemy は、スキル作成を**情報源に根拠を置く手順採用問題（source-grounded procedure-admission problem）**として捉えます。

不完全なスキル要件とオープンワールドの情報源が与えられると、SkillAlchemy は次の処理を行います。

1. 元の要件から抜け落ちている**暗黙の要件を発見**します。
2. ドキュメント、リポジトリ、論文、Issue レポートなどの公開情報から、**根拠のある手順を取得**します。
3. 根拠が再利用可能な指示、限定的な例、または除外のいずれを支持するかを判断し、**手順の適用範囲を決定**します。
4. エージェントが直接読み込んで使用できる、**インストール可能な Skill パッケージを生成**します。

## 実験結果

SkillsBench v1.1 の **87 タスク**を用い、4 種類のエージェント–モデル構成で SkillAlchemy を評価しました。

SkillAlchemy は、**4 構成中 3 構成で最も高いタスク成功率**を達成しました。

全構成の平均タスク成功率は **55.8%** です。

* Skill を使用しない場合と比べて **+19.9 ポイント**。
* 最も強い自動 Skill 作成ベースラインと比べて **+8.6 ポイント**。
* **人手で作成した Skill と同等の性能**を示し、本評価の平均ではわずかに上回りました。

<table>
  <thead>
    <tr>
      <th align="left">Skill Setting</th>
      <th align="center">Claude Code<br>DeepSeek-V4-Pro</th>
      <th align="center">Claude Code<br>Opus 4.8</th>
      <th align="center">Codex<br>DeepSeek-V4-Pro</th>
      <th align="center">Codex<br>GPT-5.5</th>
      <th align="center">Avg.</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>No Skill</td>
      <td align="right">23.4</td>
      <td align="right">45.3</td>
      <td align="right">29.7</td>
      <td align="right">45.1</td>
      <td align="right">35.9</td>
    </tr>
    <tr>
      <td>Anthropic Skill-Creator</td>
      <td align="right">31.7</td>
      <td align="right">49.2</td>
      <td align="right">32.9</td>
      <td align="right">48.5</td>
      <td align="right">40.6</td>
    </tr>
    <tr>
      <td>OpenAI Skill-Creator</td>
      <td align="right">33.3</td>
      <td align="right">49.9</td>
      <td align="right">37.0</td>
      <td align="right">48.5</td>
      <td align="right">42.2</td>
    </tr>
    <tr>
      <td>OpenSkill</td>
      <td align="right">42.3</td>
      <td align="right">51.5</td>
      <td align="right">40.7</td>
      <td align="right">49.4</td>
      <td align="right">46.0</td>
    </tr>
    <tr>
      <td>MUSE-Autoskill</td>
      <td align="right">43.2</td>
      <td align="right">53.3</td>
      <td align="right">40.2</td>
      <td align="right">52.0</td>
      <td align="right">47.2</td>
    </tr>
    <tr>
      <td>Human-Curated Skill</td>
      <td align="right">51.3</td>
      <td align="right">59.5</td>
      <td align="right"><strong>45.7</strong></td>
      <td align="right">60.9</td>
      <td align="right">54.4</td>
    </tr>
    <tr>
      <td><strong>SkillAlchemy</strong></td>
      <td align="right"><strong>54.7</strong></td>
      <td align="right"><strong>60.9</strong></td>
      <td align="right">43.9</td>
      <td align="right"><strong>63.7</strong></td>
      <td align="right"><strong>55.8</strong></td>
    </tr>
  </tbody>
</table>

## 主な機能

* **暗黙の要件を発見** — 不完全な Skill 要件から、実際の動作に関わる要件、制約、運用上の観点を復元します。
* **人物を蒸留** — 意思決定、失敗、価値観、コミュニケーションの特徴に関する公開情報から Persona Skill を作成します。
* **方法を蒸留** — 書籍、方法論、リポジトリ、ドキュメント、論文、インタビューを、条件、手順、分岐、失敗時の対応を備えた実行可能な Skill に変換します。
* **根拠のある手順を採用** — 取得したすべての情報を無条件に一般化せず、再利用可能な指示、文脈に依存する例、根拠のない内容を区別します。
* **Skill を融合** — 既存のワークフロー、ドメイン知識、作業スタイルを組み合わせ、新しい能力を作ります。
* **インストール可能な Skill を生成** — 採用した手順、例、参考資料、補助リソースを、エージェントが直接読み込んで使える Skill にまとめます。

## クイックスタート

最も簡単な方法は、Claude Code または Codex に次のように依頼することです。

```text
https://github.com/agentsope/SkillAlchemy から SkillAlchemy をインストールし、使い方を教えてください。
```

コマンドラインからインストールすることもできます。

```bash
npx skills add agentsope/SkillAlchemy
```

インストール後、作成したい Skill を説明します。

```text
SkillAlchemy を使って、RAG システムをレビューするための Skill を作成してください。
公開ドキュメントと研究論文を情報源として使用してください。
```

生成されたパッケージは、現在のプロジェクトの `output/` に保存されます。

### Skill を個別にインストール

```bash
# コアコンポーネント
npx skills add agentsope/SkillAlchemy/skills/Lens
npx skills add agentsope/SkillAlchemy/skills/LEAP

# リポジトリに含まれるその他の Skill
npx skills add agentsope/SkillAlchemy/skills/<skill-name>
```

[インストール可能な Skill の一覧](skills/)

## 論文・引用

問題設定、フレームワーク設計、実験評価の詳細については、以下の論文をご覧ください。

> **SkillAlchemy: Open-World Agent Skill Creation**
> Hengjun Wang, Shuyue Wei, Boyi Liu, Jun Yang, Yongxin Tong.
> arXiv:2608.23417, 2026
> **[arXiv](https://arxiv.org/abs/2608.23417)** · **[PDF](https://arxiv.org/pdf/2608.23417)**

研究や開発に SkillAlchemy が役立った場合は、以下の論文を引用してください。

```bibtex
@article{wang2026skillalchemy,
  title   = {SkillAlchemy: Open-World Agent Skill Creation},
  author  = {Wang, Hengjun and Wei, Shuyue and Liu, Boyi and Yang, Jun and Tong, Yongxin},
  journal = {arXiv preprint arXiv:2608.23417},
  year    = {2026}
}
```

## ライセンス

SkillAlchemy は [MIT License](LICENSE) のもとで公開されています。

---

<p align="center">
  <a href="TECHNICAL.md"><strong>技術ドキュメント</strong></a>
</p>
