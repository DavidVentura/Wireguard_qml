docker buildx build --platform linux/armhf/v7 -t wgarmhf -f ./Dockerfile_wg .
docker buildx build --platform linux/arm64/v8 -t wgaarch64 -f ./Dockerfile_wg .
docker build -t wgamd64 -f ./Dockerfile_wg .

docker run -v $PWD/wireguard-tools/src:/data wgamd64 make -j clean wg
cp wireguard-tools/src/wg ../vendored/wg-x86_64

docker run --platform linux/arm64/v8 -v $PWD/wireguard-tools/src:/data wgaarch64 make -j clean wg
cp wireguard-tools/src/wg ../vendored/wg-arm64

docker run --platform linux/armhf/v7 -v $PWD/wireguard-tools/src:/data wgarmhf make -j clean wg
cp wireguard-tools/src/wg ../vendored/wg-arm
