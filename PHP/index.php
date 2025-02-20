<?php
    require_once("session.php");

    if (!$_SESSION['logged_in']) {
        header("Location: login.php");
        exit;
    }

    if ($_SESSION['is_admin']) {
        header("Location: admin.php");
        exit;
    } else {
        header("Location: user.php");
        exit;
    }
?>