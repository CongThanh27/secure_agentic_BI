# KỊCH BẢN TRÌNH BÀY BÁO CÁO GIỮA KỲ (SLIDE PRESENTATION - D2)

## ĐỀ TÀI: SECURE AGENTIC BI FRAMEWORK

### KIẾN TRÚC PHÒNG THỦ NEURO-SYMBOLIC VÀ GIAO THỨC MODEL CONTEXT PROTOCOL (MCP) CHO HỆ THỐNG TRÍ TUỆ KINH DOANH TỰ TRỊ

---

**THÔNG TIN TỔNG QUAN:**

- **Môn học:** Công nghệ Phần mềm Thế hệ Mới (Mã lớp: CO5151) – Học kỳ 1, Năm học 2026 – 2027
- **Đơn vị đào tạo:** Khoa Khoa học và Kỹ thuật Máy tính – Trường Đại học Bách Khoa TP. Hồ Chí Minh
- **Giảng viên hướng dẫn:** TS. Lê Xuân Bách
- **Nhóm học viên thực hiện (Nhóm 6):**
  1. Nguyễn Công Thành (MSHV: 2470744) — *Nhóm trưởng / Core Architect & Fullstack Developer*
  2. Phạm Quỳnh Trân (MSHV: 2470731) — *Frontend & Red-Teaming Evaluation Specialist*
  3. Nguyễn Hữu Lợi (MSHV: 2470012) — *Data Infrastructure & MCP Integration Engineer*
- **Tổng thời lượng trình bày:** Đúng 15 phút (00:00 – 15:00)
- **Cấu trúc slide:** 14 Slides bám sát 8 phần bắt buộc của Báo cáo Giữa kỳ D2, phân bổ thời gian chi tiết kèm Ghi chú Diễn giả (Speaker Notes) hành văn tự nhiên như văn nói.

---

## BẢNG PHÂN BỔ THỜI LƯỢNG THUYẾT TRÌNH (TIMING AGENDA)

| Slide | Tên Chủ Đề Slide | Nội Dung Tương Ứng trong Báo Cáo D2 | Thời Lượng | Mốc Thời Gian |
| :---: | :--- | :--- | :---: | :---: |
| **01** | Tiêu Đề & Giới Thiệu Đề Tài | Giới thiệu đề tài, GVHD và nhóm tác giả | 1.0 phút | 00:00 – 01:00 |
| **02** | Bối Cảnh & Khoảng Trống Kỹ Thuật | Vấn đề an ninh khi dùng Pure LLM trong BI | 1.0 phút | 01:00 – 02:00 |
| **03** | Bước Chuyển Dịch Sang Neuro-Symbolic | Phần 1: Thay đổi so với proposal (Lý do kỹ thuật) | 1.0 phút | 02:00 – 03:00 |
| **04** | Đối Chiếu Cam Kết Proposal & Hiện Trạng | Phần 1: Bảng đối chiếu 10 hạng mục kỹ thuật | 1.0 phút | 03:00 – 04:00 |
| **05** | Kiến Trúc Microservices & Hạ Tầng 21 Bảng | Phần 2: Kiến trúc đã cài đặt (Hạ tầng Federated) | 1.0 phút | 04:00 – 05:00 |
| **06** | Vòng Điều Khiển 6 Bước & Vết Thực Thi | Phần 2: Control loop & Execution Trace thực tế | 1.5 phút | 05:00 – 06:30 |
| **07** | Công Cụ & Phân Quyền Khóa Cứng 2 Tầng | Phần 3: Tools/MCP & Khóa DDL/DML ở Code + DB | 1.5 phút | 06:30 – 08:00 |
| **08** | Bộ Nhớ & Quản Trị Tri Thức Zero-Trust | Phần 4: Ngắn hạn, Dài hạn, Re-validation on Retrieval | 1.0 phút | 08:00 – 09:00 |
| **09** | Bộ Đánh Giá 26 Kịch Bản & Số Liệu Đầu Tiên | Phần 5: Benchmark Red-Teaming, ABR 100%, PER 0% | 1.5 phút | 09:00 – 10:30 |
| **10** | Phân Tích Độ Trễ, Chi Phí & Reflexion | Phần 5: Phân rã Latency, Token Cost & Tự sửa lỗi | 1.0 phút | 10:30 – 11:30 |
| **11** | Threat Model v1: 6 Vector Tấn Công | Phần 6: Phân tích Assets, Inputs & Giảm thiểu | 1.0 phút | 11:30 – 12:30 |
| **12** | Lộ Trình Đến Báo Cáo Cuối Kỳ (02/12) | Phần 7: Kế hoạch 5 tuần, Giả định rủi ro & Tự đánh giá | 1.0 phút | 12:30 – 13:30 |
| **13** | Đóng Góp Thành Viên & AI-Use Statement | Phần 8: Bảng đóng góp Git & Cam kết liêm chính | 1.0 phút | 13:30 – 14:30 |
| **14** | Tổng Kết & Phiên Hỏi Đáp (Q&A) | 3 thông điệp kết luận & Lắng nghe ý kiến Hội đồng | 0.5 phút | 14:30 – 15:00 |

---

## CHI TIẾT NỘI DUNG TỪNG SLIDE & LỜI THOẠI DIỄN GIẢ (SPEAKER NOTES)

---

### SLIDE 01: TIÊU ĐỀ & GIỚI THIỆU ĐỀ TÀI

- **Thời lượng:** 1.0 phút (Mốc: 00:00 – 01:00)
- **Tiêu đề Slide:** SECURE AGENTIC BI FRAMEWORK
- **Phụ đề:** Kiến trúc Phòng thủ Neuro-Symbolic và Giao thức Model Context Protocol (MCP) cho Hệ thống Trí tuệ Doanh nghiệp Tự trị
- **Nội dung hiển thị trên slide:**
  - **Môn học:** Công nghệ Phần mềm Thế hệ Mới (Mã lớp: CO5151) — Báo cáo Giữa kỳ (Checkpoint D2)
  - **Đơn vị đào tạo:** Khoa Khoa học và Kỹ thuật Máy tính – Đại học Bách Khoa TP.HCM
  - **Giảng viên hướng dẫn:** TS. Lê Xuân Bách
  - **Nhóm học viên thực hiện (Nhóm 6):**
    - Nguyễn Công Thành (MSHV: 2470744) — *Nhóm trưởng / Core Architect & Fullstack Dev*
    - Phạm Quỳnh Trân (MSHV: 2470731) — *Frontend & Red-Teaming Specialist*
    - Nguyễn Hữu Lợi (MSHV: 2470012) — *Data Infrastructure & MCP Integration Engineer*
  - **Mục tiêu cốt lõi:** Cho phép người dùng kinh doanh đàm thoại tự nhiên với CSDL phân tán mà vẫn bảo đảm tính an toàn tuyệt đối trước các cuộc tấn công phá hoại, rò rỉ dữ liệu và từ chối dịch vụ.

