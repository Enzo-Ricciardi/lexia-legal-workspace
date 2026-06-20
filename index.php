<?php
declare(strict_types=1);

$template = __DIR__ . '/templates/index.html';
if (!is_file($template)) {
    http_response_code(500);
    exit('Interfaccia LexIA non disponibile.');
}

$html = file_get_contents($template);
if ($html === false) {
    http_response_code(500);
    exit('Impossibile leggere il template di LexIA.');
}

$html = str_replace('../static/vendor/pdf.min.js', '/LexIA/static/vendor/pdf.min.js', $html);
$html = str_replace('../static/vendor/mammoth.browser.min.js', '/LexIA/static/vendor/mammoth.browser.min.js', $html);
$html = str_replace('../static/browser-api.js', '/LexIA/static/browser-api.js', $html);
$html = str_replace(
    '<script src="/LexIA/static/vendor/pdf.min.js"></script>',
    '<script>window.LEXIA_PDF_WORKER_URL="/LexIA/static/vendor/pdf.worker.min.js";</script><script src="/LexIA/static/vendor/pdf.min.js"></script>',
    $html
);

header('Content-Type: text/html; charset=UTF-8');
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');
echo $html;
