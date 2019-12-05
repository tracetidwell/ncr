MySql

Linux
curl -OL https://dev.mysql.com/get/mysql-apt-config_0.8.14-1_all.deb
sudo dpkg -i mysql-apt-config*
    Select "Ok"
sudo apt update
sudo apt install mysql-server -y
    Enter root password: xxxxxx **Remember this!!**
    Select "Use Strong Password Encryption (RECOMMENDED)""

sudo systemctl status mysql.service
sudo mysql_secure_installation
    Enter
    Enter
    y
    y
    y
    y

mysql -u root -p
    Enter root password
    CREATE USER 'newuser'@'localhost' IDENTIFIED BY 'password';
    GRANT ALL PRIVILEGES ON * . * TO 'newuser'@'localhost';
    FLUSH PRIVILEGES;

    source app/database/create_db.sql;
