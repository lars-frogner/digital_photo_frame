#!/bin/bash
set -x
set -e

DPF_SERVER_USER=admin
DPF_WEB_USER=www-data
DPF_WEB_GROUP=www-data
DPF_READ_PERMISSIONS=750
DPF_WRITE_PERMISSIONS=770

APACHE_LOG_DIR=/var/log/apache2
DPF_APACHE_LOG_PATH=$APACHE_LOG_DIR/error.log
SERVER_LOG_DIR=/var/log/digital_photo_frame
DPF_SERVER_LOG_PATH=$SERVER_LOG_DIR/error.log

DPF_DIR=$(dirname $(readlink -f $0))
DPF_ENV_DIR=$DPF_DIR/env
DPF_ENV_EXPORTS_PATH=$DPF_ENV_DIR/envvar_exports
DPF_ENV_PATH=$DPF_ENV_DIR/envvars
DPF_SITE_DIR=/var/www/digital_photo_frame
DPF_LINKED_SITE_DIR=$DPF_DIR/site/public
DPF_MODE_LOCK_DIR=$DPF_DIR/control/.lock
DPF_MODE_LOCK_FILE=$DPF_MODE_LOCK_DIR/free

INSTALL_PACKAGES=true
if [[ "$INSTALL_PACKAGES" = true ]]; then
    # Install required Python packages
    pip3 install -r requirements.txt
fi

SETUP_BASH_CONFIG=true
if [[ "$SETUP_BASH_CONFIG" = true ]]; then
    echo -e "source $DPF_ENV_PATH\n" >> ~/.bashrc
    source ~/.bashrc
fi

SETUP_ENV=true
if [[ "$SETUP_ENV" = true ]]; then
    mkdir -p $DPF_ENV_DIR

    touch $DPF_ENV_EXPORTS_PATH
    echo "export DPF_SERVER_USER=$DPF_SERVER_USER" >> $DPF_ENV_EXPORTS_PATH
    echo "export DPF_WEB_USER=$DPF_WEB_USER" >> $DPF_ENV_EXPORTS_PATH
    echo "export DPF_WEB_GROUP=$DPF_WEB_GROUP" >> $DPF_ENV_EXPORTS_PATH
    echo "export DPF_READ_PERMISSIONS=$DPF_READ_PERMISSIONS" >> $DPF_ENV_EXPORTS_PATH
    echo "export DPF_WRITE_PERMISSIONS=$DPF_WRITE_PERMISSIONS" >> $DPF_ENV_EXPORTS_PATH
    echo "export DPF_DIR=$DPF_DIR" >> $DPF_ENV_EXPORTS_PATH
    echo "export DPF_SERVER_LOG_PATH=$DPF_SERVER_LOG_PATH" >> $DPF_ENV_EXPORTS_PATH
    echo "export DPF_MODE_LOCK_FILE=$DPF_MODE_LOCK_FILE" >> $DPF_ENV_EXPORTS_PATH
    echo "export PYTHONPATH=$(sudo -u admin python3 -m site --user-site)" >> $DPF_ENV_EXPORTS_PATH

    # Copy environment variables (without 'export') into environment file for services and PHP
    ENV_VAR_EXPORTS=$(cat $DPF_ENV_EXPORTS_PATH)
    echo "${ENV_VAR_EXPORTS//'export '/}" > $DPF_ENV_PATH
fi

