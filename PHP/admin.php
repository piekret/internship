<?php
    require_once("session.php");

    if (!$_SESSION['is_admin'] || !$_SESSION['logged_in']) {
        header("Location: login.php");
        exit;
    }
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Panel</title>
</head>
<body>
    <h1>Admin Panel</h1>
    <p>Lorem, ipsum dolor sit amet consectetur adipisicing elit. Quas blanditiis, voluptatibus omnis odit maxime doloribus cumque tenetur incidunt obcaecati alias laboriosam, veritatis expedita.</p>

    <p><a href="contact.php">Kontakt / Contact</a></p>
</body>
</html>