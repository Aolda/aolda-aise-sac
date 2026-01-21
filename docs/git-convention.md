# Git 협업 규칙

## 1. Git Repository

- Repository Name: `aolda-aise-sac`
- Reference
  - [AHP Team Branch & PR Convention](https://www.notion.so/AHP-Team-Branch-PR-Convention-2e0808f2c44e80cebc38c3474490a968?pvs=21)

---

## 2. Branch Convention

### Naming Rule

```
{prefix}/{content}
```

### Prefix 정의

| prefix   | 작업 내용                                   |
| -------- | ------------------------------------------- |
| feat     | 특정 기능 또는 페이지 단위의 신규 기능 추가 |
| refactor | 기존 기능을 구조적으로 개선하거나 재작성    |
| fix      | 개발된 기능에서 확인된 버그 수정            |
| docs     | 문서 작성 및 수정 작업                      |

---

## 3. Commit Convention

### Commit Message Format

```
prefix: content
```

- 예시
  - `feat: add user authentication logic`
  - `docs: add git convention document`
  - `fix: resolve null pointer exception`

---

## 4. Merge Request (MR) Convention

### 4.1 MR Title

```
[Prefix] content
```

- 예시
  - `[Docs] Initialize repository structure`
  - `[Feat] Implement login API`

---

### 4.2 MR Body Template

```yaml
## 💡 설명
> 추가하려는 기능에 대해 간결하게 설명해주세요

여기에_내용_작성

## ✅ 작업 상세 내용
> 세부적으로 수행한 작업을 작성해주세요

- [X] TODO
- [ ] TODO
- [ ] TODO

## 📝 추가 설명(선택)
> 부가적인 설명이 필요한 경우 작성해주세요

여기에_내용_작성

## 📚 참고 자료(선택)
> 참고한 문서, 링크, 이미지 등을 첨부해주세요

여기에_내용_작성
```
