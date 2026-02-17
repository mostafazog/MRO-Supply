<?php
/**
 * Upload brand logos to PrestaShop img/m/ directory
 * Run this script via: php upload_brand_logos.php
 */

define('_PS_ROOT_DIR_', '/home/hstgr-srv1164617/htdocs/srv1164617.hstgr.cloud');

$source_dir = __DIR__ . '/CORRECT_BRAND_LOGOS';
$target_dir = _PS_ROOT_DIR_ . '/img/m';

echo "==========================================\n";
echo "UPLOADING BRAND LOGOS TO PRESTASHOP\n";
echo "==========================================\n\n";

echo "Source: $source_dir\n";
echo "Target: $target_dir\n\n";

if (!is_dir($source_dir)) {
    die("ERROR: Source directory not found: $source_dir\n");
}

if (!is_dir($target_dir)) {
    die("ERROR: Target directory not found: $target_dir\n");
}

if (!is_writable($target_dir)) {
    die("ERROR: Target directory is not writable: $target_dir\n");
}

$files = glob($source_dir . '/*.jpg');
echo "Found " . count($files) . " logo files to upload\n\n";

$uploaded = 0;
$failed = 0;

foreach ($files as $source_file) {
    $filename = basename($source_file);
    $target_file = $target_dir . '/' . $filename;

    echo "[$filename] ";

    if (copy($source_file, $target_file)) {
        chmod($target_file, 0644);
        echo "✓ Uploaded\n";
        $uploaded++;
    } else {
        echo "✗ FAILED\n";
        $failed++;
    }
}

echo "\n==========================================\n";
echo "SUMMARY:\n";
echo "  ✓ Uploaded: $uploaded logos\n";
echo "  ✗ Failed: $failed logos\n";
echo "==========================================\n";

// Clear PrestaShop cache
echo "\nClearing PrestaShop cache...\n";

$cache_dirs = [
    _PS_ROOT_DIR_ . '/var/cache/prod',
    _PS_ROOT_DIR_ . '/var/cache/dev',
    _PS_ROOT_DIR_ . '/cache/smarty/compile',
    _PS_ROOT_DIR_ . '/cache/smarty/cache',
];

foreach ($cache_dirs as $cache_dir) {
    if (is_dir($cache_dir)) {
        $files = glob($cache_dir . '/*');
        foreach ($files as $file) {
            if (is_file($file)) {
                @unlink($file);
            }
        }
        echo "  ✓ Cleared: $cache_dir\n";
    }
}

echo "\n==========================================\n";
echo "DONE! All logos uploaded and cache cleared.\n";
echo "Visit: https://www.yarinind.com/brands\n";
echo "==========================================\n";
?>