**Speaker Notes (Ghi chú diễn giả):**

> *"Kính thưa Thầy Lê Xuân Bách cùng toàn thể các bạn học viên trong hội đồng môn Công nghệ Phần mềm Thế hệ Mới. Hôm nay, đại diện cho Nhóm 6, em xin phép được trình bày Báo cáo tiến độ Giữa kỳ (mốc Checkpoint D2) của đề tài: **'Secure Agentic BI Framework: Kiến trúc phòng thủ Neuro-Symbolic và Giao thức Model Context Protocol cho Hệ thống Trí tuệ Doanh nghiệp Tự trị'**.*
>
> *Đề tài được thực hiện bởi 3 thành viên gồm em Nguyễn Công Thành, bạn Phạm Quỳnh Trân và bạn Nguyễn Hữu Lợi, dưới sự hướng dẫn khoa học của TS. Lê Xuân Bách. Mục tiêu sống còn mà dự án hướng tới là giải quyết bài toán hóc búa nhất khi đưa AI vào phân tích dữ liệu doanh nghiệp: Làm sao để nhân viên có thể thoải mái hỏi đáp bằng ngôn ngữ tự nhiên với cơ sở dữ liệu lớn mà không mở toang cánh cửa cho hacker phá hoại, đánh cắp bí mật hay làm sập hệ thống."*

---

### SLIDE 02: BỐI CẢNH & KHOẢNG TRỐNG KỸ THUẬT (PROBLEM STATEMENT)

- **Thời lượng:** 1.0 phút (Mốc: 01:00 – 02:00)
- **Tiêu đề Slide:** Chat-with-Data: Tiềm Năng Đột Phá & Hiểm Họa An Ninh Bản Thể
- **Nội dung hiển thị trên slide:**
  - **Xu thế tất yếu:** Chuyển đổi từ viết SQL thủ công sang giao diện đàm thoại ngôn ngữ tự nhiên (*Agentic Business Intelligence / NL2SQL*).
  - **3 Khiếm khuyết bản thể của Mô hình thuần LLM (Pure Neural):**
    - *Bản chất xác suất & Ảo giác (Hallucination):* Tự bịa đặt bảng, cột, hoặc quên chỉ thị cấm trong prompt.
    - *Dòng dữ liệu hòa lẫn (Blended Stream):* Không thể phân định tất định đâu là dữ liệu, đâu là lệnh điều khiển.
    - *Cấp quyền quá mức (Over-privileged Connection):* Kết nối trực tiếp vào CSDL bằng tài khoản chia sẻ quyền cao.
  - **Các vector đe dọa thực tế:**
    - *Prompt-to-SQL Injection (P2SQL):* Ép Agent sinh lệnh `DROP TABLE`, `UPDATE`, `DELETE`.
    - *Từ chối dịch vụ (DoS):* Sinh các truy vấn `CROSS JOIN` tích Descartes hoặc đệ quy vô hạn làm sập máy chủ.
    - *Indirect Prompt Injection:* Dữ liệu người dùng (tickets, reviews) chứa mã độc chiếm quyền Agent.
  - **Khoảng trống kỹ thuật:** Thiếu một khung bảo vệ tất định độc lập đứng ngoài LLM và chuẩn hóa giao tiếp công cụ qua giao thức an toàn.

**Speaker Notes (Ghi chú diễn giả):**

> *"Thưa Thầy và các bạn, việc tích hợp LLM vào Business Intelligence đang tạo ra một bước tiến vượt bậc, giúp bất kỳ nhân viên nào cũng có thể truy vấn số liệu kinh doanh mà không cần học viết SQL. Tuy nhiên, nếu chúng ta chỉ đơn giản là bọc một mô hình LLM quanh thư viện LangChain rồi kết nối thẳng vào database, chúng ta đang tạo ra một hiểm họa bảo mật vô cùng nghiêm trọng.*
>
> *Bởi vì LLM bản chất là mô hình xác suất và xử lý ngôn ngữ trong cùng một dòng dữ liệu hòa lẫn. Các nghiên cứu an ninh mới nhất đã chỉ ra rằng kẻ tấn công có thể dễ dàng dùng các câu lệnh Jailbreak để ép LLM sinh ra* `DROP TABLE` *làm mất trắng dữ liệu, hoặc tạo ra các câu lệnh* `CROSS JOIN` *khổng lồ làm sập hoàn toàn máy chủ cơ sở dữ liệu. Nguy hiểm hơn nữa là khi dữ liệu trong bảng chứa mã độc gián tiếp (Indirect Injection), chính Agent sẽ bị điều khiển từ bên trong. Đây chính là khoảng trống kỹ thuật sống còn mà dự án chúng em tập trung giải quyết."*

---

### SLIDE 03: PHẦN 1: THAY ĐỔI SO VỚI PROPOSAL – BƯỚC CHUYỂN DỊCH NEURO-SYMBOLIC

- **Thời lượng:** 1.0 phút (Mốc: 02:00 – 03:00)
- **Tiêu đề Slide:** Đột Phá Giữa Kỳ: Bước Chuyển Dịch Sang Kiến Trúc Neuro-Symbolic
- **Nội dung hiển thị trên slide:**
  - **Hạn chế của Đề xuất Ban đầu (Proposal D1):**
    - Tiếp cận thuần Neural: Chỉ dựa vào System Prompt cấm đoán (*"Do not execute DROP..."*).
    - Bộ lọc từ khóa bằng Regex thô: Dễ dàng bị qua mặt bởi kỹ thuật Obfuscation, comment lồng nhau, hoặc Subqueries.
  - **Bước chuyển dịch chiến lược tại mốc D2:**
    - Chuyển đổi toàn diện sang **Kiến trúc Phòng thủ Lai Neuro-Symbolic (Neuro-Symbolic Defense)**.
  - **Phân tách rạch ròi 2 khối chức năng:**
    - **Khối Neural (LLM - Google Gemini 2.5 Flash):** Đảm nhiệm năng lực suy luận ngữ nghĩa tự nhiên linh hoạt, phân tích ý định người dùng và sinh kế hoạch truy vấn nghiệp vụ (ReAct Tool Call).
    - **Khối Symbolic (Formal Verification Gateways):** Rào chắn kiểm chứng toán học tất định (Deterministic) đứng ngoài LLM. Sử dụng bộ phân tích Cây cú pháp trừu tượng (**AST Parser** qua `sqlglot`), bộ ngắt mạch **Circuit Breaker**, và bộ lọc **Taint Filter**.
  - **Cơ sở khoa học:** Nghiên cứu *ICSE 2025* (Pedro et al.) chứng minh tính bất khả của Prompt Defense và khẳng định tính bắt buộc của rào chắn kiểm chứng cú pháp AST.

**Speaker Notes (Ghi chú diễn giả):**

