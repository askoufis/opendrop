FROM ubuntu:16.04
MAINTAINER Adam Skoufis "adam.skoufis@gmail.com"

RUN apt-get update \
        && apt-get install -y python2.7 python-pip python-tk cmake build-essential libgtk2.0-dev pkg-config libavcodec-dev libavformat-dev libswscale-dev libqt4-dev libjpeg-dev libjasper-dev libvtk5-qt4-dev libtiff5-dev yasm libqt4-opengl-dev libeigen3-dev libopencore-amrnb-dev libopencore-amrwb-dev libopenexr-dev libtbb-dev libfaac-dev libtheora-dev libvorbis-dev libxvidcore-dev libx264-dev sphinx-common ant libv4l-dev unzip wget \
        && apt-get clean
RUN pip2 install scipy matplotlib numpy pyserial --user
# For python3, install python-pil.imagetk

# Install opencv version 2.4.9
RUN wget http://sourceforge.net/projects/opencvlibrary/files/opencv-unix/2.4.9/opencv-2.4.9.zip \
        && unzip opencv-2.4.9
RUN mkdir build
WORKDIR /build
RUN cmake -D WITH_TBB=ON -D BUILD_NEW_PYTHON_SUPPORT=ON -D WITH_V4L=ON -D INSTALL_C_EXAMPLES=ON -D INSTALL_PYTHON_EXAMPLES=ON -D BUILD_EXAMPLES=ON -D WITH_QT=ON -D WITH_OPENGL=ON -D WITH_VTK=ON /opencv-2.4.9
RUN make && make install

RUN echo '/usr/local/lib' >> /etc/ld.so.conf.d/opencv.conf \
        && ldconfig \
        && echo 'PKG_CONFIG_PATH=$PKG_CONFIG_PATH:/usr/local/lib/pkgconfig' >> /etc/bash.bashrc \
        && echo 'export PKG_CONFIG_PATH' >> /etc/bash.bashrc 

RUN mkdir /app

# Install opendrop
WORKDIR /app
ADD opendrop /app

# ENTRYPOINT ["./run"]
