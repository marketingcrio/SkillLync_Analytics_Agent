/*  ============================================================
    CLEANUP: Drop ALL existing prep views
    ------------------------------------------------------------
    Run this FIRST before creating new prep views.

    Order matters — drop dependent views first (downstream),
    then the ones they depend on (upstream).
    ============================================================ */

-- Layer 3: views that depend on other prep views
DROP VIEW IF EXISTS prep.vw_unified_activity_with_source_attribution_V2;
DROP VIEW IF EXISTS prep.vw_unified_activity_with_source_attribution;
DROP VIEW IF EXISTS prep.vw_unified_activity_appended;

-- Layer 2: mid-level views
DROP VIEW IF EXISTS prep.LeadCaptureMessage_Source_Parsed_View;
DROP VIEW IF EXISTS prep.vw_LeadCaptureMessage_Attribution;
DROP VIEW IF EXISTS prep.vw_LeadCaptureMessage_Source_Attribution;
DROP VIEW IF EXISTS prep.vw_LeadCaptureMessage_Source_Attribution_Test;
DROP VIEW IF EXISTS prep.vw_LeadCaptureMessage_Source_Parsed;
DROP VIEW IF EXISTS prep.vw_LeadCaptureMessage_Unified;
DROP VIEW IF EXISTS prep.vw_LeadCaptureMessage_Wide;
DROP VIEW IF EXISTS prep.vw_LeadCaptureMessage_Wide_Limited;
DROP VIEW IF EXISTS prep.vw_LeadCaptureMessage_Wide_Robust;
DROP VIEW IF EXISTS prep.vw_LeadCaptureMessage_Wide_Selected;
DROP VIEW IF EXISTS prep.vw_LeadCaptureMessage_JSON_Only;
DROP VIEW IF EXISTS prep.vw_LeadCaptureMessage_Parsed;

-- Layer 1: base prep views
DROP VIEW IF EXISTS prep.unified_activity;
DROP VIEW IF EXISTS prep.unified_leads;
DROP VIEW IF EXISTS prep.unified_lead_capture_message;
DROP VIEW IF EXISTS prep.vw_LeadAssignmentActivity;

-- Prep tables (if they still exist)
DROP TABLE IF EXISTS prep.LeadCaptureMessage_Source_Parsed;
DROP TABLE IF EXISTS prep.LeadCaptureMessage_Wide;