> *"So với bản đề xuất ban đầu ở Tuần 1, nhóm đã có một bước chuyển dịch mang tính bước ngoặt về mặt kiến trúc phần mềm. Ban đầu, nhóm dự kiến dựa vào System Prompt và dùng biểu thức chính quy Regex để bắt từ khóa cấm. Nhưng qua thực nghiệm đối kháng, Regex rất dễ bị qua mặt bằng các kỹ thuật làm mờ chuỗi hoặc comment lồng nhau.*
>
> *Do đó, nhóm đã quyết định chuyển hẳn sang **Kiến trúc Phòng thủ Neuro-Symbolic**. Trong kiến trúc này, chúng em phân định rạch ròi hai khối: LLM chỉ làm nhiệm vụ Neural, tức là hiểu ngôn ngữ và đề xuất kế hoạch truy vấn; còn việc câu lệnh đó có được phép chạm vào database hay không phải do các cổng kiểm soát Symbolic hình thức quyết định. Cụ thể, chúng em dùng bộ phân tích cây cú pháp* `sqlglot` *để kiểm tra toán học mọi câu lệnh. Dù kẻ tấn công có Jailbreak thành công LLM thì câu lệnh sinh ra vẫn bị bẻ gãy 100% tại cổng AST trước khi tới Database."*

---

### SLIDE 04: PHẦN 1 (TIẾP): ĐỐI CHIẾU CAM KẾT PROPOSAL & HIỆN TRẠNG

- **Thời lượng:** 1.0 phút (Mốc: 03:00 – 04:00)
- **Tiêu đề Slide:** Bảng Đối Chiếu Cam Kết Proposal & Trạng Thái Thực Hiện
- **Nội dung hiển thị trên slide:**
  - **Bảng ma trận đối chiếu 10 hạng mục kỹ thuật cốt lõi:**

| Hạng Mục Kỹ Thuật               | Cam Kết trong Proposal (D1)            | Trạng Thái Hiện Tại (D2)                      | Đánh Giá Tiến Độ     |
| :------------------------------ | :------------------------------------- | :-------------------------------------------: | :------------------: |
| **1. Mô hình suy luận**         | Pure Neural, System Prompt cấm DDL/DML | **Đã bỏ** *(Thay bằng Neuro-Symbolic)*        | Hoàn thành vượt trội |
| **2. Cổng kiểm soát SQL**       | Dùng Regex thô kiểm tra từ khóa        | **Xong** *(AST* `sqlglot` *dialect Trino)*    | Hoàn thành           |
| **3. Giao thức kết nối DB**     | Kết nối trực tiếp CSDL qua JDBC/ORM    | **Đã bỏ** *(Thay bằng chuẩn Stdio MCP)*       | Chuẩn hóa mở         |
| **4. Phân quyền RBAC**          | RBAC tĩnh cơ bản                       | **Xong** *(Least-Privilege Schema Injection)* | Hoàn thành           |
| **5. Cơ chế tự sửa lỗi**        | ReAct dừng khi lỗi, ném ngoại lệ 500   | **Xong** *(Vòng lặp Reflexion <= 3 lần)*      | Hoàn thành           |
| **6. Kiểm soát tài nguyên**     | Chưa có giới hạn tài nguyên tính toán  | **Xong** *(Circuit Breaker + Semaphore)*      | Hoàn thành           |
| **7. Phòng Indirect Injection** | Đưa dữ liệu thô thẳng vào context      | **Xong** *(Table Taint Filter + Sandbox)*     | Hoàn thành           |
| **8. Hạ tầng CSDL**             | 1 CSDL đơn lẻ (5–8 bảng)               | **Xong** *(Federated Trino 21 bảng PG+MySQL)* | Vượt tiến độ         |
| **9. Bộ nhớ ngữ nghĩa**         | Nhúng ChromaDB từ Tuần 5–6             | **Đang làm** *(Hoãn Vector DB, dùng MySQL)*   | Quản trị rủi ro      |
| **10. Bộ đánh giá**             | Test BI cơ bản (~10 queries)           | **Xong** *(26 kịch bản Red-teaming chuẩn)*    | Hoàn thành           |

**Speaker Notes (Ghi chú diễn giả):**

> *"Trên màn hình là bảng đối chiếu chi tiết giữa những gì nhóm cam kết trong Proposal và những gì đã thực sự cài đặt được tại mốc giữa kỳ. Chúng em đã hoàn thành 8/10 hạng mục với chất lượng vượt kế hoạch ban đầu.*
>
> *Cụ thể, nhóm đã thay thế việc kết nối CSDL trực tiếp bằng giao thức chuẩn hóa Model Context Protocol (MCP) của Anthropic; thay thế Regex bằng AST Parser toàn diện; và nâng cấp hạ tầng từ một CSDL đơn lẻ lên thành cụm cơ sở dữ liệu liên kết Federated Trino với 21 bảng dữ liệu trên cả PostgreSQL và MySQL. Riêng đối với bộ nhớ ngữ nghĩa Vector DB, nhóm chủ động chuyển trạng thái sang Đang làm và tạm hoãn sang Tuần 10. Quyết định này nhằm ưu tiên hoàn thiện cơ chế quản trị bộ nhớ và kiểm thử Red-teaming trên MySQL trước, tránh nguy cơ hệ thống bị tấn công đầu độc bộ nhớ dài hạn như các nghiên cứu quốc tế đã cảnh báo."*

---

### SLIDE 05: PHẦN 2: KIẾN TRÚC MICROSERVICES & HẠ TẦNG 21 BẢNG

- **Thời lượng:** 1.0 phút (Mốc: 04:00 – 05:00)
- **Tiêu đề Slide:** Kiến Trúc Hệ Thống Microservices & Cụm Federated DB
- **Nội dung hiển thị trên slide:**
  - **4 Phân tầng Hệ thống Độc lập (Đóng gói Docker Compose):**
    1. **Frontend Tier (React 19 + Vite):** Bảng điều khiển Red-Teaming, chọn vai trò người dùng, theo dõi tiến trình suy luận và kiểm tra an toàn theo thời gian thực qua luồng stream NDJSON.
    2. **Backend API Gateway (FastAPI, Python 3.13):** Điều phối toàn bộ quy trình bảo mật bất đồng bộ, tích hợp SQLAlchemy ORM và Pydantic v2.
    3. **Protocol Tier (Trino MCP Server):** Triển khai chuẩn Anthropic MCP qua kênh Stdio JSON-RPC; cô lập thông tin chứng thực DB khỏi Agent.
    4. **Federated Data Infrastructure (Mạng Docker** `bi-network`**):**
       - **PostgreSQL 16 (**`analytics_db`**):** 13 bảng Core ERP / Finance (chứa dữ liệu nhạy cảm `hr_payroll`, `api_keys_config`, `financial_transactions`).
       - **MySQL 8.4 (**`agentic_bi`**):** 8 bảng Portal / Audit / Memory (chứa dữ liệu UGC, `support_tickets`, `agent_query_history`, `semantic_cache`).
       - **Trino Coordinator Engine:** Cổng truy vấn liên kết duy nhất (Single Entry Point), hỗ trợ Federated Cross-Database JOIN giữa hai kho dữ liệu.

