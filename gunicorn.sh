gunicorn --certfile cert.pem --keyfile key.pem -b 0.0.0.0:8443 mur2:app
