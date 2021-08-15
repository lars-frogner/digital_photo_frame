<?php
require_once(dirname(__DIR__) . '/config/site_config.php');
redirectIfLoggedOut('index.php');

waitForModeLock();
$mode = readCurrentMode($_DATABASE);
define('HIDDEN_STYLE', 'style="display: none;"');
?>

<!DOCTYPE html>
<html>

<head>
  <?php
  require_once(TEMPLATES_PATH . '/head_common.php');
  ?>
</head>

<body>
  <div class="d-flex flex-column min-vh-100 vh-100">
    <header>
      <?php
      require_once(TEMPLATES_PATH . '/navbar.php');
      require_once(TEMPLATES_PATH . '/confirmation_modal.php');
      ?>
    </header>

    <main id="main" class="d-flex flex-column flex-grow-1 justify-content-center overflow-auto">
      <div class="container-fluid h-100">
        <div class="row h-100 align-items-center justify-content-center px-0">

          <div id="mode_content_display" class="col-auto" <?php echo ($mode != MODE_VALUES['display']) ? HIDDEN_STYLE : '' ?>>
            Vise
          </div>

          <div id="mode_content_standby" class="col-auto" <?php echo ($mode != MODE_VALUES['standby']) ? HIDDEN_STYLE : '' ?>>
            Hvilemodus
          </div>

          <div id="mode_content_waiting" class="col-auto" <?php echo HIDDEN_STYLE; ?>>
            <span class="spinner-grow text-dark"></span>
          </div>

          <div id="mode_content_error" class="col-auto" <?php echo HIDDEN_STYLE; ?>>
            <div class="container">
              <div class="row">
                <span id="mode_content_error_message" class="alert alert-danger text-center">Error
                </span>
                <a class=" btn btn-secondary" href="main.php">Forny siden</a>
              </div>
            </div>
          </div>

        </div>
      </div>
    </main>

    <footer class="d-flex flex-grow-0 flex-shrink-1 justify-content-center">
      <div class="btn-group">
        <input type="radio" class="btn-check" name="mode_radio" id="mode_radio_display" autocomplete="off" disabled <?php echo ($mode == MODE_VALUES['display']) ? 'checked' : '' ?> value="<?php echo MODE_VALUES['display'] ?>">
        <label class="btn btn-outline-primary" for="mode_radio_display">Vise</label>

        <input type="radio" class="btn-check" name="mode_radio" id="mode_radio_standby" autocomplete="off" disabled <?php echo ($mode == MODE_VALUES['standby']) ? 'checked' : '' ?> value="<?php echo MODE_VALUES['standby'] ?>">
        <label class="btn btn-outline-primary" for="mode_radio_standby">Hvile</label>
      </div>
    </footer>
  </div>

  <?php
  require_once(TEMPLATES_PATH . '/bootstrap_js.php');
  require_once(TEMPLATES_PATH . '/jquery_js.php');
  ?>

  <script>
    const STANDBY_MODE = <?php echo MODE_VALUES['standby']; ?>;
    const DISPLAY_MODE = <?php echo MODE_VALUES['display']; ?>;
    const INITIAL_MODE = <?php echo $mode; ?>;
  </script>
  <script src="js/confirmation_modal.js"></script>
  <script src="js/navbar.js"></script>
  <script src="js/navbar_main.js"></script>
  <script src="js/main.js"></script>

</body>

</html>