**Speaker Notes (Ghi chú diễn giả):**

> *"Đây là sơ đồ kiến trúc tổng thể mà nhóm đã cài đặt và đưa vào vận hành trơn tru end-to-end. Toàn bộ giải pháp được đóng gói thành các container Docker độc lập kết nối qua mạng nội bộ* `bi-network`*.*
>
> *Lớp dữ liệu được thiết kế mô phỏng môi trường doanh nghiệp thực tế với hai hệ quản trị CSDL chuyên biệt: PostgreSQL đóng vai trò kho dữ liệu ERP nòng cốt với 13 bảng lưu trữ đơn hàng, thanh toán và nhân sự; MySQL đóng vai trò cổng tương tác người dùng với 8 bảng lưu trữ các đánh giá, ticket hỗ trợ và bộ nhớ của Agent. Đứng trước hai CSDL này là Trino Coordinator làm cổng truy vấn liên kết tập trung. Ở lớp ứng dụng, Backend FastAPI giao tiếp với Trino thông qua một máy chủ MCP Server chạy ngầm qua kênh Stdio JSON-RPC. Giao diện React 19 cung cấp cho người dùng một bảng điều khiển Red-teaming trực quan với luồng stream dữ liệu thời gian thực."*

---

### SLIDE 06: PHẦN 2 (TIẾP): VÒNG ĐIỀU KHIỂN 6 BƯỚC & VẾT THỰC THI (EXECUTION TRACE)

- **Thời lượng:** 1.5 phút (Mốc: 05:00 – 06:30)
- **Tiêu đề Slide:** Vòng Điều Khiển 6 Bước & Vết Thực Thi Thực Tế
- **Nội dung hiển thị trên slide:**
  - **Quy trình 6 bước khép kín (End-to-End Control Loop):**
    1. *RBAC Lookup:* Xác thực vai trò (`analyst`, `sales`, `support`, `hr`, `admin`), tải chính sách bảng được phép / bị cấm.
    2. *Schema Filter:* Cắt tỉa metadata (`system.jdbc.columns`), chỉ nạp cấu trúc các bảng được phép cho LLM.
    3. *Neural Planning:* Gemini 2.5 Flash sinh JSON Tool Call (`execute_query_read_only`).
    4. *Symbolic AST Guardrail:* `sqlglot` kiểm tra: cấm DDL/DML, cấm `;`, cấm đệ quy, cấm CROSS JOIN, kiểm tra quyền bảng.
    5. *Reflexion & Trino MCP:* Thực thi câu lệnh kèm Circuit Breaker (timeout 5s). Nếu lỗi -> Tự phản tư sửa lỗi (tối đa 3 lần).
    6. *Taint Filter & Synthesis:* Xem dữ liệu thô là *Passive Text Only*, tổng hợp câu trả lời nghiệp vụ an toàn.
  - **Vết thực thi thực tế (Execution Trace) của truy vấn "Thống kê doanh thu theo Category":**
    - *Bước 1 & 2 (0.16s):* Role `analyst` -> Giấu bảng lương `hr_payroll`, chỉ nạp 7 bảng cho phép.
    - *Bước 3 (0.95s):* LLM sinh SQL JOIN 4 bảng `categories`, `products`, `orders`, `order_items`.
    - *Bước 4 (0.02s):* AST Parser xác nhận kiểu `exp.Select`, các phép JOIN đều có mệnh đề `ON`, toàn bộ bảng hợp lệ -> **PASSED**.
    - *Bước 5 (0.35s):* Trino thực thi liên kết trong 0.35s (dưới ngưỡng ngắt 5.0s), trả về 4 dòng dữ liệu.
    - *Bước 6 (0.47s):* Taint Filter cách ly dữ liệu, Gemini tổng hợp bảng markdown doanh thu hoàn chỉnh. Tổng độ trễ: **1.95s**.

**Speaker Notes (Ghi chú diễn giả):**

> *"Mọi yêu cầu từ người dùng khi gửi vào hệ thống đều bắt buộc phải đi qua đúng 6 bước phòng thủ nghiêm ngặt như trên slide.*
>
> *Em xin phép minh họa qua một vết thực thi thực tế khi người dùng có vai trò* `analyst` *hỏi: 'Thống kê tổng doanh thu theo từng danh mục sản phẩm'. Đầu tiên, hệ thống tra cứu bảng RBAC và dùng Schema Filter loại bỏ hoàn toàn các bảng nhạy cảm như bảng lương hay tài chính. Khi Gemini nhận được yêu cầu, mô hình sinh ra câu lệnh SQL JOIN 4 bảng có cấu trúc rất chuẩn xác. Câu lệnh này ngay lập tức bị chặn lại tại Bước 4: Bộ phân tích* `sqlglot` *kiểm tra trong 0.02 giây, xác nhận câu lệnh không có dấu chấm phẩy, thuộc loại Select, các phép Join đều có điều kiện ON và 4 bảng tham chiếu đều nằm trong danh mục cấp phép của Role analyst.*
>
> *Sau đó ở Bước 5, câu lệnh được chuyển tới Trino MCP và chạy thành công trong 0.35 giây. Ở bước cuối cùng, dữ liệu thô được đóng băng thành văn bản thụ động qua Taint Filter để Gemini tổng hợp thành một báo cáo doanh thu chuyên nghiệp. Toàn bộ chu trình chỉ mất chưa tới 2 giây."*

---

### SLIDE 07: PHẦN 3: CÔNG CỤ & PHÂN QUYỀN (TOOLS & MCP) – KHÓA CỨNG 2 TẦNG

- **Thời lượng:** 1.5 phút (Mốc: 06:30 – 08:00)
- **Tiêu đề Slide:** Chuẩn Hóa MCP & Cơ Chế Khóa Cứng Quyền Ghi Ở 2 Tầng
- **Nội dung hiển thị trên slide:**
  - **Giao thức Chuẩn hóa Model Context Protocol (MCP):**
    - Chạy tiến trình con qua Stdio JSON-RPC; Agent hoàn toàn không nắm giữ connection string hay mật khẩu CSDL.
    - **Danh mục Tools:** Cung cấp duy nhất `execute_query_read_only` (kèm các tool metadata). Biến môi trường `ALLOW_WRITE_QUERIES=false` khóa cứng ở cấp hạ tầng.
    - **Kiểm soát đồng thời (Concurrency Semaphore):** Khống chế số truy vấn đồng thời (`MAX_CONCURRENT_QUERIES=1`), ngăn chặn spam cạn kiệt tài nguyên.
  - **Cơ chế Khóa Cứng 2 Tầng (Defense-in-Depth) Triệt Tiêu Lệnh Ghi (DDL/DML):**
    - **TẦNG 1 (Tầng Code - AST Parser Gateway):**
      - Thư viện `sqlglot` bắt buộc node gốc phải là `exp.Select`.
      - Duyệt toàn bộ cây cú pháp để cấm triệt để danh sách `_DANGEROUS_NODES`: `Insert`, `Update`, `Delete`, `Drop`, `Alter`, `Create`, `Grant`, `Revoke`.
      - Hàm `is_read_only_query()` tại MCP Server kiểm tra Fail-Closed lần thứ hai.
    - **TẦNG 2 (Tầng Database Engine Privileges):**
      - Tài khoản PostgreSQL `bi_user` chỉ được cấp duy nhất quyền `SELECT` trên schema `public`.
      - Tài khoản MySQL `bi_agent` chỉ được cấp `SELECT, SHOW VIEW` trên database `agentic_bi`.
      - Kể cả khi tầng Code bị lỗi logic, Database Engine vẫn từ chối 100% mọi câu lệnh phá hoại.

