FROM golang:1.24-alpine AS builder

RUN apk add --no-cache git

WORKDIR /build

RUN git clone --depth 1 https://github.com/minio/minio.git .

RUN CGO_ENABLED=0 go build -o /minio .

FROM alpine:latest

RUN apk add --no-cache ca-certificates

COPY --from=builder /minio /usr/bin/minio

VOLUME ["/data"]

EXPOSE 9000 9001

ENTRYPOINT ["/usr/bin/minio"]

CMD ["server", "/data", "--console-address", ":9001"]
