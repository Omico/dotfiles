#!/usr/bin/env fish

function get_linux_distro
    if test -f /etc/os-release
        set -l os_id (grep "^ID=" /etc/os-release 2>/dev/null | cut -d= -f2 | string trim -c '"')
        if test -n "$os_id"
            echo "$os_id"
            return 0
        end
    end

    if test -f /etc/lsb-release
        set -l distro (grep "^DISTRIB_ID=" /etc/lsb-release 2>/dev/null | cut -d= -f2 | string lower)
        if test -n "$distro"
            echo "$distro"
            return 0
        end
    end

    if test -f /etc/debian_version
        echo "debian"
        return 0
    else if test -f /etc/redhat-release
        set -l release (cat /etc/redhat-release 2>/dev/null | string lower)
        if string match -q "*fedora*" "$release"
            echo "fedora"
        else if string match -q "*centos*" "$release"
            echo "centos"
        else if string match -q "*rhel*" "$release"
            echo "rhel"
        else
            echo "redhat"
        end
        return 0
    else if test -f /etc/arch-release
        echo "arch"
        return 0
    else if test -f /etc/alpine-release
        echo "alpine"
        return 0
    else if test -f /etc/SuSE-release
        echo "opensuse"
        return 0
    end

    return 1
end

set -gx fish_linux_distro (get_linux_distro)

function is_distro
    set -l target_distro (string lower $argv[1])
    test "$fish_linux_distro" = "$target_distro"
end

function is_ubuntu
    is_distro "ubuntu"
end

function is_debian
    is_distro "debian"
end

function is_fedora
    is_distro "fedora"
end

function is_arch
    is_distro "arch"
end

function is_centos
    is_distro "centos"
end

function is_alpine
    is_distro "alpine"
end

function is_opensuse
    is_distro "opensuse"
end
