<?php

$host = '127.0.0.1';
$port = "5432";
$dbname = "mydb";
$user = "myuser";
$password = "mypassword";

$conn_string = "host=$host port=$port dbname=$dbname user=$user password=$password";

$conn = pg_connect($conn_string);

$query = "SELECT id, name FROM users";

$result = pg_query($conn, $query);

/*
$result = pg_prepare($conn, "my_query", $query);
$result = pg_execute($conn, "my_query", array(""));
*/

foreach ($result as $row) {
    var_dump($row);
}


pg_free_result($result);
pg_close($conn);
