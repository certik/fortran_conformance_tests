program ieee_binary
    use ieee_arithmetic, only: ieee_support_datatype
    implicit none
    if (.not. ieee_support_datatype(0.0)) stop 77
    if (.not. ieee_support_datatype(0.0d0)) stop 77
    if (radix(0.0) /= 2 .or. digits(0.0) /= 24) stop 77
    if (radix(0.0d0) /= 2 .or. digits(0.0d0) /= 53) stop 77
    if (storage_size(0.0) /= 32 .or. storage_size(0.0d0) /= 64) stop 77
end program
