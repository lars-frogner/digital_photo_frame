const SETTINGS_MODAL_WARNING_TEXT = 'Merk at du har endringer i innstillingene som ikke er lagret.';
const settingsFormHasChanged = () => { return DETECT_FORM_CHANGES && elementHasChangedSinceCapture(SETTINGS_FORM_ID); };
const MODAL_ADDITIONAL_SETTER = { text: SETTINGS_MODAL_WARNING_TEXT, showText: settingsFormHasChanged };
const LOGOUT_MODAL_WARNING_TEXT = 'Enheten står ikke i standby. Den vil fortsette i nåværende modus selv om du logger ut.';

$(function () {
    if (DETECT_FORM_CHANGES) {
        $('#' + SETTINGS_FORM_ID).submit(function () {
            captureElementState(SETTINGS_FORM_ID);
            return true;
        });
    }
    connectLinkToModal(MAIN_NAV_LINK_ID, Object.assign({}, MAIN_MODAL_BASE_PROPERTIES, { showModal: settingsFormHasChanged }), MODAL_ADDITIONAL_SETTER);
    connectLinkToModal(SETTINGS_NAV_LINK_ID, Object.assign({}, SETTINGS_MODAL_BASE_PROPERTIES, { showModal: settingsFormHasChanged }), MODAL_ADDITIONAL_SETTER);
    connectLinkToModal(LOGOUT_NAV_LINK_ID, LOGOUT_MODAL_BASE_PROPERTIES, [{ text: LOGOUT_MODAL_WARNING_TEXT, showText: () => { return INITIAL_MODE != STANDBY_MODE; } }, MODAL_ADDITIONAL_SETTER]);
    setDisabledForNavbar(false);
});
