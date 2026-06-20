<?php
declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['ok' => false, 'error' => 'Metodo non consentito']);
    exit;
}

$payload = json_decode((string) file_get_contents('php://input'), true);
$url = is_array($payload) ? trim((string) ($payload['url'] ?? '')) : '';
$parts = parse_url($url);
$host = strtolower((string) ($parts['host'] ?? ''));

$allowedHosts = [
    'cortedicassazione.it',
    'giustizia.it',
    'normattiva.it',
    'italgiure.giustizia.it',
    'google.com',
    'vertexaisearch.cloud.google.com',
];

$hostAllowed = false;
foreach ($allowedHosts as $allowed) {
    if ($host === $allowed || str_ends_with($host, '.' . $allowed)) {
        $hostAllowed = true;
        break;
    }
}

if (($parts['scheme'] ?? '') !== 'https' || !$hostAllowed) {
    http_response_code(400);
    echo json_encode(['ok' => false, 'error' => 'Dominio della fonte non autorizzato']);
    exit;
}

$context = stream_context_create([
    'http' => [
        'method' => 'HEAD',
        'timeout' => 8,
        'follow_location' => 0,
        'max_redirects' => 0,
        'ignore_errors' => true,
        'user_agent' => 'LexIA Source Verifier/1.0',
    ],
    'ssl' => [
        'verify_peer' => true,
        'verify_peer_name' => true,
    ],
]);

$headers = @get_headers($url, true, $context);
$status = 0;
if (is_array($headers)) {
    foreach ($headers as $key => $value) {
        if (is_int($key) && preg_match('/\s(\d{3})\s/', (string) $value, $match)) {
            $status = (int) $match[1];
        }
    }
    if (isset($headers[0])) {
        $lines = is_array($headers[0]) ? $headers[0] : [$headers[0]];
        foreach ($lines as $line) {
            if (preg_match('/\s(\d{3})\s/', (string) $line, $match)) {
                $status = (int) $match[1];
            }
        }
    }
}

$ok = $status >= 200 && $status < 400;
echo json_encode(['ok' => $ok, 'status' => $status], JSON_UNESCAPED_SLASHES);
