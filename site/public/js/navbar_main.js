const LOGOUT_MODAL_WARNING_TEXT = 'Enheten står ikke i standby. Den vil fortsette i nåværende modus selv om du logger ut.';

$(function () {
    connectLinkToModal(LOGOUT_NAV_LINK_ID, LOGOUT_MODAL_BASE_PROPERTIES, { text: LOGOUT_MODAL_WARNING_TEXT, showText: () => { return getCurrentMode() != STANDBY_MODE; } });
});
