
CREATE TABLE data (
    -- Numeric types
    BitCol BIT,
    TinyIntCol TINYINT,
    SmallIntCol SMALLINT,
    IntCol INT,
    BigIntCol BIGINT,
    DecimalCol DECIMAL(10,2),
    NumericCol NUMERIC(10,2),
    FloatCol FLOAT,
    RealCol REAL,
    MoneyCol MONEY,
    SmallMoneyCol SMALLMONEY,

    -- Date and time
    DateCol DATE,
    TimeCol TIME,
    DateTimeCol DATETIME,
    DateTime2Col DATETIME2,
    SmallDateTimeCol SMALLDATETIME,
    DateTimeOffsetCol DATETIMEOFFSET,

    -- Character strings
    CharCol CHAR(10),
    VarCharCol VARCHAR(50),
    VarCharMaxCol VARCHAR(MAX),
    NCharCol NCHAR(10),
    NVarCharCol NVARCHAR(50),
    NVarCharMaxCol NVARCHAR(MAX),
    TextCol TEXT,           -- deprecated
    NTextCol NTEXT,         -- deprecated

    -- Binary
    BinaryCol BINARY(4),
    VarBinaryCol VARBINARY(50),
    VarBinaryMaxCol VARBINARY(MAX),
    ImageCol IMAGE,         -- deprecated

    -- Other
    UniqueIdCol UNIQUEIDENTIFIER,
    XmlCol XML,
    SqlVariantCol SQL_VARIANT
);


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
    '<root><value>XML</value></root>',
    'Sample SQL_VARIANT'
);


CREATE TABLE users (
    id INT NOT NULL IDENTITY(1, 1) PRIMARY KEY,
    name varchar(200),
    email varchar(200),
    password varchar(200)
);

INSERT INTO users VALUES 
    ('admin', 'admin@mail.net', 'password123'),
    ('user', 'user@mail.net', 'Secret1'),
    ('test', 'test@mail.net', 'lovamor1984');

