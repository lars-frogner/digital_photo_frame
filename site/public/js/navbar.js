const MAIN_NAV_LINK_ID = 'main_nav_link';
const SETTINGS_NAV_LINK_ID = 'settings_nav_link';
const LOGOUT_NAV_LINK_ID = 'logout_nav_link';

const MAIN_MODAL_BASE_PROPERTIES = { href: 'main.php', header: 'Er du sikker på at du vil forlate siden?', confirm: 'Fortsett', dismiss: 'Avbryt' };
const SETTINGS_MODAL_BASE_PROPERTIES = { href: 'settings.php', header: 'Er du sikker på at du vil forlate siden?', confirm: 'Fortsett', dismiss: 'Avbryt' };
const LOGOUT_MODAL_BASE_PROPERTIES = { href: 'logout.php', header: 'Er du sikker på at du vil logge ut?', confirm: 'Logg ut', dismiss: 'Avbryt' };

$(function () {
    $('.nav-link').on('click', '.disabled', function (event) {
        event.preventDefault();
        return false;
    })
});

function setDisabledForNavbar(isDisabled) {
    if (isDisabled) {
        $('.nav-link').addClass('disabled');
    } else {
        $('.nav-link').removeClass('disabled');
    }
}
