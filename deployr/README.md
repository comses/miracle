## Dockerfile for DeployR Open

### Version information

This Dockerfile works with DeployR Open 7.4.1

### Installing and Running the Container

```bash
# Build the Image
sudo docker build -t deployr .

# Run the Container
sudo docker run -d -p 7400:7400 deployr
```

In Windows the DeployR server will be available at [http://192.168.99.100:7400/revolution](http://192.168.99.100:7400/revolution) 
In Linux the DeployR server will be availbe at [http://localhost:7400/revolution](http://localhost:7400/revolution)

If you use this with `Docker Toolbox`, uncomment line 5 in `startAll.sh`. Server will be live at `http://192.168.99.100:7400/revolution`

### Default password

* Default admin user is `admin` and password is `changeme`