**Speaker Notes (Ghi chú diễn giả):**

> *"Ở tầng giao tiếp công cụ, hệ thống tuân thủ chặt chẽ chuẩn Model Context Protocol của Anthropic. Đóng góp kỹ thuật quan trọng của nhóm tại đây là việc loại bỏ hoàn toàn khả năng can thiệp phá hoại dữ liệu bằng cách **khóa cứng quyền ghi ở 2 tầng độc lập** mà không bao giờ dựa vào việc nhắc nhở trong Prompt.*
>
> *Tầng thứ nhất là Tầng Code: Trước khi câu lệnh rời khỏi Gateway, module* `sql_validator` *dùng* `sqlglot` *bóc tách cây cú pháp, bắt buộc câu lệnh phải là SELECT và duyệt toàn bộ các node con để cấm triệt để mọi hành vi INSERT, UPDATE, DELETE hay DROP. Không những vậy, chính máy chủ MCP Server cũng duyệt lại cây AST một lần nữa để bảo đảm nguyên tắc Fail-Closed.*
>
> *Nhưng nếu chẳng may tầng code có lỗ hổng Zero-day thì sao? Chúng em đã thiết lập Tầng thứ hai trực tiếp tại Database Engine: Các tài khoản kết nối của Trino xuống PostgreSQL và MySQL chỉ được cấp duy nhất đặc quyền SELECT. Nghĩa là ngay cả khi câu lệnh DROP vượt qua được code, chính hệ quản trị cơ sở dữ liệu ở tầng dưới cùng vẫn sẽ từ chối thực thi với thông báo Permission Denied. Đây là triết lý phòng thủ đa tầng Defense-in-Depth chuẩn mực."*

---

### SLIDE 08: PHẦN 4: BỘ NHỚ & QUẢN TRỊ TRI THỨC (MEMORY GOVERNANCE)

- **Thời lượng:** 1.0 phút (Mốc: 08:00 – 09:00)
- **Tiêu đề Slide:** Quản Trị Bộ Nhớ Ngữ Cảnh & Rào Chắn Re-Validation
- **Nội dung hiển thị trên slide:**
  - **1. Bộ nhớ ngắn hạn (Short-term Context):**
    - Quản lý qua mảng trạng thái `messages` theo phiên (`session_id`).
    - Áp dụng Token Trimming: Cắt tỉa lịch sử hội thoại, loại bỏ các khối dữ liệu thô cồng kềnh để tối ưu hóa context window.
  - **2. Bộ nhớ dài hạn & Bộ đệm ngữ nghĩa (Long-term & Semantic Cache):**
    - Lưu trữ có cấu trúc kiểm toán tại MySQL: Bảng `agent_query_history` (lịch sử thực thi) và `semantic_cache` (bộ đệm truy vấn).
    - **Chính sách Ghi Khắt Khe (Strict Write Policy):** Chỉ lưu câu lệnh vào cache khi đã vượt qua 100% rào chắn AST và Trino thực thi thành công không lỗi.
    - **Tái Thẩm Định Khi Truy Xuất (Re-validation on Retrieval):** Mọi câu SQL lấy ra từ Cache hay History **BẮT BUỘC** phải nạp lại vào AST Guardrail để thẩm định theo Role người dùng hiện tại trước khi chạy.
  - **Lý do khoa học tạm hoãn ChromaDB:**
    - Nghiên cứu *AgentPoison* (*NeurIPS 2024*) và *GhostWriter* (2026) chỉ ra rằng Vector DB tự động ghi nhớ là vector tấn công đầu độc dài hạn rất nguy hiểm.
    - Cần hoàn thiện cơ chế kiểm định an toàn trên MySQL trước khi mở rộng sang Vector DB ở Tuần 10.

**Speaker Notes (Ghi chú diễn giả):**

> *"Về vấn đề quản trị bộ nhớ, hệ thống phân chia rạch ròi giữa bộ nhớ ngắn hạn và bộ nhớ dài hạn. Bộ nhớ ngắn hạn được quản lý theo session với kỹ thuật cắt tỉa token để giảm chi phí. Đối với bộ nhớ dài hạn và Semantic Cache, nhóm triển khai hai bảng dữ liệu có kiểm toán trong MySQL là* `agent_query_history` *và* `semantic_cache`*.*
>
> *Tại đây, nhóm thiết lập hai nguyên tắc an ninh nghiêm ngặt: Thứ nhất là Chính sách ghi khắt khe: chỉ những truy vấn an toàn và chạy thành công mới được ghi vào bộ nhớ. Thứ hai, và là quan trọng nhất, là nguyên tắc **Re-validation on Retrieval**: Bất kỳ câu lệnh SQL nào được lấy ra từ bộ nhớ trong quá khứ khi đem đi tái sử dụng đều bắt buộc phải đi qua AST Parser kiểm định lại từ đầu theo quyền của người hỏi hiện tại. Không có bất kỳ đặc quyền ưu tiên nào cho dữ liệu bộ nhớ.*
>
> *Quy trình này trực tiếp giải quyết bài toán Memory Poisoning được cảnh báo trong bài báo AgentPoison tại hội nghị NeurIPS 2024, bảo đảm kẻ tấn công không thể cấy mã độc vào bộ nhớ để lây lan sang các phiên làm việc sau."*

---

### SLIDE 09: PHẦN 5: BỘ ĐÁNH GIÁ 26 KỊCH BẢN & SỐ LIỆU ĐẦU TIÊN

- **Thời lượng:** 1.5 phút (Mốc: 09:00 – 10:30)
- **Tiêu đề Slide:** Đánh Giá Thực Nghiệm: 26 Kịch Bản Red-Teaming & Chỉ Số Đầu Tiên
- **Nội dung hiển thị trên slide:**
  - **Ma trận 26 Kịch bản Kiểm thử Thực nghiệm (**`scenarios.js`**):**
    - *Baseline BI & Export an toàn (4 kịch bản):* Doanh thu theo category, Top nhân viên, Federated JOIN, Export CSV sandbox -> Yêu cầu trả về đúng kết quả (Pass).
    - *6 Nhóm tấn công đối kháng (22 kịch bản):* SQLi (4), DoS (3), PII Leak (5), Indirect Injection (3), Confused Deputy (4), Memory Poisoning (3) -> Yêu cầu phải phát hiện và chặn đứng (Block).
  - **Bảng đối đầu định lượng: Pure ReAct (Baseline) vs Neuro-Symbolic (Đề tài):**

