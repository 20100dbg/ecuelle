
CREATE TABLE data (
    id SERIAL PRIMARY KEY,
    petit_int SMALLINT,
    entier INTEGER,
    grand_int BIGINT,
    decimal_num NUMERIC(10,2),
    reel_simple REAL,
    reel_double DOUBLE PRECISION,
    booleen BOOLEAN,
    texte_court VARCHAR(100),
    texte_long TEXT,
    caractere CHAR(3),
    date_simple DATE,
    heure_simple TIME,
    date_heure TIMESTAMP,
    date_heure_tz TIMESTAMPTZ,
    intervalle INTERVAL,
    donnees_json JSON,
    donnees_jsonb JSONB,
    tableau_int INTEGER[],
    uuid_col UUID,
    adresse_ip INET,
    mac_adresse MACADDR,
    point_geo POINT,
    argent MONEY,
    donnees_bin BYTEA
);

INSERT INTO data (
    petit_int,
    entier,
    grand_int,
    decimal_num,
    reel_simple,
    reel_double,
    booleen,
    texte_court,
    texte_long,
    caractere,
    date_simple,
    heure_simple,
    date_heure,
    date_heure_tz,
    intervalle,
    donnees_json,
    donnees_jsonb,
    tableau_int,
    uuid_col,
    adresse_ip,
    mac_adresse,
    point_geo,
    argent,
    donnees_bin
)
VALUES (
    10,
    1000,
    9000000000,
    1234.56,
    3.14,
    3.1415926535,
    TRUE,
    'Texte court',
    'Ceci est un texte beaucoup plus long',
    'ABC',
    '2026-03-04',
    '14:30:00',
    '2026-03-04 14:30:00',
    '2026-03-04 14:30:00+01',
    INTERVAL '2 days 3 hours',
    '{"cle": "valeur"}',
    '{"cle": "valeur"}',
    ARRAY[1,2,3,4],
    '550e8400-e29b-41d4-a716-446655440000',
    '192.168.1.1',
    '08:00:2b:01:02:03',
    POINT(48.8566, 2.3522),
    99.99,
    E'\\xDEADBEEF'
);

CREATE TABLE users (
    id SERIAL,
    name varchar(200),
    email varchar(200),
    password varchar(200)
);

INSERT INTO users VALUES 
    (1, 'admin', 'admin@mail.net', 'password123'),
    (2, 'user', 'user@mail.net', 'Secret1'),
    (3, 'test', 'test@mail.net', 'lovamor1984');

