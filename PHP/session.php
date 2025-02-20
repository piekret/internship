<?php
    session_start();

    $db = new mysqli("localhost", "root", "", "zad_php");

    if ($db->connect_error) {
        die($mysqli->connect_error);
    }

    $db->set_charset("utf8");
?>