# Vocabulary Notes

Obsidian 기반 영어 어휘 노트를 Quartz로 빌드해 GitHub Pages에 배포하는 저장소.

- 사이트: <https://eouia.github.io/English-Word/>
- 원본 노트: iCloud Drive의 Obsidian Vault 안 `English-Word`
- 배포 작업 폴더: `~/Workspace/English-Word`

## 새 Mac에서 처음 설정

```bash
mkdir -p ~/Workspace
cd ~/Workspace
git clone https://github.com/eouia/English-Word.git
cd English-Word
cd site
npm ci
```

Node.js 22 이상이 필요하다.

## Obsidian Vault 경로 설정

기본 경로가 아래와 같으면 추가 설정이 필요 없다.

```text
~/Library/Mobile Documents/com~apple~CloudDocs/Obsidian/MyObsidian/English-Word
```

다른 Mac에서 경로가 다르면:

```bash
cd ~/Workspace/English-Word
cp publish/local.env.example publish/local.env
```

그 뒤 `publish/local.env`의 `OBSIDIAN_VAULT_PATH`를 실제 경로로 수정한다.

## 노트 수정 후 배포

Obsidian에서는 iCloud Vault의 원본 노트를 수정한다. 배포는 Workspace 저장소에서 실행한다.

```bash
cd ~/Workspace/English-Word
publish/publish_notes.sh "Update notes"
```

이 스크립트는 다음 작업을 수행한다.

1. GitHub 최신 변경을 `git pull --ff-only`로 가져옴
2. iCloud Vault의 `Roots/`, `Themes/`, `scripts/`, `index.md`, `AGENTS.md`를 Workspace 저장소로 동기화
3. Quartz 빌드 확인
4. 변경 사항이 있으면 커밋 후 푸시
5. GitHub Actions가 자동으로 GitHub Pages에 배포

## 수동 작업

동기화만:

```bash
publish/sync_from_icloud.sh
```

로컬 빌드 확인:

```bash
cd site
npx quartz build
```

로컬 미리보기:

```bash
cd site
npx quartz build --serve
```

## 테마 단어를 어근 문서와 연결

`Roots/_Lexicon.json`을 기준으로 `Themes/*.md`의 `### word` 항목 제목을 어근 문서 링크로 바꿀 수 있다.

먼저 dry-run으로 확인한다.

```bash
python3 scripts/link_theme_roots.py Themes/education-school-and-university.md
```

출력이 괜찮으면 `--write`를 붙인다.

```bash
python3 scripts/link_theme_roots.py --write Themes/education-school-and-university.md
```

모든 테마 문서를 대상으로 확인하려면 파일명을 생략한다.

```bash
python3 scripts/link_theme_roots.py
```

여러 어근 후보가 있는 단어는 `ambiguous`로 표시하고 자동 수정하지 않는다.

## 운영 원칙

- iCloud Vault 안에는 `.git`, `site/`, `node_modules/`를 두지 않는다.
- Git/Quartz 작업은 `~/Workspace/English-Word`에서만 한다.
- 여러 Mac에서 작업할 때는 배포 전 항상 `git pull --ff-only`를 먼저 한다.
- 두 Mac에서 동시에 서로 다른 노트를 수정했다면 iCloud 동기화가 끝난 뒤 배포한다.
