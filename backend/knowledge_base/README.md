# Basic Artificial Intelligence Course / 人工知能基礎

## Kwansei Gakuin University - Fall 2025 / 関西学院大学 - 2025年度秋学期

[![Course Status](https://img.shields.io/badge/Status-Active-green.svg)](https://github.com/ontologist/2025AI)
[![License](https://img.shields.io/badge/License-Educational-blue.svg)](LICENSE)

---

## 📖 Course Information / コース情報

**English:**
This repository contains the complete curriculum, materials, and resources for the **Basic Artificial Intelligence** course (AI-300) at Kwansei Gakuin University's School of Policy Studies.

The course provides a comprehensive introduction to artificial intelligence fundamentals, covering the history of AI, search algorithms, probability theory, and machine learning basics. Students will acquire an understanding of the overview of artificial intelligence and machine learning through bilingual instruction.

**日本語:**
このリポジトリには、関西学院大学総合政策学部の**人工知能基礎**コース（AI-300）の完全なカリキュラム、教材、リソースが含まれています。

本コースは、AIの歴史、探索アルゴリズム、確率論、機械学習の基礎をカバーする、人工知能の基礎への包括的な入門を提供します。学生は、バイリンガル指導を通じて、人工知能と機械学習の概要を理解します。

---

## 🎯 Learning Goals / 学習目標

**By the end of this course, students should be able to:**

- Obtain basic knowledge about the history of artificial intelligence
- Recognize and recall major terms and concepts in search and game tree algorithms
- Acquire fundamental knowledge of supervised learning, unsupervised learning, and reinforcement learning

**このコースの終わりまでに、学生は以下ができるようになるべきです:**

- 人工知能の歴史に関する知識を習得している
- 探索とゲーム木の知識を習得している
- 機械学習の教師なし学習、教師あり学習、強化学習の知識を習得している

---

## 📂 Repository Structure / リポジトリ構造

```
2025AI/
├── docs/                       # Course website (GitHub Pages)
│   ├── index.html             # Main course page / メインコースページ
│   ├── styles.css             # Styling / スタイル
│   ├── bot-chat.js            # AI bot interface / AIボットインターフェース
│   └── weeks/                 # Weekly materials / 週別教材
│       ├── week-01/           # Week 1: AI History 1
│       ├── week-02/           # Week 2: AI History 2
│       ├── week-03/           # Week 3: AI History 3
│       ├── week-04/           # Week 4: Breadth/Depth-first Search
│       ├── week-05/           # Week 5: Best-first Search, A*
│       ├── week-06/           # Week 6: Game Theory
│       ├── week-07/           # Week 7: Probability & Bayes
│       ├── week-08/           # Week 8: Clustering + Review
│       ├── week-09/           # Week 9: AI/ML Overview
│       ├── week-10/           # Week 10: Supervised Learning
│       ├── week-11/           # Week 11: Classification
│       ├── week-12/           # Week 12: ML Algorithms
│       ├── week-13/           # Week 13: Reinforcement Learning
│       └── week-14/           # Week 14: Final Exam
└── README.md                  # This file / このファイル
```

---

## 🚀 Accessing the Course / コースへのアクセス

### Online Access / オンラインアクセス

**English:**
The course is hosted on GitHub Pages and can be accessed at:
👉 **[https://ontologist.github.io/2025AI](https://ontologist.github.io/2025AI)**

All course materials, lecture slides, assignments, and resources are available through the web interface.

**日本語:**
コースはGitHub Pagesでホストされており、以下からアクセスできます:
👉 **[https://ontologist.github.io/2025AI](https://ontologist.github.io/2025AI)**

すべてのコース教材、講義スライド、課題、リソースは、Webインターフェースを通じて利用できます。

---

### Local Development / ローカル開発

**English:**
If you want to run the course website locally:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ontologist/2025AI.git
   cd 2025AI
   ```

2. **Open in browser:**
   Simply open `docs/index.html` in your web browser, or use a local server:
   ```bash
   cd docs
   python3 -m http.server 8000
   ```
   Then visit `http://localhost:8000` in your browser.

**日本語:**
コースウェブサイトをローカルで実行したい場合:

1. **リポジトリをクローン:**
   ```bash
   git clone https://github.com/ontologist/2025AI.git
   cd 2025AI
   ```

2. **ブラウザで開く:**
   Webブラウザで単に `docs/index.html` を開くか、ローカルサーバーを使用:
   ```bash
   cd docs
   python3 -m http.server 8000
   ```
   その後、ブラウザで `http://localhost:8000` にアクセスしてください。

---

## 📚 Course Materials / コース教材

### Weekly Structure / 週別構造

**English:**
Each week includes:
- **Slides (スライド):** Interactive presentation slides
- **Lecture Notes (講義ノート):** Detailed notes for weeks 8-14
- **Assignments (課題):** Practice exercises for weeks 8-14

Weeks 1-7 contain generic content as they were taught by Professor Oyo before his illness.
Weeks 8-14 include comprehensive materials, real-world examples, and assignments.

**日本語:**
各週には以下が含まれます:
- **スライド:** インタラクティブなプレゼンテーションスライド
- **講義ノート:** 第8週から第14週の詳細なノート
- **課題:** 第8週から第14週の練習問題

第1週から第7週は、大用先生が病気になる前に教えた一般的な内容を含みます。
第8週から第14週には、包括的な教材、実世界の例、課題が含まれます。

---

## 🤖 AI Course Bot / AIコースボット

**English:**
An AI teaching assistant bot is planned for this course to provide:
- 24/7 learning support in English and Japanese
- Answers to questions about course content
- Study guidance and exam preparation help

**Status:** Currently under development 🏗️

**日本語:**
このコースには、以下を提供するAIティーチングアシスタントボットが計画されています:
- 英語と日本語での24時間365日の学習サポート
- コース内容に関する質問への回答
- 学習ガイダンスと試験準備のヘルプ

**ステータス:** 現在開発中 🏗️

---

## 📊 Assessment / 評価

**English:**
- **60% - In-Class Examination:** Comprehensive exam on Week 14
- **40% - Individual Reports:** Weekly assignments (Weeks 8-14)

**日本語:**
- **60% - 授業中試験:** 第14週の包括的試験
- **40% - 平常リポート:** 週次課題（第8週〜第14週）

---

## 📖 Reference Materials / 参考資料

### Recommended Textbooks / 推奨教科書

- イラストで学ぶ 人工知能概論 (KS情報科学専門書)
- 史上最強図解 これならわかる！ベイズ統計学
- 機械学習入門 ボルツマン機械学習から深層学習まで
- 強化学習 (Machine Learning Professional Series)

### Online Resources / オンラインリソース

- [Elements of AI (Free Course)](https://www.elementsofai.com/)
- [Andrew Ng's Machine Learning Course](https://www.coursera.org/learn/machine-learning)
- [TensorFlow Playground](https://playground.tensorflow.org/)
- [StatQuest YouTube Channel](https://www.youtube.com/@statquest)

---

## 👥 Course Information / コース情報

**English:**
- **University:** Kwansei Gakuin University / 関西学院大学
- **School:** School of Policy Studies / 総合政策学部
- **Course Code:** 29719300
- **Semester:** Fall 2025 / 2025年度秋学期
- **Credits:** 2
- **Language:** Bilingual (Japanese/English) / バイリンガル（日本語/英語）
- **Day/Time:** Thursday, Period 1 / 木曜日 1時限
- **Classroom:** Kobe Sanda Campus / 神戸三田キャンパス

**Instructor:**
- **Original Instructor:** Professor OYO KURATOMO (大用 庫智) - Weeks 1-6
- **Substitute Instructor:** Guest Professor - Weeks 7-14

---

## 📞 Support / サポート

**English:**
For questions about course content, assignments, or technical issues:
- Check the course website resources
- Contact the instructor during office hours
- Use the AI bot (when available) for 24/7 support

**日本語:**
コース内容、課題、技術的な問題に関する質問:
- コースウェブサイトのリソースを確認
- オフィスアワー中にインストラクターに連絡
- AIボット（利用可能な場合）を使用して24時間365日サポート

---

## ⚠️ Important Notes / 重要な注意事項

**English:**
- **Prerequisites:** Basic knowledge of statistics and programming is recommended
- **Study Time:** 1-2 hours per week outside of class for review and assignments
- **Attendance:** Regular attendance is essential as content builds week by week
- **Communication:** Course uses Slack for announcements and discussions

**日本語:**
- **前提条件:** 統計学とプログラミングの基礎知識が推奨されます
- **学習時間:** 週1〜2時間の授業外の復習と課題時間が必要
- **出席:** 内容が週ごとに構築されるため、定期的な出席が不可欠
- **コミュニケーション:** コースはアナウンスとディスカッションにSlackを使用

---

## 📜 License / ライセンス

This course material is provided for educational purposes at Kwansei Gakuin University.

このコース教材は、関西学院大学での教育目的で提供されています。

---

## 🙏 Acknowledgments / 謝辞

**English:**
- Kwansei Gakuin University School of Policy Studies
- Professor OYO KURATOMO for the original course design (Weeks 1-6)
- All reference textbook authors and open educational resources

**日本語:**
- 関西学院大学総合政策学部
- オリジナルコース設計（第1週〜第6週）の大用庫智教授
- すべての参考教科書著者とオープン教育リソース

---

**Ready to learn about Artificial Intelligence? / 人工知能について学ぶ準備はできましたか？**

Visit the course website: **[https://ontologist.github.io/2025AI](https://ontologist.github.io/2025AI)**

*Last updated: November 2025 / 最終更新: 2025年11月*
