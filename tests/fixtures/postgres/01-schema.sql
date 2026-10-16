
CREATE TABLE users (
    id SERIAL,
    name varchar(200),
    email varchar(200),
    password varchar(200)
);

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

