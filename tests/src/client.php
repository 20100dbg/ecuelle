<?php

function oldschool_mysql_query($config, $query, $parameters=null)
{
    try
    {
        $db = new mysqli($config['host'], $config['user'], $config['password'], $config['database'], $config['port']);
        $result = $db->execute_query($query, $parameters ?? []);
        $data = $result->fetch_all(MYSQLI_ASSOC);
        
        $db->close();
        return $data;

    } catch (Exception $e) {
        return $e;
    }
}

function oldschool_postgres_query($config, $query, $parameters=null)
{
    try {
        $db = pg_connect("host={$config['host']} port={$config['port']} dbname={$config['database']} user={$config['user']} password={$config['password']}");

        $result = pg_query_params($db, $query, $parameters ?? []);
        if ($result !== false) {
            $data = pg_fetch_all($result);
        }
        pg_close($db);
        return $data ?? null;

    } catch (Exception $e) {
        return $e;
    }
}


function oldschool_mssql_query($config, $query, $parameters=null)
{
    try {
        $connectionInfo = ["Database" => $config['database'],"UID" => $config['user'],"PWD" => $config['password']];
        $db = sqlsrv_connect($config['host'], $connectionInfo);
        $result = sqlsrv_query($db, $query, $parameters ?? []);

        $data = [];
        while ($row = sqlsrv_fetch_array($result, SQLSRV_FETCH_ASSOC)) {
            $data[] = $row;
        }

        sqlsrv_close($db);
        return $data;

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

        switch ($config["dbms"]) {
            case 'mysql': $driver = 'mysql'; break;
            case 'postgres': $driver = 'pgsql'; break;
            case 'mssql': $driver = 'sqlsrv'; break;
            default: break;
        }

        $dsn = $driver . ":host=" . $config["host"] . ";dbname=" . $config["database"] . ";port=". $config["port"];
        $pdo = new PDO($dsn, $config["user"], $config["password"], $options);

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

function replace_placeholder($query) {
    $i = 0;
    return preg_replace_callback('/\?/', function() use (&$i) {
        return '$' . ++$i;
    }, $query);
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

    //old school query doesn't support named parameters
    //so we check if the parameter array is sequential and not associative

    if (count($queries[$i]["params"]) == 0 || isset($queries[$i]["params"][0])) {

        if ($config['dbms'] == 'mysql') {
            $result = oldschool_mysql_query($config, $queries[$i]["query"], $queries[$i]["params"]);
        }
        else if ($config['dbms'] == 'postgres') {
            $query = replace_placeholder($queries[$i]["query"]);
            $result = oldschool_postgres_query($config, $query, $queries[$i]["params"]);
        }
        else if ($config['dbms'] == 'mssql') {
            $result = oldschool_mssql_query($config, $queries[$i]["query"], $queries[$i]["params"]);
        }

    }

    echo '> '. $queries[$i]["query"] . PHP_EOL;
    echo '<';
    print_var($result);
    echo PHP_EOL;
}