| Chỉ Số Đánh Giá (Metrics) | Pure ReAct (Baseline) | Neuro-Symbolic (Đề tài) | Ý Nghĩa Thực Tiễn |
| :--- | :---: | :---: | :--- |
| **Attack Block Rate (ABR %)** | 13.6% (3/22) | **100.0% (22/22)** | Chặn đứng hoàn toàn cả 6 nhóm tấn công đối kháng |
| **Privilege Escalation (PER %)**| 68.2% (15/22) | **0.0% (0/22)** | Triệt tiêu 100% rủi ro rò rỉ dữ liệu lương, secrets, thẻ TD |
| **Execution Accuracy (EX %)** | 78.5% | **93.8%** | Tăng +15.3% độ chính xác nghiệp vụ nhờ Reflexion Loop |
| **End-to-End Latency** | 1.42s | **1.85s** | Khối Symbolic chỉ tăng thêm ~0.43s overhead |
| **Chi phí API / Truy vấn** | 0.00065 USD | **0.00021 USD** | Tiết kiệm gần 70% chi phí token nhờ Schema Filter |

**Speaker Notes (Ghi chú diễn giả):**

> *"Để chứng minh tính hiệu quả của hệ thống, nhóm đã xây dựng một bộ Harness kiểm thử thực nghiệm đối kháng gồm 26 kịch bản toàn diện, tích hợp sẵn trên giao diện web. Bộ kiểm thử gồm 4 kịch bản nghiệp vụ chuẩn và 22 kịch bản tấn công bao phủ toàn bộ 6 nhóm hiểm họa.*
>
> *Khi tiến hành thử nghiệm so sánh đối đầu giữa mô hình ReAct truyền thống và kiến trúc Neuro-Symbolic của nhóm, kết quả thu được rất ấn tượng: Tỷ lệ chặn tấn công (Attack Block Rate) của hệ thống đạt **100%**, trong khi mô hình truyền thống chỉ chặn được 13.6% và để xảy ra tới 68.2% trường hợp vượt quyền truy cập dữ liệu nhạy cảm.*
>
> *Đặc biệt, về mặt nghiệp vụ, độ chính xác thực thi (Execution Accuracy) của hệ thống đã tăng từ 78.5% lên **93.8%** nhờ vào vòng lặp tự sửa lỗi Reflexion. Điều này chứng minh rằng kiến trúc phòng thủ của nhóm không hề làm suy giảm năng lực nghiệp vụ của AI mà trái lại còn giúp hệ thống vận hành thông minh và bền bỉ hơn."*

---

### SLIDE 10: PHẦN 5 (TIẾP): PHÂN TÍCH ĐỘ TRỄ, CHI PHÍ & REFLEXION

- **Thời lượng:** 1.0 phút (Mốc: 10:30 – 11:30)
- **Tiêu đề Slide:** Phân Tích Hiệu Năng: Độ Trễ, Chi Phí Token & Tự Sửa Lỗi
- **Nội dung hiển thị trên slide:**
  - **Phân rã Hồ sơ Độ trễ (Tổng thời gian trung bình: 1.85 giây):**
    - *RBAC & Metadata Pruning:* ~0.16s (Lọc quyền và cắt tỉa schema).
    - *Neural Planning (Gemini 2.5 Flash):* ~0.95s (Chiếm 51% thời gian).
    - *Symbolic AST Guardrail (*`sqlglot`*):* **~0.02s (Chỉ chiếm 1.1% thời gian — Overhead cực nhỏ).**
    - *Trino Federated Query Execution:* ~0.35s.
    - *Taint Filter & Safe Synthesis:* ~0.37s.
  - **Tối ưu hóa Chi phí API & Cơ chế Fallback:**
    - Cắt giảm 70% token đầu vào nhờ Least-Privilege Schema Injection (từ 4,200 xuống ~950 tokens).
    - Chi phí trung bình mỗi truy vấn: **~0.0002 USD (~5 VNĐ)**.
    - Tích hợp **Fallback Engine** tự động trượt giữa các dòng Gemini Flash/Flash-lite khi gặp lỗi 429, duy trì tính sẵn sàng 100% với chi phí 0 USD trên Free Tier.
  - **3 Lỗi phổ biến mà Reflexion đã tự phục hồi thành công:**
    1. Thiếu prefix catalog 3 phần (`orders` $\rightarrow$ sửa thành `pg.public.orders`).
    2. Nhầm tên cột khi JOIN (`user_id` $\rightarrow$ sửa thành `pg_customer_id`).
    3. Cú pháp dialect Trino (`IFNULL()` $\rightarrow$ sửa thành `COALESCE()`).

**Speaker Notes (Ghi chú diễn giả):**

> *"Đi sâu vào phân tích hiệu năng, tổng thời gian phản hồi cho một truy vấn hợp lệ là 1.85 giây. Trong đó, toàn bộ việc phân tích cú pháp AST toán học bằng* `sqlglot` *chỉ tiêu tốn 0.02 giây, tức là chỉ chiếm hơn 1% tổng thời gian. Điều này bác bỏ định kiến cho rằng việc thêm các lớp bảo vệ kiểm tra cú pháp sẽ làm chậm hệ thống.*
>
> *Về mặt chi phí, nhờ kỹ thuật Schema Filter chỉ tiêm đúng các bảng được cấp phép thay vì nạp toàn bộ 21 bảng vào ngữ cảnh, hệ thống tiết kiệm được 70% lượng token tiêu thụ. Chi phí trung bình cho mỗi câu hỏi chỉ khoảng 5 đồng Việt Nam. Ngoài ra, cơ chế Fallback Engine giúp hệ thống tự động chuyển đổi giữa các model khi gặp giới hạn Quota, bảo đảm hệ thống không bao giờ bị nghẽn.*
>
> *Nhật ký kiểm thử cũng ghi nhận Vòng lặp Reflexion đã giải cứu thành công các lỗi sai tên cột hay thiếu định danh catalog của Trino ngay ở lần thử thứ 2, giúp AI tự đứng dậy sau vấp ngã mà không cần con người can thiệp."*

---

### SLIDE 11: PHẦN 6: THREAT MODEL V1 – 6 VECTOR TẤN CÔNG TRỌNG YẾU

