
CREATE TABLE users (
    id INT NOT NULL IDENTITY(1, 1) PRIMARY KEY,
    name varchar(200),
    email varchar(200),
    password varchar(200)
);

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
    XmlCol XML
    --SqlVariantCol SQL_VARIANT
);

