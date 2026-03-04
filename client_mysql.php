<?php

$host = '127.0.0.1';
$dbname = 'sample';
$username = 'root';
$password = 'my-secret-password';
$port = 3306;

$db = mysqli_connect($host, $username, $password, $dbname, $port);

/*
$query = "SELECT * FROM ts";
$query = "SELECT * FROM data";

$query = 'SELECT id,name,password FROM users WHERE id = 1 or id = 2';
$args = [];
*/

$query = 'SELECT "","","" FROM users WHERE id = 1';
$args = [];


//prepared statement
//$result = $db->execute_query($query, $args);

//query
$result = $db->query($query);

foreach ($result as $row) {
    var_dump($row);
}

/*
foreach ($result as $row) {
    echo $row['id'] . ' - ' . $row['name'] . PHP_EOL;
}
*/



/*
try {
    $pdo = new PDO("mysql:host=$host;dbname=$dbname;charset=utf8;port=$port", $username, $password);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    $sql = "SELECT id, name FROM users WHERE id=:id OR name=:name";
    $stmt = $pdo->prepare($sql);

    $id = 1;
    $name = 'admin';

    //PDO::PARAM_BOOL
    //PDO::PARAM_NULL

    $stmt->bindParam(':id', $id, PDO::PARAM_INT);
    $stmt->bindParam(':name', $name, PDO::PARAM_STR);
    $stmt->execute();
    $resultat = $stmt->fetchAll(PDO::FETCH_ASSOC);
    var_dump($resultat);

    /*
    $sql = "INSERT INTO utilisateurs (nom, email) VALUES (:nom, :email)";
    $stmt = $pdo->prepare($sql);
    $stmt->bindParam(':id', $id, PDO::PARAM_INT);
    $stmt->execute();
    */

/*
} catch (PDOException $e) {
    echo "Erreur : " . $e->getMessage();
}
*/
