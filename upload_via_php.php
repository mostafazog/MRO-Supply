<?php
/**
 * REMOTE UPLOADER FOR BRAND LOGOS
 *
 * INSTRUCTIONS:
 * 1. Upload this file to your PrestaShop server root directory
 * 2. Visit: https://www.yarinind.com/upload_via_php.php
 * 3. It will download and install all 36 brand logos automatically
 * 4. Delete this file after use for security
 */

set_time_limit(300);
ini_set('memory_limit', '512M');

define('_PS_ROOT_DIR_', '/home/hstgr-srv1164617/htdocs/srv1164617.hstgr.cloud');

// GitHub raw URLs for logos
$GITHUB_BASE = 'https://raw.githubusercontent.com/mostafazog/MRO-Supply/main/CORRECT_BRAND_LOGOS';

// All 36 brand logos
$LOGOS = [
    1, 2, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228,
    229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242,
    243, 244, 245, 246, 247, 248, 249
];

$TARGET_DIR = _PS_ROOT_DIR_ . '/img/m';

echo "<!DOCTYPE html>
<html>
<head>
    <title>Brand Logos Uploader</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 900px; margin: 50px auto; padding: 20px; }
        .success { color: #2ecc71; }
        .error { color: #e74c3c; }
        .info { color: #3498db; }
        .warning { color: #f39c12; }
        pre { background: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }
        .logo-item { padding: 5px 0; border-bottom: 1px solid #eee; }
        h1 { color: #2c3e50; }
        .summary { background: #ecf0f1; padding: 20px; border-radius: 5px; margin: 20px 0; }
    </style>
</head>
<body>
<h1>🚀 Brand Logos Uploader for PrestaShop</h1>
<hr>";

// Check if target directory exists and is writable
echo "<h2>Step 1: Checking Permissions</h2>";
if (!is_dir($TARGET_DIR)) {
    echo "<p class='error'>✗ ERROR: Target directory does not exist: $TARGET_DIR</p>";
    echo "</body></html>";
    exit;
}

if (!is_writable($TARGET_DIR)) {
    echo "<p class='error'>✗ ERROR: Target directory is not writable: $TARGET_DIR</p>";
    echo "<p class='info'>Run: chmod 755 $TARGET_DIR</p>";
    echo "</body></html>";
    exit;
}

echo "<p class='success'>✓ Target directory is writable: $TARGET_DIR</p>";

// Download and install logos
echo "<h2>Step 2: Downloading and Installing Logos</h2>";
echo "<pre>";

$success_count = 0;
$failed = [];

foreach ($LOGOS as $logo_id) {
    $url = "$GITHUB_BASE/$logo_id.jpg";
    $target_file = "$TARGET_DIR/$logo_id.jpg";

    echo sprintf("[%3d] %-30s ", $logo_id, "$logo_id.jpg");
    flush();

    // Download logo
    $context = stream_context_create([
        'http' => [
            'timeout' => 30,
            'user_agent' => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        ]
    ]);

    $image_data = @file_get_contents($url, false, $context);

    if ($image_data === false) {
        echo "<span class='error'>✗ Download failed</span>\n";
        $failed[] = $logo_id;
        continue;
    }

    // Save logo
    if (file_put_contents($target_file, $image_data) === false) {
        echo "<span class='error'>✗ Save failed</span>\n";
        $failed[] = $logo_id;
        continue;
    }

    // Set permissions
    @chmod($target_file, 0644);

    $size = strlen($image_data);
    echo "<span class='success'>✓ Installed (" . number_format($size/1024, 1) . " KB)</span>\n";
    $success_count++;

    flush();
}

echo "</pre>";

// Summary
echo "<div class='summary'>";
echo "<h2>📊 Upload Summary</h2>";
echo "<p><strong>Total logos:</strong> " . count($LOGOS) . "</p>";
echo "<p class='success'><strong>✓ Successfully installed:</strong> $success_count</p>";

if (!empty($failed)) {
    echo "<p class='error'><strong>✗ Failed:</strong> " . count($failed) . "</p>";
    echo "<p class='warning'>Failed logo IDs: " . implode(', ', $failed) . "</p>";
} else {
    echo "<p class='success'><strong>🎉 All logos uploaded successfully!</strong></p>";
}
echo "</div>";

// Clear cache
echo "<h2>Step 3: Clearing PrestaShop Cache</h2>";
echo "<pre>";

$cache_dirs = [
    _PS_ROOT_DIR_ . '/var/cache/prod',
    _PS_ROOT_DIR_ . '/var/cache/dev',
    _PS_ROOT_DIR_ . '/cache/smarty/compile',
    _PS_ROOT_DIR_ . '/cache/smarty/cache',
];

$cleared = 0;
foreach ($cache_dirs as $cache_dir) {
    if (is_dir($cache_dir)) {
        $files = glob($cache_dir . '/*');
        foreach ($files as $file) {
            if (is_file($file)) {
                @unlink($file);
                $cleared++;
            }
        }
        echo "✓ Cleared: $cache_dir\n";
    }
}

echo "</pre>";
echo "<p class='success'>✓ Cleared $cleared cache files</p>";

// Final instructions
echo "<div class='summary'>";
echo "<h2>✅ UPLOAD COMPLETE!</h2>";
echo "<p><strong>Next Steps:</strong></p>";
echo "<ol>";
echo "<li>Visit your brands page: <a href='https://www.yarinind.com/brands' target='_blank'>https://www.yarinind.com/brands</a></li>";
echo "<li>Check admin panel: <a href='https://www.yarinind.com/admin' target='_blank'>Admin → Catalog → Brands</a></li>";
echo "<li><strong class='error'>DELETE THIS FILE</strong> for security: <code>rm " . __FILE__ . "</code></li>";
echo "</ol>";

echo "<p><strong>Expected Results:</strong></p>";
echo "<ul>";
echo "<li class='success'>✓ 10 brands with REAL logos from MRO Supply (Alemite, Bando, Mitutoyo, etc.)</li>";
echo "<li class='success'>✓ 26 brands with professional text placeholders</li>";
echo "<li class='error'>✗ NO MORE wrong Wikipedia images (bison, people photos, Star Wars blaster, etc.)</li>";
echo "</ul>";
echo "</div>";

echo "</body></html>";
?>
