<?php

function oldschool_query($config, $query, $parameters=null)
{
    try
    {
        $db = new mysqli($config['host'], $config['user'], $config['password'], $config['database'], $config['port']);
        /*
        $stmt = $db->prepare($query);
        if ($parameters) {
            $types = str_repeat("s", count($parameters));
            $stmt->bind_param($types, ...$parameters);
        }
        $stmt->execute();
        $result = $stmt->get_result()->fetch_all(MYSQLI_ASSOC);
        var_dump($result);
        */

        $result = $db->execute_query($query, $parameters ?? []);
        $data = $result->fetch_all(MYSQLI_ASSOC);

        $db->close();

        return $result;
    } catch (Exception $e) {
        return $e;
    }
}

function pdo_query($config, $query, $parameters = null)
{
    try {

        $options = [
            PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES   => false,
        ];

        $dsn = $config["dbms"] . ":host=" . $config["host"] . ";dbname=" . $config["database"] . ";port=". $config["port"] ."charset=utf8";
        $pdo = new PDO($dsn, $config["user"], $config["password"], $options);

        /*
        $stmt = $pdo->prepare($query);
        if ($parameters) {
            for ($i = 0; $i < count($parameters); $i++) {
                $stmt->bindValue($i + 1, $parameters[$i], PDO::PARAM_STR);
            }
        }
        $stmt->execute();
        $result1 = $stmt->fetchAll(PDO::FETCH_ASSOC);
        var_dump($result1);
        */

        if ($parameters)
        {
            $stmt = $pdo->prepare($query);
            $stmt->execute($parameters ?? []);
            $result = $stmt->fetchAll(PDO::FETCH_ASSOC);
        }
        else
        {
            $stmt = $pdo->query($query);
            $result = $stmt->fetchAll(PDO::FETCH_ASSOC);
        }
        return $result;

    } catch (PDOException $e) {
        return $e->getMessage();
    }
}



$config = [
    "host"=> getenv('DB_HOST'),
    "user"=> getenv('DB_USER'),
    "password"=> getenv('DB_PASSWORD'),
    "database"=> getenv('DB_NAME'),
    "port"=> intval(getenv('PROXY_PORT')),
    "dbms" => getenv('DB_TYPE')
];

$debug = getenv('DEBUG') and strtolower(getenv('DEBUG')) == "true";


$queries = [
    ["SELECT * FROM users;", null],
    ["SELECT * FROM data;", null],
    ["SELECT * FROM NOT_A_TABLE;", null],
    ["SELECT '',0,null", null],
    ["SELECT * FROM users WHERE id = 9999;", null],
    ["SELECT id, name, password FROM users WHERE id=?", array(1)],
    ["SELECT id, name, password FROM users WHERE id IN (?,?,?)", array(1,999,"salut")],
    ["SELECT id, name, password FROM users WHERE id=:id", array('id'=> 2)],
];


for ($i=0; $i < count($queries); $i++) {

    //old school query doesn't support named parameters
    //so we check if the parameter array is sequential and not associative
    if (isset($array[0])) {
        $result = oldschool_query($config, $queries[$i][0], $queries[$i][1]);
        var_dump($result);
    } 

    $result = pdo_query($config, $queries[$i][0], $queries[$i][1]);
    var_dump($result);
}
