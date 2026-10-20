

# TÀI LIỆU THIẾT KẾ HỆ THỐNG

# SECURE MCP GATEWAY (MVP)

**Phiên bản:** MVP\
**Thời gian triển khai:** 4 ngày làm việc\
**Mục tiêu:** Xây dựng lớp bảo mật trung gian giữa AI Agent và hệ thống Trino MCP, đảm bảo kiểm soát quyền truy cập, thực thi truy vấn SQL an toàn và ghi nhật ký kiểm toán.

---

## 1\. Tổng quan kiến trúc và mô hình Proxy

### 1.1. Tổng quan hệ thống

Secure MCP Gateway đóng vai trò là một **Security Choke Point** (điểm kiểm soát bảo mật bắt buộc), nằm giữa AI Agent và repository `trino-mcp` gốc.

Gateway chịu trách nhiệm kiểm tra quyền truy cập, kiểm duyệt truy vấn SQL và ghi nhật ký bảo mật trước khi chuyển tiếp các yêu cầu hợp lệ đến hệ thống upstream.

**Nguyên tắc thiết kế cốt lõi:**

- **Không sửa đổi mã nguồn upstream:** Tuyệt đối không thay đổi repository `trino-mcp` gốc.
- **Tuân thủ giao thức MCP:** Gateway giao tiếp với upstream theo chuẩn Model Context Protocol (MCP).
- **Kiểm soát tập trung:** Mọi yêu cầu từ AI Agent phải đi qua Gateway trước khi được chuyển tiếp.
- **Bảo mật theo nguyên tắc mặc định từ chối:** Các yêu cầu không được cấp quyền hoặc không đáp ứng chính sách bảo mật sẽ bị từ chối.

### 1.2. Mô hình hoạt động kép (Dual-Role)

Secure MCP Gateway đảm nhận hai vai trò:

- **Đối với AI Agent:** Gateway hoạt động như một MCP Server, tiếp nhận yêu cầu khám phá và thực thi công cụ.
- **Đối với Trino MCP gốc:** Gateway hoạt động như một MCP Client, chuyển tiếp các yêu cầu đã vượt qua bước kiểm tra bảo mật.

### 1.3. Sơ đồ kiến trúc tổng thể

```
+-------------+
|  AI Agent   |
+-------------+
       |
       | MCP Protocol
       | tools/list / tool execution
       v
+--------------------------------------------------+
|              SECURE MCP GATEWAY                  |
|                                                  |
|  1. Tool Discovery & Visibility                  |
|  2. RBAC Engine                                  |
|  3. SQL Security Engine (AST Parser)              |
|  4. Audit Logger                                 |
|  5. MCP Proxy Client                             |
+--------------------------------------------------+
       |
       | Chỉ chuyển tiếp khi được cấp quyền
       | Standard MCP Transport
       v
+-------------------------+
|      Trino MCP Gốc      |
|    (Giữ nguyên 100%)    |
+-------------------------+
       |
       | Trino Protocol
       | Read-only theo chính sách Gateway
       v
+-------------------------+
|      Trino Engine       |
|     (PG / MySQL)        |
+-------------------------+
```

---

## 2\. Các thành phần và luồng xử lý chi tiết

### 2.1. Module 1: Tool Discovery & Visibility (`tools/list`)

**Mục tiêu:** Chỉ hiển thị những công cụ mà AI Agent được phép sử dụng theo chính sách phân quyền.

Khi AI Agent khởi tạo kết nối, nó gửi yêu cầu `tools/list` để lấy danh sách công cụ khả dụng.

**Luồng xử lý:**

1. Gateway tiếp nhận request và xác định `principal_id` từ ngữ cảnh xác thực đáng tin cậy do tầng server cung cấp.
2. Gateway truy vấn RBAC Engine để xác định role tương ứng với principal.
3. Gateway lấy danh sách công cụ từ Trino MCP upstream.
4. Gateway lọc danh sách công cụ theo allowlist được quy định cho role.
5. Gateway trả về danh sách công cụ đã được kiểm soát cho AI Agent.

**Ví dụ:**

Role `data_analyst` chỉ được phép sử dụng các công cụ đọc dữ liệu như:

- `execute_query_read_only`
- `list_tables`
- Các công cụ đọc metadata được chính sách cho phép.

Công cụ thực thi truy vấn tổng quát như `execute_query` sẽ bị ẩn nếu role không được cấp quyền tương ứng.

**Nguyên tắc bảo mật:** Việc ẩn công cụ chỉ là lớp kiểm soát hiển thị. Gateway vẫn phải kiểm tra quyền ở thời điểm thực thi để ngăn Agent gọi trực tiếp một công cụ không được phép.

### 2.2. Module 2: RBAC Engine (Role-Based Access Control)

#### 2.2.1. Vai trò và nguồn chính sách

RBAC Engine chịu trách nhiệm xác định quyền hạn của từng principal và kiểm tra quyền truy cập ở cấp độ công cụ, catalog và bảng dữ liệu.

