CREATE DATABASE IF NOT EXISTS sample;

USE sample;

CREATE TABLE IF NOT EXISTS data (
    tiny_int_col TINYINT,
    small_int_col SMALLINT,
    medium_int_col MEDIUMINT,
    int_col INT,
    big_int_col BIGINT,
    decimal_col DECIMAL(10,2),
    numeric_col NUMERIC(8,3),

    float_col FLOAT,
    double_col DOUBLE,
    real_col REAL,

    boolean_col BOOLEAN,

    date_col DATE,
    datetime_col DATETIME,
    timestamp_col TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    time_col TIME,
    year_col YEAR,

    char_col CHAR(10),
    varchar_col VARCHAR(255),
    tinytext_col TINYTEXT,
    text_col TEXT,
    mediumtext_col MEDIUMTEXT,
    longtext_col LONGTEXT,

    binary_col BINARY(16),
    varbinary_col VARBINARY(255),
    tinyblob_col TINYBLOB,
    blob_col BLOB,
    mediumblob_col MEDIUMBLOB,
    longblob_col LONGBLOB,

    enum_col ENUM('valeur1', 'valeur2', 'valeur3'),
    set_col SET('a', 'b', 'c'),

    json_col JSON
);

CREATE TABLE IF NOT EXISTS users (
    id int auto_increment primary key,
    name varchar(200),
    email varchar(200),
    password varchar(200)
);
