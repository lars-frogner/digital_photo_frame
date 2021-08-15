<?php
require_once(__DIR__ . '/error_config.php');
require_once(__DIR__ . '/config.php');
require_once(__DIR__ . '/env_config.php');

function getModeAttributes($attribute_name, $mode_name = null, $converter = null) {
  global $_CONFIG;
  if (is_null($mode_name)) {
    $attributes = array();
    foreach ($_CONFIG['modes']['current']['values'] as $mode_name => $content) {
      $attribute = $content[$attribute_name];
      $attributes[$mode_name] = is_callable($converter) ? $converter($attribute) : $attribute;
    }
    return $attributes;
  } else {
    $attribute = $_CONFIG['modes']['current']['values'][$mode_name][$attribute_name];
    return is_callable($converter) ? $converter($attribute) : $attribute;
  }
}

function getWaitForRequirement($mode_name) {
  return getModeAttributes('wait_for', $mode_name, function ($wait_for) {
    if (!is_null($wait_for)) {
      $split = explode('=', $wait_for, 2);
      if (empty($split)) {
        dpf_error("Invalid wait_for entry: $wait_for");
      }
      $type = $split[0];
      $content = $split[1];
      switch ($type) {
        case 'file':
          $file_path = getenv($content) ? getenv($content) : $content;
          return array('type' => $type, 'file_path' => $file_path);
        case 'socket':
          $split = explode(':', $content, 2);
          if (empty($split)) {
            $hostname = getenv($content) ? getenv($content) : $content;
            $port = -1;
          } else {
            $hostname = getenv($split[0]) ? getenv($split[0]) : $split[0];
            $port = getenv($split[1]) ? getenv($split[1]) : $split[1];
          }
          return array('type' => $type, 'hostname' => $hostname, 'port' => $port);
        default:
          dpf_error("Invalid wait_for type: $type");
      }
    } else {
      return null;
    }
  });
}

define('MODE_VALUES', getModeAttributes('value'));
define('MODE_NAMES', array_flip(MODE_VALUES));

define('ACTION_OK', 0);
define('ACTION_TIMED_OUT', 1);

$_CONTROL_INFO = $_CONFIG['control'];
define('FILE_QUERY_INTERVAL', intval($_CONTROL_INFO['file_query_interval'] * 1e6)); // In microseconds
define('MODE_SWITCH_TIMEOUT', intval($_CONTROL_INFO['mode_switch_timeout'] * 1e6));

define('SERVER_LOCK_COMMANDS', $_CONTROL_INFO['lock_commands']);
