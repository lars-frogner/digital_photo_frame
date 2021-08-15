<?php
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
ini_set('log_errors', 1);
error_reporting(E_ALL);

function dpf_error($message) {
  error_log('Error: ' . $message);
  exit(1);
}

function dpf_warning($message) {
  error_log('Warning: ' . $message);
}
