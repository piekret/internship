<?php
    require_once("session.php");

    if ($_SERVER['REQUEST_METHOD'] == "POST" && isset($_POST["user"]) && isset($_POST["pass"])) {
        $user = $_POST['user'];
        $pass = $_POST['pass'];

        $r = $db->query("SELECT id, password, admin FROM users WHERE username='$user'")->fetch_row();
        $db->close();

        if (isset($r) && hash("sha256", $pass) == $r[1]) {
            $is_admin = $r[2];

            if (!$is_admin) {
                $_SESSION['lang'] = 'pl';
            }

            $_SESSION['logged_in'] = 1;
            $_SESSION['is_admin'] = $is_admin;
            $_SESSION['u_id'] = $r[0];

            header("Location: index.php");
            echo $_SESSION['u_id'];
            exit;
        } else {
            $error = "login failed";
        }
    } else {
        $error = "hej hej siema";
    }
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login</title>
</head>
<body>
    <form action="login.php" method="POST">
        <input type="text" name="user" placeholder="username" required>
        <input type="password" name="pass" placeholder="password" required>
        <input type="submit" value="Enter">
    </form>
</body>
</html>