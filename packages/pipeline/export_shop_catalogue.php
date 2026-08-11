<?php
/**
 * Export the YOYAKU catalogue as JSON, for the DiscoWorld corpus build.
 *
 * Run on the shop host:
 *   sudo -u www-data -- wp --path=/var/www/yoyaku.io/public_html \
 *     eval-file export_shop_catalogue.php > shop_catalogue.json
 *
 * One row per published product carrying `_discogs_release_id` — the join key
 * the rest of the pipeline already uses (artwork cache, by-discogs, corpus
 * `discogs_id`). Products without it cannot be placed in the world and are
 * skipped rather than guessed at.
 *
 * Taxonomy is read through the canonical music taxonomies (rules/82):
 * musicartist / musiclabel / musicstyle. They are the authority for those
 * facts; the product title is not parsed for an artist name.
 *
 * Deliberately absent: price and stock. They change hourly, the corpus is a
 * snapshot, and a stale price shown next to a record is worse than no price.
 * The permalink leads to the page that owns both.
 */

if (!defined('ABSPATH')) {
    // wp eval-file bootstraps WordPress; this only guards direct php invocation.
    fwrite(STDERR, "must run under wp eval-file\n");
    exit(1);
}

global $wpdb;

$rows = $wpdb->get_results(
    "SELECT p.ID AS post_id,
            p.post_title AS title,
            dm.meta_value AS discogs_id,
            sm.meta_value AS sku,
            rd.meta_value AS release_date,
            ry.meta_value AS release_year
     FROM {$wpdb->posts} p
     JOIN {$wpdb->postmeta} dm
       ON dm.post_id = p.ID AND dm.meta_key = '_discogs_release_id' AND dm.meta_value != ''
     LEFT JOIN {$wpdb->postmeta} sm ON sm.post_id = p.ID AND sm.meta_key = '_sku'
     LEFT JOIN {$wpdb->postmeta} rd ON rd.post_id = p.ID AND rd.meta_key = '_release_date'
     LEFT JOIN {$wpdb->postmeta} ry ON ry.post_id = p.ID AND ry.meta_key = '_release_year'
     WHERE p.post_type = 'product' AND p.post_status = 'publish'",
    ARRAY_A
);

/** First term name of a taxonomy, or null. */
$first_term = function ($post_id, $taxonomy) {
    $terms = wp_get_object_terms($post_id, $taxonomy, ['fields' => 'names']);
    if (is_wp_error($terms) || empty($terms)) {
        return null;
    }
    return $terms[0];
};

$all_terms = function ($post_id, $taxonomy) {
    $terms = wp_get_object_terms($post_id, $taxonomy, ['fields' => 'names']);
    return (is_wp_error($terms) || empty($terms)) ? [] : array_values($terms);
};

$out = [];
foreach ($rows as $r) {
    $discogs_id = (int) $r['discogs_id'];
    if ($discogs_id <= 0) {
        continue;
    }

    // The year is thin in the shop on purpose — it is not a field the catalogue
    // maintains. 1,143 products carry _release_date and 70 carry _release_year
    // out of 10,226; the `year` taxonomy is registered but empty. Whatever is
    // absent here stays absent: a release with no year simply does not appear
    // on the timeline, which is honest. Guessing one would place records in
    // the wrong decade.
    $year = null;
    if (!empty($r['release_year']) && ctype_digit((string) $r['release_year'])) {
        $year = (int) $r['release_year'];
    } elseif (!empty($r['release_date'])) {
        $ts = strtotime($r['release_date']);
        if ($ts) {
            $year = (int) date('Y', $ts);
        }
    }

    $out[] = [
        'discogs_id' => $discogs_id,
        'title'      => $r['title'],
        'artist'     => $first_term($r['post_id'], 'musicartist'),
        'label'      => $first_term($r['post_id'], 'musiclabel'),
        'styles'     => $all_terms($r['post_id'], 'musicstyle'),
        'country'    => $first_term($r['post_id'], 'musiccountry'),
        'year'       => $year,
        'sku'        => $r['sku'] ?: null,
        'shop_url'   => get_permalink($r['post_id']),
    ];
}

echo json_encode(['site' => 'yoyaku.io', 'count' => count($out), 'releases' => $out]);
