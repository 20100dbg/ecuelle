<?php
$json = file_get_contents('queries.json');

$queries = json_decode($json, true);

var_dump($queries);
