####################################################################################################
# Step 1: Build the app and plugin
####################################################################################################

FROM rwynn/monstache-builder-cache-rel6:1.0.7 AS build-app

RUN mkdir /app

WORKDIR /app

RUN git clone --depth 1 --branch v6.7.10 https://github.com/rwynn/monstache.git .
    
# where to save the go file
COPY ./plugins/some_cases_plugin.go .

RUN go get github.com/gofrs/uuid

RUN make release

RUN go build -buildmode=plugin -o build/some_cases_plugin.so some_cases_plugin.go
####################################################################################################
# Step 2: Copy output build files to an alpine image
####################################################################################################

FROM rwynn/monstache-alpine:3.15.0 AS final

ENTRYPOINT ["/bin/monstache"]

COPY --from=build-app /app/build/linux-amd64/monstache /bin/monstache
COPY --from=build-app /app/build/some_cases_plugin.so /bin/some_cases_plugin.so
