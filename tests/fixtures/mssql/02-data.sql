
INSERT INTO data VALUES (
    -- Numeric
    1,                      -- BIT
    255,                    -- TINYINT
    32767,                  -- SMALLINT
    2147483647,             -- INT
    9223372036854775807,    -- BIGINT
    12345.67,               -- DECIMAL
    98765.43,               -- NUMERIC
    123.456,                -- FLOAT
    78.9,                   -- REAL
    1000.50,                -- MONEY
    500.25,                 -- SMALLMONEY

    -- Date/time
    '2026-04-09',           -- DATE
    '14:30:00',             -- TIME
    '2026-04-09 14:30:00',  -- DATETIME
    '2026-04-09 14:30:00.1234567', -- DATETIME2
    '2026-04-09 14:30:00',  -- SMALLDATETIME
    '2026-04-09 14:30:00 +02:00', -- DATETIMEOFFSET

    -- Strings
    'CHARTEST',
    'VarChar example',
    'This is a VARCHAR(MAX) example',
    N'NCHARTEST',
    N'NVarchar example',
    N'This is an NVARCHAR(MAX) example',
    'Old text data',
    N'Old ntext data',

    -- Binary
    0x1234,
    0x123456,
    0x1234567890,
    0x123456,               -- IMAGE

    -- Other
    NEWID(),                -- UNIQUEIDENTIFIER
    '<root><value>XML</value></root>' 
    --'Sample SQL_VARIANT'
);



INSERT INTO users VALUES 
    ('admin', 'admin@mail.net', 'password123'),
    ('user', 'user@mail.net', 'Secret1'),
    ('test', 'test@mail.net', 'lovamor1984');