INSTALL_BOOTSTRAP=true
if [[ "$INSTALL_BOOTSTRAP" = true ]]; then
    BOOTSTRAP_VERSION=5.0.2
    if [[ "$BOOTSTRAP_VERSION" = "latest" ]]; then
        DOWNLOAD_URL=$(curl https://api.github.com/repos/twbs/bootstrap/releases/latest | grep browser_download_url | grep dist.zip | cut -d '"' -f 4)
        FILENAME=$(echo $DOWNLOAD_URL | cut -d "/" -f 9)
    else
        FILENAME="bootstrap-${BOOTSTRAP_VERSION}-dist.zip"
        DOWNLOAD_URL="https://github.com/twbs/bootstrap/releases/download/v${BOOTSTRAP_VERSION}/$FILENAME"
    fi
    FILENAME_ROOT="${FILENAME%%.zip}"
    cd /tmp
    wget $DOWNLOAD_URL
    unzip $FILENAME
    mkdir -p $DPF_LINKED_SITE_DIR/library/bootstrap
    mv $FILENAME_ROOT/* $DPF_LINKED_SITE_DIR/library/bootstrap/
    rm  -r $FILENAME $FILENAME_ROOT
    cd -
fi

INSTALL_JQUERY=true
if [[ "$INSTALL_JQUERY" = true ]]; then
    JQUERY_VERSION=3.6.0
    FILENAME=jquery-$JQUERY_VERSION.min.js
    DOWNLOAD_URL=https://code.jquery.com/$FILENAME
    cd /tmp
    wget $DOWNLOAD_URL
    mkdir -p $DPF_LINKED_SITE_DIR/library
    mv $FILENAME $DPF_LINKED_SITE_DIR/library/jquery.min.js
    cd -
fi

SETUP_SERVICES=true
if [[ "$SETUP_SERVICES" = true ]]; then
    UNIT_DIR=/lib/systemd/system
    LINKED_UNIT_DIR=$DPF_DIR/control/services
    SYSTEMCTL=/usr/bin/systemctl

    mkdir -p $LINKED_UNIT_DIR

    STARTUP_SERVICE_FILENAME=dpf_startup.service
    echo "[Unit]
Description=Digital photo frame startup script
After=mysqld.service

[Service]
Type=oneshot
User=$DPF_SERVER_USER
Group=$DPF_WEB_GROUP
EnvironmentFile=$DPF_ENV_PATH
ExecStart=$DPF_DIR/control/startup.sh
StandardError=append:$DPF_SERVER_LOG_PATH

[Install]
WantedBy=multi-user.target" > $LINKED_UNIT_DIR/$STARTUP_SERVICE_FILENAME

    sudo ln -sfn {$LINKED_UNIT_DIR,$UNIT_DIR}/$STARTUP_SERVICE_FILENAME

    sudo systemctl enable $STARTUP_SERVICE_FILENAME

    CMD_ALIAS='Cmnd_Alias DPF_MODES ='

    for SERVICE in standby display
    do
        SERVICE_ROOT_NAME=dpf_$SERVICE
        SERVICE_FILENAME=$SERVICE_ROOT_NAME.service

        echo "[Unit]
Description=Digital photo frame $SERVICE service

[Service]
Type=simple
EnvironmentFile=$DPF_ENV_PATH
ExecStart=$DPF_DIR/control/$SERVICE.sh
StandardError=append:$DPF_SERVER_LOG_PATH" > $LINKED_UNIT_DIR/$SERVICE_FILENAME

        sudo ln -sfn {$LINKED_UNIT_DIR,$UNIT_DIR}/$SERVICE_FILENAME

        CMD_ALIAS+=" $SYSTEMCTL stop $SERVICE_ROOT_NAME, $SYSTEMCTL start $SERVICE_ROOT_NAME, $SYSTEMCTL restart $SERVICE_ROOT_NAME,"
    done

    # Allow users in web group to manage the mode services without providing a password
    echo -e "${CMD_ALIAS%,}\n%$DPF_WEB_GROUP ALL = NOPASSWD: DPF_MODES" | (sudo su -c "EDITOR=\"tee\" visudo -f /etc/sudoers.d/$DPF_WEB_GROUP")
fi

INSTALL_SERVER=true
if [[ "$INSTALL_SERVER" = true ]]; then
    # Ensure permissions are correct in project folder
    sudo chmod -R $DPF_READ_PERMISSIONS $DPF_DIR
    sudo chown -R $DPF_SERVER_USER:$DPF_WEB_GROUP $DPF_DIR

    # Create folders where the group has write permissions
    mkdir -p $DPF_SERVER_ACTION_DIR $DPF_MODE_LOCK_DIR

    # Set write permissions
    sudo chmod $DPF_WRITE_PERMISSIONS $DPF_MODE_LOCK_DIR

    sudo mkdir -p $SERVER_LOG_DIR
    sudo touch $DPF_SERVER_LOG_PATH
    sudo chown $DPF_SERVER_USER:$DPF_WEB_GROUP $DPF_SERVER_LOG_PATH
    sudo chmod $DPF_WRITE_PERMISSIONS $DPF_SERVER_LOG_PATH

    # Link site folder to default Apache site root
    sudo ln -s $DPF_LINKED_SITE_DIR $DPF_SITE_DIR

    # Setup new site
    SITE_NAME=$(basename $DPF_SITE_DIR)
    echo "Alias /digital_photo_frame \"$DPF_SITE_DIR\"

<Directory $DPF_SITE_DIR/>
  AllowOverride All
</Directory>
" | sudo tee /etc/apache2/sites-available/$SITE_NAME.conf
    sudo a2ensite $SITE_NAME
    sudo systemctl restart apache2
fi

INITIALIZE_DATABASE=true
if [[ "$INITIALIZE_DATABASE" = true ]]; then
    $DPF_DIR/site/config/init/init_database.sh
fi
