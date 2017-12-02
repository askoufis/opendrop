#/bin/bash
KEY=$(xauth list  |grep $(hostname) | awk '{ print $3 }' | head -n 1)
DCK_HOST=opendrop
xauth add $DCK_HOST/unix:0 . $KEY

docker run -i -t --rm \
    -e DISPLAY=$DISPLAY \
    -e XAUTHORITY=/tmp/.Xauthority \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v $HOME/.Xauthority:/tmp/.XAuthority \
    -h $DCK_HOST \
    --name opendrop1 \
    askoufis/opendrop:latest \
    /bin/bash
