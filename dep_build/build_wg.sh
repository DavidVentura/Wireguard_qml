docker buildx build --platform linux/arm64/v8 -t wgaarch64 -f ./Dockerfile_wg .
docker run -v $PWD/wireguard-tools/src:/data amd64 make -j
docker run --platform linux/arm64/v8 -v $PWD/wireguard-tools/src:/data wgaarch64 make -j
