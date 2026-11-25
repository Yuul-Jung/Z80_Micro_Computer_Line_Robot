# Z80 마이크로컴퓨터 라인 로봇 — 프로젝트 지도서 웹판

1999년 대한상공회의소 직업교육훈련사업단 프로젝트지도서 99-36 「라인 마이크로 로봇 제작하기」(전기계측제어 응용, 집필 정병우·검토 안상채)를 GitHub Pages 웹 교재로 옮긴 저장소입니다.

Z80 원보드 컴퓨터, DC 모터 제어회로, 센서 신호 검출회로, 프레임·바퀴 제작, 운용 프로그램을 차례로 완성해 라인 트레이싱 로봇을 만듭니다.

- 웹 교재: https://yuul-jung.github.io/Z80_Micro_Computer_Line_Robot/
- 회로도·도면·슬라이드는 그림을 누르면 전체 화면에서 확대(최대 1200%)·이동할 수 있습니다.

## 구성

| 장 | 파일 | 내용 |
|---|---|---|
| INDEX | `index.html` | 과정 개요, 학습 테크트리, 장별 목차 |
| 01 | `ch01_project_overview_v01.html` | 로봇 조립도·회로도, 과제계획서, 지도 절차, 기능 설명서, 작업분담표, 재료 목록 |
| 02 | `ch02_z80_one_board_computer_v01.html` | 디지털 시스템, Z80 CPU, 주변소자 IC(8255·8253·8251) |
| 03 | `ch03_8251_serial_v01.html` | 8251 시리얼 통신 |
| 04 | `ch04_dc_motor_control_v01.html` | DC 모터 개념, 토크, On/Off·PWM·PID 제어 |
| 05 | `ch05_sensors_v01.html` | 센서 정의, 신호 검출, 센서별 원리, 릴레이 |
| 06 | `ch06_frame_and_wheels_v01.html` | 프레임 및 바퀴 제작 도면 |
| 07 | `ch07_z80_assembly_v01.html` | Z80 어셈블리 개론과 명령어 |
| 08 | `ch08_learning_activities_v01.html` | 학습활동 안내 질문, 기술·기능 학습활동 |
| 09 | `ch09_plan_report_evaluation_v01.html` | 작업계획서, 실습결과보고서, 평가표, 작업분석표, 연습과제 |
| 10 | `ch10_resources_v01.html` | Z80 하드웨어 슬라이드, 시스템 구성도, 원본 파일 내려받기 |

- `assets/` — 공통 스타일(`site.css`)·탐색(`site.js`)·그림 확대(`zoom.js`)·책장 배너, 본문 그림(`img/`), 슬라이드(`slides/`)
- `source/` — 원본 한글 97 원고(.hwp), OrCAD 회로도(.DSN/.opj), PowerPoint(.ppt)
- `tools/` — 원고를 웹으로 바꾼 변환 도구(HWP 3.0 파서, 그림 변환, 페이지 생성기)
- `VERIFICATION.md` — 게시 전 적대적 검증 결과

## GitHub Pages 게시

**Settings → Pages → Build and deployment**에서 Source를 `Deploy from a branch`, 브랜치를 `main` / `(root)`로 지정합니다.

## 📘 교육용 HTML 공통 제작 규칙

이 저장소의 교육자료(웹페이지·강의 HTML)는 [Yuul-Jung 교육용 HTML 공통 표준](https://github.com/Yuul-Jung/rule_md/tree/main/web/education-html)을 적용합니다.

- [제작 규칙](https://github.com/Yuul-Jung/rule_md/blob/main/web/education-html/STANDARD.md)
- [다른 저장소 적용 안내](https://github.com/Yuul-Jung/rule_md/blob/main/web/education-html/INTEGRATION.md)
- [기준 디자인 사례](https://github.com/Yuul-Jung/ai-agent-engineering)

공통 책장 이미지, 컴팩트한 상단 배너, 좌측 전체 장/절 탐색, 모바일 메뉴, 파일 버전 및 검증 기준을 따릅니다.
