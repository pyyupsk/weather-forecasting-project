# โครงการพยากรณ์อากาศ

CLI tool สำหรับดึงข้อมูลพยากรณ์อากาศจาก API ของกรมอุตุนิยมวิทยา รองรับหลายสถานที่ต่อครั้ง ทั้งแบบรายชั่วโมงและรายวัน บันทึกผลเป็น CSV

## การติดตั้ง

```bash
git clone https://github.com/pyyupsk/weather-forecasting-project.git
cd weather-forecasting-project
uv sync
```

## การตั้งค่า

สร้างไฟล์ `.env` และใส่ API Token ของกรมอุตุนิยมวิทยา:

```env
TMD_API_TOKEN=your_api_token_here
```

## การใช้งาน

```bash
# สถานที่เดียว
uv run src/main.py --location นครปฐม สามพราน

# หลายสถานที่
uv run src/main.py --location นครปฐม สามพราน --location กรุงเทพมหานคร พระนคร

# อ่านจากไฟล์ JSON
uv run src/main.py --locations locations.example.json

# พิกัด GPS
uv run src/main.py --lat 13.8 --lon 100.1

# พยากรณ์รายวัน 7 วัน
uv run src/main.py --location นครปฐม สามพราน --forecast daily --duration 7

# กำหนด output เอง
uv run src/main.py --location นครปฐม สามพราน --output results.csv
```

หรือใช้ `make run` แทน `uv run src/main.py`

## Flags

| Flag                         | ค่าเริ่มต้น                      | คำอธิบาย                             |
| ---------------------------- | ---------------------------- | ---------------------------------- |
| `--location PROVINCE AMPHOE` | —                            | จังหวัด + อำเภอ (ใช้ซ้ำได้)               |
| `--locations PATH`           | —                            | ไฟล์ JSON รายการสถานที่               |
| `--lat` / `--lon`            | —                            | พิกัด GPS (ต้องใช้คู่กัน)                 |
| `--forecast`                 | `hourly`                     | `hourly` หรือ `daily`               |
| `--fields`                   | `tc,rh` / `tc_min,tc_max,rh` | ฟิลด์ที่ต้องการ คั่นด้วยคอมมา              |
| `--date`                     | วันนี้ (GMT+7)                  | วันที่ในรูปแบบ `YYYY-MM-DD`            |
| `--hour`                     | ชั่วโมงปัจจุบัน (GMT+7)           | ชั่วโมง 0–23 (เฉพาะ hourly)          |
| `--duration`                 | `24`                         | จำนวนชั่วโมง (max 48) หรือวัน (max 126) |
| `--output`                   | `weather_<ISO8601>.csv`      | path ไฟล์ CSV                       |
| `--verbose`                  | `false`                      | เปิด DEBUG logging                  |

## รูปแบบ locations JSON

```json
[
  { "province": "นครปฐม", "amphoe": "สามพราน" },
  { "province": "กรุงเทพมหานคร", "amphoe": "พระนคร" },
  { "lat": 13.7563, "lon": 100.5018 }
]
```

## คำสั่ง make

| คำสั่ง              | ทำอะไร                   |
| ---------------- | ----------------------- |
| `make run`       | รัน CLI                  |
| `make test`      | รัน pytest               |
| `make check`     | lint + typecheck + test |
| `make lint`      | ruff check              |
| `make format`    | ruff format             |
| `make typecheck` | pyright                 |
| `make sync`      | uv sync                 |
| `make audit`     | pip-audit               |
