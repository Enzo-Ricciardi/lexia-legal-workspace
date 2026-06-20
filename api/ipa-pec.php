<?php
declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');

function respond(array $payload, int $status = 200): never
{
    http_response_code($status);
    echo json_encode($payload, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

function ipaPost(string $endpoint, array $fields): array
{
    $context = stream_context_create([
        'http' => [
            'method' => 'POST',
            'header' => "Content-Type: application/x-www-form-urlencoded\r\n"
                . "User-Agent: LexIA IPA Client/1.0\r\n",
            'content' => http_build_query($fields),
            'timeout' => 20,
            'ignore_errors' => true,
        ],
        'ssl' => [
            'verify_peer' => true,
            'verify_peer_name' => true,
        ],
    ]);
    $raw = @file_get_contents('https://www.indicepa.gov.it/' . $endpoint, false, $context);
    if ($raw === false) {
        throw new RuntimeException('Servizio IPA temporaneamente non raggiungibile.');
    }
    $decoded = json_decode($raw, true);
    if (!is_array($decoded)) {
        throw new RuntimeException('Risposta IPA non valida.');
    }
    $result = $decoded['result'] ?? [];
    if ((int) ($result['cod_err'] ?? -1) !== 0) {
        throw new RuntimeException((string) ($result['desc_err'] ?? 'Errore restituito da IPA.'));
    }
    return is_array($decoded['data'] ?? null) ? $decoded['data'] : [];
}

function words(string $value): array
{
    $normalized = strtolower(iconv('UTF-8', 'ASCII//TRANSLIT//IGNORE', $value) ?: $value);
    $parts = preg_split('/[^a-z0-9]+/', $normalized, -1, PREG_SPLIT_NO_EMPTY) ?: [];
    $ignored = ['di', 'del', 'della', 'delle', 'dei', 'degli', 'la', 'il', 'lo', 'le', 'i', 'un', 'una', 'ufficio'];
    return array_values(array_filter(array_unique($parts), static fn(string $part): bool =>
        strlen($part) >= 3 && !in_array($part, $ignored, true)
    ));
}

function valueOf(array $item, array $names): string
{
    $lower = array_change_key_case($item, CASE_LOWER);
    foreach ($names as $name) {
        $value = $lower[strtolower($name)] ?? null;
        if (is_scalar($value) && trim((string) $value) !== '') {
            return trim((string) $value);
        }
    }
    return '';
}

function normalizePec(array $item, string $fallbackEntity = '', string $fallbackCode = ''): array
{
    return [
        'pec' => valueOf($item, ['pec', 'dom_dig', 'email', 'indirizzo']),
        'ente' => valueOf($item, ['des_amm', 'denominazione', 'des_aoo', 'des_ou']) ?: $fallbackEntity,
        'codice_ipa' => valueOf($item, ['cod_amm', 'codice_ipa']) ?: $fallbackCode,
        'comune' => valueOf($item, ['comune', 'des_comune']),
        'provincia' => valueOf($item, ['provincia', 'sigla_provincia']),
        'data_pubblicazione' => valueOf($item, ['data_pubblicazione', 'data_inizio']),
    ];
}

function ipaRecords(array $data, array $recordKeys): array
{
    $lowerKeys = array_map('strtolower', array_keys(array_change_key_case($data, CASE_LOWER)));
    foreach ($recordKeys as $key) {
        if (in_array(strtolower($key), $lowerKeys, true)) {
            return [$data];
        }
    }

    $records = [];
    foreach ($data as $item) {
        if (!is_array($item)) {
            continue;
        }
        foreach (ipaRecords($item, $recordKeys) as $record) {
            $records[] = $record;
        }
    }
    return $records;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    respond(['ok' => false, 'error' => 'Metodo non consentito.'], 405);
}

$body = json_decode((string) file_get_contents('php://input'), true);
$authId = trim((string) ($body['auth_id'] ?? ''));
$query = trim((string) ($body['query'] ?? ''));
if (!preg_match('/^[A-Za-z0-9_-]{4,64}$/', $authId)) {
    respond(['ok' => false, 'error' => 'AUTH_ID IPA mancante o non valido.'], 422);
}
if (strlen($query) < 3 || strlen($query) > 320) {
    respond(['ok' => false, 'error' => 'Inserisci una denominazione valida.'], 422);
}

try {
    $tokens = words($query);
    $results = [];
    $mode = 'denominazione';

    if (filter_var($query, FILTER_VALIDATE_EMAIL)) {
        $mode = 'pec';
        $items = ipaPost('public-ws/WS13_DOM_DIG.php', [
            'AUTH_ID' => $authId,
            'DOM_DIG' => $query,
        ]);
        foreach (ipaRecords($items, ['pec', 'dom_dig', 'email', 'indirizzo']) as $item) {
            $result = normalizePec($item);
            $result['pec'] = $result['pec'] ?: strtolower($query);
            $result['score'] = 100;
            $results[] = $result;
        }
    } elseif (preg_match('/^\d{11}$/', preg_replace('/\D/', '', $query))) {
        $mode = 'codice fiscale';
        $items = ipaPost('ws/WS23DOMDIGCFServices/api/WS23_DOM_DIG_CF', [
            'AUTH_ID' => $authId,
            'CF' => preg_replace('/\D/', '', $query),
        ]);
        foreach (ipaRecords($items, ['pec', 'dom_dig', 'email', 'indirizzo']) as $item) {
            $result = normalizePec($item);
            $result['score'] = 100;
            $results[] = $result;
        }
    } else {
        $isCode = (bool) preg_match('/^[a-z][a-z0-9_-]{1,19}$/i', $query)
            && !str_contains($query, ' ');
        $isJustice = (bool) preg_match('/\b(tribunale|procura|cassazione|giudice di pace|corte d.appello|unep)\b/i', $query);
        if ($isCode) {
            $mode = 'codice IPA';
            $entities = [['cod_amm' => $query, 'des_amm' => '']];
        } elseif ($isJustice) {
            $entities = [['cod_amm' => 'm_dg', 'des_amm' => 'Ministero della Giustizia']];
        } else {
            $entities = ipaRecords(ipaPost('public-ws/WS16_DES_AMM.php', [
                'AUTH_ID' => $authId,
                'DESCR' => $query,
            ]), ['cod_amm', 'codice_ipa']);
        }

        foreach (array_slice($entities, 0, 12) as $entity) {
            $code = valueOf($entity, ['cod_amm', 'codice_ipa']);
            if ($code === '') {
                continue;
            }
            $entityName = valueOf($entity, ['des_amm', 'denominazione']);
            $pecItems = ipaPost('ws/WS20PECServices/api/WS20_PEC', [
                'AUTH_ID' => $authId,
                'COD_AMM' => $code,
            ]);
            $pecRecords = ipaRecords($pecItems, ['pec', 'dom_dig', 'email', 'indirizzo']);
            foreach ($pecRecords as $item) {
                $result = normalizePec($item, $entityName, $code);
                $haystack = strtolower($result['pec'] . ' ' . $result['ente'] . ' ' . $result['comune']);
                $matches = 0;
                foreach ($tokens as $token) {
                    if (str_contains($haystack, $token)) {
                        $matches++;
                    }
                }
                if (!$isCode && $tokens !== [] && count($pecRecords) > 50 && $matches < count($tokens)) {
                    continue;
                }
                $result['score'] = $isCode ? 100 : $matches;
                $results[] = $result;
            }
        }
    }

    $results = array_values(array_filter($results, static fn(array $result): bool =>
        filter_var($result['pec'] ?? '', FILTER_VALIDATE_EMAIL) !== false
    ));

    usort($results, static fn(array $a, array $b): int => $b['score'] <=> $a['score']);
    $unique = [];
    foreach ($results as $result) {
        $unique[strtolower($result['pec'])] = $result;
    }
    respond([
        'ok' => true,
        'query' => $query,
        'mode' => $mode,
        'source' => 'IndicePA - Agenzia per l’Italia Digitale',
        'results' => array_values(array_slice($unique, 0, 50)),
    ]);
} catch (Throwable $error) {
    respond(['ok' => false, 'error' => $error->getMessage()], 502);
}
