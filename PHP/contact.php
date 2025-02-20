<?php
    require_once("session.php");

    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
        $to = $_POST['to'];
        $subject = $_POST['subject'];
        $msg = $_POST['msg'];

        $msg2 = "";
        if (mail($to, $subject, $msg)) {
            $msg2 = "Success";
        } else {
            $msg = "Something went wrong";
        }
    }

?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mail Form</title>
</head>
<body>
    <h1>Mail Form</h1>

    <?php if (isset($msg2)) {echo "<p>$msg2</p>";} ?>

    <form method="post">
        <label for="to">To:</label><br>
        <input type="email" name="to" id="to" required><br><br>

        <label for="subject">Subject:</label><br>
        <textarea name="subject" id="subject" required></textarea><br><br>
        
        <label for="msg">Message:</label><br>
        <textarea name="msg" id="msg" required></textarea><br><br>
        
        <input type="submit" value="Enter">
    </form>
</body>
</html>