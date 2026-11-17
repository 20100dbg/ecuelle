<?php

function pdo_query($config, $query, $parameters)
{
    try {

        switch ($config["dbms"]) {
            case 'mysql': $driver = 'mysql'; break;
            case 'postgres': $driver = 'pgsql'; break;
            case 'mssql': $driver = 'sqlsrv'; break;
            default: break;
        }

        $options = [
            PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES   => true,
        ];

        $dsn = $driver . ":host=" . $config["host"] . ";dbname=" . $config["database"] . ";port=". $config["port"];
        $pdo = new PDO($dsn, $config["user"], $config["password"], $options);

        if (count($parameters) > 0)
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

function print_var($var) {
    $var = var_export($var, true);
    $var = preg_replace("/\s+/", " ", $var);
    echo $var . PHP_EOL;
}

$envvars = ['DB_TYPE','PROXY_PORT','DB_HOST','DB_USER','DB_PASSWORD','DB_NAME'];
foreach ($envvars as $var)
{
    if (getenv($var) === false)
    {
        echo "Please set ". $var . PHP_EOL;
        die;
    }
}


$debug = getenv('DEBUG') and strtolower(getenv('DEBUG')) == "true";

$config = [
    "host"=> getenv('DB_HOST'),
    "user"=> getenv('DB_USER'),
    "password"=> getenv('DB_PASSWORD'),
    "database"=> getenv('DB_NAME'),
    "port"=> intval(getenv('PROXY_PORT')),
    "dbms" => getenv('DB_TYPE')
];


if ($debug) {
    var_dump($config);
}

$json = file_get_contents('queries.json');
$all_queries = json_decode($json, true);
$queries = [];
$queries_type = [];

if ($argc == 2) {
    $queries_type = explode(',', $argv[1]);
}

foreach ($all_queries as $query_type=>$queries_arr) {
    if (count($queries_type) == 0 || in_array($query_type, $queries_type)) {
        $queries = array_merge($queries, $queries_arr);
    }
}

for ($i=0; $i < count($queries); $i++) {

    echo "query " . $queries[$i]["query"] . PHP_EOL;
    print_var($queries[$i]["params"]);
    echo PHP_EOL;

    $result = pdo_query($config, $queries[$i]["query"], $queries[$i]["params"]);
    echo '> '. $queries[$i]["query"] . PHP_EOL;
    echo '< ';
    print_var($result);
    echo PHP_EOL;
}
