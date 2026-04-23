<?php
$host = "127.0.0.1";
$user = "root";
$password = "my-secret-password123";
$database = "sample";

$sql = "SELECT * FROM users";
$sql = "SELECT null,'',0";


$conn = mysqli_connect($host, $user, $password, $database);
$result = mysqli_query($conn, $sql);

$tab = [];
if ($result) {
    while ($row = mysqli_fetch_assoc($result)) {
        $tab[] = $row;
    }
}
var_dump($tab);
mysqli_close($conn);
die;


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
