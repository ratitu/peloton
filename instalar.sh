#!/bin/bash

echo "Ativando modulo wsgi..."
sudo a2enmod wsgi

echo "Copiando configuracao..."
sudo cp bicicletaria.conf /etc/apache2/sites-available/

echo "Ativando site..."
sudo a2ensite bicicletaria.conf

echo "Reiniciando Apache..."
sudo systemctl restart apache2

echo "Concluido! Acesse http://localhost"