Bảng `agent_role_permissions` trong catalog MySQL được sử dụng làm **Security Control Plane**, đóng vai trò là nguồn chính sách RBAC chính thức của Secure MCP Gateway.

Các chức năng chính:

- Ánh xạ `principal` sang `role`.
- Kiểm tra quyền sử dụng công cụ.
- Kiểm tra phạm vi catalog được phép truy cập.
- Kiểm tra danh sách bảng được phép và bị cấm.
- Cung cấp thông tin chính sách phục vụ Audit Logger.

#### 2.2.2. Đặc tả schema `agent_role_permissions`

| Tên cột | Ý nghĩa | Ghi chú thực thi trong MVP |
| --- | --- | --- |
| `id` | Định danh policy | Khóa chính (Primary Key), dùng để định danh bản ghi và liên kết với `policy_version` trong Audit Log. |
| `role_name` | Role áp dụng | Tên vai trò, ví dụ `public_viewer`, `business_analyst`. Không suy diễn quyền chỉ dựa trên tên role. |
| `allowed_catalogs` | Catalog được phép | Danh sách catalog được phép truy cập, ví dụ `pg`, `mysql`. |
| `allowed_tables` | Danh sách bảng được phép | Các bảng được phép đọc dữ liệu hoặc metadata. |
| `denied_tables` | Danh sách bảng bị cấm | Các bảng bị từ chối tường minh; ưu tiên từ chối nếu trùng với `allowed_tables`. |
| `can_export_file` | Quyền xuất dữ liệu ra file | Mặc định `false` trong MVP nếu chưa có yêu cầu xuất file. |
| `max_row_limit` | Giới hạn số dòng | Số dòng tối đa được trả về cho mỗi truy vấn nhằm hạn chế tiêu thụ tài nguyên. |
| `can_execute_ddl` | Quyền thực thi DDL | Mặc định không cho phép Agent thực hiện DDL trong MVP, bất kể cấu hình. |
| `can_access_pii` | Quyền truy cập PII | Xác định role có được truy cập dữ liệu cá nhân nhạy cảm hay không, ví dụ trong bảng `customers`, `employees`. |
| `created_at` | Thời điểm tạo policy | Thời điểm khởi tạo bản ghi chính sách. |
| `updated_by` | Chủ thể cập nhật policy | Danh tính quản trị viên hoặc hệ thống có thẩm quyền thay đổi chính sách. |

**Lưu ý:** Schema trên gồm 11 cột theo đặc tả ban đầu. Kiểu dữ liệu cụ thể và cách biểu diễn danh sách trong `allowed_catalogs`, `allowed_tables`, `denied_tables` cần được xác định khi triển khai.

### 2.3. Module 3: SQL Security Engine (AST Parser)

**Mục tiêu:** Kiểm duyệt truy vấn SQL trước khi chuyển tiếp đến upstream, ngăn chặn thao tác ghi trái phép và giới hạn phạm vi dữ liệu được truy cập.

Module này áp dụng cho các công cụ thực thi truy vấn, đặc biệt là `execute_query_read_only`.

Để kiểm tra truy vấn, Gateway sử dụng thư viện phân tích cú pháp SQL AST như `sqlglot`, thay vì dựa vào Regex.

#### 2.3.1. Quy trình kiểm tra SQL

**Bước 1: Parse AST**

Phân tích chuỗi SQL thành cây cú pháp trừu tượng (Abstract Syntax Tree - AST) với dialect phù hợp với Trino.

Nếu truy vấn không hợp lệ hoặc không thể phân tích an toàn, Gateway từ chối thực thi.

**Bước 2: Chặn thao tác ghi (Read-Only Enforcement)**

Kiểm tra cấu trúc AST và từ chối các câu lệnh không được phép, bao gồm:

- DML: `INSERT`, `UPDATE`, `DELETE`, `MERGE`.
- DDL: `CREATE`, `DROP`, `ALTER`.
- Các thao tác quản trị quyền như `GRANT`, cùng những câu lệnh không nằm trong allowlist.

Không chỉ kiểm tra từ khóa ở dạng chuỗi; việc kiểm duyệt phải dựa trên cấu trúc cú pháp thực tế.

**Bước 3: Kiểm tra quyền truy cập bảng (Table-Level Authorization)**

Gateway trích xuất toàn bộ bảng được tham chiếu trong AST, bao gồm các trường hợp:

- Truy vấn trực tiếp.
- `JOIN`.
- `SUBQUERY`.
- `CTE`.

Danh sách bảng được đối chiếu với chính sách RBAC:

- Catalog phải thuộc `allowed_catalogs`.
- Bảng phải thuộc phạm vi được phép.
- Bảng thuộc `denied_tables` luôn bị từ chối, kể cả khi đồng thời xuất hiện trong `allowed_tables`.

Nếu phát hiện bất kỳ bảng nào không được phép truy cập, Gateway từ chối toàn bộ truy vấn.