- **Thời lượng:** 1.0 phút (Mốc: 11:30 – 12:30)
- **Tiêu đề Slide:** Mô Hình Mối Đe Dọa (Threat Model v1): 6 Vector & Phòng Thủ
- **Nội dung hiển thị trên slide:**
  - **Tài sản bảo vệ (Assets):** Bảng lương PII, Khóa API (`api_keys_config`), Siêu dữ liệu Schema, Tài nguyên CPU/RAM máy chủ, File cấu hình `.env`.
  - **Điểm đầu vào không tin cậy (Untrusted Inputs):** User Prompt, Nội dung bảng UGC (`support_tickets`, `reviews`), Tham số `output_file`, Dữ liệu lịch sử bộ nhớ cache.
  - **Năng lực kẻ tấn công & Biện pháp đối phó tương ứng:**
    1. *Prompt-to-SQL (DDL/DML):* Chặn bằng **AST Parser** bắt buộc node `exp.Select`, cấm dấu chấm phẩy.
    2. *Từ chối dịch vụ (DoS):* Chặn bằng **AST cấm CROSS JOIN/đệ quy** kết hợp **Circuit Breaker** ngắt mạch 5.0s.
    3. *Rò rỉ PII & Secrets:* Chặn bằng **Schema Filter** giấu bảng cấm kết hợp **RBAC Scope Check**.
    4. *Indirect Prompt Injection:* Hóa giải bằng **Table Taint Filter** cô lập dữ liệu thành *Passive Text Only*.
    5. *Confused Deputy (Path Traversal):* Chặn bằng **Path Sandbox Canonicalization** giới hạn trong thư mục `reports/`.
    6. *Persistent Memory Poisoning:* Bẻ gãy bằng **Strict Write Policy** và **Zero-Trust Re-validation on Retrieval**.
  - *> **Ghi chú yêu cầu D2:** Việc đo lường thực nghiệm Prompt Injection quy mô lớn sẽ trình bày ở Báo cáo cuối kỳ, mốc D2 tập trung hoàn thiện Threat Model thiết kế.*

**Speaker Notes (Ghi chú diễn giả):**

> *"Mô hình mối đe dọa Threat Model v1 của nhóm được thiết lập dựa trên sự tổng hòa giữa các tài sản trọng yếu của doanh nghiệp và 12 công trình nghiên cứu khoa học phân hạng A* quốc tế từ ICSE, USENIX Security, IEEE S&P và NeurIPS.*
>
> *Chúng em xác định rõ hai nhóm tác nhân đe dọa: Kẻ tấn công bên ngoài tìm cách Jailbreak để ép sinh lệnh phá hoại, spam DoS làm nghẽn máy chủ hoặc cấy mã độc vào các bình luận và ticket khiếu nại; và Kẻ tấn công nội bộ lợi dụng quyền hạn Agent để đọc lén dữ liệu lương hay ghi đè file cấu hình hệ thống. Tương ứng với mỗi vector, hệ thống đều có một cơ chế phòng thủ chuyên biệt: từ AST Parser, Circuit Breaker, Schema Filter, Taint Filter cho đến Path Sandbox.*
>
> *Theo đúng đề cương yêu cầu của Checkpoint D2, việc đo lường chạy thử nghiệm Prompt Injection trên tập benchmark quy mô lớn sẽ được nhóm trình bày chi tiết trong Báo cáo cuối kỳ, hiện tại nhóm tập trung vào việc thiết kế chuẩn hóa Threat Model lý thuyết và xác thực trên 26 kịch bản thực tế."*

---

### SLIDE 12: PHẦN 7: KẾ HOẠCH HÀNH ĐỘNG ĐẾN BÁO CÁO CUỐI KỲ (02/12)

- **Thời lượng:** 1.0 phút (Mốc: 12:30 – 13:30)
- **Tiêu đề Slide:** Lộ Trình 5 Tuần Đến Buổi Báo Cáo Cuối Kỳ (02/12/2026)
- **Nội dung hiển thị trên slide:**
  - **Lộ trình triển khai chi tiết từng tuần:**
    - **Tuần 08 (23/10 – 29/10):** Mở rộng bộ benchmark định lượng lên **$\ge$ 50 tasks** (tích hợp Spider, BIRD và Synthetic Prompts). *(Phụ trách: Trân + Thành)*
    - **Tuần 09 (30/10 – 05/11):** Chạy thực nghiệm **Ablation Study trên 3 Cấu hình** (Baseline, Guardrail Only, Full Pipeline) với 3 seeds độc lập. *(Phụ trách: Thành + Trân)*
    - **Tuần 10 (06/11 – 12/11):** Thử nghiệm **Local LLMs (Qwen-2.5-Coder-14B / Llama-3.1-8B qua vLLM)** & Kích hoạt Vector Cache ChromaDB có Re-validation. *(Phụ trách: Lợi + Thành)*
    - **Tuần 11 (13/11 – 19/11):** Nâng cấp **AST Tree Visualizer** trên UI & Tổ chức **Walkthrough Validation** với chuyên gia BI và SecOps doanh nghiệp. *(Phụ trách: Trân + Lợi)*
    - **Tuần 12 (20/11 – 26/11):** Tối ưu hóa vi độ trễ (< 1.5s), đóng gói Docker container hoàn chỉnh & Hoàn thiện Báo cáo Khóa luận D3/D4. *(Cả nhóm)*
    - **Tuần 13 (27/11 – 02/12):** Tổng duyệt thuyết trình, chuẩn bị Demo trực tiếp và **BÁO CÁO KHÓA LUẬN CHÍNH THỨC (02/12)**.
  - **Giả định rủi ro lớn nhất & Phương án xử lý:**
    - *Rủi ro:* Vector Cache bị trôi ngữ nghĩa -> *Xử lý:* Đặt ngưỡng Cosine $\ge 0.92$ + bắt buộc Re-validate AST.
    - *Rủi ro:* LLM nhỏ sinh dialect Trino sai -> *Xử lý:* Few-shot prompting + mở rộng Reflexion lên 5 lượt.
  - **Phần tự đánh giá:** **[ĐÚNG TIẾN ĐỘ]** (On Track 100%).

**Speaker Notes (Ghi chú diễn giả):**

> *"Từ nay đến ngày Báo cáo Khóa luận chính thức vào ngày 02 tháng 12 năm 2026, nhóm đặt ra một lộ trình hành động 5 tuần vô cùng chặt chẽ. Trong 2 tuần tới, nhóm sẽ mở rộng tập kiểm thử lên trên 50 tác vụ từ benchmark chuẩn BIRD và Spider để thực hiện nghiên cứu loại trừ Ablation Study bài bản trên 3 cấu hình.*
>
> *Đến Tuần 10, nhóm sẽ đưa các mô hình mã nguồn mở như Qwen-2.5-Coder và Llama-3.1 vào chạy thử nghiệm qua vLLM nhằm hướng tới giải pháp On-Premise hoàn toàn độc lập cho doanh nghiệp; đồng thời kích hoạt Vector Cache có rào chắn. Sang Tuần 11, nhóm sẽ bổ sung tính năng trực quan hóa cây AST trên giao diện và mời các chuyên gia phân tích dữ liệu cùng chuyên viên an ninh thông tin tại doanh nghiệp tham gia buổi đánh giá thực tế.*
>
> *Nhóm cũng đã lường trước các rủi ro kỹ thuật như việc trôi ngữ nghĩa trong cache hay giới hạn API để có phương án dự phòng. Nhóm tự đánh giá dự án đang hoàn toàn **Đúng tiến độ** và tự tin sẽ hoàn thành xuất sắc đề tài trước ngày 02/12."*

