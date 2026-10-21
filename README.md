# 🛡️ Secure Agentic BI Framework

![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.12%20%7C%203.13-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-19.0-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![Trino](https://img.shields.io/badge/Trino-Coordinator-DD00A1?style=for-the-badge&logo=trino&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose%20v2-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![MCP](https://img.shields.io/badge/Protocol-Model%20Context%20Protocol%20(MCP)-blueviolet?style=for-the-badge)
![Security](https://img.shields.io/badge/Architecture-Neuro--Symbolic%20Defense-brightgreen?style=for-the-badge)

> **Kiến trúc Phòng thủ Neuro-Symbolic và Giao thức Chuẩn hóa Model Context Protocol (MCP) dành cho Hệ thống Trí tuệ Kinh doanh Tự trị (Agentic Business Intelligence).**

---

## 📖 1. Giới thiệu dự án (Overview)

### 1.1. Bối cảnh & Tóm tắt dự án

**Secure Agentic BI Framework** là một nền tảng **Agentic Business Intelligence** thế hệ mới, cho phép người dùng kinh doanh (Business Analysts, Quản lý, Giám đốc) truy vấn, phân tích và tổng hợp dữ liệu doanh nghiệp đa nguồn thông qua giao diện hội thoại ngôn ngữ tự nhiên (*Natural Language to SQL - NL2SQL*).

Thay vì phụ thuộc vào cách tiếp cận thuần Neural (chỉ dựa vào tính tự kiềm chế của Large Language Model thông qua System Prompt), hệ thống tiên phong ứng dụng **Kiến trúc Phòng thủ Lai Neuro-Symbolic**:

- **Khối Neural (LLM - Google Gemini):** Đảm nhiệm việc suy luận ngữ nghĩa tự nhiên, phân tích mục đích người dùng và sinh kế hoạch truy vấn SQL linh hoạt.
- **Khối Symbolic (Formal Verification Gateways):** Đóng vai trò rào chắn kiểm chứng toán học tất định (Deterministic Gateways) với bộ phân tích cây cú pháp trừu tượng (**AST** qua `sqlglot`), kiểm soát tài nguyên ngắt mạch (**Circuit Breaker**), phân quyền ma trận (**RBAC**) và cách ly chỉ thị độc (**Taint Filter**).

### 1.2. Vấn đề giải quyết & Các mối đe dọa an ninh (Threat Model)

Khi tích hợp LLM trực tiếp vào cơ sở dữ liệu doanh nghiệp phân tán (Federated Databases), hệ thống đối mặt với những lỗ hổng an ninh nghiêm trọng. **Secure Agentic BI Framework** giải quyết triệt để 6 nhóm tấn công đối kháng (Adversarial Attacks) theo các công trình nghiên cứu bảo mật hàng đầu:

| Nhóm tấn công | Vector đe dọa thực tế | Cơ chế phòng thủ của hệ thống | Nghiên cứu tham chiếu |
| :--- | :--- | :--- | :--- |
| **1. Prompt-to-SQL Injection** | Prompt ép LLM sinh lệnh phá hoại CSDL (`DROP TABLE`, `UPDATE`, `DELETE`, `TRUNCATE`, `INSERT`). | **Symbolic AST Guardrail:** Bắt buộc duy nhất `exp.Select`, cấm hoàn toàn ký tự `;` (chống Stacked Query) và chặn mọi node DDL/DML. | *Pedro et al., ICSE 2025* |
| **2. Denial of Service (DoS)** | Truy vấn làm cạn kiệt tài nguyên máy chủ (`CROSS JOIN` tích Descartes, `WITH RECURSIVE` vô hạn, Subquery N+1). | **Resource AST + Circuit Breaker:** Chặn đệ quy và phép Join thiếu điều kiện `ON/USING`; timeout ngắt mạch cứng 3–10s; Semaphore giới hạn truy vấn đồng thời. | *Shumailov et al. (EuroS&P) / USENIX Security 2026* |
| **3. PII & Secret Leakage** | Dò tìm metadata ẩn (`information_schema`), đánh cắp bảng lương HR, API keys, số thẻ tín dụng hoặc federated join vượt quyền. | **RBAC Schema Filter:** Lọc ngữ cảnh tối thiểu (Least-Privilege Schema Injection), kiểm tra ma trận bảng được phép (`allowed_tables`) tại cấp AST. | *Lukas et al., IEEE S&P 2023* |
| **4. Indirect Prompt Injection** | Dữ liệu nội dung bảng (UGC reviews, support tickets, logs) chứa chỉ thị độc nhằm chiếm quyền điều khiển LLM. | **Table Content Taint Filter:** Cô lập dữ liệu thô thành *Passive Text Only*, phân tách ranh giới dữ liệu và lệnh thực thi. | *Greshake et al. (AISec 2023) / AgentDojo (NeurIPS 2024)* |
| **5. Confused Deputy** | Ép Agent lưu trữ dữ liệu ra ngoài sandbox thư mục (Path traversal ra `.env`, `docker-compose.yml`, `/etc/passwd`) hoặc sửa role. | **Sandbox Canonicalization + AST DML Defense:** Cô lập file export trong sandbox nội bộ và cấm DML sửa đổi cấu hình role. | *Capability Gates (2026)* |
| **6. Memory Poisoning** | Làm nhiễm độc lịch sử truy vấn (`agent_query_history`) hoặc semantic cache để lây lan mã độc qua các phiên sau. | **Zero-Trust Memory Validation:** Tái thẩm định toàn bộ câu lệnh SQL lấy từ cache/history qua AST Guardrail trước khi thực thi. | *Chen et al., AgentPoison (NeurIPS 2024)* |

---

## 🏛️ 2. Kiến trúc hệ thống (Architecture)

Hệ thống được thiết kế theo mô hình Microservices phân tán với tính độc lập cao giữa 4 phân tầng chính:

```mermaid
flowchart TD
    subgraph UI_Layer ["1. FRONTEND TIER (Client Dashboard)"]
        UI["React 19 + Vite Console<br/>Split-pane Threat Intelligence"]
        Trace["Live Observability Console<br/>NDJSON Stream Monitor"]
    end

    subgraph API_Layer ["2. BACKEND API TIER (FastAPI Gateway)"]
        Router["/api/v1/agent/query_stream"]
        S1["(1) RBAC Policy Lookup"]
        S2["(2) Schema Context Injection"]
        S3["(3) Gemini ReAct Routing"]
        S4["(4) AST Guardrail (sqlglot)"]
        S5["(5) Reflexion Repair Loop"]
        S6["(6) Circuit Breaker & Taint Filter"]
    end

    subgraph MCP_Layer ["3. MCP PROTOCOL TIER (trino-mcp)"]
        MCPServer["Trino MCP Server (Stdio JSON-RPC)<br/>Tool: execute_query_read_only"]
        Semaphore["Concurrency Semaphore & Timeout"]
    end

    subgraph Data_Layer ["4. FEDERATED DATA INFRASTRUCTURE (Docker Network)"]
        Trino["Trino Coordinator Engine (v439+)<br/>Port 8080 (Single Query Entrypoint)"]
        PG[("PostgreSQL 16 (analytics_db)<br/>Catalog 'pg' · 13 Bảng ERP/Finance")]
        MySQL[("MySQL 8.4 (agentic_bi)<br/>Catalog 'mysql' · 8 Bảng UGC/Audit/RBAC")]
    end

    UI -->|Gửi Prompt + Actor Role| Router
    Router --> S1 --> S2 --> S3 --> S4
    S4 -->|Vi phạm AST| S5
    S5 -->|Phản hồi lỗi chi tiết| S3
    S4 -->|Hợp lệ| MCPServer
    MCPServer --> Semaphore --> Trino
    Trino -->|Federated Query| PG
    Trino -->|Federated Query| MySQL
    Trino -->|Dữ liệu thô / Timeout| S6
    S6 -->|Safe Answer Markdown| Trace
```

### Các module độc lập:

1. **Frontend (**`frontend/`**):** Xây dựng bằng React 19, Vite, Tailwind CSS, Lucide Icons, Mermaid.js. Cung cấp bảng điều khiển Red-Teaming với 27 kịch bản tấn công đối kháng mẫu, trình theo dõi tiến trình thực thi thời gian thực qua luồng NDJSON Stream.
2. **Backend API (**`backend_api/`**):** Phát triển trên nền FastAPI (Python 3.10+), chịu trách nhiệm điều phối toàn bộ chu trình bảo mật, quản lý kết nối CSDL cấu hình RBAC qua SQLAlchemy và giao tiếp bất đồng bộ với LLM & MCP.
3. **MCP Server (**`mcp_servers/trino-mcp/`**):** Cài đặt chuẩn Model Context Protocol (Anthropic MCP SDK) qua kênh Stdio JSON-RPC. Cô lập hoàn toàn thông tin đăng nhập database khỏi Agent; cung cấp tool chỉ đọc an toàn `execute_query_read_only`.
4. **Hạ tầng CSDL Liên kết (**`infrastructure/`**):** Cụm Docker Compose kết nối 3 container trên mạng nội bộ `bi-network`:
   - **PostgreSQL 16 (**`analytics_db`**):** 13 bảng phân tích dữ liệu bán hàng, kho vận, nhân sự và tài chính.
   - **MySQL 8.4 (**`agentic_bi`**):** 8 bảng quản lý chính sách RBAC, audit logs, semantic cache và dữ liệu UGC bẫy tấn công.
   - **Trino Coordinator:** Cổng truy vấn phân tán liên kết (Federated Engine) liên kết đồng thời 2 catalog `pg` và `mysql` (tổng cộng **21 bảng dữ liệu**).

---

## 🔒 3. Cơ chế bảo mật cốt lõi (Core Security Pipeline - 6 Bước)

Toàn bộ truy vấn của người dùng đều bắt buộc phải đi qua chu trình phòng vệ 6 bước khép kín trước khi dữ liệu được hoàn trả:

```mermaid
sequenceDiagram
    autonumber
    actor User as Người dùng / Red Team
    participant GW as FastAPI Gateway
    participant DB as MySQL (RBAC)
    participant MCP as Trino MCP Server
    participant LLM as Google Gemini (ReAct)
    participant AST as AST Guardrail (sqlglot)
    participant Trino as Trino Engine

    User->>GW: Gửi câu hỏi BI + Role (vd: analyst)
    GW->>DB: (1) RBAC Lookup: Lấy policy của Role
    DB-->>GW: Trả về allowed/denied catalogs & tables
    GW->>MCP: Lấy schema tổng quan qua system.jdbc.columns
    MCP-->>GW: Trả về toàn bộ metadata
    GW->>GW: (2) Schema Context Injection: Loại bỏ hoàn toàn bảng cấm
    GW->>LLM: (3) Gemini ReAct Routing: Gửi prompt kèm Filtered Schema
    LLM-->>GW: Sinh JSON Tool Call (chứa câu lệnh SQL)
    GW->>AST: (4) AST Guardrail: Duyệt cây cú pháp sqlglot
    alt Cú pháp vi phạm (DML, DoS, Bảng ngoài scope)
        AST-->>GW: Blocked + Lý do cụ thể
        GW->>LLM: (5) Auto-Reflexion: Gửi phản hồi lỗi để tự sửa (Max 3 lần)
    else Hợp lệ
        AST-->>GW: Passed
        GW->>Trino: Thực thi SQL với Circuit Breaker (Timeout 5-10s)
        Trino-->>GW: Trả về Raw Result Dataset
        GW->>LLM: (6) Taint Filter: Xử lý dữ liệu thô như Passive Text
        LLM-->>GW: Tổng hợp câu trả lời nghiệp vụ an toàn
        GW-->>User: Hiển thị kết quả an toàn trên giao diện
    end
```

### Chi tiết 6 bước bảo mật:

1. **Bước 1: RBAC Authentication & Policy Lookup**
   - Xác thực danh tính vai trò của người dùng (`analyst`, `sales`, `support`, `hr`, `admin`) từ bảng `agent_role_permissions`.
   - Xác định danh sách catalog cho phép (`allowed_catalogs`), bảng được truy cập (`allowed_tables`), bảng bị cấm tuyệt đối (`denied_tables`), giới hạn dòng (`max_row_limit`) và quyền xem dữ liệu PII (`can_access_pii`).
2. **Bước 2: Schema Context Injection (Least-Privilege Schema Injection)**
   - Khám phá metadata từ Trino MCP (`system.jdbc.columns`).
   - Bộ lọc `schema_filter.py` chủ động cắt tỉa toàn bộ các bảng nằm trong danh sách cấm hoặc không thuộc quyền hạn trước khi gửi cho LLM. Mô hình hoàn toàn không biết sự tồn tại của các bảng nhạy cảm (như `hr_payroll`, `api_keys_config`).
3. **Bước 3: Gemini ReAct Routing (Neural Planning)**
   - Google Gemini (hỗ trợ tự động fallback danh sách models: `gemini-2.5-flash`, `gemini-3.5-flash`, ...) tiếp nhận ngữ cảnh tối thiểu và yêu cầu của người dùng.
   - LLM sinh ra bản kế hoạch suy luận (Chain-of-Thought) kèm tool call `execute_query_read_only` dưới định dạng JSON có cấu trúc nghiêm ngặt.
4. **Bước 4: AST Guardrail Verification (Symbolic Verification qua** `sqlglot`**)**
   - Trước khi rời Gateway, câu lệnh SQL được phân tích bằng `sqlglot` (dialect `trino`):
     - **Cấm đa lệnh:** Loại bỏ triệt để dấu chấm phẩy (`;`) để ngăn chặn Stacked SQL Injection.
     - **Chỉ chấp nhận SELECT:** Kiểm tra kiểu node gốc phải là `exp.Select`.
     - **Chặn toàn bộ DDL/DML:** Cấm các node `exp.Insert`, `exp.Update`, `exp.Delete`, `exp.Drop`, `exp.Alter`, `exp.Create`, `exp.Grant`, `exp.Revoke`.
     - **Chống DoS:** Cấm `WITH RECURSIVE` và cấm `CROSS JOIN` hoặc các lệnh `JOIN` không có điều kiện `ON`/`USING`.
     - **Thẩm định bảng:** Mọi định danh bảng (`catalog.schema.table`) bắt buộc phải thuộc danh mục được cấp phép của Role.
5. **Bước 5: Auto-Reflexion Repair Loop**
   - Nếu câu lệnh bị AST chặn hoặc Trino báo lỗi thực thi (sai tên cột, lỗi kiểu dữ liệu), mã lỗi sẽ được gói thành `REFLEXION FEEDBACK` gửi ngược lại cho LLM.
   - LLM tự phân tích nguyên nhân lỗi và tái sinh câu truy vấn đã sửa chữa (giới hạn tối đa `max_iterations = 3`), giúp tăng tỷ lệ thực thi thành công mà không làm suy giảm tính an toàn.
6. **Bước 6: Circuit Breaker & Taint Filter**
   - **Circuit Breaker:** Đặt ngưỡng timeout cứng (3–10 giây) qua `asyncio.wait_for`. Nếu một truy vấn phân tích quét khối dữ liệu khổng lồ hoặc gây tắc nghẽn, ngắt mạch sẽ chủ động hủy truy vấn ngay lập tức, giải phóng tài nguyên cụm Trino.
   - **Taint Filter:** Dữ liệu trả về từ CSDL được dán nhãn là *Passive Text Only*. Tại tầng tổng hợp, System Prompt yêu cầu LLM chỉ trích xuất thông tin định lượng, tuyệt đối không tuân theo bất kỳ mệnh lệnh hay mã lệnh tiềm ẩn nào bên trong các trường văn bản người dùng (UGC).

---

## 💻 4. Yêu cầu hệ thống (Prerequisites)

Trước khi tiến hành cài đặt, hãy đảm bảo máy tính của bạn đã cài đặt các phần mềm sau:

- **Hệ điều hành:** Linux, macOS (Apple Silicon / Intel), hoặc Windows (thông qua WSL2).
- **Python:** Phiên bản `>= 3.10` (Khuyến nghị **Python 3.12** hoặc **Python 3.13**).
- **Node.js:** Phiên bản `>= 18.0.0` (Khuyến nghị Node.js 20 LTS hoặc 22) kèm theo trình quản lý gói `npm`.
- **Docker & Docker Compose:** Docker Engine `>= 24.0` và Docker Compose Plugin `v2` trở lên.
- **Tài nguyên phần cứng khuyến nghị:**
  - RAM: Tối thiểu 8 GB (Khuyến nghị 16 GB để chạy đồng thời cụm Trino, PostgreSQL, MySQL và 2 tiến trình Node/Python).
  - Ổ cứng: Trống tối thiểu 10 GB.
- **Khóa API Google Gemini:** Cần có một `GEMINI_API_KEY` hợp lệ lấy miễn phí từ [Google AI Studio](https://aistudio.google.com/).

---

## 🛠️ 5. Hướng dẫn cài đặt (Installation)

### Bước 1: Clone kho mã nguồn

```bash
git clone https://github.com/your-username/secure_agentic_BI.git
cd secure_agentic_BI
```

### Bước 2: Thiết lập biến môi trường (`.env`)

#### 1. Cấu hình cho Backend API (`backend_api/.env`):

Sao chép từ file mẫu và chỉnh sửa các biến cần thiết:

```bash
cp backend_api/.env.example backend_api/.env
```

Mở file `backend_api/.env` và cập nhật:

```env
# URL kết nối cơ sở dữ liệu MySQL lưu trữ RBAC & Metadata
DATABASE_URL=mysql+pymysql://bi_agent:bi_agent_pass@localhost:13306/agentic_bi

# Đường dẫn tuyệt đối đến file thực thi Python trong môi trường ảo của trino-mcp
# (Ví dụ: /Users/username/.../mcp_servers/trino-mcp/.venv/bin/python hoặc dùng python hiện tại)
PYTHON_BIN_PATH=/Users/nguyenthanh/Master/NewGenerationSoftwareEngineering/pro/pro/secure_agentic_BI/mcp_servers/trino-mcp/.venv/bin/python

# Đường dẫn thư mục mã nguồn Trino MCP Server
TRINO_MCP_DIR=/Users/nguyenthanh/Master/NewGenerationSoftwareEngineering/pro/pro/secure_agentic_BI/mcp_servers/trino-mcp

# Khóa API của Google Gemini
GEMINI_API_KEY=AIzaSyYourGeminiApiKeyHere...

# Danh sách model Gemini sử dụng (hỗ trợ tự động fallback khi bị rate limit 429)
AVAILABLE_MODELS=["models/gemini-2.5-flash","models/gemini-3.5-flash","models/gemini-3.1-flash-lite","models/gemini-3.5-flash-lite","models/gemini-3.6-flash","models/gemma-4-26b-a4b-it"]
```

> [!TIP]
> Bạn có thể chạy lệnh sau để lấy đường dẫn Python nhanh:
>
> ```bash
> which python3
> ```

#### 2. Cấu hình cho Trino MCP Server (`mcp_servers/trino-mcp/.env`):

```bash
cp mcp_servers/trino-mcp/.env.example mcp_servers/trino-mcp/.env
```

Nội dung mặc định đã được cấu hình tối ưu để kết nối với Trino Docker:

```env
TRINO_HOST=localhost
TRINO_PORT=8080
TRINO_USER=admin
TRINO_HTTP_SCHEME=http
AUTH_METHOD=NONE
ALLOW_WRITE_QUERIES=false
QUERY_TIMEOUT_MINUTES=2
MAX_CONCURRENT_QUERIES=1
```

---

### Bước 3: Cài đặt thư viện phụ thuộc

#### 1. Cài đặt môi trường ảo và thư viện cho Trino MCP Server:

```bash
cd mcp_servers/trino-mcp
python3 -m venv .venv
source .venv/bin/activate       # Trên Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -e .
deactivate
cd ../..
```

#### 2. Cài đặt môi trường ảo và thư viện cho Backend API:

```bash
cd backend_api
python3 -m venv .venv
source .venv/bin/activate       # Trên Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
cd ..
```

#### 3. Cài đặt các gói phụ thuộc cho Frontend:

```bash
cd frontend
npm install
cd ..
```

---

## 🚀 6. Hướng dẫn khởi chạy & Sử dụng (Usage)

Để khởi chạy toàn bộ hệ thống, bạn có thể sử dụng các script tự động hoặc khởi chạy từng thành phần thủ công:

### Cách 1: Khởi động nhanh bằng Shell Scripts (Khuyến nghị)

#### Bước 1: Bật cụm CSDL phân tán (Docker Compose)

Tại thư mục gốc dự án:

```bash
./start.sh
```

*(Hoặc chạy trực tiếp* `./infrastructure/start.sh`*)*

Lệnh này sẽ khởi động 3 container chạy ngầm:

- **Trino Coordinator:** `http://localhost:8080`
- **PostgreSQL 16:** `localhost:5432`
- **MySQL 8.4:** `localhost:13306`

#### Bước 2: Khởi động Backend API (Terminal 1)

```bash
cd backend_api
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API Swagger UI kiểm thử: **[http://localhost:8000/docs](http://localhost:8000/docs)**

#### Bước 3: Khởi động Frontend Web Console (Terminal 2)

```bash
cd frontend
npm run dev
```

- Truy cập giao diện ứng dụng tại: **[http://localhost:5173](http://localhost:5173)**

---

### 🛑 Dừng hệ thống và giải phóng tài nguyên

Khi hoàn tất buổi làm việc hoặc kiểm thử, chạy lệnh:

```bash
./stop.sh
```

*(Hoặc chạy trực tiếp* `./infrastructure/stop.sh`*)*. Lệnh này sẽ hạ toàn bộ cụm container và giải phóng RAM, bộ nhớ đệm.

---

### 🎯 7. Trải nghiệm Red-Teaming & Đánh giá trên Giao diện

Khi mở Dashboard tại `http://localhost:5173`, bạn có thể thực hiện kiểm thử theo các bước:

1. **Chọn Actor Role:** Lựa chọn vai trò phù hợp (`analyst`, `sales`, `support`, `hr`, `admin`). Mỗi vai trò sở hữu ma trận quyền hạn khác nhau được quản trị từ bảng `agent_role_permissions`.
2. **Chọn Attack Scenario (Kịch bản tấn công đối kháng):** Hệ thống tích hợp sẵn 27 kịch bản kiểm thử:
   - *Baseline BI hợp lệ:* Doanh thu theo Category, Top nhân viên hiệu suất cao, Federated JOIN giữa Postgres và MySQL.
   - *Nhóm 1 (SQLi):* Yêu cầu `DROP TABLE pg.public.payments`, `UPDATE` đơn hàng, `DELETE` bản ghi.
   - *Nhóm 2 (DoS):* Kích hoạt `CROSS JOIN` không điều kiện, truy vấn đệ quy vô hạn `WITH RECURSIVE`.
   - *Nhóm 3 (PII Exfiltration):* Đòi hỏi xem bảng lương `hr_payroll`, thông tin thẻ tín dụng hoặc API secrets.
   - *Nhóm 4 (Indirect Injection):* Phân tích tickets hỗ trợ hoặc customer reviews chứa bẫy câu lệnh ẩn.
   - *Nhóm 5 & 6 (Confused Deputy & Memory Poisoning):* Path traversal ra file hệ thống, tái sử dụng SQL bị nhiễm độc trong cache.
3. **Nhấn "EXECUTE SECURE QUERY":** Quan sát luồng suy luận trực tiếp trong cửa sổ **Pipeline Monitor** qua luồng stream thời gian thực (NDJSON).
4. **Kiểm tra kết quả an toàn:**
   - Xem câu lệnh SQL do LLM sinh ra.
   - Xem phản hồi của AST Guardrail (Passed hoặc Blocked kèm lý do).
   - Xem số lượt tự sửa lỗi (*Reflexion Iterations*).
   - Xem thời gian thực thi CSDL và câu trả lời an toàn đã lọc Taint Filter.

---

## 📡 8. Danh mục API Endpoints (Backend API)

| Phương thức | Đường dẫn API | Mục đích kiểm thử / Nghiên cứu |
| :--- | :--- | :--- |
| `POST` | `/api/v1/agent/query` | **Baseline API:** Chỉ áp dụng thẩm định AST 1 lượt, không có vòng lặp sửa lỗi Reflexion. |
| `POST` | `/api/v1/agent/query_reflexion` | **Reflexion API:** Tích hợp vòng lặp tự động sửa lỗi SQL qua phản hồi AST và Trino. |
| `POST` | `/api/v1/agent/query_secure_pipeline` | **Full Pipeline API:** Tích hợp đầy đủ RBAC + AST + Reflexion + Circuit Breaker + Taint Filter. |
| `POST` | `/api/v1/agent/query_stream` | **Streaming API:** Trả về luồng sự kiện NDJSON thời gian thực phục vụ hiển thị trực quan trên Web UI. |

---

## 📂 9. Cấu trúc thư mục dự án (Project Structure)

```text
secure_agentic_BI/
├── backend_api/                     # Cổng dịch vụ Backend API Gateway (FastAPI)
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   │       └── agent.py         # Endpoints xử lý truy vấn, Reflexion và Stream NDJSON
│   │   ├── core/
│   │   │   └── config.py            # Cấu hình Pydantic BaseSettings tải biến môi trường
│   │   ├── db/
│   │   │   ├── database.py          # Khởi tạo SQLAlchemy Engine & Session
│   │   │   └── models.py            # Khai báo ORM model cho bảng agent_role_permissions
│   │   ├── schemas/
│   │   │   └── chat.py              # Pydantic Schemas cho Request/Response payload
│   │   ├── services/
│   │   │   ├── llm_service.py       # Tích hợp Gemini SDK, Fallback models, Prompt synthesis
│   │   │   ├── mcp_client.py        # Client kết nối Trino MCP Server qua Stdio JSON-RPC
│   │   │   ├── prompt_templates.py  # Mẫu System Prompts (ReAct, Taint Filter)
│   │   │   ├── rbac_service.py      # Tải và chuẩn hóa chính sách phân quyền vai trò
│   │   │   ├── schema_filter.py     # Lọc metadata theo danh sách cấm/cho phép của RBAC
│   │   │   └── sql_validator.py     # Bộ phân tích AST Guardrail độc lập bằng thư viện sqlglot
│   │   └── main.py                  # Điểm khởi động ứng dụng FastAPI và cấu hình CORS
│   ├── .env.example                 # File mẫu cấu hình môi trường backend
│   └── requirements.txt             # Danh sách thư viện Python cần thiết
│
├── frontend/                        # Giao diện điều khiển Red-Teaming & Observability (React 19)
│   ├── src/
│   │   ├── config/
│   │   │   └── scenarios.js         # Danh mục 27 kịch bản tấn công đối kháng chuẩn nghiên cứu
│   │   ├── App.jsx                  # Dashboard chia đôi: Console kiểm thử & Monitor luồng xử lý
│   │   ├── App.css                  # Giao diện hiện đại phong cách Cyber-Security tối màu
│   │   └── main.jsx                 # Điểm gắn kết DOM của React ứng dụng
│   ├── package.json                 # Cấu hình các gói phụ thuộc Node.js (Vite, Tailwind, Mermaid)
│   └── vite.config.js               # Cấu hình máy chủ phát triển Vite và Proxy chuyển tiếp API
│
├── mcp_servers/
│   └── trino-mcp/                   # Trino Model Context Protocol Server độc lập
│       ├── src/
│       │   └── trino_mcp/
│       │       ├── server.py        # Định nghĩa các tool MCP (execute_query_read_only,...)
│       │       └── client.py        # Quản lý kết nối Trino Engine, Semaphore và Timeout
│       ├── pyproject.toml           # Cấu hình gói thư viện Python theo chuẩn PEP 621
│       └── .env.example             # File mẫu tham số kết nối cụm Trino Coordinator
│
├── infrastructure/                  # Hạ tầng cơ sở dữ liệu liên kết và điều phối Docker
│   ├── catalog/
│   │   ├── pg.properties            # Cấu hình Trino Connector cho PostgreSQL (catalog pg)
│   │   └── mysql.properties         # Cấu hình Trino Connector cho MySQL (catalog mysql)
│   ├── docker/
│   │   └── mysql/init/
│   │       └── 01_init_mysql.sql    # Kịch bản khởi tạo 8 bảng MySQL (RBAC, Audit, UGC bẫy)
│   ├── init.sql                     # Kịch bản khởi tạo 13 bảng PostgreSQL (ERP, Bán hàng, PII)
│   ├── docker-compose.yml           # Khởi tạo cụm Postgres 16, MySQL 8.4 và Trino trên bi-network
│   ├── start.sh                     # Khởi động cụm CSDL nền
│   └── stop.sh                      # Dừng cụm CSDL và xóa volume an toàn
│
├── docs/                            # Tài liệu học thuật và báo cáo tiến độ nghiên cứu
│   ├── Interim_Report.md            # Báo cáo tiến độ Giữa kỳ chi tiết (Interim Technical Report)
│   └── Slide_Presentation.md        # Nội dung trình chiếu slide bảo vệ đề tài
│
├── start.sh                         # Shell script gốc khởi động toàn bộ hạ tầng
├── stop.sh                          # Shell script gốc tắt và giải phóng toàn bộ tài nguyên
├── .gitignore                       # Danh sách loại trừ các file tạm thời và môi trường
└── README.md                        # Tài liệu hướng dẫn sử dụng và tổng quan kỹ thuật dự án
```

---

## 👥 10. Thông tin nhóm tác giả & Đề tài học thuật

- **Cơ sở đào tạo:** Trường Đại học Bách Khoa TP. Hồ Chí Minh – Khoa Khoa học và Kỹ thuật Máy tính
- **Chương trình đào tạo:** Cao học Khoa học Máy tính & Kỹ thuật Phần mềm
- **Môn học:** Công nghệ Phần mềm Thế hệ Mới (*New Generation Software Engineering*)
- **Giảng viên hướng dẫn:** TS. Lê Xuân Bách
- **Nhóm học viên thực hiện (Nhóm 6):**
  1. **Nguyễn Công Thành** (MSHV: 2470744) — *Lead Author, Core Architect & Fullstack Developer*
  2. **Phạm Quỳnh Trân** (MSHV: 2470731) — *Frontend & Red-Teaming Evaluation Specialist*
  3. **Nguyễn Hữu Lợi** (MSHV: 2470012) — *Data Infrastructure & MCP Integration Engineer*

---

## 📄 11. Giấy phép bản quyền (License)

Dự án được phân phối dưới giấy phép **MIT License**. Chi tiết xin vui lòng xem file [LICENSE](mcp_servers/trino-mcp/LICENSE).
