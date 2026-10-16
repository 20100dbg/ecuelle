<?php

$dbms = getenv('DB_TYPE')
$config = [
    "host"=> getenv('DB_HOST'),
    "user"=> getenv('DB_USER'),
    "password"=> getenv('DB_PASSWORD'),
    "database"=> getenv('DB_NAME'),
    "port"=> intval(getenv('PROXY_PORT')),
];

$debug = getenv('DEBUG') and strtolower(getenv('DEBUG')) == "true";

$queries = [
    "SELECT * FROM users;",
    "SELECT * FROM data;",
    "SELECT * FROM NOT_A_TABLE;",
    "SELECT '',0,null"
];


$conn = mysqli_connect($host, $user, $password, $database);

for ($i=0; $i < count($queries); $i++) { 
    $tab = [];
    $result = mysqli_query($conn, $queries[$i]);
    if ($result) {
        while ($row = mysqli_fetch_assoc($result)) {
            $tab[] = $row;
        }
    }
    var_dump($queries[$i]);
    var_dump($tab);
}

/*
$stmt = $mysqli->prepare("SELECT District FROM City WHERE Name=?");
$stmt->bind_param("s", $city);
*/
mysqli_close($conn);


try {
    $pdo = new PDO("mysql:host=$host;dbname=$database;charset=utf8", $user, $password);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    
    $stmt = $pdo->query($sql);

    $tab = [];
    while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
        $tab[] = $row;
    }
    var_dump($tab);



    $stmt = $pdo->prepare($sql);
    
    $params = array('id' => 1);
    $params = [];

    $stmt->execute($params);

    $tab = [];
    while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
        $tab[] = $row;
    }
    var_dump($tab);

    

} catch (PDOException $e) {
    echo "Erreur : " . $e->getMessage();
}
