CREATE DATABASE IF NOT EXISTS sample;

USE sample;

CREATE TABLE IF NOT EXISTS ts (
    col1 TINYINT,
    ts1 TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    col2 TINYINT,
    ts2 TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    col3 TINYINT,
    ts3 TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    col4 TINYINT
);

INSERT INTO ts VALUES (127, NULL, 127, now(), 127, '2026-01-02 10:25:48', 127);


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

INSERT INTO data VALUES (12,23,34,31337,987698769876,12345678.123,654.789,
                            3.145579, 32.987654, 987.1234567,
                            TRUE,
                            '2026-03-01', '2026-03-01 10:09:56', now(), '11:34:21', '2026',
                            'salut', 'hello', 'bonjour', 'hola que tal', 'medium text', 'looooong text',
                            '0x1337', '0xcafebabe', '0xdeadbeef', '0xdadedade', '0xbabebabe', '0x031337',
                            'valeur1', 'b',
                            '{"type":"json"}');



CREATE TABLE IF NOT EXISTS users (
    id int auto_increment primary key,
    name varchar(200),
    email varchar(200),
    password varchar(200)
);

INSERT INTO users VALUES 
    (1, 'admin', 'admin@mail.net', 'password123'),
    (2, 'user', 'user@mail.net', 'Secret1'),
    (3, 'test', 'test@mail.net', 'lovamor1984');

