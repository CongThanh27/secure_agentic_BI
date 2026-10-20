-- Secure Agentic BI Framework — PostgreSQL 16 / analytics_db / Trino catalog pg

-- Synthetic demo data only. Secret-shaped values and PII are fictional.

BEGIN;

CREATE TABLE IF NOT EXISTS regions (
    id SERIAL PRIMARY KEY,
    code VARCHAR(12) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    country VARCHAR(80) NOT NULL
);

CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(160) NOT NULL,
    email VARCHAR(200) NOT NULL UNIQUE,
    phone_number VARCHAR(30),
    address TEXT,
    region_id INTEGER REFERENCES regions(id),
    loyalty_tier VARCHAR(20) NOT NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    sku VARCHAR(40) NOT NULL UNIQUE,
    name VARCHAR(180) NOT NULL,
    category_id INTEGER REFERENCES categories(id),
    unit_price NUMERIC(12,2) NOT NULL,
    cost_price NUMERIC(12,2) NOT NULL,
    stock_qty INTEGER NOT NULL,
    is_active BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS employees (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(160) NOT NULL,
    email VARCHAR(200) NOT NULL UNIQUE,
    role VARCHAR(80) NOT NULL,
    department VARCHAR(100) NOT NULL,
    region_id INTEGER REFERENCES regions(id),
    hire_date DATE NOT NULL,
    is_active BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS hr_payroll (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL UNIQUE REFERENCES employees(id),
    gross_salary NUMERIC(14,2) NOT NULL,
    net_salary NUMERIC(14,2) NOT NULL,
    tax_code VARCHAR(24) NOT NULL,
    bank_account_number VARCHAR(40) NOT NULL,
    bank_name VARCHAR(100) NOT NULL,
    pay_period VARCHAR(20) NOT NULL,
    last_paid_date DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS api_keys_config (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(120) NOT NULL,
    key_type VARCHAR(60) NOT NULL,
    key_value TEXT NOT NULL,
    environment VARCHAR(30) NOT NULL,
    created_by VARCHAR(120) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS warehouses (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(160) NOT NULL,
    region_id INTEGER REFERENCES regions(id),
    capacity INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    employee_id INTEGER REFERENCES employees(id),
    order_date TIMESTAMP NOT NULL,
    total_amount NUMERIC(14,2) NOT NULL,
    amount NUMERIC(14,2) NOT NULL,
    product_name VARCHAR(180) NOT NULL,
    status VARCHAR(30) NOT NULL,
    shipping_address TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id),
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(12,2) NOT NULL,
    discount_pct NUMERIC(5,2) NOT NULL,
    warehouse_id INTEGER REFERENCES warehouses(id)
);

CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id),
    method VARCHAR(40) NOT NULL,
    amount NUMERIC(14,2) NOT NULL,
    paid_at TIMESTAMP NOT NULL,
    status VARCHAR(30) NOT NULL,
    transaction_ref VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS financial_transactions (
    id SERIAL PRIMARY KEY,
    payment_id INTEGER REFERENCES payments(id),
    card_last_four CHAR(4) NOT NULL,
    card_brand VARCHAR(40) NOT NULL,
    billing_address TEXT NOT NULL,
    amount NUMERIC(14,2) NOT NULL,
    currency CHAR(3) NOT NULL,
    processor_response TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS inventory_snapshots (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id),
    warehouse_id INTEGER REFERENCES warehouses(id),
    snapshot_date DATE NOT NULL,
    qty_on_hand INTEGER NOT NULL,
    qty_reserved INTEGER NOT NULL,
    qty_available INTEGER NOT NULL
);

INSERT INTO regions (id, code, name, country) VALUES
(1, 'VN-N', 'Northern Vietnam', 'Vietnam'),
(2, 'VN-NE', 'Northeast Vietnam', 'Vietnam'),
(3, 'VN-NW', 'Northwest Vietnam', 'Vietnam'),
(4, 'VN-RED', 'Red River Delta', 'Vietnam'),
(5, 'VN-COAST-N', 'North Central Coast', 'Vietnam'),
(6, 'VN-COAST-C', 'South Central Coast', 'Vietnam'),
(7, 'VN-CENTRAL', 'Central Highlands', 'Vietnam'),
(8, 'VN-SE', 'Southeast Vietnam', 'Vietnam'),
(9, 'VN-MEKONG', 'Mekong Delta', 'Vietnam'),
(10, 'VN-HCMC', 'Ho Chi Minh City', 'Vietnam'),
(11, 'VN-HN', 'Hanoi', 'Vietnam'),
(12, 'VN-DN', 'Da Nang', 'Vietnam'),
(13, 'VN-HP', 'Hai Phong', 'Vietnam'),
(14, 'VN-CT', 'Can Tho', 'Vietnam'),
(15, 'VN-BD', 'Binh Duong', 'Vietnam'),
(16, 'VN-DN2', 'Dong Nai', 'Vietnam'),
(17, 'VN-BR', 'Ba Ria - Vung Tau', 'Vietnam'),
(18, 'VN-QN', 'Quang Ninh', 'Vietnam'),
(19, 'VN-KH', 'Khanh Hoa', 'Vietnam'),
(20, 'VN-LD', 'Lam Dong', 'Vietnam')
ON CONFLICT (id) DO NOTHING;

INSERT INTO categories (id, name, description) VALUES
(1, 'Laptops', 'Portable computers and accessories'),
(2, 'Smartphones', 'Mobile devices and accessories'),
(3, 'Tablets', 'Tablet devices'),
(4, 'Networking', 'Routers, switches and network equipment'),
(5, 'Storage', 'Drives and storage media'),
(6, 'Monitors', 'Displays and monitor accessories'),
(7, 'Peripherals', 'Keyboards, mice and input devices'),
(8, 'Audio', 'Headphones, speakers and audio equipment'),
(9, 'Printers', 'Printers and supplies'),
(10, 'Components', 'Computer components'),
(11, 'Cameras', 'Cameras and imaging'),
(12, 'Wearables', 'Wearable devices'),
(13, 'Cables', 'Cables and adapters'),
(14, 'Power', 'Power supplies and UPS'),
(15, 'Software', 'Licensed software'),
(16, 'Servers', 'Server hardware'),
(17, 'Security', 'Security devices'),
(18, 'Smart Home', 'Connected home devices'),
(19, 'Accessories', 'General accessories'),
(20, 'Refurbished', 'Certified refurbished products')
ON CONFLICT (id) DO NOTHING;

INSERT INTO customers (id, full_name, email, phone_number, address, region_id, loyalty_tier, created_at) VALUES
(1, 'An Pham', 'customer01@example.test', '+84 900000001', '11 Demo Street, District 2, Ho Chi Minh City', 1, 'Bronze', '2025-02-02 09:00:00'),
(2, 'Binh Phan', 'customer02@example.test', '+84 900000002', '12 Demo Street, District 3, Ho Chi Minh City', 2, 'Silver', '2025-03-03 09:00:00'),
(3, 'Chi Dang', 'customer03@example.test', '+84 900000003', '13 Demo Street, District 4, Ho Chi Minh City', 3, 'Gold', '2025-04-04 09:00:00'),
(4, 'Duc Ngo', 'customer04@example.test', '+84 900000004', '14 Demo Street, District 5, Ho Chi Minh City', 4, 'Platinum', '2025-05-05 09:00:00'),
(5, 'Giang Mai', 'customer05@example.test', '+84 900000005', '15 Demo Street, District 6, Ho Chi Minh City', 5, 'Bronze', '2025-06-06 09:00:00'),
(6, 'Hanh Cao', 'customer06@example.test', '+84 900000006', '16 Demo Street, District 7, Ho Chi Minh City', 6, 'Silver', '2025-07-07 09:00:00'),
(7, 'Khanh Luu', 'customer07@example.test', '+84 900000007', '17 Demo Street, District 8, Ho Chi Minh City', 7, 'Gold', '2025-08-08 09:00:00'),
(8, 'Linh Trinh', 'customer08@example.test', '+84 900000008', '18 Demo Street, District 9, Ho Chi Minh City', 8, 'Platinum', '2025-09-09 09:00:00'),
(9, 'Minh Le', 'customer09@example.test', '+84 900000009', '19 Demo Street, District 10, Ho Chi Minh City', 9, 'Bronze', '2025-10-10 09:00:00'),
(10, 'Ngoc Huynh', 'customer10@example.test', '+84 900000010', '20 Demo Street, District 11, Ho Chi Minh City', 10, 'Silver', '2025-11-11 09:00:00'),
(11, 'Phuc Vo', 'customer11@example.test', '+84 900000011', '21 Demo Street, District 12, Ho Chi Minh City', 11, 'Gold', '2025-12-12 09:00:00'),
(12, 'Quang Do', 'customer12@example.test', '+84 900000012', '22 Demo Street, District 1, Ho Chi Minh City', 12, 'Platinum', '2025-01-13 09:00:00'),
(13, 'Thao Ly', 'customer13@example.test', '+84 900000013', '23 Demo Street, District 2, Ho Chi Minh City', 13, 'Bronze', '2025-02-14 09:00:00'),
(14, 'Tuan Dinh', 'customer14@example.test', '+84 900000014', '24 Demo Street, District 3, Ho Chi Minh City', 14, 'Silver', '2025-03-15 09:00:00'),
(15, 'Vy Lam', 'customer15@example.test', '+84 900000015', '25 Demo Street, District 4, Ho Chi Minh City', 15, 'Gold', '2025-04-16 09:00:00'),
(16, 'Yen Thai', 'customer16@example.test', '+84 900000016', '26 Demo Street, District 5, Ho Chi Minh City', 16, 'Platinum', '2025-05-17 09:00:00'),
(17, 'Bao Tran', 'customer17@example.test', '+84 900000017', '27 Demo Street, District 6, Ho Chi Minh City', 17, 'Bronze', '2025-06-18 09:00:00'),
(18, 'Dung Hoang', 'customer18@example.test', '+84 900000018', '28 Demo Street, District 7, Ho Chi Minh City', 18, 'Silver', '2025-07-19 09:00:00'),
(19, 'Hoa Vu', 'customer19@example.test', '+84 900000019', '29 Demo Street, District 8, Ho Chi Minh City', 19, 'Gold', '2025-08-20 09:00:00'),
(20, 'Kiet Bui', 'customer20@example.test', '+84 900000020', '30 Demo Street, District 9, Ho Chi Minh City', 20, 'Platinum', '2025-09-21 09:00:00'),
(21, 'Lan Duong', 'customer21@example.test', '+84 900000021', '31 Demo Street, District 10, Ho Chi Minh City', 1, 'Bronze', '2025-10-22 09:00:00'),
(22, 'Nam Truong', 'customer22@example.test', '+84 900000022', '32 Demo Street, District 11, Ho Chi Minh City', 2, 'Silver', '2025-11-23 09:00:00')
ON CONFLICT (id) DO NOTHING;

INSERT INTO products (id, sku, name, category_id, unit_price, cost_price, stock_qty, is_active) VALUES
(1, 'VTS-0001', 'VietTech Product 01', 1, 157.5, 97.25, 23, TRUE),
(2, 'VTS-0002', 'VietTech Product 02', 2, 195.0, 119.5, 26, TRUE),
(3, 'VTS-0003', 'VietTech Product 03', 3, 232.5, 141.75, 29, TRUE),
(4, 'VTS-0004', 'VietTech Product 04', 4, 270.0, 164.0, 32, TRUE),
(5, 'VTS-0005', 'VietTech Product 05', 5, 307.5, 186.25, 35, TRUE),
(6, 'VTS-0006', 'VietTech Product 06', 6, 345.0, 208.5, 38, TRUE),
(7, 'VTS-0007', 'VietTech Product 07', 7, 382.5, 230.75, 41, TRUE),
(8, 'VTS-0008', 'VietTech Product 08', 8, 420.0, 253.0, 44, TRUE),
(9, 'VTS-0009', 'VietTech Product 09', 9, 457.5, 275.25, 47, FALSE),
(10, 'VTS-0010', 'VietTech Product 10', 10, 495.0, 297.5, 50, TRUE),
(11, 'VTS-0011', 'VietTech Product 11', 11, 532.5, 319.75, 53, TRUE),
(12, 'VTS-0012', 'VietTech Product 12', 12, 570.0, 342.0, 56, TRUE),
(13, 'VTS-0013', 'VietTech Product 13', 13, 607.5, 364.25, 59, TRUE),
(14, 'VTS-0014', 'VietTech Product 14', 14, 645.0, 386.5, 62, TRUE),
(15, 'VTS-0015', 'VietTech Product 15', 15, 682.5, 408.75, 65, TRUE),
(16, 'VTS-0016', 'VietTech Product 16', 16, 720.0, 431.0, 68, TRUE),
(17, 'VTS-0017', 'VietTech Product 17', 17, 757.5, 453.25, 71, TRUE),
(18, 'VTS-0018', 'VietTech Product 18', 18, 795.0, 475.5, 74, FALSE),
(19, 'VTS-0019', 'VietTech Product 19', 19, 832.5, 497.75, 77, TRUE),
(20, 'VTS-0020', 'VietTech Product 20', 20, 870.0, 520.0, 80, TRUE),
(21, 'VTS-0021', 'VietTech Product 21', 1, 907.5, 542.25, 83, TRUE),
(22, 'VTS-0022', 'VietTech Product 22', 2, 945.0, 564.5, 86, TRUE),
(23, 'VTS-0023', 'VietTech Product 23', 3, 982.5, 586.75, 89, TRUE),
(24, 'VTS-0024', 'VietTech Product 24', 4, 1020.0, 609.0, 92, TRUE),
(25, 'VTS-0025', 'VietTech Product 25', 5, 1057.5, 631.25, 95, TRUE)
ON CONFLICT (id) DO NOTHING;

INSERT INTO employees (id, full_name, email, role, department, region_id, hire_date, is_active) VALUES
(1, 'Hanh Vo', 'employee01@viettech.example.test', 'Sales Executive', 'Sales', 1, '2018-02-02', TRUE),
(2, 'Khanh Dang', 'employee02@viettech.example.test', 'Support Specialist', 'Support', 2, '2018-03-03', TRUE),
(3, 'Linh Bui', 'employee03@viettech.example.test', 'HR Officer', 'Human Resources', 3, '2018-04-04', TRUE),
(4, 'Minh Do', 'employee04@viettech.example.test', 'Operations Lead', 'Operations', 4, '2018-05-05', TRUE),
(5, 'Ngoc Ngo', 'employee05@viettech.example.test', 'Analyst', 'Analytics', 5, '2018-06-06', TRUE),
(6, 'Phuc Duong', 'employee06@viettech.example.test', 'Sales Executive', 'Sales', 6, '2018-07-07', TRUE),
(7, 'Quang Ly', 'employee07@viettech.example.test', 'Support Specialist', 'Support', 7, '2018-08-08', TRUE),
(8, 'Thao Mai', 'employee08@viettech.example.test', 'HR Officer', 'Human Resources', 8, '2018-09-09', TRUE),
(9, 'Tuan Truong', 'employee09@viettech.example.test', 'Operations Lead', 'Operations', 9, '2018-10-10', TRUE),
(10, 'Vy Dinh', 'employee10@viettech.example.test', 'Analyst', 'Analytics', 10, '2018-11-11', TRUE),
(11, 'Yen Cao', 'employee11@viettech.example.test', 'Sales Executive', 'Sales', 11, '2018-12-12', FALSE),
(12, 'Bao Chau', 'employee12@viettech.example.test', 'Support Specialist', 'Support', 12, '2018-01-13', TRUE),
(13, 'Dung Lam', 'employee13@viettech.example.test', 'HR Officer', 'Human Resources', 13, '2018-02-14', TRUE),
(14, 'Hoa Luu', 'employee14@viettech.example.test', 'Operations Lead', 'Operations', 14, '2018-03-15', TRUE),
(15, 'Kiet Ta', 'employee15@viettech.example.test', 'Analyst', 'Analytics', 15, '2018-04-16', TRUE),
(16, 'Lan Thai', 'employee16@viettech.example.test', 'Sales Executive', 'Sales', 16, '2018-05-17', TRUE),
(17, 'Nam Trinh', 'employee17@viettech.example.test', 'Support Specialist', 'Support', 17, '2018-06-18', TRUE),
(18, 'Oanh Nguyen', 'employee18@viettech.example.test', 'HR Officer', 'Human Resources', 18, '2018-07-19', TRUE),
(19, 'Son Tran', 'employee19@viettech.example.test', 'Operations Lead', 'Operations', 19, '2018-08-20', TRUE),
(20, 'Trang Le', 'employee20@viettech.example.test', 'Analyst', 'Analytics', 20, '2018-09-21', TRUE),
(21, 'An Pham', 'employee21@viettech.example.test', 'Sales Executive', 'Sales', 1, '2018-10-22', TRUE),
(22, 'Binh Hoang', 'employee22@viettech.example.test', 'Support Specialist', 'Support', 2, '2018-11-23', FALSE)
ON CONFLICT (id) DO NOTHING;

INSERT INTO hr_payroll (id, employee_id, gross_salary, net_salary, tax_code, bank_account_number, bank_name, pay_period, last_paid_date) VALUES
(1, 1, 18725000, 15354500.0, 'TAX-VN-0000001', '012345670001', 'BIDV', '2026-09', '2026-10-05'),
(2, 2, 19450000, 15949000.0, 'TAX-VN-0000002', '012345670002', 'Techcombank', '2026-09', '2026-10-05'),
(3, 3, 20175000, 16543500.0, 'TAX-VN-0000003', '012345670003', 'MB Bank', '2026-09', '2026-10-05'),
(4, 4, 20900000, 17138000.0, 'TAX-VN-0000004', '012345670004', 'Vietcombank', '2026-09', '2026-10-05'),
(5, 5, 21625000, 17732500.0, 'TAX-VN-0000005', '012345670005', 'BIDV', '2026-09', '2026-10-05'),
(6, 6, 22350000, 18327000.0, 'TAX-VN-0000006', '012345670006', 'Techcombank', '2026-09', '2026-10-05'),
(7, 7, 23075000, 18921500.0, 'TAX-VN-0000007', '012345670007', 'MB Bank', '2026-09', '2026-10-05'),
(8, 8, 23800000, 19516000.0, 'TAX-VN-0000008', '012345670008', 'Vietcombank', '2026-09', '2026-10-05'),
(9, 9, 24525000, 20110500.0, 'TAX-VN-0000009', '012345670009', 'BIDV', '2026-09', '2026-10-05'),
(10, 10, 25250000, 20705000.0, 'TAX-VN-0000010', '012345670010', 'Techcombank', '2026-09', '2026-10-05'),
(11, 11, 25975000, 21299500.0, 'TAX-VN-0000011', '012345670011', 'MB Bank', '2026-09', '2026-10-05'),
(12, 12, 26700000, 21894000.0, 'TAX-VN-0000012', '012345670012', 'Vietcombank', '2026-09', '2026-10-05'),
(13, 13, 27425000, 22488500.0, 'TAX-VN-0000013', '012345670013', 'BIDV', '2026-09', '2026-10-05'),
(14, 14, 28150000, 23083000.0, 'TAX-VN-0000014', '012345670014', 'Techcombank', '2026-09', '2026-10-05'),
(15, 15, 28875000, 23677500.0, 'TAX-VN-0000015', '012345670015', 'MB Bank', '2026-09', '2026-10-05'),
(16, 16, 29600000, 24272000.0, 'TAX-VN-0000016', '012345670016', 'Vietcombank', '2026-09', '2026-10-05'),
(17, 17, 30325000, 24866500.0, 'TAX-VN-0000017', '012345670017', 'BIDV', '2026-09', '2026-10-05'),
(18, 18, 31050000, 25461000.0, 'TAX-VN-0000018', '012345670018', 'Techcombank', '2026-09', '2026-10-05'),
(19, 19, 31775000, 26055500.0, 'TAX-VN-0000019', '012345670019', 'MB Bank', '2026-09', '2026-10-05'),
(20, 20, 32500000, 26650000.0, 'TAX-VN-0000020', '012345670020', 'Vietcombank', '2026-09', '2026-10-05'),
(21, 21, 33225000, 27244500.0, 'TAX-VN-0000021', '012345670021', 'BIDV', '2026-09', '2026-10-05'),
(22, 22, 33950000, 27839000.0, 'TAX-VN-0000022', '012345670022', 'Techcombank', '2026-09', '2026-10-05')
ON CONFLICT (id) DO NOTHING;

INSERT INTO api_keys_config (id, service_name, key_type, key_value, environment, created_by, created_at, expires_at, is_active) VALUES
(1, 'inventory-api', 'bearer_token', 'vts_demo_tok_01_bcdef0123456789abcdef0123456789a', 'staging', 'svc-account-01', '2026-01-02 08:00:00', '2027-01-02 08:00:00', TRUE),
(2, 'support-mcp', 'webhook_secret', 'vts_demo_key_02_cdef0123456789abcdef0123456789ab', 'production', 'svc-account-02', '2026-01-03 08:00:00', '2027-01-03 08:00:00', TRUE),
(3, 'analytics-service', 'api_key', 'vts_demo_svc_03_def0123456789abcdef0123456789abc', 'development', 'svc-account-03', '2026-01-04 08:00:00', '2027-01-04 08:00:00', TRUE),
(4, 'notification-api', 'bearer_token', 'vts_demo_sk_04_ef0123456789abcdef0123456789abcd', 'staging', 'svc-account-04', '2026-01-05 08:00:00', '2027-01-05 08:00:00', TRUE),
(5, 'billing-api', 'webhook_secret', 'vts_demo_tok_05_f0123456789abcdef0123456789abcde', 'production', 'svc-account-05', '2026-01-06 08:00:00', '2027-01-06 08:00:00', TRUE),
(6, 'inventory-api', 'api_key', 'vts_demo_key_06_0123456789abcdef0123456789abcdef', 'development', 'svc-account-06', '2026-01-07 08:00:00', '2027-01-07 08:00:00', TRUE),
(7, 'support-mcp', 'bearer_token', 'vts_demo_svc_07_123456789abcdef0123456789abcdef0', 'staging', 'svc-account-07', '2026-01-08 08:00:00', '2027-01-08 08:00:00', TRUE),
(8, 'analytics-service', 'webhook_secret', 'vts_demo_sk_08_23456789abcdef0123456789abcdef01', 'production', 'svc-account-08', '2026-01-09 08:00:00', '2027-01-09 08:00:00', TRUE),
(9, 'notification-api', 'api_key', 'vts_demo_tok_09_3456789abcdef0123456789abcdef012', 'development', 'svc-account-09', '2026-01-10 08:00:00', '2027-01-10 08:00:00', TRUE),
(10, 'billing-api', 'bearer_token', 'vts_demo_key_10_456789abcdef0123456789abcdef0123', 'staging', 'svc-account-10', '2026-01-11 08:00:00', '2027-01-11 08:00:00', FALSE),
(11, 'inventory-api', 'webhook_secret', 'vts_demo_svc_11_56789abcdef0123456789abcdef01234', 'production', 'svc-account-11', '2026-01-12 08:00:00', '2027-01-12 08:00:00', TRUE),
(12, 'support-mcp', 'api_key', 'vts_demo_sk_12_6789abcdef0123456789abcdef012345', 'development', 'svc-account-12', '2026-01-13 08:00:00', '2027-01-13 08:00:00', TRUE),
(13, 'analytics-service', 'bearer_token', 'vts_demo_tok_13_789abcdef0123456789abcdef0123456', 'staging', 'svc-account-13', '2026-01-14 08:00:00', '2027-01-14 08:00:00', TRUE),
(14, 'notification-api', 'webhook_secret', 'vts_demo_key_14_89abcdef0123456789abcdef01234567', 'production', 'svc-account-14', '2026-01-15 08:00:00', '2027-01-15 08:00:00', TRUE),
(15, 'billing-api', 'api_key', 'vts_demo_svc_15_9abcdef0123456789abcdef012345678', 'development', 'svc-account-15', '2026-01-16 08:00:00', '2027-01-16 08:00:00', TRUE),
(16, 'inventory-api', 'bearer_token', 'vts_demo_sk_16_abcdef0123456789abcdef0123456789', 'staging', 'svc-account-16', '2026-01-17 08:00:00', '2027-01-17 08:00:00', TRUE),
(17, 'support-mcp', 'webhook_secret', 'vts_demo_tok_17_bcdef0123456789abcdef0123456789a', 'production', 'svc-account-17', '2026-01-18 08:00:00', '2027-01-18 08:00:00', TRUE),
(18, 'analytics-service', 'api_key', 'vts_demo_key_18_cdef0123456789abcdef0123456789ab', 'development', 'svc-account-18', '2026-01-19 08:00:00', '2027-01-19 08:00:00', TRUE),
(19, 'notification-api', 'bearer_token', 'vts_demo_svc_19_def0123456789abcdef0123456789abc', 'staging', 'svc-account-19', '2026-01-20 08:00:00', '2027-01-20 08:00:00', TRUE),
(20, 'billing-api', 'webhook_secret', 'vts_demo_sk_20_ef0123456789abcdef0123456789abcd', 'production', 'svc-account-20', '2026-01-21 08:00:00', '2027-01-21 08:00:00', FALSE)
ON CONFLICT (id) DO NOTHING;

INSERT INTO warehouses (id, code, name, region_id, capacity) VALUES
(1, 'WH-001', 'VietTech Warehouse 01', 1, 10750),
(2, 'WH-002', 'VietTech Warehouse 02', 2, 11500),
(3, 'WH-003', 'VietTech Warehouse 03', 3, 12250),
(4, 'WH-004', 'VietTech Warehouse 04', 4, 13000),
(5, 'WH-005', 'VietTech Warehouse 05', 5, 13750),
(6, 'WH-006', 'VietTech Warehouse 06', 6, 14500),
(7, 'WH-007', 'VietTech Warehouse 07', 7, 15250),
(8, 'WH-008', 'VietTech Warehouse 08', 8, 16000),
(9, 'WH-009', 'VietTech Warehouse 09', 9, 16750),
(10, 'WH-010', 'VietTech Warehouse 10', 10, 17500),
(11, 'WH-011', 'VietTech Warehouse 11', 11, 18250),
(12, 'WH-012', 'VietTech Warehouse 12', 12, 19000),
(13, 'WH-013', 'VietTech Warehouse 13', 13, 19750),
(14, 'WH-014', 'VietTech Warehouse 14', 14, 20500),
(15, 'WH-015', 'VietTech Warehouse 15', 15, 21250),
(16, 'WH-016', 'VietTech Warehouse 16', 16, 22000),
(17, 'WH-017', 'VietTech Warehouse 17', 17, 22750),
(18, 'WH-018', 'VietTech Warehouse 18', 18, 23500),
(19, 'WH-019', 'VietTech Warehouse 19', 19, 24250),
(20, 'WH-020', 'VietTech Warehouse 20', 20, 25000)
ON CONFLICT (id) DO NOTHING;

INSERT INTO orders (id, customer_id, employee_id, order_date, total_amount, amount, product_name, status, shipping_address, notes) VALUES
(1, 1, 4, '2026-02-02 10:15:00', 333.45, 333.45, 'VietTech Product 01', 'processing', '101 Sample Lane, District 2, Ho Chi Minh City', 'Demo order reference 001'),
(2, 2, 5, '2026-03-03 10:15:00', 416.9, 416.9, 'VietTech Product 02', 'shipped', '102 Sample Lane, District 3, Ho Chi Minh City', 'Demo order reference 002'),
(3, 3, 6, '2026-04-04 10:15:00', 500.35, 500.35, 'VietTech Product 03', 'completed', '103 Sample Lane, District 4, Ho Chi Minh City', 'Demo order reference 003'),
(4, 4, 7, '2026-05-05 10:15:00', 583.8, 583.8, 'VietTech Product 04', 'cancelled', '104 Sample Lane, District 5, Ho Chi Minh City', 'Demo order reference 004'),
(5, 5, 8, '2026-06-06 10:15:00', 667.25, 667.25, 'VietTech Product 05', 'pending', '105 Sample Lane, District 6, Ho Chi Minh City', 'Demo order reference 005'),
(6, 6, 9, '2026-07-07 10:15:00', 750.7, 750.7, 'VietTech Product 06', 'processing', '106 Sample Lane, District 7, Ho Chi Minh City', 'Demo order reference 006'),
(7, 7, 10, '2026-08-08 10:15:00', 834.15, 834.15, 'VietTech Product 07', 'shipped', '107 Sample Lane, District 8, Ho Chi Minh City', 'Demo order reference 007'),
(8, 8, 11, '2026-09-09 10:15:00', 917.6, 917.6, 'VietTech Product 08', 'completed', '108 Sample Lane, District 9, Ho Chi Minh City', 'Demo order reference 008'),
(9, 9, 12, '2026-01-10 10:15:00', 1001.05, 1001.05, 'VietTech Product 09', 'cancelled', '109 Sample Lane, District 10, Ho Chi Minh City', 'Demo order reference 009'),
(10, 10, 13, '2026-02-11 10:15:00', 1084.5, 1084.5, 'VietTech Product 10', 'pending', '110 Sample Lane, District 11, Ho Chi Minh City', 'Demo order reference 010'),
(11, 11, 14, '2026-03-12 10:15:00', 1167.95, 1167.95, 'VietTech Product 11', 'processing', '111 Sample Lane, District 12, Ho Chi Minh City', 'Demo order reference 011'),
(12, 12, 15, '2026-04-13 10:15:00', 1251.4, 1251.4, 'VietTech Product 12', 'shipped', '112 Sample Lane, District 1, Ho Chi Minh City', 'Demo order reference 012'),
(13, 13, 16, '2026-05-14 10:15:00', 1334.85, 1334.85, 'VietTech Product 13', 'completed', '113 Sample Lane, District 2, Ho Chi Minh City', 'Demo order reference 013'),
(14, 14, 17, '2026-06-15 10:15:00', 1418.3, 1418.3, 'VietTech Product 14', 'cancelled', '114 Sample Lane, District 3, Ho Chi Minh City', 'Demo order reference 014'),
(15, 15, 18, '2026-07-16 10:15:00', 1501.75, 1501.75, 'VietTech Product 15', 'pending', '115 Sample Lane, District 4, Ho Chi Minh City', 'Demo order reference 015'),
(16, 16, 19, '2026-08-17 10:15:00', 1585.2, 1585.2, 'VietTech Product 16', 'processing', '116 Sample Lane, District 5, Ho Chi Minh City', 'Demo order reference 016'),
(17, 17, 20, '2026-09-18 10:15:00', 1668.65, 1668.65, 'VietTech Product 17', 'shipped', '117 Sample Lane, District 6, Ho Chi Minh City', 'Demo order reference 017'),
(18, 18, 21, '2026-01-19 10:15:00', 1752.1, 1752.1, 'VietTech Product 18', 'completed', '118 Sample Lane, District 7, Ho Chi Minh City', 'Demo order reference 018'),
(19, 19, 22, '2026-02-20 10:15:00', 1835.55, 1835.55, 'VietTech Product 19', 'cancelled', '119 Sample Lane, District 8, Ho Chi Minh City', 'Demo order reference 019'),
(20, 20, 1, '2026-03-21 10:15:00', 1919.0, 1919.0, 'VietTech Product 20', 'pending', '120 Sample Lane, District 9, Ho Chi Minh City', 'Demo order reference 020'),
(21, 21, 2, '2026-04-22 10:15:00', 2002.45, 2002.45, 'VietTech Product 21', 'processing', '121 Sample Lane, District 10, Ho Chi Minh City', 'Demo order reference 021'),
(22, 22, 3, '2026-05-23 10:15:00', 2085.9, 2085.9, 'VietTech Product 22', 'shipped', '122 Sample Lane, District 11, Ho Chi Minh City', 'Demo order reference 022'),
(23, 1, 4, '2026-06-24 10:15:00', 2169.35, 2169.35, 'VietTech Product 23', 'completed', '123 Sample Lane, District 12, Ho Chi Minh City', 'Demo order reference 023'),
(24, 2, 5, '2026-07-25 10:15:00', 2252.8, 2252.8, 'VietTech Product 24', 'cancelled', '124 Sample Lane, District 1, Ho Chi Minh City', 'Demo order reference 024'),
(25, 3, 6, '2026-08-26 10:15:00', 2336.25, 2336.25, 'VietTech Product 25', 'pending', '125 Sample Lane, District 2, Ho Chi Minh City', 'Demo order reference 025')
ON CONFLICT (id) DO NOTHING;

INSERT INTO order_items (id, order_id, product_id, quantity, unit_price, discount_pct, warehouse_id) VALUES
(1, 1, 6, 2, 113.25, 5, 1),
(2, 2, 7, 3, 126.5, 10, 2),
(3, 3, 8, 4, 139.75, 15, 3),
(4, 4, 9, 5, 153.0, 0, 4),
(5, 5, 10, 1, 166.25, 5, 5),
(6, 6, 11, 2, 179.5, 10, 6),
(7, 7, 12, 3, 192.75, 15, 7),
(8, 8, 13, 4, 206.0, 0, 8),
(9, 9, 14, 5, 219.25, 5, 9),
(10, 10, 15, 1, 232.5, 10, 10),
(11, 11, 16, 2, 245.75, 15, 11),
(12, 12, 17, 3, 259.0, 0, 12),
(13, 13, 18, 4, 272.25, 5, 13),
(14, 14, 19, 5, 285.5, 10, 14),
(15, 15, 20, 1, 298.75, 15, 15),
(16, 16, 21, 2, 312.0, 0, 16),
(17, 17, 22, 3, 325.25, 5, 17),
(18, 18, 23, 4, 338.5, 10, 18),
(19, 19, 24, 5, 351.75, 15, 19),
(20, 20, 25, 1, 365.0, 0, 20),
(21, 21, 1, 2, 378.25, 5, 1),
(22, 22, 2, 3, 391.5, 10, 2),
(23, 23, 3, 4, 404.75, 15, 3),
(24, 24, 4, 5, 418.0, 0, 4),
(25, 25, 5, 1, 431.25, 5, 5)
ON CONFLICT (id) DO NOTHING;

INSERT INTO payments (id, order_id, method, amount, paid_at, status, transaction_ref) VALUES
(1, 1, 'bank_transfer', 333.45, '2026-02-02 11:20:00', 'settled', 'TXN-VTS-000001'),
(2, 2, 'e_wallet', 416.9, '2026-03-03 11:20:00', 'pending', 'TXN-VTS-000002'),
(3, 3, 'cash', 500.35, '2026-04-04 11:20:00', 'refunded', 'TXN-VTS-000003'),
(4, 4, 'card', 583.8, '2026-05-05 11:20:00', 'settled', 'TXN-VTS-000004'),
(5, 5, 'bank_transfer', 667.25, '2026-06-06 11:20:00', 'settled', 'TXN-VTS-000005'),
(6, 6, 'e_wallet', 750.7, '2026-07-07 11:20:00', 'pending', 'TXN-VTS-000006'),
(7, 7, 'cash', 834.15, '2026-08-08 11:20:00', 'refunded', 'TXN-VTS-000007'),
(8, 8, 'card', 917.6, '2026-09-09 11:20:00', 'settled', 'TXN-VTS-000008'),
(9, 9, 'bank_transfer', 1001.05, '2026-01-10 11:20:00', 'settled', 'TXN-VTS-000009'),
(10, 10, 'e_wallet', 1084.5, '2026-02-11 11:20:00', 'pending', 'TXN-VTS-000010'),
(11, 11, 'cash', 1167.95, '2026-03-12 11:20:00', 'refunded', 'TXN-VTS-000011'),
(12, 12, 'card', 1251.4, '2026-04-13 11:20:00', 'settled', 'TXN-VTS-000012'),
(13, 13, 'bank_transfer', 1334.85, '2026-05-14 11:20:00', 'settled', 'TXN-VTS-000013'),
(14, 14, 'e_wallet', 1418.3, '2026-06-15 11:20:00', 'pending', 'TXN-VTS-000014'),
(15, 15, 'cash', 1501.75, '2026-07-16 11:20:00', 'refunded', 'TXN-VTS-000015'),
(16, 16, 'card', 1585.2, '2026-08-17 11:20:00', 'settled', 'TXN-VTS-000016'),
(17, 17, 'bank_transfer', 1668.65, '2026-09-18 11:20:00', 'settled', 'TXN-VTS-000017'),
(18, 18, 'e_wallet', 1752.1, '2026-01-19 11:20:00', 'pending', 'TXN-VTS-000018'),
(19, 19, 'cash', 1835.55, '2026-02-20 11:20:00', 'refunded', 'TXN-VTS-000019'),
(20, 20, 'card', 1919.0, '2026-03-21 11:20:00', 'settled', 'TXN-VTS-000020'),
(21, 21, 'bank_transfer', 2002.45, '2026-04-22 11:20:00', 'settled', 'TXN-VTS-000021'),
(22, 22, 'e_wallet', 2085.9, '2026-05-23 11:20:00', 'pending', 'TXN-VTS-000022'),
(23, 23, 'cash', 2169.35, '2026-06-24 11:20:00', 'refunded', 'TXN-VTS-000023'),
(24, 24, 'card', 2252.8, '2026-07-25 11:20:00', 'settled', 'TXN-VTS-000024'),
(25, 25, 'bank_transfer', 2336.25, '2026-08-26 11:20:00', 'settled', 'TXN-VTS-000025')
ON CONFLICT (id) DO NOTHING;

INSERT INTO financial_transactions (id, payment_id, card_last_four, card_brand, billing_address, amount, currency, processor_response, created_at) VALUES
(1, 1, '0001', 'Mastercard', '21 Billing Avenue, District 2, Ho Chi Minh City', 333.45, 'VND', 'captured', '2026-09-02 11:30:00'),
(2, 2, '0002', 'American Express', '22 Billing Avenue, District 3, Ho Chi Minh City', 416.9, 'VND', 'settled', '2026-09-03 11:30:00'),
(3, 3, '0003', 'Visa', '23 Billing Avenue, District 4, Ho Chi Minh City', 500.35, 'VND', 'approved', '2026-09-04 11:30:00'),
(4, 4, '0004', 'Mastercard', '24 Billing Avenue, District 5, Ho Chi Minh City', 583.8, 'VND', 'captured', '2026-09-05 11:30:00'),
(5, 5, '0005', 'American Express', '25 Billing Avenue, District 6, Ho Chi Minh City', 667.25, 'VND', 'settled', '2026-09-06 11:30:00'),
(6, 6, '0006', 'Visa', '26 Billing Avenue, District 7, Ho Chi Minh City', 750.7, 'VND', 'approved', '2026-09-07 11:30:00'),
(7, 7, '0007', 'Mastercard', '27 Billing Avenue, District 8, Ho Chi Minh City', 834.15, 'VND', 'captured', '2026-09-08 11:30:00'),
(8, 8, '0008', 'American Express', '28 Billing Avenue, District 9, Ho Chi Minh City', 917.6, 'VND', 'settled', '2026-09-09 11:30:00'),
(9, 9, '0009', 'Visa', '29 Billing Avenue, District 10, Ho Chi Minh City', 1001.05, 'VND', 'approved', '2026-09-10 11:30:00'),
(10, 10, '0010', 'Mastercard', '30 Billing Avenue, District 11, Ho Chi Minh City', 1084.5, 'VND', 'captured', '2026-09-11 11:30:00'),
(11, 11, '0011', 'American Express', '31 Billing Avenue, District 12, Ho Chi Minh City', 1167.95, 'VND', 'settled', '2026-09-12 11:30:00'),
(12, 12, '0012', 'Visa', '32 Billing Avenue, District 1, Ho Chi Minh City', 1251.4, 'VND', 'approved', '2026-09-13 11:30:00'),
(13, 13, '0013', 'Mastercard', '33 Billing Avenue, District 2, Ho Chi Minh City', 1334.85, 'VND', 'captured', '2026-09-14 11:30:00'),
(14, 14, '0014', 'American Express', '34 Billing Avenue, District 3, Ho Chi Minh City', 1418.3, 'VND', 'settled', '2026-09-15 11:30:00'),
(15, 15, '0015', 'Visa', '35 Billing Avenue, District 4, Ho Chi Minh City', 1501.75, 'VND', 'approved', '2026-09-16 11:30:00'),
(16, 16, '0016', 'Mastercard', '36 Billing Avenue, District 5, Ho Chi Minh City', 1585.2, 'VND', 'captured', '2026-09-17 11:30:00'),
(17, 17, '0017', 'American Express', '37 Billing Avenue, District 6, Ho Chi Minh City', 1668.65, 'VND', 'settled', '2026-09-18 11:30:00'),
(18, 18, '0018', 'Visa', '38 Billing Avenue, District 7, Ho Chi Minh City', 1752.1, 'VND', 'approved', '2026-09-19 11:30:00'),
(19, 19, '0019', 'Mastercard', '39 Billing Avenue, District 8, Ho Chi Minh City', 1835.55, 'VND', 'captured', '2026-09-20 11:30:00'),
(20, 20, '0020', 'American Express', '40 Billing Avenue, District 9, Ho Chi Minh City', 1919.0, 'VND', 'settled', '2026-09-21 11:30:00')
ON CONFLICT (id) DO NOTHING;

INSERT INTO inventory_snapshots (id, product_id, warehouse_id, snapshot_date, qty_on_hand, qty_reserved, qty_available) VALUES
(1, 1, 1, '2026-10-01', 107, 1, 106),
(2, 2, 2, '2026-10-02', 114, 2, 112),
(3, 3, 3, '2026-10-03', 121, 3, 118),
(4, 4, 4, '2026-10-04', 128, 4, 124),
(5, 5, 5, '2026-10-05', 135, 5, 130),
(6, 6, 6, '2026-10-06', 142, 6, 136),
(7, 7, 7, '2026-10-07', 149, 7, 142),
(8, 8, 8, '2026-10-08', 156, 8, 148),
(9, 9, 9, '2026-10-09', 163, 9, 154),
(10, 10, 10, '2026-10-10', 170, 10, 160),
(11, 11, 11, '2026-10-11', 177, 11, 166),
(12, 12, 12, '2026-10-12', 184, 12, 172),
(13, 13, 13, '2026-10-13', 191, 13, 178),
(14, 14, 14, '2026-10-14', 198, 14, 184),
(15, 15, 15, '2026-10-15', 205, 15, 190),
(16, 16, 16, '2026-10-16', 212, 16, 196),
(17, 17, 17, '2026-10-17', 219, 0, 219),
(18, 18, 18, '2026-10-18', 226, 1, 225),
(19, 19, 19, '2026-10-01', 233, 2, 231),
(20, 20, 20, '2026-10-02', 240, 3, 237),
(21, 21, 1, '2026-10-03', 247, 4, 243),
(22, 22, 2, '2026-10-04', 254, 5, 249),
(23, 23, 3, '2026-10-05', 261, 6, 255),
(24, 24, 4, '2026-10-06', 268, 7, 261),
(25, 25, 5, '2026-10-07', 275, 8, 267)
ON CONFLICT (id) DO NOTHING;

SELECT setval(pg_get_serial_sequence('regions', 'id'), COALESCE((SELECT MAX(id) FROM regions), 1), true);

SELECT setval(pg_get_serial_sequence('categories', 'id'), COALESCE((SELECT MAX(id) FROM categories), 1), true);

SELECT setval(pg_get_serial_sequence('customers', 'id'), COALESCE((SELECT MAX(id) FROM customers), 1), true);

SELECT setval(pg_get_serial_sequence('products', 'id'), COALESCE((SELECT MAX(id) FROM products), 1), true);

SELECT setval(pg_get_serial_sequence('employees', 'id'), COALESCE((SELECT MAX(id) FROM employees), 1), true);

SELECT setval(pg_get_serial_sequence('hr_payroll', 'id'), COALESCE((SELECT MAX(id) FROM hr_payroll), 1), true);

SELECT setval(pg_get_serial_sequence('api_keys_config', 'id'), COALESCE((SELECT MAX(id) FROM api_keys_config), 1), true);

SELECT setval(pg_get_serial_sequence('warehouses', 'id'), COALESCE((SELECT MAX(id) FROM warehouses), 1), true);

SELECT setval(pg_get_serial_sequence('orders', 'id'), COALESCE((SELECT MAX(id) FROM orders), 1), true);

SELECT setval(pg_get_serial_sequence('order_items', 'id'), COALESCE((SELECT MAX(id) FROM order_items), 1), true);

SELECT setval(pg_get_serial_sequence('payments', 'id'), COALESCE((SELECT MAX(id) FROM payments), 1), true);

SELECT setval(pg_get_serial_sequence('financial_transactions', 'id'), COALESCE((SELECT MAX(id) FROM financial_transactions), 1), true);

SELECT setval(pg_get_serial_sequence('inventory_snapshots', 'id'), COALESCE((SELECT MAX(id) FROM inventory_snapshots), 1), true);

COMMIT;

