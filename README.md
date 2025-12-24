# Agilent E3632A Power Supply Monitor

이 프로젝트는 RS-232 통신을 통해 Agilent E3632A 파워 서플라이의 실시간 전압 및 전류 데이터를 모니터링하고 로그를 저장하는 GUI 프로그램입니다.

## 주요 기능

- **실시간 데이터 수집**: 1초 간격으로 장비의 현재 전압(V)과 전류(A)를 측정합니다.
- **로그 표시**: 시간, 전압, 전류 데이터를 화면에 실시간으로 표시합니다.
- **데이터 저장**: 수집된 데이터를 CSV 파일로 내보낼 수 있습니다.
- **독립 실행**: Python 설치 없이 실행 가능한 `.exe` 파일을 제공합니다.

---

## 설치 및 실행 방법 (사용자용)

1. `dist/agilent_monitor.exe` 파일을 다운로드합니다.
2. PC와 Agilent E3632A를 RS-232 케이블로 연결합니다. (전용 Null Modem 케이블 권장)
3. 장비 설정에서 RS-232 인터페이스가 활성화되어 있고, Baud Rate가 **9600**으로 되어 있는지 확인합니다.
4. 프로그램을 실행하고 해당 COM 포트를 선택한 후 **Start** 버튼을 누릅니다.

---

## 개발자용 가이드 (소스 코드 빌드 방법)

이 코드를 직접 수정하거나 빌드하여 배포하려면 다음 단계를 따르세요.

### 1. 개발 환경 설치
- Python 3.8 이상의 환경이 필요합니다.

### 2. 라이브러리 설치
터미널에서 아래 명령어를 실행하여 필요한 라이브러리를 설치합니다.
```bash
pip install pyserial pyinstaller
```

### 3. 프로그램 실행
소스 코드를 직접 실행하려면 아래 명령어를 입력합니다.
```bash
python agilent_monitor.py
```

### 4. 실행 파일(.exe) 생성
독립 실행형 프로그램을 만들려면 `PyInstaller`를 사용합니다.

```bash
python -m PyInstaller --noconsole --onefile agilent_monitor.py
```

- `--noconsole`: 실행 시 명령 프롬프트 창이 뜨지 않게 합니다.
- `--onefile`: 모든 관련 파일을 하나의 `.exe` 파일로 합칩니다.
- 실행 결과물은 `dist/` 폴더 내에 생성됩니다.

---

## 참고 사항
- **통신 설정**: 9600 Baud, 8 Data bits, No Parity, 1 Stop bit, DTR/DSR Flow control 설정을 기본값으로 사용합니다.
- **SCPI 명령어**: 본 프로그램은 `MEAS:VOLT?`, `MEAS:CURR?` 등의 표준 SCPI 명령어를 사용하여 장비를 제어합니다.
