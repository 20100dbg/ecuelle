<?php

$serverName = "localhost";  // or hostname/IP
$connectionOptions = array(
    "Database" => "mydb",
    "Uid" => "sa",
    "PWD" => "Mys3cretPassword-123",
    "CharacterSet" => "UTF-8"
);

$conn = sqlsrv_connect($serverName, $connectionOptions);

if ($conn === false) {
    die(print_r(sqlsrv_errors(), true));
}

$sql = "SELECT id, name FROM users";
$stmt = sqlsrv_query($conn, $sql);

if ($stmt === false) {
    die(print_r(sqlsrv_errors(), true));
}

while ($row = sqlsrv_fetch_array($stmt, SQLSRV_FETCH_ASSOC)) {
    echo "ID: " . $row['id'] . " Name: " . $row['name'] . PHP_EOL;
}

sqlsrv_free_stmt($stmt);
sqlsrv_close($conn);

