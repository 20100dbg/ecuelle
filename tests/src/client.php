<?php
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


echo '--- PHP script start' . PHP_EOL;

if ($debug) {
    var_dump($config);
}

$basic_queries = [
    ["SELECT * FROM users;", null],
];

$extended_queries = [
    ["SELECT * FROM data;", null],
    ["SELECT * FROM NOT_A_TABLE;", null],
    ["SELECT '',0,null", null],
    ["SELECT * FROM users WHERE id = 9999;", null],
    ["SELECT id, name, password FROM users WHERE id IN (?,?) or name=?", array(1,2,"salut")],
    ["SELECT id, name, password FROM users WHERE id=:id", array('id'=> 2)],
];

$queries = $basic_queries;

if ($argc == 2 && ($argv[1] == "all" || $argv[1] == "--all")) {
    $queries = array_merge($basic_queries, $extended_queries);
}


for ($i=0; $i < count($queries); $i++) {

    //old school query doesn't support named parameters
    //so we check if the parameter array is sequential and not associative

    if ($queries[$i][1] == null || isset($queries[$i][1][0])) {

        if ($config['dbms'] == 'mysql') {
            $result = oldschool_mysql_query($config, $queries[$i][0], $queries[$i][1]);
        }
        else if ($config['dbms'] == 'postgres') {
            $query = replace_placeholder($queries[$i][0]);
            $result = oldschool_postgres_query($config, $query, $queries[$i][1]);
        }
        else if ($config['dbms'] == 'mssql') {
            $result = oldschool_mssql_query($config, $queries[$i][0], $queries[$i][1]);
        }
        echo '> '. $queries[$i][0] . PHP_EOL;
        echo '<';
        print_var($result);
    } 

    $result = pdo_query($config, $queries[$i][0], $queries[$i][1]);
    echo '> '. $queries[$i][0] . PHP_EOL;
    echo '< ';
    print_var($result);
    echo PHP_EOL;
}

echo '--- PHP script done' . PHP_EOL;