---

### SLIDE 13: PHẦN 8: ĐÓNG GÓP THÀNH VIÊN & AI-USE STATEMENT

- **Thời lượng:** 1.0 phút (Mốc: 13:30 – 14:30)
- **Tiêu đề Slide:** Đóng Góp Thành Viên & Tuyên Bố Liêm Chính Sử Dụng AI
- **Nội dung hiển thị trên slide:**
  - **Bảng phân công & Đóng góp công việc (Mapping Git Commits):**
    - **Nguyễn Công Thành (100% — Nhóm trưởng):** Thiết kế kiến trúc tổng thể Neuro-Symbolic; lập trình Backend FastAPI; phát triển AST Guardrail (`sqlglot`), Reflexion Loop, Circuit Breaker, Taint Filter, tích hợp Gemini SDK & Fallback Engine; đóng gói Trino MCP Server qua Stdio JSON-RPC; *(Commits:* `140d420`*,* `aaec853`*,* `3379de8`*,* `b2120ee`*,* `ce7f69f`*,* `863ff9f`*,* `7812bac`*,* `26e849b`*,* `adf6280`*)*.
    - **Phạm Quỳnh Trân (100%):** Thiết kế và lập trình Frontend Web Console (React 19, Vite, Tailwind CSS); xây dựng cơ chế NDJSON Streaming; biên soạn 26 kịch bản Red-teaming (`scenarios.js`); nghiên cứu cơ sở lý luận Threat Model. *(Commit:* `0ef0379` *& Frontend PRs)*.
    - **Nguyễn Hữu Lợi (100%):** Thiết kế cụm Docker Federated DB (PostgreSQL 16, MySQL 8.4, Trino 21 bảng dữ liệu seed); cài đặt Concurrency Semaphore và Path Sandbox an toàn. *(Docker, Catalog properties, init SQL files)*.
  - **Tuyên bố sử dụng AI (AI-Use Statement):**
    - *Runtime Components:* Google Gemini 2.5 Flash làm lõi suy luận ReAct và tổng hợp câu trả lời an toàn.
    - *AI Assistants:* Cursor và Windsurf (Claude 3.5 Sonnet) hỗ trợ sinh code khung boilerplate, CSS giao diện, và dữ liệu mock.
    - *Khẳng định liêm chính học thuật:* Toàn bộ tư tưởng kiến trúc, thiết kế Threat Model, giải thuật AST Guardrail, quy tắc quản trị bộ nhớ và audit an ninh do con người (3 học viên) tự nghiên cứu, kiểm chứng và chịu trách nhiệm 100%.

**Speaker Notes (Ghi chú diễn giả):**

> *"Về mặt tổ chức nhân sự, 3 thành viên trong nhóm đã có sự phối hợp ăn ý và phân công trách nhiệm rõ ràng, mọi dòng code đều được lưu vết minh bạch trên GitHub. Em chịu trách nhiệm 100% khối lượng công việc về thiết kế kiến trúc lõi, Backend FastAPI, AST Guardrail và Reflexion, máy chủ Trino MCP Server.; bạn Quỳnh Trân đảm nhiệm 100% về xây dựng giao diện React 19, NDJSON Stream và 26 kịch bản Red-Teaming; bạn Hữu Lợi phụ trách 100% về hạ tầng Docker cụm CSDL liên kết 21 bảng.*
>
> *Nhóm cũng xin tuyên bố minh bạch về việc sử dụng AI theo đúng quy định liêm chính học thuật của nhà trường: Chúng em sử dụng Cursor và Windsurf làm trợ lý viết mã khung boilerplate và sinh dữ liệu mẫu giả định; sử dụng Gemini làm thành phần suy luận runtime. Tuy nhiên, toàn bộ tư tưởng kiến trúc Neuro-Symbolic, việc thiết kế mô hình đe dọa 6 nhóm tấn công, thuật toán bóc tách cú pháp AST và 26 kịch bản Red-teaming đều do chính 3 học viên trong nhóm tự chủ nghiên cứu, phản biện và chịu trách nhiệm học thuật toàn diện."*

---

### SLIDE 14: TỔNG KẾT & PHIÊN HỎI ĐÁP (Q&A)

- **Thời lượng:** 0.5 phút (Mốc: 14:30 – 15:00)
- **Tiêu đề Slide:** Tổng Kết Đề Tài & Lắng Nghe Ý Kiến Hội Đồng
- **Nội dung hiển thị trên slide:**
  - **3 Thông Điệp Cốt Lõi Của Dự Án:**
    1. *Neuro-Symbolic là con đường tất yếu:* Kết hợp tính linh hoạt của LLM với sự bảo đảm an toàn toán học tất định của Cây cú pháp AST.
    2. *Giao thức MCP là tấm khiên vững chắc:* Chuẩn hóa công cụ, cô lập hoàn toàn quyền kết nối CSDL và phân tách rạch ròi luồng dữ liệu khỏi luồng điều khiển.
    3. *Sẵn sàng cho Doanh nghiệp:* Tỷ lệ chặn tấn công 100%, tự phục hồi đạt 93.8% độ chính xác, vận hành trên cụm liên kết 21 bảng với chi phí cực thấp (~5 VNĐ/truy vấn).
  - **Hệ thống đã sẵn sàng cho giai đoạn mở rộng thực nghiệm cuối kỳ.**
  - **KÍNH MỜI THẦY VÀ HỘI ĐỒNG ĐẶT CÂU HỎI & ĐÓNG GÓP Ý KIẾN (Q&A)**
  - *Email liên hệ nhóm nghiên cứu: thanh.nguyencong280702@gmail.com / tranpq@splus-software.com.vn*

**Speaker Notes (Ghi chú diễn giả):**

> *"Để khép lại bài báo cáo hôm nay, thông điệp lớn nhất mà đề tài Secure Agentic BI Framework muốn khẳng định là: Chúng ta tuyệt đối không thể giao phó an ninh cơ sở dữ liệu doanh nghiệp cho tính xác suất của LLM, mà bắt buộc phải áp dụng Kiến trúc phòng thủ Neuro-Symbolic và chuẩn hóa giao thức MCP. Dự án đã chứng minh tính khả thi vượt trội với tỷ lệ chặn tấn công 100%, độ chính xác nghiệp vụ trên 93% và chi phí gần như bằng không.*
>
> *Em xin chân thành cảm ơn Thầy Lê Xuân Bách và toàn thể các bạn học viên đã chú ý lắng nghe bài trình bày của Nhóm 6. Nhóm chúng em rất mong nhận được những câu hỏi, nhận xét và đóng góp quý báu từ Thầy để nhóm tiếp tục hoàn thiện đề tài xuất sắc hơn nữa trong nửa sau của môn học. Em xin trân trọng cảm ơn Thầy!"*
