<?php
require_once(dirname(__DIR__) . '/config/settings_config.php');

function line($string) {
  echo $string . "\n";
}

function generateInputs($setting_type, $grouped_setting_values) {
  $settings = getSettings($setting_type);
  $group_names = getSettingGroups($setting_type);
  foreach ($grouped_setting_values as $group => $content) {
    generateGroupStart($group_names[$group]);
    foreach ($content as $setting_name => $initial_value) {
      $setting = $settings[$setting_name];
      if (array_key_exists('values', $setting)) {
        generateSelect($setting, $setting_name, $initial_value);
      } elseif (array_key_exists('range', $setting)) {
        generateRange($setting, $setting_name, $initial_value);
      } elseif (array_key_exists('number', $setting)) {
        generateNumber($setting, $setting_name, $initial_value);
      } elseif (array_key_exists('textarea', $setting)) {
        generateTextarea($setting, $setting_name, $initial_value);
      } else {
        generateCheckbox($setting, $setting_name, $initial_value);
      }
    }
    generateGroupEnd();
  }
}

function generateGroupStart($name) {
  line('<div class="col-md">');
  line("<h2>$name</h2>");
}

function generateGroupEnd() {
  line('</div>');
}

function generateSelect($setting, $setting_name, $initial_value) {
  $id = $setting_name;
  $name = $setting['name'];
  $values = $setting['values'];

  line('<div class="mb-3">');
  line('  <div class="row">');
  line('    <div class="col-10">');
  line("  <label class=\"form-label\" for=\"$id\">$name</label>");
  line("  <select name=\"$setting_name\" class=\"form-select\" id=\"$id\">");
  foreach ($values as $name => $value) {
    $selected = ($value == $initial_value) ? ' selected' : '';
    line("    <option value=\"$value\"$selected>$name</option>");
  }
  line('  </select>');
  line('  </div>');
  line('  </div>');
  line('</div>');
}

function generateRange($setting, $setting_name, $initial_value) {
  $id = $setting_name;
  $value_id = $id . '_value';
  $name = $setting['name'];
  $min = $setting['range']['min'];
  $max = $setting['range']['max'];
  $step = $setting['range']['step'];

  line('<div class="mb-3">');
  line("  <label class=\"form-label\" for=\"$id\">$name</label>");
  line('  <div class="row flex-nowrap">');
  line('    <div class="col-10">');
  line("      <input type=\"range\" name=\"$setting_name\" class=\"form-range\" value=\"$initial_value\" min=\"$min\" max=\"$max\" step=\"$step\" id=\"$id\" oninput=\"$('#' + '$value_id').prop('value', this.value);\">");
  line('    </div>');
  line('    <div class="col-1">');
  line("      <output id=\"$value_id\">$initial_value</output>");
  line('    </div>');
  line('  </div>');
  line('</div>');
}

function generateCheckbox($setting, $setting_name, $initial_value) {
  $id = $setting_name;
  $name = $setting['name'];
  $name_attribute =
    "name=\"$setting_name\"";
  if ($initial_value) {
    $checked = 'checked';
    $hidden_input_name = '';
    $checkbox_name = $name_attribute;
    $checkbox_value = '1';
  } else {
    $checked = '';
    $hidden_input_name =
      $name_attribute;
    $checkbox_name = '';
    $checkbox_value = '0';
  }
  line('<div class="mb-3 form-check">');
  line("  <input type=\"hidden\" $hidden_input_name value=\"0\"><input type=\"checkbox\" class=\"form-check-input\" $checkbox_name value=\"$checkbox_value\" id=\"$id\" onclick=\"if (this.checked) { this.value = 1; this.name = this.previousSibling.name; this.previousSibling.name = ''; } else { this.value = 0; this.previousSibling.name = this.name; this.name = ''; }\"$checked>");
  line("  <label class=\"form-check-label\" for=\"$id\">$name</label>");
  line('</div>');
}

function generateNumber($setting, $setting_name, $initial_value) {
  $id = $setting_name;
  $name = $setting['name'];
  $number = $setting['number'];
  $max = array_key_exists('max', $number) ? (' max="' . $number['max'] . '" style="width: ' . strval(strlen($number['max']) + 2) . 'em;"') : '';
  $min = array_key_exists('min', $number) ? (' min="' . $number['min'] . '" oninput="validity.valid || (value=\'\');"') : '';

  line('<div class="mb-3">');
  line("  <label class=\"form-label\" for=\"$id\">$name</label>");
  line("  <input type=\"number\" name=\"$setting_name\" class=\"form-control\"$max$min value=\"$initial_value\" id=\"$id\"></input>");
  line('</div>');
}

function generateTextarea($setting, $setting_name, $initial_value) {
  $id = $setting_name;
  $name = $setting['name'];
  $textarea = $setting['textarea'];
  $rows = array_key_exists('rows', $textarea) ? (' rows="' . $textarea['rows'] . '"') : '';
  $placeholder = array_key_exists('placeholder', $textarea) ? (' placeholder="' . htmlspecialchars($textarea['placeholder']) . '"') : '';

  line('<div class="mb-3">');
  line("  <label class=\"form-label\" for=\"$id\">$name</label>");
  line("  <textarea name=\"$setting_name\" class=\"form-control\"$rows$placeholder id=\"$id\">$initial_value</textarea>");
  line('</div>');
}

function generateBehavior($setting_type) {
  $disabled_when = getSettingAttributes($setting_type, 'disabled_when');
  $condition_statements = array();
  foreach ($disabled_when as $setting_name => $criteria) {
    foreach ($criteria as $id => $condition) {
      $operator = $condition['operator'];
      $value = $condition['value'];
      $condition_statement = "$('#$id').prop('value') $operator '$value'";
      if (array_key_exists($setting_name, $condition_statements)) {
        $condition_statements[$setting_name] = $condition_statements[$setting_name] . ' || ' . $condition_statement;
      } else {
        $condition_statements[$setting_name] =
          $condition_statement;
      }
    }
  }
  $change_statements = array();
  foreach ($disabled_when as $setting_name => $criteria) {
    $condition_statement = $condition_statements[$setting_name];
    $setter_statement = "$('#$setting_name').prop('disabled', $condition_statement); ";
    foreach ($criteria as $id => $condition) {
      if (array_key_exists($id, $change_statements)) {
        $change_statements[$id] = $change_statements[$id] . $setter_statement;
      } else {
        $change_statements[$id] =
          $setter_statement;
      }
    }
  }
  line('$(function() {');
  foreach ($change_statements as $id => $statement) {
    line("$('#$id').change(function() { $statement });");
    line("$('#$id').change();");
  }
  line('});');
}
