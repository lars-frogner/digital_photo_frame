<?php
require_once(dirname(__DIR__) . '/config/error_config.php');
require_once(dirname(__DIR__) . '/config/env_config.php');
require_once(dirname(__DIR__) . '/config/database_config.php');
require_once(dirname(__DIR__) . '/config/control_config.php');
require_once(__DIR__ . '/io.php');
require_once(__DIR__ . '/database.php');

function readCurrentMode($database) {
  return readValuesFromTable($database, 'modes', 'current', true);
}

function acquireModeLock() {
  waitForModeLock();
  $output = null;
  $result_code = null;
  exec(ENVVAR_ASSIGNMENT . SERVER_LOCK_COMMANDS['acquire'], $output, $result_code);
  if ($result_code != 0) {
    dpf_error("Lock acquisition command failed with error code $result_code:\n" . join("\n", $output));
  }
}

function releaseModeLock() {
  $output = null;
  $result_code = null;
  exec(ENVVAR_ASSIGNMENT . SERVER_LOCK_COMMANDS['release'], $output, $result_code);
  if ($result_code != 0) {
    dpf_error("Lock release command failed with error code $result_code:\n" . join("\n", $output));
  }
}

function waitForModeLock() {
  $result = waitForFileToExist(getenv('DPF_MODE_LOCK_FILE'), FILE_QUERY_INTERVAL, MODE_SWITCH_TIMEOUT);
  if ($result == ACTION_TIMED_OUT) {
    releaseModeLock();
  }
}

function startMode($mode) {
  $mode_start_command = getModeAttributes('start_command', MODE_NAMES[$mode]);
  if (!is_null($mode_start_command)) {
    $output = null;
    $result_code = null;
    exec($mode_start_command, $output, $result_code);
    if ($result_code != 0) {
      releaseModeLock();
      dpf_error("Request for mode start failed with error code $result_code:\n" . join("\n", $output));
    }
  }
}

function stopMode($mode) {
  $mode_stop_command = getModeAttributes('stop_command', MODE_NAMES[$mode]);
  if (!is_null($mode_stop_command)) {
    $output = null;
    $result_code = null;
    exec($mode_stop_command, $output, $result_code);
    if ($result_code != 0) {
      releaseModeLock();
      dpf_error("Request for mode stop failed with error code $result_code:\n" . join("\n", $output));
    }
  }
}

function restartMode($mode) {
  $mode_restart_command = getModeAttributes('restart_command', MODE_NAMES[$mode]);
  if (!is_null($mode_restart_command)) {
    $output = null;
    $result_code = null;
    exec($mode_restart_command, $output, $result_code);
    if ($result_code != 0) {
      releaseModeLock();
      dpf_error("Request for mode restart failed with error code $result_code:\n" . join("\n", $output));
    }
  }
}

function waitForModeSwitch($database, $new_mode) {
  $elapsed_time = 0;
  while (readCurrentMode($database) != $new_mode) {
    usleep(FILE_QUERY_INTERVAL);
    $elapsed_time += FILE_QUERY_INTERVAL;
    if ($elapsed_time > MODE_SWITCH_TIMEOUT) {
      updateCurrentMode($database, MODE_VALUES['standby']);
      releaseModeLock();
      dpf_error('Request for mode switch timed out');
    }
  }
}

function updateCurrentMode($database, $new_mode) {
  updateValuesInTable($database, 'modes', withPrimaryKey(array('current' => $new_mode)));
}

function waitForFileToExist($file_path, $interval, $timeout) {
  $elapsed_time = 0;
  while (!file_exists($file_path)) {
    usleep($interval);
    $elapsed_time += $interval;
    if ($elapsed_time > $timeout) {
      dpf_warning("Wait for creation of $file_path timed out");
      return ACTION_TIMED_OUT;
    }
  }
  return ACTION_OK;
}

function waitForFileUpdate($file_path, $interval, $timeout) {
  $initial_timestamp = time();
  $elapsed_time = 0;
  while (!file_exists($file_path) || filemtime($file_path) <= $initial_timestamp) {
    usleep($interval);
    $elapsed_time += $interval;
    if ($elapsed_time > $timeout) {
      dpf_warning("Wait for update of $file_path timed out");
      return ACTION_TIMED_OUT;
    }
  }
  return ACTION_OK;
}

function switchMode($database, $new_mode, $skip_if_same = true) {
  $current_mode = readCurrentMode($database);
  if ($current_mode == $new_mode && ($skip_if_same || $current_mode == MODE_VALUES['standby'])) {
    return ACTION_OK;
  }
  acquireModeLock();
  stopMode($current_mode);
  waitForModeSwitch($database, MODE_VALUES['standby']);
  startMode($new_mode);
  waitForModeSwitch($database, $new_mode);
  $requirement = getWaitForRequirement(MODE_NAMES[$new_mode]);
  if (!is_null($requirement)) {
    $type = $requirement['type'];
    switch ($type) {
      case 'file':
        waitForFileUpdate($requirement['file_path'], FILE_QUERY_INTERVAL, MODE_SWITCH_TIMEOUT);
        break;
      default:
        dpf_warning("Unknown wait_for requirement type $type");
        break;
    }
  }
  releaseModeLock();
  return ACTION_OK;
}

function restartCurrentMode($database) {
  switchMode($database, readCurrentMode($database), false);
}
