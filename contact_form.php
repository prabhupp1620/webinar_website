<?php

use PHPMailer\PHPMailer\PHPMailer;
use PHPMailer\PHPMailer\SMTP;
use PHPMailer\PHPMailer\Exception;

require 'vendor/autoload.php';

//get data from form
$name = $_POST['name'];
$email = $_POST['email'];
$phone = $_POST['phone'];
$message = $_POST['message'];

if ($_POST['name']) {
    $name = $_POST['name'];
}
if ($_POST['email']) {
    $email = $_POST['email'];
}
if ($_POST['phone']) {
    $phone = $_POST['phone'];
}
if ($_POST['message']) {
    $message = $_POST['message'];
}


// preparing mail content
if ($message) {
    $messagecontent = '
    <html>
      <head>
        <title>MayaPreneur - Dropshipping Mastery</title>
      </head>
      <body style="font-family: Arial, sans-serif; background-color:#f9f9f9; padding:20px;">
        <table width="100%" border="0" cellspacing="0" cellpadding="0" style="max-width:600px; margin:auto; background:#ffffff; border:1px solid #ddd; border-radius:8px;">
          <tr>
            <td style="padding:20px; text-align:center; background:#4CAF50; color:#ffffff; border-radius:8px 8px 0 0;">
              <h2 style="margin:0; font-size:22px;">Contact Enquiries</h2>
            </td>
          </tr>
          <tr>
            <td style="padding:20px; color:#333333;">
              <p><strong>Full Name:</strong> ' . htmlspecialchars($name) . '</p>
              <p><strong>Email Address:</strong> ' . htmlspecialchars($email) . '</p>
              <p><strong>Phone Number:</strong> ' . htmlspecialchars($phone) . '</p>
              <p><strong>Message:</strong><br>' . nl2br(htmlspecialchars($message)) . '</p>
            </td>
          </tr>
        </table>
      </body>
    </html>';
} else {
    $messagecontent = '
    <html>
      <head>
        <title>MayaPreneur - Dropshipping Mastery</title>
      </head>
      <body style="font-family: Arial, sans-serif; background-color:#f9f9f9; padding:20px;">
        <table width="100%" border="0" cellspacing="0" cellpadding="0" style="max-width:600px; margin:auto; background:#ffffff; border:1px solid #ddd; border-radius:8px;">
          <tr>
            <td style="padding:20px; text-align:center; background:#2196F3; color:#ffffff; border-radius:8px 8px 0 0;">
              <h2 style="margin:0; font-size:22px;">Subscription Updates</h2>
            </td>
          </tr>
          <tr>
            <td style="padding:20px; color:#333333;">
              <p><strong>Email Address:</strong> ' . htmlspecialchars($email) . '</p>
              
            </td>
          </tr>
        </table>
      </body>
    </html>';
}


//Create an instance; passing `true` enables exceptions
$mail = new PHPMailer(true);
try {
    //$mail->SMTPDebug = SMTP::DEBUG_SERVER;
    $mail->isSMTP();
    $mail->Host = 'smtp.gmail.com';
    $mail->SMTPAuth = true;
    $mail->Username = 'mayapreneur64@gmail.com';
    $mail->Password = 'jiaeiwnzgqvzkhzr';
    $mail->SMTPSecure = PHPMailer::ENCRYPTION_STARTTLS;
    $mail->Port = 587;

    $mail->setFrom($email, $name);
    $mail->addAddress('mayapreneur64@gmail.com', 'MayaPreneur - Dropshipping Mastery');
    // $mail->addCC('mayapreneur64@gmail.com', 'MayaPreneur – Dropshipping Mastery');
    // $mail->addAddress($email);
    $mail->isHTML(true);
    $mail->Subject = 'MayaPreneur - Dropshipping Mastery';
    $mail->Body = $messagecontent;

    $mail->send();
    header('Location: https://sanidhyaborewells.in/public/MayaPreneur/thank-you.html?status=success&message=' . urlencode('Thank you for contacting us. We will contact you shortly.'));
    exit;
} catch (Exception $e) {
    header('Location: https://sanidhyaborewells.in/public/MayaPreneur/?status=error&message=' . urlencode("Message could not be sent. Mailer Error: {$mail->ErrorInfo}"));
    exit;
}