**Bước 4: Kiểm soát tài nguyên**

Áp dụng các biện pháp giới hạn cơ bản:

- Kiểm tra giới hạn số dòng trả về theo `max_row_limit`.
- Từ chối hoặc kiểm duyệt các truy vấn có cấu trúc rủi ro cao, chẳng hạn `CROSS JOIN`.
- Xử lý các truy vấn không đáp ứng yêu cầu kiểm soát tài nguyên theo chính sách.

### 2.4. Module 4: Audit Logger (Ghi nhật ký bảo mật)

**Mục tiêu:** Ghi nhận đầy đủ các quyết định truy cập để phục vụ giám sát, truy vết và báo cáo bảo mật.

Mọi quyết định truy cập, bao gồm `ALLOW` và `DENY`, đều phải được ghi lại dưới dạng JSON có cấu trúc.

#### 2.4.1. Các trường thông tin bắt buộc

| Trường | Mô tả |
| --- | --- |
| `request_id` | Mã định danh duy nhất của request. |
| `timestamp` | Thời điểm phát sinh quyết định. |
| `principal_id` | Định danh chủ thể thực hiện request. |
| `role` | Vai trò của principal tại thời điểm kiểm tra. |
| `tool_name` | Tên công cụ được yêu cầu thực thi. |
| `query_hash` | Giá trị băm của câu SQL, nếu request có truy vấn SQL. |
| `decision` | Kết quả quyết định: `ALLOW` hoặc `DENY`. |
| `reason_code` | Mã lý do cho quyết định, đặc biệt đối với các trường hợp từ chối. |

Audit Log cần được thiết kế theo hướng hạn chế ghi trực tiếp dữ liệu nhạy cảm, đồng thời đảm bảo khả năng liên kết giữa request, chính sách áp dụng và quyết định bảo mật.

---

## 3\. Cấu trúc thư mục dự án

Cấu trúc dưới đây được tối ưu cho **MVP triển khai trong 4 ngày làm việc**. Phạm vi được tinh gọn, tập trung vào năm thành phần cốt lõi:

1. Tool Discovery & Visibility.
2. RBAC Engine.
3. SQL AST Parser.
4. MCP Proxy Client.
5. Audit Logger.

### 3.1. Cây thư mục

```
secure-agentic-bi-gateway/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── context.py
│   │   └── exceptions.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── rbac_engine.py
│   │   ├── sql_engine.py
│   │   └── proxy_client.py
│   │
│   └── utils/
│       ├── __init__.py
│       └── audit_logger.py
│
├── tests/
│   ├── __init__.py
│   ├── test_rbac.py
│   ├── test_sql_engine.py
│   └── test_security_flow.py
│
├── .env.example
├── Dockerfile
├── requirements.txt
└── README.md
```

### 3.2. Mô tả chức năng từng thành phần

| Thành phần | Trách nhiệm |
| --- | --- |
| `app/main.py` | Điểm khởi chạy Gateway; tiếp nhận yêu cầu MCP, xử lý `tools/list` và điều phối luồng thực thi công cụ. |
| `app/config.py` | Quản lý cấu hình thông qua biến môi trường, bao gồm kết nối MySQL và cấu hình Trino MCP upstream. |
| `app/core/context.py` | Quản lý ngữ cảnh request, trích xuất `principal_id` và `request_id` từ nguồn đáng tin cậy. |
| `app/core/exceptions.py` | Định nghĩa các ngoại lệ bảo mật chuẩn, ví dụ `SecurityError`, `PermissionError`. |
| `app/services/rbac_engine.py` | Truy vấn bảng `agent_role_permissions`, ánh xạ principal sang role và kiểm tra quyền truy cập. |
| `app/services/sql_engine.py` | Sử dụng `sqlglot` để phân tích AST, chặn câu lệnh không hợp lệ và kiểm tra quyền truy cập bảng. |
| `app/services/proxy_client.py` | Hoạt động như MCP Client, chuyển tiếp request hợp lệ đến repository `trino-mcp` gốc mà không sửa đổi upstream. |
| `app/utils/audit_logger.py` | Ghi nhật ký JSON cho các quyết định `ALLOW` và `DENY`. |
| `tests/test_rbac.py` | Kiểm thử phân quyền role và allowlist công cụ. |
| `tests/test_sql_engine.py` | Kiểm thử AST Parser, chặn thao tác ghi và phát hiện bảng không được phép. |
| `tests/test_security_flow.py` | Kiểm thử end-to-end, đảm bảo request độc hại bị chặn trước khi đến upstream. |
| `.env.example` | Cung cấp mẫu cấu hình môi trường, không chứa thông tin bí mật thực tế. |
| `Dockerfile` | Định nghĩa cấu hình đóng gói Gateway thành container. |
| `requirements.txt` | Khai báo các thư viện Python cần thiết. |
| `README.md` | Hướng dẫn cài đặt, cấu hình, chạy hệ thống và thực hiện kiểm thử. |

---