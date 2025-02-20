<?php
    require_once("session.php");

    if ($_SESSION['is_admin'] || !$_SESSION['logged_in']) {
        header("Location: login.php");
        exit;
    }

    if (isset($_GET['lang'])) {
        $lang = $_GET['lang'];
        if (in_array($lang, ['pl', 'en'])) {
            $_SESSION['lang'] = $lang;
        }
    }
    $lang = $_SESSION['lang'] ?? "pl";

    if ($lang === "pl") {
        $main = "Panel użytkownika";
        $contentLabel = "Dodaj treść:";
        $submit  = "Zapisz";
    } else {
        $main = "User panel";
        $contentLabel = "Add content:";
        $submit  = "Save";
    }

    $u_id = $_SESSION['u_id'];

    if ($_SERVER['REQUEST_METHOD'] == "POST" && !empty($_POST['content'])) {
        $content = $_POST['content'];

        $rs = $db->query("SELECT id FROM wysiwyg WHERE user_id = '{$u_id}'");

        if ($rs->num_rows > 0) {
            $db->query("UPDATE wysiwyg SET content = '{$content}' WHERE user_id = '{$u_id}'");
        } else {
            $db->query("INSERT INTO wysiwyg (user_id, content) VALUES ('{$u_id}', '{$content}')");
        }
    }

    $content = "";
    $r = $db->query("SELECT content FROM wysiwyg WHERE user_id = '{$u_id}'")->fetch_row();

    $content = $r[0] ?? "";
?>

<!DOCTYPE html>
<html lang=<?php echo $lang; ?>>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><?php echo $main; ?></title>
    <script src="https://cdn.ckeditor.com/4.16.2/standard/ckeditor.js"></script>
</head>
<body>
    <p>
        <a href="?lang=pl">pl</a> | <a href="?lang=en">en</a>
    </p>

    <h1><?php echo $main; ?></h1>

    <form method="post">
        <label><?php echo $contentLabel; ?></label><br>
        <textarea name="content" id="editor"><?php echo htmlspecialchars($content); ?></textarea>
        <script>
            CKEDITOR.replace('editor');
        </script>
        <br><br>
        <input type="submit" value=<?php echo $submit; ?>>
    </form>
    
    <p><a href="contact.php">Kontakt / Contact</a></p>
</body>
</html>