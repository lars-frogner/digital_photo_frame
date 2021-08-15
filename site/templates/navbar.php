<nav class="navbar navbar-expand-lg navbar-light bg-light">
  <div class="container-fluid">
    <a class="navbar-brand">Digital fotoramme</a>
    <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbar_entries">
      <span class="navbar-toggler-icon"></span>
    </button>
    <div class="collapse navbar-collapse" id="navbar_entries">
      <ul class="navbar-nav me-auto mb-2 mb-lg-0">
        <li class="nav-item">
          <a id="main_nav_link" class="nav-link<?php echo LOCATION == 'main' ? ' active' : '' ?> disabled" href="main.php">Kontroll</a>
        </li>
        <li class="nav-item">
          <a id="settings_nav_link" class="nav-link<?php echo LOCATION == 'settings' ? ' active' : '' ?> disabled" href="settings.php">Innstillinger</a>
        </li>
        <li class="nav-item">
          <a id="logout_nav_link" class="nav-link disabled" href="logout.php">Logg ut</a>
        </li>
      </ul>
    </div>
  </div>
</nav>
