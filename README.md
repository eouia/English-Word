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

`Roots/`, `Themes/`, `scripts/`, `AGENTS.md`, `RTK.md`, `index.md`를 수정한 작업은 이 스크립트 실행까지가 완료 조건이다. 사용자가 명시적으로 배포나 커밋을 금지하지 않은 한, 노트 수정 후에는 최종 응답 전에 반드시 실행한다.

이 스크립트는 다음 작업을 수행한다.

1. GitHub 최신 변경을 `git pull --ff-only`로 가져옴
2. iCloud Vault 원본에서 `Roots/_Lexicon.json` 갱신
3. iCloud Vault 원본에서 테마 heading과 어근 문서 링크 갱신
4. iCloud Vault 원본에서 `Themes/_Lexicon.json` 갱신
5. iCloud Vault의 `Roots/`, `Themes/`, `scripts/`, `index.md`, `AGENTS.md`, `RTK.md`를 Workspace 저장소로 동기화
6. Workspace 저장소에서도 역색인과 테마 링크를 한 번 더 갱신
7. Quartz 빌드 확인
8. 변경 사항이 있으면 커밋 후 푸시
9. GitHub Actions가 자동으로 GitHub Pages에 배포

## 수동 작업

동기화만:

```bash
publish/sync_from_icloud.sh
```

로컬 빌드 확인:

```bash
cd site
npx quartz build -d ..
```

로컬 미리보기:

```bash
cd site
npx quartz build --serve -d ..
```

## 테마 단어를 어근 문서와 연결

`Roots/_Lexicon.json`을 기준으로 `Themes/*.md`의 `### word` 항목 제목을 어근 문서의 해당 단어 heading 링크로 바꿀 수 있다.

먼저 dry-run으로 확인한다.

```bash
python3 scripts/link_theme_roots.py Themes/education-school-and-university.md
```

출력이 괜찮으면 `--write`를 붙인다. 여러 어근 후보가 있는 단어는 표제어 뒤에 후보 어근 링크를 모두 붙이려면 `--list-ambiguous`를 함께 쓴다.

```bash
python3 scripts/link_theme_roots.py --write --list-ambiguous Themes/education-school-and-university.md
```

모든 테마 문서를 대상으로 확인하려면 파일명을 생략한다.

```bash
python3 scripts/link_theme_roots.py
```

예: `### curriculum` -> `### [[curr#curriculum|curriculum]]`

여러 어근 후보가 있는 단어를 `--list-ambiguous`로 처리하면 표제어 뒤에 후보 링크를 나열한다.

예: `### aqueduct` -> `### aqueduct ([[aqua#aqueduct|aqua]], [[duc#aqueduct|duc]])`

전체 적용:

```bash
python3 scripts/build_lexicon.py
python3 scripts/link_theme_roots.py --write --list-ambiguous
python3 scripts/build_theme_lexicon.py
```

`--skip-ambiguous`를 쓰면 복수 후보 항목을 건드리지 않는다. 특정 테마에서 후보 링크가 너무 복잡해 보이면 수동으로 하나만 남겨도 된다.

## 테마 역색인 갱신

`Themes/_Lexicon.json`은 테마 문서의 `###` 단어 항목을 기준으로 만든 단어-테마 역색인이다. 수동으로 갱신하려면:

```bash
python3 scripts/build_theme_lexicon.py
```

`publish/publish_notes.sh`를 쓰면 배포 전에 자동으로 갱신된다.

## 운영 원칙

- **노트 데이터 원본은 항상 iCloud Obsidian Vault다.**
- `~/Workspace/English-Word`는 Quartz 설정, Git 이력, GitHub Pages 배포를 위한 작업 폴더다.
- GitHub 저장소가 최신이어도 노트 본문의 정답으로 간주하지 않는다. 다른 Mac에서 작업한 노트는 iCloud Vault에 먼저 들어온다고 본다.
- "최신화" 순서는 `git pull --ff-only`로 배포 스크립트와 Quartz 설정을 받은 뒤, `publish/sync_from_icloud.sh`로 **Vault → Workspace** 방향 동기화다.
- Workspace/GitHub 내용을 iCloud Vault에 역으로 덮어쓰지 않는다. Vault 파일 삭제나 복구는 사용자가 명시적으로 요청한 경우에만 한다.
- iCloud Vault 안에는 `.git`, `site/`, `node_modules/`를 두지 않는다.
- Git/Quartz 작업은 `~/Workspace/English-Word`에서만 한다.
- 새 작업 세션을 시작할 때, 노트 데이터 동기화가 아니라 스크립트·설정 최신화만 필요하면 아래 명령을 먼저 실행한다.

```bash
cd ~/Workspace/English-Word
publish/update_workspace_tools.sh
```

빌드까지 확인하려면:

```bash
publish/update_workspace_tools.sh --build
```

이 스크립트는 `git pull --ff-only`, Python 스크립트 문법 검사, shell 스크립트 문법 검사를 수행한다. `--build`를 붙인 경우에만 Quartz 빌드를 실행한다. iCloud Obsidian Vault에서 Workspace로 노트 본문을 동기화하지 않고, Vault 파일도 쓰지 않는다.
- 여러 Mac에서 작업할 때는 배포 전 항상 `git pull --ff-only`를 먼저 한다.
- 두 Mac에서 동시에 서로 다른 노트를 수정했다면 iCloud 동기화가 끝난 뒤 배포한다.
- 스크립트, 배포 방식, 작업 규칙이 바뀌면 변경한 Mac에서 즉시 `publish/publish_notes.sh "설명적인 커밋 메시지"`로 GitHub 저장소까지 갱신한다.
- 다른 Mac에서 작업을 시작할 때는 먼저 `cd ~/Workspace/English-Word && publish/update_workspace_tools.sh`를 실행해 최신 스크립트와 README를 받는다.
- iCloud 원본 노트와 GitHub 저장소의 역할을 구분한다. 노트 본문은 iCloud가 원본이고, Quartz 설정·README·Git 이력은 Workspace 저장소가 원본이다.
